import torch


def positive_diagnostics(output, labels):
    pos = labels.present.nonzero(as_tuple=True)[0]
    if not len(pos):
        return []
    source, program, target = labels.sources[pos], labels.programs[pos], labels.targets[pos]
    records = []
    for row, s, p, t in zip(pos.tolist(), source.tolist(), program.tolist(), target.tolist()):
        probability = output["final"][row, t].clamp_min(1e-30)
        rec = {"row": row, "nll": float(-probability.log()),
               "hit1": int(output["final"][row].argmax().item() == t),
               "source_p": float(output["source"][row, s]),
               "program_p_true_source": float(output["program"][row, s, p]),
               "final_p": float(probability), "base_p": float(output["base"][row, t])}
        if output["route"] is not None:
            rec["route_p"] = float(output["route"]["prior"][row, t])
            rec["sink_p"] = float(output["route"]["sink"][row])
        records.append(rec)
    return records
