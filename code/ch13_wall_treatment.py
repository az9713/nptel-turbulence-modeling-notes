"""Restricted wall-law inference and smooth-wall limiting checks."""
from math import exp, log, sqrt

nu,rho,kappa,B,Cmu=1.5e-5,1.2,.41,5.2,.09
E=exp(kappa*B)
print(f"logarithm factor E for B=5.2: {E:.8f}")
print(f"B implied by lecture illustrative E=9: {log(9)/kappa:.8f}")

def infer_friction(speed,distance):
    """Positive root on the increasing branch E*y*u/nu >= 1."""
    assert speed>0 and distance>0
    lower=nu/(E*distance)
    upper=max(speed,2*lower)
    def residual(value):
        return value*log(E*distance*value/nu)/kappa-speed
    while residual(upper)<0:
        upper*=2
    for _ in range(80):
        middle=(lower+upper)/2
        if residual(middle)>0:
            upper=middle
        else:
            lower=middle
    value=(lower+upper)/2
    return value,residual(value)

speed,distance=8.,.002
ut,residual=infer_friction(speed,distance)
yp=distance*ut/nu
kp=ut**2/sqrt(Cmu)
ep=ut**3/(kappa*distance)
omega=ep/(Cmu*kp)
effective_viscosity=ut**2*distance/speed
print(f"inferred friction m/s: {ut:.8f}; residual m/s: {residual:.3e}")
print(f"inferred y-plus: {yp:.8f}; wall stress Pa: {rho*ut**2:.8f}")
print(f"equilibrium k, epsilon, omega SI: {kp:.8f}, {ep:.8f}, {omega:.8f}")
print(f"effective wall-face viscosity m2/s: {effective_viscosity:.8f}")
print(f"wall-face turbulent adjustment m2/s: {effective_viscosity-nu:.8f}")
assert abs(residual)<1e-12 and 30<yp<100

# Generate exact log samples, then move the point into the viscous region.
known=.4
for yplus in (1.,50.):
    distance=yplus*nu/known
    sample=known*(yplus if yplus==1 else log(E*yplus)/kappa)
    inferred,_=infer_friction(sample,distance)
    print(f"manufactured y-plus={yplus:.0f}: recovered u_tau={inferred:.8f}, "
          f"relative error={(inferred/known-1):.8f}")

for trial in (.2,.4,.8):
    print(f"fixed first distance2mm with u_tau={trial:.1f}: y-plus={.002*trial/nu:.8f}")

# Kinematic, divergence-free ensemble near a flat no-slip wall.
# u'=-a*y*cos(x), v'=-a*y^2*sin(x)/2, w'=c*y.
# a,c are independent equiprobable +/-1; zero means, not an NS solution.
for y in (.1,.05,.025):
    x=1.
    from math import cos, sin
    R11=y*y*cos(x)**2
    R22=y**4*sin(x)**2/4
    R33=y*y
    energy=(R11+R22+R33)/2
    R12=y**3*cos(x)*sin(x)/2
    print(f"kinematic y={y:.3f}: R22/(2k)={R22/(2*energy):.8f}, "
          f"R12/y^3={R12/y**3:.8f}")

# Finite physical dissipation and molecular diffusion at the wall.
A=.7
eps_wall=2*nu*A
print(f"k=A*y^2 wall epsilon and molecular diffusion: {eps_wall:.8e}, {2*nu*A:.8e}")
print(f"bare k-epsilon nu_t/y^4 coefficient: {Cmu*A*A/eps_wall:.8f}")
