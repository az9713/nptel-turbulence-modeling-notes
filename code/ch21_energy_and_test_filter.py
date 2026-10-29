"""Wall variants, homogeneous SGS energy and exact two-filter identity."""
from math import atanh, exp, sin, cos, pi, sqrt, tanh

nu, ut, y, delta, cs, shear, kappa = 1.5e-5, .5, .0001, .002, .1, 100., .41
yp = ut*y/nu
f = 1-exp(-yp/26)
base = (cs*delta)**2*shear
print(f"wall coordinate and damping factor: {yp:.8f}, {f:.8f}")
print(f"nu_s variants direct damping, length damping: {f*base:.10e}, {f*f*base:.10e}")
lecture_l = cs*min(delta,kappa*y)
mixing_l = min(cs*delta,kappa*y)
print(f"wall-limited lengths lecture-Delta and mixing-length m: {lecture_l:.10e}, {mixing_l:.10e}")
print(f"corresponding nu_s: {lecture_l**2*shear:.10e}, {mixing_l**2*shear:.10e}")

ck, ce, q0, end = .094, 1., .0001, .1
qeq = ck/ce*delta**2*shear**2
req = sqrt(qeq)
rate = sqrt(ck*ce)*abs(shear)/2
exact = (req*tanh(rate*end+atanh(sqrt(q0)/req)))**2
print(f"fixed-shear SGS energy equilibrium: {qeq:.10f}")
print(f"equivalent equilibrium Cs: {ck**.75/ce**.25:.8f}")
def rhs(q):
    return ck*delta*sqrt(q)*shear**2-ce*q**1.5/delta
errors=[]
for steps in (20,40):
    q, h = q0,end/steps
    for _ in range(steps):
        a=rhs(q); b=rhs(q+h*a/2); c=rhs(q+h*b/2); d=rhs(q+h*c)
        q+=h*(a+2*b+2*c+d)/6
    errors.append(abs(q-exact))
    print(f"SGS energy RK4 steps={steps}: q={q:.10f}, error={errors[-1]:.8e}")
print(f"SGS energy RK4 refinement ratio: {errors[0]/errors[1]:.8f}")
assert errors[0]/errors[1] > 12

tdecay=.05
qdecay = (qeq**-.5+ce*tdecay/(2*delta))**-2
print(f"energy after shear-off .05s: {qdecay:.10f}; retained nu_s={ck*delta*sqrt(qdecay):.10e}")
production=ck*delta*sqrt(q0)*shear**2
destruction=ce*q0**1.5/delta
print(f"instantaneous Pi, modeled destruction, sum-of-budgets sink: {production:.8f}, {destruction:.8f}, {-destruction:.8f}")

# Component-wise periodic linear filters with normalized positive weights.
n=32
u=[[sin(2*pi*j/n)+.2*cos(6*pi*j/n), cos(4*pi*j/n), .3*sin(8*pi*j/n)] for j in range(n)]
def filt(values, weights):
    return [weights[0]*values[(j-1)%n]+weights[1]*values[j]+weights[2]*values[(j+1)%n] for j in range(n)]
F=lambda a:filt(a,(.25,.5,.25))
H=lambda a:filt(a,(.125,.75,.125))
v=[F([row[i] for row in u]) for i in range(3)]
hv=[H(v[i]) for i in range(3)]
maximum=0.
for i in range(3):
    for j in range(3):
        fprod=F([row[i]*row[j] for row in u])
        tau=[fprod[m]-v[i][m]*v[j][m] for m in range(n)]
        htau=H(tau)
        hprod=H(fprod)
        hvprod=H([v[i][m]*v[j][m] for m in range(n)])
        for m in range(n):
            total=hprod[m]-hv[i][m]*hv[j][m]
            leonard=hvprod[m]-hv[i][m]*hv[j][m]
            maximum=max(maximum,abs(total-htau[m]-leonard))
print(f"all-component Germano identity maximum residual: {maximum:.3e}")
assert maximum < 1e-12
