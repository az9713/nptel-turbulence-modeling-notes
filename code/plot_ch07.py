"""Export the exact decay curves; requires Matplotlib, no downloaded data."""

from pathlib import Path
import os
from math import exp

ROOT = Path(__file__).resolve().parents[1]
os.environ.update(
    MPLCONFIGDIR=str(ROOT / "work/cache/matplotlib"),
    TEMP=str(ROOT / "work/tmp"),
    TMP=str(ROOT / "work/tmp"),
)
import matplotlib  # noqa: E402 (backend/cache setup first)

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402 (backend/cache setup first)

plt.rcParams["svg.hashsalt"] = "turbulence-ch07"
ink, panel = "#e7edf0", "#10171b"
x = [i / 100 for i in range(401)]
fig, ax = plt.subplots(figsize=(6.6, 3.8), layout="constrained")
fig.patch.set_facecolor(panel)
ax.set_facecolor(panel)
ax.plot(
    x,
    [exp(-q / 2) for q in x],
    color="#ffc66d",
    lw=2.5,
    label="Velocity amplitude A/a",
)
ax.plot(
    x, [exp(-q) for q in x], color="#8cdbce", lw=2.5, label="Energy k/k(0)"
)
ax.axhline(0.5, color=ink, ls=":", lw=1)
ax.set(
    xlabel="Dimensionless time 4νκ²t",
    ylabel="Normalized value",
    xlim=(0, 4),
    ylim=(0, 1.05),
    title="Exact periodic decay — no turbulent dataset",
)
ax.tick_params(colors=ink)
for s in ax.spines.values():
    s.set_color("#657784")
for item in (ax.xaxis.label, ax.yaxis.label, ax.title):
    item.set_color(ink)
ax.legend(facecolor=panel, edgecolor="#657784", labelcolor=ink)
ax.grid(alpha=0.15)
for suffix in ("svg", "png"):
    extra = {"metadata": {"Date": None}} if suffix == "svg" else {}
    fig.savefig(ROOT / f"assets/ch07-energy-decay.{suffix}", dpi=160, **extra)
plt.close(fig)
print(
    "Exported assets/ch07-energy-decay.svg and .png from exact "
    "exponential formulas."
)
