"""Off: endpoint only. Every On: presence+source+program+endpoint, weights1."""
import torch
from torch.nn import functional as F
from lapa.training.losses import joint_loss

AXIS_VARIANTS=('route_axis','route_joint','cnn_joint')

def formula_loss(model, output, labels):
    positive=labels.present.bool()
    if model.variant=='off':
        assert output['route'] is None
        p=output['final'][positive].gather(1, labels.targets[positive,None]).clamp_min(1e-30)
        value=-p.log().mean()
        return value, {'endpoint':value}
    total,parts=joint_loss(output,labels)
    if model.variant in AXIS_VARIANTS and positive.any():
        axis_loss=[]
        for axis,ids in model.bank.axis_ids().items():
            logits=output['axis_logits'][axis][positive]
            logits=logits[torch.arange(len(logits),device=logits.device),labels.sources[positive]]
            target=ids.to(logits.device)[labels.programs[positive]]
            axis_loss.append(F.cross_entropy(logits,target))
        replacement=torch.stack(axis_loss).mean()
        total=total-parts['program']+replacement
        parts['program']=replacement
    assert set(parts)=={'presence','source','program','endpoint'}
    return total,parts
