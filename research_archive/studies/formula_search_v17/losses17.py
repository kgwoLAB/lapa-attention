"""All On variants keep four nonzero losses; altered supervision is explicit."""
import torch
from torch.nn import functional as F
from lapa.training.losses import joint_loss

def loss(model,output,labels):
    positive=labels.present.bool()
    if model.variant=='off':
        value=-output['final'][positive].gather(1,labels.targets[positive,None]).clamp_min(1e-30).log().mean()
        return value,dict(endpoint=value)
    _,parts=joint_loss(output,labels)
    if model.variant=='axis_direct':
        values=[]
        for axis,ids in model.bank.axis_ids().items():
            logits=output['axis_logits'][axis][positive]
            actual=logits[torch.arange(len(logits),device=logits.device),labels.sources[positive]]
            values.append(F.cross_entropy(actual,ids.to(actual.device)[labels.programs[positive]]))
        parts['program']=4*torch.stack(values).mean()
    if model.variant=='equivalent_program':
        execution=output['route']['execution']
        i=torch.arange(int(positive.sum()),device=positive.device)
        sources=labels.sources[positive]
        valid=execution.valid[positive][i,sources]
        destinations=execution.target[positive][i,sources]
        same=valid&(destinations==labels.targets[positive,None])
        assert same.any(-1).all()
        lp=F.log_softmax(output['program_logits'][positive][i,sources],-1)
        parts['program']=-torch.logsumexp(lp.masked_fill(~same,float('-inf')),-1).mean()
    weighted={k:v*model.loss_weights[k] for k,v in parts.items()}
    assert set(weighted)=={'presence','source','program','endpoint'}
    return sum(weighted.values()),weighted
