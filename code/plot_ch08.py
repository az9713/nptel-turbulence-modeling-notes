"""Plot the conditional viscous crossover; requires Matplotlib."""

from pathlib import Path
import os
from math import sqrt

ROOT = Path(__file__).resolve().parents[1]
os.environ.update(
    MPLCONFIGDIR=str(ROOT / "work/cache/matplotlib"),
    TEMP=str(ROOT / "work/tmp"),
    TMP=str(ROOT / "work/tmp"),
)
import matplotlib  # noqa: E402 (backend/cache setup first)

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402 (backend/cache setup first)

plt.rcParams["svg.hashsalt"] = "turbulence-ch08"
Re = 20 / 1.5e-5
aspect = [10 ** (-4 + 3.3 * i / 400) for i in range(401)]
ratio = [1 / (Re * e * e) for e in aspect]
ink, panel = "#e7edf0", "#10171b"
fig, ax = plt.subplots(figsize=(6.6, 4), layout="constrained")
fig.patch.set_facecolor(panel)
ax.set_facecolor(panel)
ax.loglog(
    aspect,
    ratio,
    color="#8cdbce",
    lw=2.5,
    label="Normal viscous / inertial scale",
)
ax.axhline(1, color="#ffc66d", ls="--", label="Comparable scales")
ax.axvline(1 / sqrt(Re), color=ink, ls=":", label="e = 1/√Re")
ax.scatter([0.05], [1 / (Re * 0.05**2)], color="#ffc66d", s=40, zorder=5)
ax.annotate(
    "Selected outer estimate",
    (0.05, 1 / (Re * 0.05**2)),
    xytext=(0.006, 0.015),
    color=ink,
    arrowprops={"arrowstyle": "->", "color": ink},
)
ax.set(
    xlabel="Aspect ratio e = δ/L",
    ylabel="1 / (Re e²)",
    title="Fixed Re = 1.333333 × 10⁶; conditional scale comparison",
)
ax.tick_params(colors=ink, which="both")
for s in ax.spines.values():
    s.set_color("#657784")
for item in (ax.xaxis.label, ax.yaxis.label, ax.title):
    item.set_color(ink)
ax.legend(facecolor=panel, edgecolor="#657784", labelcolor=ink, fontsize=8)
ax.grid(alpha=0.15, which="both")
for suffix in ("svg", "png"):
    extra = {"metadata": {"Date": None}} if suffix == "svg" else {}
    fig.savefig(
        ROOT / f"assets/ch08-viscous-crossover.{suffix}", dpi=160, **extra
    )
plt.close(fig)
print(
    f"Exported crossover figure: e_at_ratio_one={1 / sqrt(Re):.10f}; "
    f"outer_ratio={1 / (Re * 0.05 ** 2):.10f}"
)
