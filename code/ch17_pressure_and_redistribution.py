"""Analytic pressure ensemble and restricted redistribution checks."""
from math import cos, sin, pi, sqrt

# Taylor-Green family in units U0=1 m/s, inverse length=1/m, at t=0.
# Random amplitude -1 with probability2/3 and +2 with probability1/3.
# Mean velocity0, mean amplitude squared2, mean amplitude cubed2.
states=[(-1.,2/3),(2.,1/3)]
x,y=.4,.7
shape=cos(2*x)+cos(2*y)
qmean=sum(w*a*a*shape/4 for a,w in states)
pistrain=[0.,0.]
fluct_mean=0.
for amplitude,weight in states:
    qprime=amplitude**2*shape/4-qmean
    fluct_mean+=weight*qprime
    g11=amplitude*cos(x)*cos(y)
    pistrain[0]+=weight*qprime*2*g11
    pistrain[1]-=weight*qprime*2*g11
print(f"pressure-fluctuation ensemble mean: {fluct_mean:.3e}")
print(f"analytic pressure-strain diagonal: {pistrain[0]:.8f}, {pistrain[1]:.8f}, {0.:.8f}")
print(f"analytic pressure-strain trace: {sum(pistrain):.3e}")

# Periodic five-point Laplacian convergence, sample amplitude+2.
errors=[]
for count in (32,64):
    h=2*pi/count
    def q(i,j):
        return (4-2)*(cos(2*i*h)+cos(2*j*h))/4
    maximum=0.
    source_mean=0.
    for i in range(count):
        for j in range(count):
            source=-(4-2)*(cos(2*i*h)+cos(2*j*h))
            source_mean+=source/count**2
            lap=(q(i+1,j)+q(i-1,j)+q(i,j+1)+q(i,j-1)-4*q(i,j))/h**2
            maximum=max(maximum,abs(lap-source))
    errors.append(maximum)
    print(f"periodic pressure N={count}: max Poisson residual={maximum:.8e}, source mean={source_mean:.3e}")
print(f"Poisson residual refinement ratio: {errors[0]/errors[1]:.8f}")
assert 3.9<errors[0]/errors[1]<4.1

R0=[.25,.09,.04,-.08,0.,0.]
k0,eps0,CS,CE2=.19,.5,1.8,1.92
def rhs(state):
    r=state[:6]
    e=state[6]
    k=sum(r[:3])/2
    result=[-CS*e/k*(r[i]-(2*k/3 if i<3 else 0.))
            -(2*e/3 if i<3 else 0.) for i in range(6)]
    return result+[-CE2*e*e/k]

def exact(t):
    theta=1+(CE2-1)*eps0/k0*t
    k=k0*theta**(-1/(CE2-1))
    e=eps0*theta**(-CE2/(CE2-1))
    alpha=theta**(-(CS-1)/(CE2-1))
    r=[2*k*((1-alpha)/3*(i<3)+alpha*R0[i]/(2*k0)) for i in range(6)]
    return r+[e],alpha

def rk4(steps,tfinal):
    state=R0+[eps0]
    dt=tfinal/steps
    for _ in range(steps):
        f1=rhs(state)
        f2=rhs([v+dt*f/2 for v,f in zip(state,f1)])
        f3=rhs([v+dt*f/2 for v,f in zip(state,f2)])
        f4=rhs([v+dt*f for v,f in zip(state,f3)])
        state=[v+dt*(a+2*b+2*c+d)/6 for v,a,b,c,d in zip(state,f1,f2,f3,f4)]
    return state
target,alpha=exact(.2)
errors=[]
for steps in (20,40):
    result=rk4(steps,.2)
    error=max(abs(a-b) for a,b in zip(result,target))
    errors.append(error)
    print(f"homogeneous Rotta decay steps={steps}: R11={result[0]:.8f}, R12={result[3]:.8f}, max error={error:.8e}")
print(f"Rotta decay refinement ratio: {errors[0]/errors[1]:.8f}")
print(f"normalized anisotropy multiplier t=.2: {alpha:.8f}")
assert 0<alpha<1 and errors[1]<errors[0]

# Trace-preserving wall map for normal y, on any symmetric tensor.
def wall_map(T):
    nn=T[1][1]
    n=[0.,1.,0.]
    tn=[T[i][1] for i in range(3)]
    return [[nn*(i==j)-1.5*(tn[i]*n[j]+n[i]*tn[j]) for j in range(3)] for i in range(3)]
T=[[1.,.2,.1],[.2,2.,-.3],[.1,-.3,3.]]
W=wall_map(T)
print(f"wall-map normal/parallel/shear: {W[1][1]:.8f}, {W[0][0]:.8f}, {W[0][1]:.8f}")
print(f"wall-map trace: {sum(W[i][i] for i in range(3)):.3e}")
for d in (.002,.001):
    k=.7*d*d
    eps=2*1.5e-5*.7
    f=k**1.5/(2.55*d*eps)
    print(f"physical-wall illustrative factor d={d:.3f}: {f:.8f}")
wall_values=[3.67,.83,2.17]
print(f"lecture wall-function k/u_tau²: {sum(wall_values)/2:.8f}")
print(f"lecture wall-function planar covariance determinant/u_tau4: {3.67*.83-1:.8f}")
