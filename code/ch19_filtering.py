"""Analytic and discrete filter identities; not a spatial LES solver."""

from math import pi, sin


def sinc(z):
    return sin(z) / z if z else 1.0


x, delta = 0.4, 0.6
once = x * x + delta**2 / 12
twice = x * x + delta**2 / 6
residual = -(delta**2) / 12
variance = x * x * delta**2 / 3 + delta**4 / 180
print(
    f"quadratic field: original={x * x:.8f}, filtered={once:.8f}, "
    f"double filtered={twice:.8f}"
)
print(f"filtered residual (not zero): {residual:.8f}")
print(
    f"quadratic exact stress and residual-square average: "
    f"{variance:.8f}, {residual ** 2:.8f}"
)
assert abs(once - twice - residual) < 1e-15

for small in (0.2, 0.1):
    width = small * (1 + x)
    commutator = -width * small / 6
    print(
        f"variable-width quadratic commutator delta0={small}: "
        f"{commutator:.10f}"
    )

wave = 3
gain = sinc(wave * delta / 2)
print(f"top-hat mode gain once and twice: {gain:.8f}, {gain * gain:.8f}")

# The lecture's illustrative discrete averaging stencil, not an exact
# continuum box.
data = [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]


def smooth(values):
    n = len(values)
    return [
        values[(i - 1) % n] / 8 + 0.75 * values[i] + values[(i + 1) % n] / 8
        for i in range(n)
    ]


first, second = smooth(data), smooth(smooth(data))
print(
    f"discrete impulse center after one and two passes: {first[2]:.8f}, "
    f"{second[2]:.8f}"
)
print(f"discrete filter sums: {sum(first):.8f}, {sum(second):.8f}")

shear, dy = 100.0, 0.002
tau11 = shear**2 * dy**2 / 12
print(f"linear-shear exact box stress tau11: {tau11:.10f}")
print("linear-shear residual velocity: zero; exact stress divergence: zero")

# Positive box quadrature: trace/stress PSD and resolved+subfilter energy
# identity.
vectors = [
    (1.0, 2.0, 0.0),
    (3.0, -1.0, 1.0),
    (-2.0, 0.5, 2.0),
    (0.5, -3.0, -1.0),
]
n = len(vectors)
mean = [sum(v[i] for v in vectors) / n for i in range(3)]
tau = [
    [
        sum(v[i] * v[j] for v in vectors) / n - mean[i] * mean[j]
        for j in range(3)
    ]
    for i in range(3)
]
resolved = sum(v * v for v in mean) / 2
subfilter = sum(tau[i][i] for i in range(3)) / 2
total = sum(sum(c * c for c in v) for v in vectors) / (2 * n)
print(
    f"box energy total, resolved, subfilter: {total:.8f}, "
    f"{resolved:.8f}, {subfilter:.8f}"
)
print(f"energy partition residual: {total - resolved - subfilter:.3e}")
for a in ((1, 0, 0), (0, 1, 0), (0, 0, 1), (1, -2, 3), (-3, 1, 2)):
    quadratic = sum(
        a[i] * tau[i][j] * a[j] for i in range(3) for j in range(3)
    )
    centered = (
        sum(
            sum(a[i] * (v[i] - mean[i]) for i in range(3)) ** 2
            for v in vectors
        )
        / n
    )
    assert quadratic >= -1e-12 and abs(quadratic - centered) < 1e-12

# Filter width is held fixed while the representation grid changes.
print(
    f"fixed-filter continuum gain (independent of representation grid): "
    f"{gain:.8f}"
)
for h in (0.2, 0.1, 0.05):
    print(f"grid-tied width={h}: continuum mode gain={sinc(wave * h / 2):.8f}")
