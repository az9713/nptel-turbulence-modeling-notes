"""Original analytic pressure and homogeneous redistribution figure."""

from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402 (backend/cache setup first)
import numpy as np  # noqa: E402 (backend/cache setup first)

root = Path(__file__).resolve().parents[1]
with plt.rc_context({"font.size": 11, "svg.fonttype": "none"}):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), layout="constrained")
    x = np.linspace(0, 2 * np.pi, 121)
    X, Y = np.meshgrid(x, x)
    q = 0.5 * (np.cos(2 * X) + np.cos(2 * Y))
    image = axes[0].pcolormesh(
        X, Y, q, shading="auto", cmap="RdBu_r", vmin=-1, vmax=1
    )
    axes[0].set(
        xlabel="x (reference length units)",
        ylabel="y (reference length units)",
        title="Analytic pressure fluctuation\namplitude +2 ensemble member",
    )
    fig.colorbar(image, ax=axes[0], label="q prime / reference speed squared")
    k0, eps0, Cs, Ce2 = 0.19, 0.5, 1.8, 1.92
    t = np.linspace(0, 1, 201)
    theta = 1 + (Ce2 - 1) * eps0 / k0 * t
    alpha = theta ** (-(Cs - 1) / (Ce2 - 1))
    for value, label in zip(
        (0.25, 0.09, 0.04), ("streamwise", "normal", "spanwise")
    ):
        fraction = (1 - alpha) / 3 + alpha * value / (2 * k0)
        axes[1].plot(t, fraction, label=label, linewidth=2)
    axes[1].axhline(
        1 / 3, color="#666666", linestyle=":", label="isotropic fraction"
    )
    axes[1].set(
        xlabel="time (s)",
        ylabel="normal variance / (2 k)",
        title=(
            "Homogeneous return to isotropy\n"
            "Rotta model with isotropic destruction"
        ),
    )
    axes[1].legend(fontsize=9)
    axes[1].grid(alpha=0.25)
    for ext in ("svg", "png"):
        fig.savefig(root / f"assets/ch17-pressure-and-return.{ext}", dpi=160)
    plt.close(fig)
