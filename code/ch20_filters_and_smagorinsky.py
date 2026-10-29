"""Exact filter symbols, projection counterexample and local closure checks."""

from math import exp, pi, sin, sqrt


def sinc(z):
    return sin(z) / z if z else 1.0


for q in (0.5, 1.0, pi, 2 * pi, 3 * pi):
    box = sinc(q / 2)
    gaussian = exp(-q * q / 24)
    cutoff = 1.0 if q <= pi else 0.0
    print(
        f"kDelta={q:.8f}: box={box:.8f}, Gaussian={gaussian:.8f}, "
        f"cutoff={cutoff:.0f}"
    )

print(
    f"same-width box variance after one/two passes: {1 / 12:.8f}, {1 / 6:.8f}"
)
print(f"same-width Gaussian effective-width multiplier: {sqrt(2):.8f}")
print(
    f"grid Delta and test width2Delta Gaussian composite width/Delta: "
    f"{sqrt(5):.8f}"
)

# Positive scalar field (1+cos x)^2 projected to retain only modes0,+/-1.
positive_original = (1 + (-1)) ** 2
projected = 1.5 + 2 * (-1)
print(
    f"nonnegative field at pi and its sharp projection: "
    f"{positive_original:.8f}, {projected:.8f}"
)
assert projected < 0
# Velocity cos(x), sharp cutoff retains modes0,+/-1: F(u)=u, F(u^2)=1/2.
print(f"signed-kernel scalar stress at x0: {0.5 - 1:.8f}")

delta, shear, nu = 0.002, 100.0, 1.5e-5
for cs in (0.065, 0.1, 0.25):
    nut = (cs * delta) ** 2 * abs(shear)
    stress12 = -nut * shear
    transfer = nut * shear**2
    print(
        f"Cs={cs}: nu_sgs={nut:.10f}, tau12={stress12:.8f}, "
        f"Pi={transfer:.8f}, nu_sgs/nu={nut / nu:.8f}"
    )
print(f"viscosity ratio Cs .25/.065: {(0.25 / 0.065) ** 2:.8f}")
# Rigid rotation has zero symmetric strain; pure extension does not.
a, cs = 100.0, 0.1
extension_norm = 2 * abs(a)
extension_nut = (cs * delta) ** 2 * extension_norm
print(
    f"pure extension strain norm and modeled transfer: "
    f"{extension_norm:.8f}, {extension_nut * 4 * a * a:.8f}"
)
print(
    "rigid rotation strain norm and modeled transfer: 0.00000000, 0.00000000"
)
for n in (16, 32, 64):
    h = 2 * pi / n
    # Samples of a mode differing by n are identical on n equispaced nodes.
    alias_error = max(
        abs(sin((n + 3) * j * h) - sin(3 * j * h)) for j in range(n)
    )
    print(f"alias identity N={n}: maximum sample difference={alias_error:.3e}")
