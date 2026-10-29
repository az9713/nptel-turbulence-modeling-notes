"""Covariance and production diagnostics; no spatial RANS solution."""

from math import sqrt

k, epsilon, Cmu = 0.19, 0.5, 0.09
base = Cmu * k * k / epsilon
print(f"baseline viscosity m2/s: {base:.8f}")
print(
    f"pairwise-bound counterexample eigenvalues: {-0.5:.8f}, "
    f"{1.75:.8f}, {1.75:.8f}"
)
det = (1 - (-0.75)) ** 2 * (1 + 2 * (-0.75))
print(f"pairwise-bound counterexample determinant: {det:.8f}")

a = 100.0
strain_norm = sqrt(2 * a * a)
lambda_bound = sqrt(2 / 3) * strain_norm
exact_cap = k / (3 * a)
safe_cap = k / (3 * lambda_bound)
for label, viscosity in (
    ("baseline", base),
    ("eigenvalue cap", min(base, exact_cap)),
    ("invariant cap", min(base, safe_cap)),
):
    variances = [
        2 * k / 3 - 2 * viscosity * a,
        2 * k / 3 + 2 * viscosity * a,
        2 * k / 3,
    ]
    production = 4 * viscosity * a * a
    print(
        f"planar strain {label}: nu_t={viscosity:.8f}, min "
        f"variance={min(variances):.8f}, production={production:.8f}"
    )
    if label != "baseline":
        assert min(variances) >= -1e-14

# Rotate planar strain 45 degrees so positive eigenstrain is off diagonal.
row_estimate = sqrt(2 / 3) * a
row_cap = k / (3 * row_estimate)
bad_eigenvalue = 2 * k / 3 - 2 * row_cap * a
print(
    f"rotated row-norm cap: nu_t={row_cap:.8f}, min covariance "
    f"eigenvalue={bad_eigenvalue:.8f}"
)
assert bad_eigenvalue < 0

production = 4 * base * a * a
limited = min(production, 10 * epsilon)
print(
    f"production-only cap: original={production:.8f}, "
    f"capped={limited:.8f}, unchanged min "
    f"variance={2 * k / 3 - 2 * base * a:.8f}"
)
print(
    f"mean-plus-turbulent transfer imbalance with unchanged stress: "
    f"{limited - production:.8f}"
)
print(f"isotropic instantaneous exact production: {0.0:.8f}")
print(f"Kato-Launder pure strain production: {0.0:.8f}")

shear = 100.0
S = shear
Omega = shear
print(
    f"simple shear baseline and Kato-Launder: {base * S * S:.8f}, "
    f"{base * S * Omega:.8f}"
)
print(
    f"invariant limited k-epsilon time s: "
    f"{min(k / epsilon, 1 / (3 * Cmu * lambda_bound)):.8f}"
)
omega = epsilon / (Cmu * k)
print(
    f"invariant limited k-omega time s: "
    f"{min(1 / omega, 1 / (3 * lambda_bound)):.8f}"
)

print(f"10% k high/epsilon low length ratio: {1.1 ** 1.5 / 0.9:.8f}")
print(f"10% k high/epsilon low viscosity ratio: {1.1 ** 2 / 0.9:.8f}")
kappa, y = 0.41, 0.002
ut = 0.4
gradient = ut / (kappa * y)
curvature = ut / (kappa * y * y)
print(f"log-profile von Karman length m: {kappa * gradient / curvature:.8f}")
print(
    "uniform shear and nonzero linear strain: Laplacian=0; raw von "
    "Karman ratio undefined"
)
