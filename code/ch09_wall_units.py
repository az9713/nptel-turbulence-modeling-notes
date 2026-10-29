"""Wall-unit conversions and manufactured stress partition, not fitted DNS."""
from math import sqrt

rho, nu, tau_wall, outer_delta = 1.2, 1.5e-5, 0.2, 0.05
u_tau = sqrt(tau_wall/rho)
length = nu/u_tau
Re_tau = outer_delta/length
print(f"friction velocity m/s: {u_tau:.8f}")
print(f"viscous length micrometres: {length*1e6:.8f}")
print(f"Re_tau based on stipulated outer thickness: {Re_tau:.6f}")
for y_plus in (1.0, 5.0, 30.0):
    print(f"y+={y_plus:.0f}: distance mm={y_plus*length*1000:.8f}")
print(f"linear wall gradient 1/s: {u_tau**2/nu:.6f}")

def molecular_fraction(s):
    return 1/(1+(s/10)**3)

def integrate(s, n=4000):
    step=s/n
    return step/3*(molecular_fraction(0)+molecular_fraction(s)
        +4*sum(molecular_fraction(step*i) for i in range(1,n,2))
        +2*sum(molecular_fraction(step*i) for i in range(2,n,2)))

for s in (1.0, 5.0, 10.0, 30.0):
    m=molecular_fraction(s)
    r=1-m
    print(f"constructed y+={s:.0f}: U+={integrate(s):.8f}, "
          f"molecular={m:.8f}, turbulent={r:.8f}, P+={r*m:.8f}")
    assert abs(m+r-1)<1e-14 and r*m<=.25+1e-14

# Pressure-driven channel: exact total shear, stipulated local gradient.
gradient, channel_half_height, pressure_gradient, y = 100.0, .02, 10.0, .001
assert abs(pressure_gradient*channel_half_height-tau_wall)<1e-14
total=tau_wall-pressure_gradient*y
molecular=rho*nu*gradient
turbulent=total-molecular
print(f"channel local total Pa: {total:.8f}")
print(f"channel turbulent-only wall estimate Pa: {turbulent:.8f}")
print(f"channel wall estimate relative error: {(turbulent-tau_wall)/tau_wall:.8f}")
for rt in (120.0, Re_tau):
    print(f"heuristic overlap at Re_tau={rt:.3f}: "
          f"30 < y+ < {0.1*rt:.3f}; nonempty={0.1*rt>30}")
