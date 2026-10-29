"""Closed homogeneous k-epsilon subproblem and conservative flux checks."""

from math import isfinite

Cmu, C2 = 0.09, 1.92
k0, e0 = 0.19, 0.5
power = 1 / (C2 - 1)


def exact(t):
    theta = 1 + (C2 - 1) * e0 * t / k0
    return k0 * theta ** (-power), e0 * theta ** (-power - 1)


def rhs(state):
    k, e = state
    assert k > 0 and e > 0 and isfinite(k + e)
    return -e, -C2 * e * e / k


def rk4(steps, duration=1.0):
    state = (k0, e0)
    dt = duration / steps
    for _ in range(steps):
        a = rhs(state)
        b = rhs(tuple(state[i] + dt * a[i] / 2 for i in range(2)))
        c = rhs(tuple(state[i] + dt * b[i] / 2 for i in range(2)))
        d = rhs(tuple(state[i] + dt * c[i] for i in range(2)))
        state = tuple(
            state[i] + dt * (a[i] + 2 * b[i] + 2 * c[i] + d[i]) / 6
            for i in range(2)
        )
    return state


target = exact(1)
errors = []
for steps in (50, 100):
    state = rk4(steps)
    error = max(abs(state[i] - target[i]) for i in range(2))
    errors.append(error)
    print(
        f"RK4 steps={steps}: k={state[0]:.10f}, "
        f"epsilon={state[1]:.10f}, max error={error:.3e}"
    )
print(f"refinement error ratio: {errors[0] / errors[1]:.6f}")
print(f"model decay exponent: {power:.8f}")
print(f"exact t=1 time scale s: {target[0] / target[1]:.8f}")
print(f"exact t=1 eddy viscosity m2/s: {Cmu * target[0] ** 2 / target[1]:.8f}")
assert errors[1] < errors[0] / 12

for exponent in (1.19, 1.25, 1.31):
    print(
        f"measured power m={exponent:.2f}: inferred "
        f"C_epsilon2={1 + 1 / exponent:.8f}"
    )
print(f"power required by C_epsilon2=1.92: {1 / (1.92 - 1):.8f}")
ratio = 0.3
print(f"equilibrium shear/energy ratio 0.3 gives C_mu={ratio ** 2:.8f}")

# Isolated equal-volume cells, unit face area, no outer flux.
dx, nu, nut, sigma = 0.1, 1.5e-5, 0.004, 1.0
left, right = 1.0, 0.2
flux = -(nu + nut / sigma) * (right - left) / dx
rates = (-flux / dx, flux / dx)
print(f"two-cell outward rightward energy flux m3/s3: {flux:.8f}")
print(f"two-cell rates m2/s3: {rates[0]:.8f}, {rates[1]:.8f}")
assert abs(sum(rates) * dx) < 1e-14
