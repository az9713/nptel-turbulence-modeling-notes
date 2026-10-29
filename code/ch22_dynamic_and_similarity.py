"""Tensor least-squares, signed transfer and Galilean-invariance checks."""
from math import cos, sin, sqrt

def dot(a,b):
    return sum(a[i][j]*b[i][j] for i in range(3) for j in range(3))

M=[[2.,1.,0.],[1.,-1.,.5],[0.,.5,-1.]]
N=[[1.,0.,0.],[0.,1.,0.],[0.,0.,-2.]]
projection=dot(N,M)/dot(M,M)
Nperp=[[N[i][j]-projection*M[i][j] for j in range(3)] for i in range(3)]
true=.04
L=[[-2*true*M[i][j]+.03*Nperp[i][j] for j in range(3)] for i in range(3)]
fit=-dot(L,M)/(2*dot(M,M))
residual=[[L[i][j]+2*fit*M[i][j] for j in range(3)] for i in range(3)]
print(f"least-squares C: {fit:.10f}; residual Frobenius norm={sqrt(dot(residual,residual)):.10f}")
print(f"residual dot M: {dot(residual,M):.3e}")
assert abs(fit-true)<1e-14 and abs(dot(residual,M))<1e-14

# One-direction tensor examples: weight by M:M, not arithmetic mean of C.
magnitudes=(1.,10.)
coefficients=(.01,.09)
weighted=sum(m*m*c for m,c in zip(magnitudes,coefficients))/sum(m*m for m in magnitudes)
print(f"mean of local C and joint least-squares C: {sum(coefficients)/2:.8f}, {weighted:.8f}")
print("zero M: least-squares coefficient unidentifiable, not divided by zero")
nu,delta,G=1.5e-5,.002,100.
for C in (-.01,-.05):
    nus=C*delta**2*G
    print(f"signed C={C}: nu_s={nus:.10f}, total nu={nu+nus:.10f}, Pi={nus*G*G:.8f}")
print(f"frozen-strain strict lower C bound: {-nu/(delta**2*G):.8f}")

# Scalar analog of the source Leonard/cross ansatz, with an exact top-hat.
x,width,boost=.4,.6,2.
gain=sin(width/2)/(width/2)
gain2=sin(width)/width
v=cos(x)
fv=gain*v
fvv=.5*(1+gain2*cos(2*x))
def decomposition_model(V,cr):
    vp=v+V
    fvp=fv+V
    fvp2=fvv+2*V*fv+V*V
    leonard=fvp2-vp*vp
    cross_model=cr*(vp*vp-fvp*fvp)
    return leonard+cross_model
for cr in (1.,1.1):
    change=decomposition_model(boost,cr)-decomposition_model(0,cr)
    print(f"source cross coefficient Cr={cr}: model change under constant boost={change:.10f}")
    if cr==1.: assert abs(change)<1e-14
similarity=fvv-fv*fv
print(f"central similarity stress scalar: {similarity:.10f}")

# Local divergence-free affine extension, positive box filter.
width=.2
for rates in ((20.,-10.,-10.),(-20.,10.,10.)):
    diagonal=[width**2*a*a/12 for a in rates]
    transfer=-sum(diagonal[i]*rates[i] for i in range(3))
    print(f"affine similarity diagonal={diagonal}; transfer={transfer:.8f}")
