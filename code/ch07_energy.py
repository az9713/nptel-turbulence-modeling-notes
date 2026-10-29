"""Closed-form periodic Navier-Stokes checks; no turbulence simulation."""
from math import cos, exp, pi, sin

nu, rho, amplitude, wave = 0.01, 1.2, 2.0, 2.0
n = 32
for time in (0.0, 5.0):
    A = amplitude*exp(-2*nu*wave**2*time)
    energy, dissipation, div_error, momentum_error = 0.0, 0.0, 0.0, 0.0
    for i in range(n):
        for j in range(n):
            X, Y = 2*pi*i/n, 2*pi*j/n
            u, v = A*sin(X)*cos(Y), -A*cos(X)*sin(Y)
            ux, uy = A*wave*cos(X)*cos(Y), -A*wave*sin(X)*sin(Y)
            vx, vy = A*wave*sin(X)*sin(Y), -A*wave*cos(X)*cos(Y)
            pressure_x = -rho*A*A*wave*sin(2*X)/2
            pressure_y = -rho*A*A*wave*sin(2*Y)/2
            rate_u, rate_v = -2*nu*wave**2*u, -2*nu*wave**2*v
            lap_u, lap_v = -2*wave**2*u, -2*wave**2*v
            energy += (u*u+v*v)/2
            dissipation += nu*(ux*ux+uy*uy+vx*vx+vy*vy)
            div_error = max(div_error, abs(ux+vy))
            momentum_error = max(momentum_error,
                abs(rate_u+u*ux+v*uy+pressure_x/rho-nu*lap_u),
                abs(rate_v+u*vx+v*vy+pressure_y/rho-nu*lap_v))
    energy /= n*n
    dissipation /= n*n
    exact_energy = amplitude**2*exp(-4*nu*wave**2*time)/4
    energy_rate = -4*nu*wave**2*exact_energy
    assert abs(energy-exact_energy) < 1e-12
    assert abs(energy_rate+dissipation) < 1e-12
    assert div_error < 1e-12 and momentum_error < 1e-12
    print(f"t={time:.1f}: k={energy:.8f}, epsilon={dissipation:.8f}, "
          f"dk/dt+epsilon={energy_rate+dissipation:.3e}")
    print(f"  max divergence={div_error:.3e}, "
          f"max momentum residual={momentum_error:.3e}")

# Two positive-definite covariances with identical k and different transfer.
S = 100.0
for shear_cov in (-0.08, 0.0, 0.08):
    R11, R22, R33 = 0.25, 0.09, 0.04
    assert R11*R22-shear_cov**2 > 0
    k = (R11+R22+R33)/2
    transfer = -shear_cov*S
    print(f"R12={shear_cov:+.2f}: k={k:.6f}, "
          f"TKE exchange={transfer:+.6f}, mean exchange={-transfer:+.6f}")
