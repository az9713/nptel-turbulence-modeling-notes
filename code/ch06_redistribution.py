"""Analytic sampling and constructed local stress budgets, not DNS data."""
from math import cos, pi, sin, sqrt

phases = [2*pi*j/8 for j in range(8)]
mean = lambda values: sum(values)/len(values)
for shift in (0.0, 0.37, 1.41):
    values = [10.0 + 2.0*cos(p+shift) for p in phases]
    gradients = [-6.0*sin(p+shift) for p in phases]
    mu = mean(values)
    var = mean([(v-mu)**2 for v in values])
    print(f"phase shift {shift:.2f}: mean={mu:.6f}, variance={var:.6f}, "
          f"mean gradient-square={mean([g*g for g in gradients]):.6f}")

# Positive covariance in m^2/s^2; A_ij = partial_j U_i in 1/s.
R = [[0.25,-0.08,0.0],[-0.08,0.09,0.0],[0.0,0.0,0.04]]
A = [[0.0,100.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]
P = [[-sum(R[i][l]*A[j][l]+R[j][l]*A[i][l]
           for l in range(3)) for j in range(3)] for i in range(3)]
eps = [[6.0,-1.0,0.0],[-1.0,6.0,0.0],[0.0,0.0,4.0]]
Pi = [[-10.0,8.0,0.0],[8.0,6.0,0.0],[0.0,0.0,4.0]]
trace = lambda M: sum(M[i][i] for i in range(3))
print("production matrix:", P)
print(f"k={trace(R)/2:.6f}, production of k={trace(P)/2:.6f}, "
      f"dissipation of k={trace(eps)/2:.6f}")
print(f"redistribution trace={trace(Pi):.6f}")
print("zero-transport residual:",
      max(abs(P[i][j]+Pi[i][j]-eps[i][j])
          for i in range(3) for j in range(3)))

# A second bookkeeping state: transport can supply a normal component.
Pi2 = [[-3.0,8.0,0.0],[8.0,4.0,0.0],[0.0,0.0,-1.0]]
D2 = [[-7.0,0.0,0.0],[0.0,2.0,0.0],[0.0,0.0,5.0]]
print("transport-assisted residual:",
      max(abs(P[i][j]+Pi2[i][j]+D2[i][j]-eps[i][j])
          for i in range(3) for j in range(3)))
print(f"R12 correlation coefficient={R[0][1]/sqrt(R[0][0]*R[1][1]):.6f}")

# An intentionally wrong audit can cancel two errors in a total trace.
wrong_diag = [0.4,-0.4,0.0]
print(f"cancelling-error trace={sum(wrong_diag):.6f}, "
      f"largest component error={max(abs(x) for x in wrong_diag):.6f}")
