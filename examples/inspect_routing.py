import torch
from lapa import LapaModel
from _sample import sample_inputs


def main():
    torch.set_num_threads(1)
    torch.manual_seed(7)
    model = LapaModel().eval()
    inputs, description = sample_inputs(model)
    with torch.no_grad():
        output = model(inputs)
        route = output["route"]
        source = int(route["source"][0].argmax())
        program = int(route["program"][0, source].argmax())
        print({
            "model": "untrained", "note": "API smoke demonstration, not accuracy; no labels scored",
            "input": description,
            "source_shape": list(route["source"].shape),
            "program_shape": list(route["program"].shape),
            "top_source_index": source,
            "top_program_at_source": model.bank.programs[program].to_dict(),
            "source_probability_sum": float(route["source"][0].sum()),
            "route_probability_sum": float(route["prior"][0].sum()),
            "sink_probability": float(route["sink"][0]),
            "final_probability_sum": float(output["final"][0].sum()),
        })


if __name__ == "__main__":
    main()
