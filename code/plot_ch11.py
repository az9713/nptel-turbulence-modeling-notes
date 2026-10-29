"""Plot the exact calibration algebra, not experimental observations."""

from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
os.environ.update(
    MPLCONFIGDIR=str(ROOT / "work/cache/matplotlib"),
    TEMP=str(ROOT / "work/tmp"),
    TMP=str(ROOT / "work/tmp"),
)
import matplotlib  # noqa: E402 (backend/cache setup first)

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402 (backend/cache setup first)

plt.rcParams["svg.hashsalt"] = "turbulence-ch11"
m = [1 + i / 500 for i in range(251)]
ink, panel = "#e7edf0", "#10171b"
fig, ax = plt.subplots(figsize=(6.6, 3.8), layout="constrained")
fig.patch.set_facecolor(panel)
ax.set_facecolor(panel)
ax.axvspan(
    1.19, 1.31, color="#8cdbce", alpha=0.15, label="Caption exponent interval"
)
ax.plot(
    m,
    [1 + 1 / q for q in m],
    color="#8cdbce",
    lw=2.5,
    label="Derived C₂ = 1 + 1/m",
)
ax.axhline(
    1.92, color="#ffc66d", ls="--", label="Documented baseline C₂ = 1.92"
)
ax.scatter(
    [1.25, 1 / 0.92], [1.8, 1.92], color=["#8cdbce", "#ffc66d"], zorder=5
)
ax.set(
    xlabel="Decay exponent m",
    ylabel="Destruction coefficient C₂",
    xlim=(1, 1.5),
    ylim=(1.65, 2.02),
    title="Caption arithmetic versus baseline choice — no new data fit",
)
ax.tick_params(colors=ink)
for s in ax.spines.values():
    s.set_color("#657784")
for item in (ax.xaxis.label, ax.yaxis.label, ax.title):
    item.set_color(ink)
ax.legend(facecolor=panel, edgecolor="#657784", labelcolor=ink, fontsize=8)
ax.grid(alpha=0.15)
for suffix in ("svg", "png"):
    extra = {"metadata": {"Date": None}} if suffix == "svg" else {}
    fig.savefig(
        ROOT / f"assets/ch11-decay-calibration.{suffix}", dpi=160, **extra
    )
plt.close(fig)
print(
    "Exported exact calibration relation: m=1.25 gives1.8; C2=1.92 "
    "gives m=1.08695652."
)
