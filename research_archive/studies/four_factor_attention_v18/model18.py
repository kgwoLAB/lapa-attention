"""Source/width/endian/base attention in EVERY encoder layer and final readout.

No learned Q/K projections, dot-product similarity, old attention backbone,
program classifier, or learned sign/mask heads are constructed. Values remain
learned. Additive nonlinear source selection is one of the four factors.
"""
import math

import common18
import torch
from torch import nn
from lapa.attention.masks import masked_softmax
from executor18 import FourFactorExecutor, WIDTHS, ENDIANS, BASES


class SourceFactor(nn.Module):
    """Nonlinear additive origin selector, not dot-product Q/K attention."""
    def __init__(self, dim, heads, max_length, rank=12):
        super().__init__()
        self.receiver = nn.Linear(dim, rank, bias=False)
        self.origin = nn.Linear(dim, rank, bias=False)
        self.relative = nn.Linear(4, rank)
        self.energy = nn.Linear(rank, heads, bias=False)
        self.max_length = max_length

    def forward(self, receiver, origin, receiver_positions, observed):
        batch, length, _ = origin.shape
        n = observed.sum(-1).to(origin.dtype).clamp_min(1)
        source_positions = torch.arange(length, device=origin.device, dtype=origin.dtype)
        left, right = self.receiver(receiver), self.origin(origin)
        scores = []
        for start in range(0, receiver.shape[1], 16):
            stop = min(start+16, receiver.shape[1])
            rp = receiver_positions[start:stop][None,:,None].expand(batch,-1,length)
            sp = source_positions[None,None,:].expand_as(rp)
            features = torch.stack((rp/self.max_length, sp/self.max_length,
                                    (sp-rp)/n[:,None,None], (sp-rp).abs()/n[:,None,None]), -1)
            hidden = torch.tanh(left[:,start:stop,None,:]+right[:,None,:,:]+self.relative(features))
            scores.append(self.energy(hidden).permute(0,3,1,2))
        return masked_softmax(torch.cat(scores, dim=2), observed[:,None,None,:])


class FourFactorRoute(nn.Module):
    def __init__(self, dim, heads, max_length, mode, epsilon=.02):
        super().__init__()
        assert mode in ('direct','sink')
        self.heads, self.mode, self.epsilon = heads, mode, epsilon
        self.source_factor = SourceFactor(dim, heads, max_length)
        self.width_factor = nn.Linear(dim, heads*len(WIDTHS))
        self.endian_factor = nn.Linear(dim, heads*len(ENDIANS))
        self.base_factor = nn.Linear(dim, heads*len(BASES))

    def forward(self, receiver, origin, receiver_positions, observed, execution):
        batch, length, _ = origin.shape
        def factor(head, size):
            logits = head(origin).view(batch,length,self.heads,size).permute(0,2,1,3)
            return torch.softmax(logits,-1)*observed[:,None,:,None]
        source = self.source_factor(receiver,origin,receiver_positions,observed)
        width = factor(self.width_factor,len(WIDTHS))
        endian = factor(self.endian_factor,len(ENDIANS))
        base = factor(self.base_factor,len(BASES))
        joint = width[..., :,None,None]*endian[...,None,:,None]*base[...,None,None,:]
        joint = joint*execution.valid[:,None]
        indices = execution.target.flatten(2)[:,None].expand(batch,self.heads,length,-1)
        source_destination = torch.zeros(batch,self.heads,length,length+2,device=origin.device,dtype=origin.dtype)
        source_destination = source_destination.scatter_add(-1,indices,joint.flatten(3))
        # This is probability transport, not a hidden-state similarity product.
        transported = torch.matmul(source,source_destination)
        valid_mass = transported.sum(-1,keepdim=True)
        support = torch.cat((observed,torch.ones(batch,2,device=origin.device,dtype=torch.bool)),-1)
        uniform = support.to(origin.dtype)/support.sum(-1,keepdim=True)
        if self.mode == 'direct':
            normalized = torch.where(valid_mass>0,transported/valid_mass.clamp_min(1e-30),uniform[:,None,None,:])
            destination = (1-self.epsilon)*normalized+self.epsilon*uniform[:,None,None,:]
        else:
            destination = (1-self.epsilon)*transported+(1-(1-self.epsilon)*valid_mass)*uniform[:,None,None,:]
        return dict(source=source,width=width,endian=endian,base=base,
                    destination=destination,valid_mass=valid_mass.squeeze(-1))


class FourFactorBlock(nn.Module):
    def __init__(self, dim, heads, ff_dim, max_length, mode):
        super().__init__()
        self.heads, self.dim = heads, dim
        self.routing = FourFactorRoute(dim,heads,max_length,mode)
        self.value = nn.Linear(dim,dim,bias=False)
        self.output = nn.Linear(dim,dim,bias=False)
        self.norm = nn.LayerNorm(dim)
        self.ff = nn.Sequential(nn.Linear(dim,ff_dim),nn.GELU(),nn.Linear(ff_dim,dim))
        self.ff_norm = nn.LayerNorm(dim)

    def forward(self, hidden, inputs, execution):
        batch, count, dim = hidden.shape
        receiver_positions = torch.arange(-1,count-1,device=hidden.device,dtype=hidden.dtype)
        route = self.routing(hidden,hidden[:,1:],receiver_positions,inputs.observed,execution)
        # END/NULL do not have byte values. For encoder value transport only,
        # their mass stays at the receiver; final readout keeps them separate.
        support = torch.cat((torch.ones(batch,1,device=hidden.device,dtype=torch.bool),inputs.observed),-1)
        for name in ('source','destination'):
            route[name] = route[name]*support[:,None,:,None]
        route['valid_mass'] = route['valid_mass']*support[:,None,:]
        destination = route['destination']
        attention = torch.cat((torch.zeros_like(destination[...,:1]),destination[...,:count-1]),-1)
        special_mass = destination[...,-2:].sum(-1)
        attention = attention + torch.diag_embed(special_mass)
        attention = attention*support[:,None,:,None]
        values = self.value(hidden).view(batch,count,self.heads,dim//self.heads).transpose(1,2)
        mixed = torch.matmul(attention,values).transpose(1,2).reshape(batch,count,dim)
        mask = support[:,:,None]
        hidden = self.norm(hidden+self.output(mixed))*mask
        hidden = self.ff_norm(hidden+self.ff(hidden))*mask
        return hidden,dict(route,attention=attention)


class FourFactorModel(nn.Module):
    def __init__(self, mode='direct', dim=32, heads=4, layers=2, ff_dim=64, max_length=1024, slots=64):
        super().__init__()
        assert mode in ('direct','sink') and dim%heads == 0
        self.config = dict(mode=mode,dim=dim,heads=heads,layers=layers,ff_dim=ff_dim,max_length=max_length,slots=slots)
        self.byte_embedding = nn.Embedding(257,dim)
        self.slot_embedding = nn.Embedding(slots,dim)
        self.task_token = nn.Parameter(torch.empty(dim))
        nn.init.normal_(self.task_token,std=.02)
        self.position = nn.Linear(4,dim,bias=False)
        self.input_norm = nn.LayerNorm(dim)
        self.blocks = nn.ModuleList([FourFactorBlock(dim,heads,ff_dim,max_length,mode) for _ in range(layers)])
        self.readout = FourFactorRoute(dim,heads,max_length,mode)
        self.presence = nn.Linear(dim,1)
        self.executor = FourFactorExecutor()

    def forward(self, inputs, diagnostics=True):
        data, observed = inputs.data, inputs.observed
        assert data.ndim == 2 and observed.shape == data.shape and observed.dtype == torch.bool
        assert data.dtype == torch.long and inputs.slots.dtype == torch.long
        assert ((data>=0)&(data<=255)).all() and (observed.sum(-1)>0).all()
        assert data.shape[1] <= self.config['max_length']
        assert ((inputs.slots>=0)&(inputs.slots<self.config['slots'])).all()
        assert torch.equal(observed,torch.arange(data.shape[1],device=data.device)[None]<observed.sum(-1,keepdim=True))
        batch,length = data.shape
        raw = self.byte_embedding(torch.where(observed,data,torch.full_like(data,256)))
        n = observed.sum(-1,keepdim=True).to(raw.dtype)
        positions = torch.arange(length,device=data.device,dtype=raw.dtype)[None].expand(batch,-1)
        features = torch.stack((positions/self.config['max_length'],positions/n,
                                (n-positions)/n,torch.log1p(n).expand_as(positions)/math.log1p(self.config['max_length'])),-1)
        raw = (raw+self.position(features))*observed[:,:,None]
        task = self.task_token[None]+self.slot_embedding(inputs.slots)
        support = torch.cat((torch.ones(batch,1,device=data.device,dtype=torch.bool),observed),-1)
        hidden = self.input_norm(torch.cat((task[:,None],raw),1))*support[:,:,None]
        execution = self.executor(inputs)
        stages = []
        for block in self.blocks:
            hidden,stage = block(hidden,inputs,execution)
            if diagnostics: stages.append(stage)
        route = self.readout(hidden[:,:1],hidden[:,1:],torch.tensor([-1.],device=data.device),observed,execution)
        return dict(final=route['destination'][:,:,0].mean(1),presence_logits=self.presence(hidden[:,0]).squeeze(-1),
                    source=route['source'][:,:,0].mean(1),width=route['width'].mean(1),
                    endian=route['endian'].mean(1),base=route['base'].mean(1),
                    readout=route,layers=stages)
