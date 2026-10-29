"""Restricted second-moment evolution, diffusion and trace checks."""

from math import sqrt

R = [[0.25, -0.08, 0.0], [-0.08, 0.09, 0.0], [0.0, 0.0, 0.04]]
shear = 100.0
A = [[0.0, shear, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
P = [
    [
        -sum(A[i][ell] * R[ell][j] + R[i][ell] * A[j][ell] for ell in range(3))
        for j in range(3)
    ]
    for i in range(3)
]
k = sum(R[i][i] for i in range(3)) / 2
scalar = -sum(R[i][j] * A[i][j] for i in range(3) for j in range(3))
print("production matrix:", P)
print(
    f"half production trace and scalar contraction: "
    f"{sum((P[i][i] for i in range(3))) / 2:.8f}, {scalar:.8f}"
)

# Exact production-only evolution R(t)=F R(0) F^T for nilpotent A.
t = 0.01
b = shear * t
R11 = R[0][0] - 2 * b * R[0][1] + b * b * R[1][1]
R12 = R[0][1] - b * R[1][1]
det0 = R[0][0] * R[1][1] - R[0][1] ** 2
det1 = R11 * R[1][1] - R12**2
print(f"exact shear production t=.01: R11={R11:.8f}, R12={R12:.8f}")
print(
    f"planar covariance determinant initial and final: {det0:.8f}, {det1:.8f}"
)
assert abs(det0 - det1) < 1e-14

# A large single Euler step can violate PSD even for this PSD-preserving ODE.
b = 2.0
exact_min = (2 + b * b - sqrt((b * b) ** 2 + 4 * b * b)) / 2
euler_min = 1 - b
print(
    f"unit-covariance shear-step minimum eigenvalues: "
    f"exact={exact_min:.8f}, Euler={euler_min:.8f}"
)
assert exact_min > 0 > euler_min

epsilon, CD, Cmu, sigma = 0.5, 0.2, 0.09, 1.0
D = [[CD * k / epsilon * entry for entry in row] for row in R]
gradient = [0.0, 10.0, 0.0]
flux = [-sum(D[i][j] * gradient[j] for j in range(3)) for i in range(3)]
dot = sum(gradient[i] * flux[i] for i in range(3))
isotropic = Cmu * k * k / epsilon / sigma
print("anisotropic diffusivity matrix:", D)
print("energy flux with zero x-gradient:", flux)
print(f"gradient dot anisotropic flux: {dot:.8f}")
print(f"isotropic x and y flux: {0.0:.8f}, {-isotropic * gradient[1]:.8f}")
assert dot <= 0 and flux[0] != 0

# Freeze one common positive face diffusivity and diffuse all matrix
# components.
left = R
right = [[0.16, 0.02, 0.0], [0.02, 0.08, 0.0], [0.0, 0.0, 0.06]]
face_diff = 0.003
dx, dt = 0.1, 0.5
theta = dt * face_diff / dx**2
updated = [
    [
        [(1 - theta) * left[i][j] + theta * right[i][j] for j in range(3)]
        for i in range(3)
    ],
    [
        [theta * left[i][j] + (1 - theta) * right[i][j] for j in range(3)]
        for i in range(3)
    ],
]
error = max(
    abs(updated[0][i][j] + updated[1][i][j] - left[i][j] - right[i][j])
    for i in range(3)
    for j in range(3)
)
print(
    f"two-cell common diffusion weight: {theta:.8f}; conservation "
    f"error: {error:.3e}"
)
print(
    f"initial and final total trace: "
    f"{sum((left[i][i] + right[i][i] for i in range(3))):.8f}, "
    f"{sum((updated[0][i][i] + updated[1][i][i] for i in range(3))):.8f}"
)
assert 0 <= theta <= 1 and error < 1e-14

# Tensor destruction trace convention and a deliberately incomplete reduced
# source.
e_tensor = [2 * epsilon / 3] * 3
print(f"isotropic destruction half trace: {sum(e_tensor) / 2:.8f}")
dt = 0.01
print(
    f"zero initial directional variance under isolated isotropic sink: "
    f"{-dt * e_tensor[0]:.8f}"
)
