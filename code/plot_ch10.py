"""Plot stipulated covariance diagnostics; requires Matplotlib."""
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
os.environ.update(MPLCONFIGDIR=str(ROOT/'work/cache/matplotlib'),
                  TEMP=str(ROOT/'work/tmp'),TMP=str(ROOT/'work/tmp'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['svg.hashsalt']='turbulence-ch10'
ink,panel='#e7edf0','#10171b'
fig,axes=plt.subplots(1,2,figsize=(8,3.7),layout='constrained')
fig.patch.set_facecolor(panel)
x=[0,1,2]
axes[0].bar([i-.18 for i in x],[.25,.09,.04],width=.34,color='#8cdbce',label='Stipulated covariance')
axes[0].bar([i+.18 for i in x],[.38/3]*3,width=.34,color='#ffc66d',label='Shear-fitted linear model')
axes[0].set(xticks=x,xticklabels=['R₁₁','R₂₂','R₃₃'],
            title='Matching shear misses normal anisotropy',ylabel='Variance (m²/s²)')
axes[1].bar(x,[.38/3-.2,.38/3,.38/3+.2],
            color=['#ff9990','#8cdbce','#8cdbce'])
axes[1].axhline(0,color=ink,lw=1)
axes[1].set(xticks=x,xticklabels=['Minimum','Middle','Maximum'],
            title='Larger viscosity can violate positivity',ylabel='Covariance eigenvalue (m²/s²)')
for ax in axes:
    ax.set_facecolor(panel)
    ax.tick_params(colors=ink,labelsize=9)
    for spine in ax.spines.values(): spine.set_color('#657784')
    for item in (ax.xaxis.label,ax.yaxis.label,ax.title): item.set_color(ink)
    ax.title.set_fontsize(10)
    ax.grid(axis='y',alpha=.15)
axes[0].legend(facecolor=panel,edgecolor='#657784',labelcolor=ink,fontsize=7)
for suffix in ('svg','png'):
    extra={'metadata':{'Date':None}} if suffix=='svg' else {}
    fig.savefig(ROOT/f'assets/ch10-covariance-diagnostics.{suffix}',dpi=160,**extra)
plt.close(fig)
print('Exported stipulated diagonal comparison and negative-eigenvalue diagnostic.')
