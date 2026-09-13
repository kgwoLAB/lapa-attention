"""Thirty explicit alternatives: attribute QK, execution, fusion, and locators."""
from common17 import VARIANTS,NO_BACKBONE,ATTRIBUTE_VARIANTS
import torch
from torch import nn
from torch.nn import functional as F
from models16 import FormulaModel,encoder_without_retrieval
from lapa.attention.masks import masked_softmax
from lapa.programs.executor import execute
from lapa.routing.pushforward import pushforward
from lapa.routing.fusion import route_prior
from attribute17 import AttributeDestination
from locator17 import SharedSlotQuery,make_encoder
from execution_features17 import ExecutionFeatureScore

ROUTE_ONLY={'route_sink','route_direct','route_joint','axis_direct','smooth_route','soft_joint',
    'valid_mass_route','cnn_shared_route','gru_shared_route','shared_slot_route','execute_score','equivalent_program','bilinear_program'}
ATTRIBUTE=set(ATTRIBUTE_VARIANTS)

class SearchModel(FormulaModel):
    def __init__(self,variant,backbone='tape'):
        assert variant in ('off',)+VARIANTS
        super().__init__('off' if variant=='off' else 'hybrid','tape' if backbone=='none' else backbone)
        self.variant=variant
        self.backbone=backbone
        self.loss_weights={'endpoint':1.} if variant=='off' else dict(presence=1.,source=1.,program=1.,endpoint=1.)
        if variant in ('aux_small','aux_large'):
            for key in ('presence','source','program'):self.loss_weights[key]=.25 if variant=='aux_small' else 4.
        self.native_endpoint_qk=variant not in ROUTE_ONLY|ATTRIBUTE
        self.encoder_qkv=variant not in NO_BACKBONE
        if not self.native_endpoint_qk:
            del self.host.retrieval_query;del self.host.retrieval_key;del self.special_endpoints
        if variant in ('shared_slot_hybrid','shared_slot_route'):
            self.host.query_id_embedding=SharedSlotQuery(self.config)
        if variant in NO_BACKBONE:
            self.host=make_encoder(self.host,self.config,'cnn_shared' if variant.startswith('cnn_') else 'recurrent_shared')
        if variant in ATTRIBUTE:
            self.attribute=AttributeDestination(self.config.dim,self.bank,self.config.heads,self.config.max_length)
        if variant=='execute_score':self.execution_score=ExecutionFeatureScore(self.config.dim,self.bank)
        if variant=='bilinear_program':
            self.interaction_source=nn.Linear(self.config.dim,16,bias=False)
            self.interaction_task=nn.Linear(self.config.dim,16,bias=False)
            self.interaction_program=nn.Parameter(torch.empty(len(self.bank),16))
            nn.init.normal_(self.interaction_program,std=.02)
        if variant in ('mix_learned','power_learned','attr_mix'):
            self.mix_gate=nn.Sequential(nn.Linear(2*self.config.dim+3,self.config.dim),nn.GELU(),nn.Linear(self.config.dim,1))
            nn.init.zeros_(self.mix_gate[-1].weight);nn.init.zeros_(self.mix_gate[-1].bias)

    def forward(self,inputs,*,attention=None,lapa_enabled=None):
        self._validate(inputs)
        if lapa_enabled is not None:assert bool(lapa_enabled)==(self.variant!='off')
        if self.variant in ('off','hybrid'):
            return super().forward(inputs,attention=attention,lapa_enabled=lapa_enabled)
        backbone=attention or self.config.attention
        pos=cope=None;host_logits=None
        if self.variant in NO_BACKBONE:hidden=self.host(inputs)
        elif self.native_endpoint_qk:hidden,host_logits,pos,cope=self.host(inputs,backbone)
        else:hidden,pos=encoder_without_retrieval(self.host,inputs,backbone)
        task,raw=hidden[:,0],hidden[:,1:]
        support=torch.cat((inputs.observed,torch.ones(len(task),2,device=task.device,dtype=torch.bool)),-1)
        uniform=support.to(raw.dtype)/support.sum(-1,keepdim=True)
        latent=self.host.router.latents(raw,inputs.observed)
        axis_logits={axis:head(raw) for axis,head in self.host.router.axis_heads.items()}
        execution=execute(self.bank,inputs.data,inputs.observed)
        if self.variant=='execute_score':
            latent['program_logits']=latent['program_logits']+self.execution_score(inputs,raw,task,latent,execution)
        if self.variant=='bilinear_program':
            h=torch.tanh(self.interaction_source(raw)+self.interaction_task(task)[:,None])
            latent['program_logits']=latent['program_logits']+torch.einsum('bld,pd->blp',h,self.interaction_program)/4
        if self.variant in ('execute_score','bilinear_program'):
            latent['program']=torch.softmax(latent['program_logits'],-1)*inputs.observed[:,:,None]
        unconditioned=latent['source'][:,:,None]*latent['program']
        score=F.log_softmax(latent['source_logits'].masked_fill(~inputs.observed,torch.finfo(raw.dtype).min),-1)[:,:,None]+F.log_softmax(latent['program_logits'],-1)
        if self.variant in ('route_joint','soft_joint'):
            score=latent['source_logits'][:,:,None]+latent['program_logits']
        if self.variant=='soft_joint':score=score/2.
        joint=masked_softmax(score.flatten(1),execution.valid.flatten(1)).reshape_as(score)
        if self.variant=='valid_mass_route':joint=unconditioned*execution.valid
        real=pushforward(execution.target,joint,inputs.data.shape[1]+2)
        route=dict(source=latent['source'],program=latent['program'],joint=joint,execution=execution,
            source_marginal=joint.sum(-1),valid_mass=(unconditioned*execution.valid).sum((1,2)),
            **route_prior(real,support,.2 if self.variant=='smooth_route' else .02))
        route['program_conditional']=joint/route['source_marginal'][:,:,None].clamp_min(1e-30)
        direct=route['prior'];attribute_diagnostics=None
        native_logits=None
        if self.native_endpoint_qk:
            special=self.special_endpoints(task).view(len(task),self.config.heads,2)
            native_logits=torch.cat((host_logits,special),-1)
            base=masked_softmax(native_logits,support[:,None]).mean(1)
        else:base=uniform
        if self.variant in ATTRIBUTE:
            kind='attr_content' if self.variant=='attr_content' else 'attr_distance' if self.variant=='attr_distance' else 'attr_only'
            logits,attribute_diagnostics=self.attribute(inputs,raw,task,latent,axis_logits,execution,kind)
            attribute_base=masked_softmax(logits,support[:,None]).mean(1)
        source_entropy=-(latent['source']*latent['source'].clamp_min(1e-30).log()).sum(-1)
        source_entropy=source_entropy/inputs.observed.sum(-1).to(raw.dtype).clamp_min(2).log()
        program_entropy=-(latent['program']*latent['program'].clamp_min(1e-30).log()).sum(-1)
        program_entropy=(latent['source']*program_entropy).sum(-1)/torch.tensor(float(len(self.bank)),device=raw.device).log()
        if hasattr(self,'mix_gate'):
            selected=torch.einsum('bl,bld->bd',latent['source'],raw)
            gate=self.mix_gate(torch.cat((task,selected,source_entropy[:,None],program_entropy[:,None],route['valid_mass'][:,None]),-1)).sigmoid()
        else:gate=None
        if self.variant in ('route_sink','stopgrad_product','weak_product','aux_small','aux_large','shared_slot_hybrid'):
            route=self.host.router.route(inputs,task,raw,latent,.02)
            if self.variant=='route_sink':final=route['prior']
            else:
                bias=route['bias'].detach() if self.variant=='stopgrad_product' else route['bias']
                strength=.1 if self.variant=='weak_product' else 1.
                final=masked_softmax(native_logits+strength*bias[:,None],support[:,None]).mean(1)
        elif self.variant in ROUTE_ONLY:final=direct
        elif self.variant in ATTRIBUTE:
            if self.variant=='attr_product':final=masked_softmax(logits+route['bias'][:,None],support[:,None]).mean(1)
            elif self.variant=='attr_mix':final=(1-gate)*attribute_base+gate*direct
            else:final=attribute_base
        elif self.variant in ('mix_half','mix_learned','mix_entropy'):
            if self.variant=='mix_half':gate=.5
            if self.variant=='mix_entropy':gate=((1-source_entropy)*(1-program_entropy)*route['valid_mass']).clamp(0,1)[:,None]
            final=(1-gate)*base+gate*direct
        elif self.variant=='power_learned':final=masked_softmax(native_logits+gate[:,None]*route['bias'][:,None],support[:,None]).mean(1)
        else:raise ValueError(self.variant)
        return dict(presence_logits=self.presence(task).squeeze(-1),**latent,axis_logits=axis_logits,
            base=base,final=final,route=route,enabled=True,observed=inputs.observed,
            attention='none' if not self.encoder_qkv else backbone,tape_position=pos,cope_positions=cope,
            variant=self.variant,base_available=self.native_endpoint_qk,
            base_kind='retrieval_qk' if self.native_endpoint_qk else 'uniform_reference_no_native_qk',
            encoder_kind='transformer_qkv' if self.encoder_qkv else 'shared_'+self.host.kind,
            attribute_diagnostics=attribute_diagnostics,gate=gate)
