import torch
from lapa import LapaModel
from _sample import sample_inputs


def main():
    torch.set_num_threads(1)
    torch.manual_seed(7)
    model = LapaModel().eval()
    inputs, description = sample_inputs(model)
    print({"model": "untrained", "note": "API smoke demonstration, not accuracy",
           "input": description})
    with torch.no_grad():
        for attention in ("sdpa", "rope", "cope", "tape"):
            off = model(inputs, attention=attention, lapa_enabled=False)
            on = model(inputs, attention=attention, lapa_enabled=True)
            assert off["final"] is off["base"] and off["route"] is None
            assert torch.equal(off["base"], on["base"])
            print({"attention": attention, "off_base_exact": torch.equal(off["base"], off["final"]),
                   "base_shared_on_off": torch.equal(off["base"], on["base"]),
                   "on_probability_sum": float(on["final"].sum())})


if __name__ == "__main__":
    main()
