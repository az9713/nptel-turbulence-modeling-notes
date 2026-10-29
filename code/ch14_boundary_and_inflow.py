"""Limit and input-sensitivity checks; no spatial turbulence solution."""
from math import exp, sqrt

def fmu(rt):
    return exp(-3.4/(1+rt/50)**2)

print(f"bounded damping limit exp(-3.4): {fmu(0):.8f}")
nu,A,Cmu=1.5e-5,.7,.09
eps_wall=2*nu*A
previous=None
for y in (.002,.001,.0005):
    k=A*y*y
    rt=k*k/(nu*eps_wall)
    viscosity=Cmu*fmu(rt)*k*k/eps_wall
    ratio=0 if previous is None else previous/viscosity
    print(f"fixed physical epsilon y={y:.4f}: f_mu={fmu(rt):.8f}, "
          f"nu_t={viscosity:.8e}, previous/current={ratio:.8f}")
    previous=viscosity

# Manufactured k with a higher-order term, not a modeled channel solution.
B=40.
for y in (.002,.001,.0005):
    k=A*y*y+B*y**3
    ratio_estimate=2*nu*k/y**2
    sqrt_gradient=(2*A*y+3*B*y*y)/(2*sqrt(k))
    derivative_estimate=2*nu*sqrt_gradient**2
    print(f"wall estimate y={y:.4f}: ratio={ratio_estimate:.8e}, "
          f"sqrt-gradient={derivative_estimate:.8e}, target={eps_wall:.8e}")

# The wall derivative identity contains cancellation at finite distance.
y=.001
k=A*y*y+B*y**3
kp=2*A*y+3*B*y*y
kpp=2*A+6*B*y
identity=2*nu*((kp/(2*sqrt(k)))**2
              +sqrt(k)*(kpp/(2*sqrt(k))-kp**2/(4*k**1.5)))
print(f"finite-distance nu*k_second identity difference: {abs(nu*kpp-identity):.3e}")

Uref,length=20.,.02
factor_rms=(2/3)**1.5
print(f"inflow coefficients: rms-cube={factor_rms:.8f}, "
      f"Cmu-quarter={Cmu**.25:.8f}, Cmu-three-quarter={Cmu**.75:.8f}")
for intensity in (.01,.05,.1):
    k=1.5*(intensity*Uref)**2
    eps=Cmu**.75*k**1.5/length
    omega=eps/(Cmu*k)
    viscosity=Cmu*k*k/eps
    print(f"inflow I={intensity:.2f}: k={k:.8f}, epsilon={eps:.8f}, "
          f"omega={omega:.8f}, nu_t={viscosity:.8f}, nu_t/nu={viscosity/nu:.8f}")

# Controlled scalar source integration illustrates numerical initialization.
k0,eps0=.19,.5
for dt in (.2,.4):
    euler=k0-dt*eps0
    print(f"initial frozen-sink Euler dt={dt:.1f}: k_next={euler:.8f}")
print(f"hydrostatic normal pressure gradient Pa/m: {1.2*(-9.81):.8f}")
