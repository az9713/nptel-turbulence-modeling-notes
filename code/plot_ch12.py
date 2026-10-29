"""Create an original diagnostic plot; requires optional matplotlib."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[1]
eta = [i/100 for i in range(1001)]
effective = [1.42-x*(1-x/4.38)/(1+.012*x**3) for x in eta]
distance = [5+i/4 for i in range(181)]  # micrometres
step = [(y*1e-6)**2/(6*1.5e-5)*1e6 for y in distance]
with plt.rc_context({"font.size": 11, "svg.fonttype": "none"}):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), layout="constrained")
    axes[0].plot(eta, effective, color="#226f87", linewidth=2)
    axes[0].axhline(1.42, color="#ad5429", linestyle="--", label="uncorrected 1.42")
    axes[0].axvline(4.38, color="#666666", linestyle=":", label="threshold 4.38")
    axes[0].set(xlabel="eta = strain magnitude × turbulent time",
                ylabel="effective epsilon production coefficient",
                title="Strain-dependent source response")
    axes[0].legend(fontsize=9)
    axes[1].plot(distance, step, color="#226f87", linewidth=2)
    axes[1].scatter([10, 20], [1.111111111, 4.444444444], color="#ad5429", zorder=3)
    axes[1].set(xlabel="distance from wall (micrometres)",
                ylabel="isolated explicit-sink bound (microseconds)",
                title="Near-wall time scale\nproportional to distance squared")
    for ax in axes:
        ax.grid(alpha=.25)
    for extension in ("svg", "png"):
        fig.savefig(root / f"assets/ch12-response-and-wall-time.{extension}", dpi=160)
    plt.close(fig)
