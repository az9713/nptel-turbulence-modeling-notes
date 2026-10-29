"""Conditional scale ledger, not a boundary-layer solution."""
from math import sqrt

Us, L, delta, nu = 20.0, 1.0, 0.05, 1.5e-5
Re = Us*L/nu
aspect = delta/L
for beta in (0.1, 1.0):
    dU = beta*Us
    Vs = dU*aspect
    q2 = Us*dU*aspect  # Chosen to make shear-stress divergence comparable.
    leading = Us*dU/L
    estimates = {
        "streamwise advection": leading,
        "normal advection": Vs*dU/delta,
        "streamwise viscosity": nu*dU/L**2,
        "normal viscosity": nu*dU/delta**2,
        "normal-stress x gradient": q2/L,
        "shear-stress y gradient": q2/delta,
    }
    print(f"beta={beta:.1f}: Vs={Vs:.6f} m/s, q={sqrt(q2):.6f} m/s")
    for term, value in estimates.items():
        print(f"  {term}: {value:.8f} m/s2, ratio={value/leading:.8f}")
    print(f"  intensity q/Us={sqrt(q2)/Us:.8f}")
    assert abs((q2/delta)/leading-1) < 1e-12
    assert abs((nu*dU/delta**2)/leading-1/(Re*aspect**2)) < 1e-12

laminar_scale = L/sqrt(Re)
print(f"Re_L={Re:.6f}, delta/L={aspect:.6f}")
print(f"laminar balance length scale={laminar_scale:.8f} m")
print(f"normal-viscous/streamwise-viscous ratio={(L/delta)**2:.6f}")

# The same rms scale does not determine the shear correlation.
q2 = Us*(0.1*Us)*aspect
for coefficient in (1.0, 0.1, 0.0):
    shear_gradient = coefficient*q2/delta
    print(f"shear-correlation magnitude={coefficient:.1f}: "
          f"shear-gradient/leading={shear_gradient/(Us*(0.1*Us)/L):.6f}")
