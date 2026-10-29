"""A conservative 1D diffusion solver and iteration checks, not a \
turbulence solver."""

from math import pi, sin


def solve_diffusion(intervals, height, viscosity, source):
    """-nu U''=source, homogeneous Dirichlet data, nodal control volumes."""
    spacing = height / intervals
    count = intervals - 1
    lower = [-viscosity / spacing**2] * count
    diag = [2 * viscosity / spacing**2] * count
    upper = [-viscosity / spacing**2] * count
    rhs = [source((i + 1) * spacing) for i in range(count)]
    original_rhs = rhs[:]
    # Thomas elimination; positive diffusion gives a nonsingular SPD system.
    for i in range(1, count):
        factor = lower[i] / diag[i - 1]
        diag[i] -= factor * upper[i - 1]
        rhs[i] -= factor * rhs[i - 1]
    interior = [0.0] * count
    interior[-1] = rhs[-1] / diag[-1]
    for i in range(count - 2, -1, -1):
        interior[i] = (rhs[i] - upper[i] * interior[i + 1]) / diag[i]
    values = [0.0] + interior + [0.0]
    residual = max(
        abs(
            viscosity
            * (2 * values[i] - values[i - 1] - values[i + 1])
            / spacing**2
            - original_rhs[i - 1]
        )
        for i in range(1, intervals)
    )
    return spacing, values, residual


height, nu, G = 0.02, 1.5e-5, 0.05
h, u, res = solve_diffusion(32, height, nu, lambda y: G)
error = max(
    abs(value - G * y * (height - y) / (2 * nu))
    for y, value in ((i * h, v) for i, v in enumerate(u))
)
left = nu * (u[1] - u[0]) / h
right = nu * (u[-1] - u[-2]) / h
# Boundary half control volumes contain half-cell forcing.
left_wall = left + G * h / 2
right_wall = right - G * h / 2
print(f"laminar channel maximum speed m/s: {max(u):.10f}")
print(f"laminar nodal error and equation residual: {error:.3e}, {res:.3e}")
print(
    f"wall stress-per-density difference and integrated forcing: "
    f"{left_wall - right_wall:.10f}, {G * height:.10f}"
)
assert error < 1e-12 and abs(left_wall - right_wall - G * height) < 1e-12

errors = []
for n in (16, 32, 64):

    def source(y):
        return nu * (pi / height) ** 2 * sin(pi * y / height)

    h, u, res = solve_diffusion(n, height, nu, source)
    errors.append(max(abs(v - sin(pi * i / n)) for i, v in enumerate(u)))
    print(
        f"manufactured sine N={n}: maximum error={errors[-1]:.8e}, "
        f"equation residual={res:.3e}"
    )
print(
    f"manufactured last spatial refinement ratio: "
    f"{errors[-2] / errors[-1]:.8f}"
)
assert 3.9 < errors[-2] / errors[-1] < 4.1

# x=g(x)=3-2x has exact root1. Relaxed error factor1-3alpha.
for alpha in (1.0, 0.5, 0.8):
    x = 0.0
    for _ in range(8):
        x = (1 - alpha) * x + alpha * (3 - 2 * x)
    print(
        f"fixed-point alpha={alpha}: x after8={x:.8f}, root "
        f"residual={3 - 3 * x:.8f}"
    )
alpha = 1e-6
x = 0.0
new = (1 - alpha) * x + alpha * (3 - 2 * x)
print(
    f"tiny relaxation: update={new - x:.8e}, unrelaxed fixed-point "
    f"residual={3 - 3 * x:.8f}"
)

# Inner convergence for one implicit Euler step, lambda*dt=4.
old = 1.0
target = old / (1 + 4)
q = old
for count in range(1, 41):
    q = 0.9 * q + 0.1 * (old - 4 * q)
    if count in (1, 40):
        print(
            f"implicit-step inner iterations={count}: q={q:.10f}, exact "
            f"discrete target={target:.10f}"
        )
assert abs(q - target) < 1e-10
