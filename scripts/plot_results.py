"""Matplotlib PNG/SVG and Markdown table from actual evaluation JSON files."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCOPES = ("dns", "modbus", "tls", "smb2", "macro")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    cohort = None
    for path in args.metrics:
        data = json.loads(path.read_text())
        if data.get("status") != "COMPLETE_SELECTED_COHORT":
            raise ValueError(f"not a completed selected-cohort evaluation: {path}")
        identity = (data["data_sha256"], data["messages"], data["fields"], data["partial_selection"])
        if cohort is None:
            cohort = identity
        if identity != cohort:
            raise ValueError("refuse to combine different selected evaluation cohorts")
        if data.get("field_score_role", "primary") != "primary":
            raise ValueError("endpoint-only training's unsupervised presence head is not a primary field-F1 baseline")
        cfg = data["config"]
        enabled = cfg["lapa_enabled"]
        meta = data.get("checkpoint_metadata", {})
        seed = meta.get("seed")
        label = {"sdpa": "SDPA", "rope": "RoPE", "cope": "CoPE*", "tape": "TAPE*"}[cfg["attention"]]
        label += " / LAPA " + ("on" if enabled else "off")
        if seed is not None:
            label += f" / seed {seed}"
        rows.append({"label": label, "enabled": enabled, "values":
                     {**{p: data["protocols"].get(p, {}).get("f1") for p in SCOPES[:4]},
                      "macro": data.get("protocol_macro_field_f1")}, "path": str(path), "steps": meta.get("steps")})
    args.output.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "svg.fonttype": "none",
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 5, figsize=(15, max(4.3, 2.6 + .45 * len(rows))), sharey=True)
    fig.subplots_adjust(left=.26, right=.985, top=.73, bottom=.30, wspace=.16)
    for axis, scope in zip(axes, SCOPES):
        axis.set_xlim(-.025, 1.55)
        axis.set_ylim(len(rows) - .4, -.6)
        axis.set_yticks(range(len(rows)), [r["label"] for r in rows])
        axis.set_xticks([0, .5, 1])
        axis.set_xlabel("Exact typed-span F1")
        axis.set_title(scope.upper() if scope != "macro" else "Protocol macro")
        axis.spines["left"].set_visible(False)
        axis.spines["bottom"].set_bounds(0, 1)
        axis.tick_params(axis="y", length=0, pad=10)
        axis.grid(axis="x", color="#e3e6e8", linewidth=.6)
        axis.set_axisbelow(True)
        for i, row in enumerate(rows):
            value = row["values"][scope]
            color = "#087f8c" if row["enabled"] else "#82909d"
            if value is None:
                axis.axhspan(i - .25, i + .25, color="#f0f1f2")
                axis.text(.06, i, "Not evaluated", va="center", fontsize=8)
                text = "NA"
            else:
                axis.barh(i, value, height=.36, color=color)
                if value == 0:
                    axis.plot(0, i, "o", color=color, ms=3)
                text = f"{value:.4f}"
            axis.text(1.53, i, text, ha="right", va="center", fontsize=9)
    fig.suptitle("LAPA package: selected evaluation runs", y=.96, fontsize=15)
    fig.text(.5, .86, f"{cohort[1]} messages / {cohort[2]} fields | Stored per-run values; no inferred confidence intervals", ha="center")
    foot = "Single-run measurements, not the historical ten-seed results. NA is not zero. CoPE*/TAPE*: compact native-v4 ports."
    if cohort[3]:
        foot += "\nCapped evaluation subset: functional smoke only; missing protocols have no macro."
    if any(r["steps"] is not None and r["steps"] < 600 for r in rows):
        foot += "\nShort training runs are smoke checks, not completed research comparisons."
    fig.text(.035, .08, foot, fontsize=8.5, va="bottom", linespacing=1.5)
    for extension in ("png", "svg"):
        fig.savefig(args.output / f"field_f1.{extension}", dpi=300)
    plt.close(fig)
    lines = ["# Selected evaluation runs", "", foot.replace("\n", " "), "",
             "| Condition | DNS | Modbus | TLS | SMB2 | Macro |", "|---|---:|---:|---:|---:|---:|"]
    for row in rows:
        lines.append("| " + row["label"] + " | " + " | ".join("NA" if row["values"][p] is None else f"{row['values'][p]:.4f}" for p in SCOPES) + " |")
    (args.output / "TABLES.md").write_text("\n".join(lines) + "\n")
    (args.output / "SOURCES.json").write_text(json.dumps({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in args.metrics}, indent=2) + "\n")
    print(args.output / "field_f1.png")


if __name__ == "__main__":
    main()
