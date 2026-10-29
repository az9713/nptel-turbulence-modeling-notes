"""Export the explicitly manufactured local stress ledger; requires Matplotlib."""
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
os.environ.update(MPLCONFIGDIR=str(ROOT/'work/cache/matplotlib'),
                  TEMP=str(ROOT/'work/tmp'),TMP=str(ROOT/'work/tmp'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['svg.hashsalt']='turbulence-ch09'
s=[i/20 for i in range(801)]
m=[1/(1+(x/10)**3) for x in s]
r=[1-value for value in m]
production=[a*b for a,b in zip(m,r)]
ink,panel='#e7edf0','#10171b'
fig,(top,bottom)=plt.subplots(2,1,figsize=(6.6,5),sharex=True,layout='constrained')
fig.patch.set_facecolor(panel)
for ax in (top,bottom):
    ax.set_facecolor(panel)
    ax.tick_params(colors=ink)
    for spine in ax.spines.values(): spine.set_color('#657784')
    ax.grid(alpha=.15)
    for item in (ax.xaxis.label,ax.yaxis.label,ax.title): item.set_color(ink)
top.plot(s,m,color='#ffc66d',lw=2.2,label='Molecular share m')
top.plot(s,r,color='#8cdbce',lw=2.2,label='Turbulent share 1−m')
top.set(ylabel='Fraction of total shear',ylim=(0,1.05),
        title='Manufactured partition — no fitted wall law')
top.yaxis.label.set_color(ink)
top.title.set_color(ink)
top.legend(facecolor=panel,edgecolor='#657784',labelcolor=ink)
bottom.plot(s,production,color='#8cdbce',lw=2.2)
bottom.scatter([10],[.25],color='#ffc66d',zorder=5)
bottom.set(xlim=(0,40),ylim=(0,.27),xlabel='Wall coordinate y⁺',
           ylabel='Normalized production m(1−m)')
bottom.xaxis.label.set_color(ink)
bottom.yaxis.label.set_color(ink)
for suffix in ('svg','png'):
    extra={'metadata':{'Date':None}} if suffix=='svg' else {}
    fig.savefig(ROOT/f'assets/ch09-stress-partition.{suffix}',dpi=160,**extra)
plt.close(fig)
print('Exported manufactured stress fractions and production: peak at y+=10, P+=0.25.')
