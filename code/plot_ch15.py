"""Original covariance/production diagnostic curves; optional matplotlib."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parents[1]
k,eps,Cmu=.19,.5,.09
base=Cmu*k*k/eps
rates=[i/2 for i in range(401)]
minimum=[2*k/3-2*base*a for a in rates]
safe=[min(base,k/(3*(4/3)**.5*a)) if a else base for a in rates]
corrected=[2*k/3-2*v*a for a,v in zip(rates,safe)]
production=[4*base*a*a for a in rates]
capped=[min(p,10*eps) for p in production]
with plt.rc_context({"font.size":11,"svg.fonttype":"none"}):
    fig,axs=plt.subplots(1,2,figsize=(10,4.2),layout="constrained")
    axs[0].plot(rates,minimum,label="baseline",color="#ad5429")
    axs[0].plot(rates,corrected,label="invariant viscosity cap",color="#226f87")
    axs[0].axhline(0,color="#666666",linestyle=":")
    axs[0].set(xlabel="planar strain rate a (1/s)",
               ylabel="minimum covariance eigenvalue (m²/s²)",
               title="A covariance constraint")
    axs[1].plot(rates,production,label="baseline",color="#ad5429")
    axs[1].plot(rates,capped,label="production cap 10 epsilon",color="#226f87")
    axs[1].set(xlabel="planar strain rate a (1/s)",
               ylabel="energy production (m²/s³)",
               title="A separate scalar source constraint")
    for ax in axs:
        ax.legend(fontsize=9)
        ax.grid(alpha=.25)
    for ext in ("svg","png"):
        fig.savefig(root/f"assets/ch15-covariance-and-source.{ext}",dpi=160)
    plt.close(fig)
