"""Advection amplification, statistical partition and hybrid-interface algebra."""
from itertools import product
from math import cos, pi, sin, sqrt, tanh

n,m,cfl=64,3,.5
h=2*pi/n
theta=2*pi*m/n
steps=int(n/cfl)
central_gain=sqrt(1+(cfl*sin(theta))**2)
upwind_gain=sqrt((1-cfl+cfl*cos(theta))**2+(cfl*sin(theta))**2)
print(f"forward Euler centered/upwind amplitude after one crossing: {central_gain**steps:.8f}, {upwind_gain**steps:.8f}")
print(f"leading forward-Euler upwind numerical viscosity at unit speed: {h*(1-cfl)/2:.8f}")
print("centered-space Crank-Nicolson linear-advection amplitude: 1.00000000")

shear,dy,fluct_variance=100.,.002,.04
mean_filter_stress=shear**2*dy**2/12
resolved_k=fluct_variance/2
mean_q=mean_filter_stress/2
true_filtered_k=resolved_k
corrected=resolved_k+mean_q-mean_filter_stress/2
print(f"filtered turbulence energy, naive resolved+SGS, corrected: {true_filtered_k:.10f}, {resolved_k+mean_q:.10f}, {corrected:.10f}")

# Eight equiprobable signs exactly realize this one-point target covariance.
rows=[]
for a,b,c in product((-1.,1.),repeat=3):
    rows.append((.5*a,-.16*a+sqrt(.09-.16**2)*b,.2*c))
means=[sum(row[i] for row in rows)/len(rows) for i in range(3)]
cov=[[sum(row[i]*row[j] for row in rows)/len(rows) for j in range(3)] for i in range(3)]
print(f"synthetic one-point fluctuation mean: {means}")
print(f"synthetic one-point covariance: {cov}")
print(f"synthetic one-point energy: {sum(cov[i][i] for i in range(3))/2:.8f}")
assert abs(cov[0][1]+.08)<1e-14 and abs(cov[1][1]-.09)<1e-14
print(f"energy-feedback multiplier for one illustrative partition .12+.07: {(.12+.07)/.12:.8f}")

cd=.65
for d,grid,fd in ((.01,.02,1.),(.01,.005,1.),(.01,.005,0.),(.05,.005,1.)):
    des=min(d,cd*grid)
    delayed=d-fd*max(0.,d-cd*grid)
    print(f"wall distance={d}, grid length={grid}, fd={fd}: DES length={des:.8f}, shielded length={delayed:.8f}")
for rd in (.01,.1,1.):
    fd=1-tanh((8*rd)**3)
    print(f"shielding rd={rd}: fd={fd:.10f}")
for label,power in (("WM illustrative",1.),("WR high-Re plate",13/7),("homogeneous DNS",9/4),("uniform-cross-plane plate DNS",37/14)):
    print(f"tenfold Reynolds ratio, {label}: point multiplier={10**power:.8f}")
