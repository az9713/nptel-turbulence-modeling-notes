"""Regenerate the analytic dissipation figure under assets/; requires Matplotlib."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR'] = str(ROOT / 'work/cache/matplotlib')
os.environ['TEMP'] = str(ROOT / 'work/tmp')
os.environ['TMP'] = str(ROOT / 'work/tmp')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from math import cos, pi

plt.rcParams['svg.hashsalt'] = 'turbulence-ch05'
ink, panel, accent = '#e7edf0', '#10171b', '#8cdbce'
x = [pi * i / 400 for i in range(401)]
physical = [2 * cos(value)**2 for value in x]
fig, ax = plt.subplots(figsize=(6.6, 3.8), layout='constrained')
fig.patch.set_facecolor(panel)
ax.set_facecolor(panel)
ax.plot(x, physical, color=accent, linewidth=2.5,
        label='Physical dissipation')
ax.axhline(1, color='#ffc66d', linestyle='--', linewidth=2,
           label='Pseudo-dissipation')
ax.set(xlim=(0, pi), ylim=(-.08, 2.15),
       xticks=[0, pi / 4, pi / 2, 3 * pi / 4, pi],
       xticklabels=['0', 'π/4', 'π/2', '3π/4', 'π'],
       xlabel='κy (dimensionless)',
       ylabel='Rate / (ν a² κ²)',
       title='Analytic phase field — no measured data')
ax.tick_params(colors=ink)
for spine in ax.spines.values():
    spine.set_color('#657784')
for item in [ax.xaxis.label, ax.yaxis.label, ax.title]:
    item.set_color(ink)
legend = ax.legend(facecolor=panel, edgecolor='#657784', labelcolor=ink)
ax.grid(alpha=.15)
(ROOT / 'assets').mkdir(exist_ok=True)
for suffix in ['svg', 'png']:
    kwargs = {'metadata': {'Date': None}} if suffix == 'svg' else {}
    fig.savefig(ROOT / f'assets/ch05-dissipation.{suffix}', dpi=160, **kwargs)
plt.close(fig)
print(json.dumps({'assets': ['assets/ch05-dissipation.svg',
                            'assets/ch05-dissipation.png'],
                  'landmarks': [physical[i] for i in [0, 100, 200, 300, 400]],
                  'scope': 'Original analytic figure, not measured or DNS data'}))
