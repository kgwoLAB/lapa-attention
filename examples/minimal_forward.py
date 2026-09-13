import torch
from lapa import LapaConfig, LapaModel
from _sample import sample_inputs


def main():
    torch.set_num_threads(1)
    torch.manual_seed(7)
    model = LapaModel(LapaConfig(attention="tape")).eval()
    inputs, description = sample_inputs(model)
    with torch.no_grad():
        out = model(inputs)
    print({"model": "untrained", "note": "API smoke demonstration, not accuracy",
           "input": description, "attention": out["attention"],
           "final_shape": list(out["final"].shape),
           "probability_sum": float(out["final"].sum()), "programs": len(model.bank)})


if __name__ == "__main__":
    main()
