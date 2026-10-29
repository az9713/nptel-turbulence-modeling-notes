"""Educational low-Mach, calibration and tensor-structure checks; no combustor simulation."""
from math import sqrt

print(f"illustrative Mach at40m/s and sound speed343m/s: {40/343:.8f}")
print(f"constant-pressure ideal-gas density ratio1500K/300K: {300/1500:.8f}")
rho=(1.2,.24); velocity=(10.,50.)
mean=sum(velocity)/2
favre=sum(r*u for r,u in zip(rho,velocity))/sum(rho)
favre_variance=sum(r*(u-favre)**2 for r,u in zip(rho,velocity))/sum(rho)
print(f"two-state Reynolds/Favre velocities: {mean:.8f}, {favre:.8f}")
print(f"two-state Reynolds/Favre variances: {sum((u-mean)**2 for u in velocity)/2:.8f}, {favre_variance:.8f}")
for pr in (.7,1.):
    print(f"turbulent Prandtl={pr}: diffusivity for nu_t .001={.001/pr:.8f}")

R=[[.25,-.08,0.],[-.08,.09,0.],[0.,0.,.04]]
k=sum(R[i][i] for i in range(3))/2
G=100.
nut=-R[0][1]/G
scalar=[[2*k/3 if i==j else (-nut*G if {i,j}=={0,1} else 0.) for j in range(3)] for i in range(3)]
error=sqrt(sum((scalar[i][j]-R[i][j])**2 for i in range(3) for j in range(3)))
print(f"shear-matched scalar viscosity: {nut:.8f}; covariance error norm={error:.8f}")

# A local illustrative nonlinear basis, not a calibrated EASM implementation.
time=.01
S=[[0.,G/2,0.],[G/2,0.,0.],[0.,0.,0.]]
W=[[0.,G/2,0.],[-G/2,0.,0.],[0.,0.,0.]]
def mul(a,b):
    return [[sum(a[i][l]*b[l][j] for l in range(3)) for j in range(3)] for i in range(3)]
SW,WS,SS=mul(S,W),mul(W,S),mul(S,S)
traceSS=sum(SS[i][i] for i in range(3))
b1=2*R[0][1]/(2*k*time*G)
b3=(R[2][2]/(2*k)-1/3)/(-time*time*G*G/6)
b2=((R[0][0]/(2*k)-1/3)-b3*time*time*G*G/12)/(-time*time*G*G/2)
nonlinear=[[2*k*((1/3 if i==j else 0)+b1*time*S[i][j]+b2*time*time*(SW[i][j]-WS[i][j])+b3*time*time*(SS[i][j]-(traceSS/3 if i==j else 0))) for j in range(3)] for i in range(3)]
maxerror=max(abs(nonlinear[i][j]-R[i][j]) for i in range(3) for j in range(3))
print(f"local fitted nonlinear coefficients: {b1:.8f}, {b2:.8f}, {b3:.8f}; maximum reconstruction error={maxerror:.3e}")
assert maxerror<1e-14

# Constant-epsilon1 decay exponent relation from the homogeneous k-epsilon model.
for exponent in (1.19,1.25,1.31):
    print(f"decay exponent m={exponent}: inferred Cepsilon2={1+1/exponent:.8f}")
print(f"baseline Cepsilon2=1.92 implies m={1/(1.92-1):.8f}")
