"""
Time evolution of a disordered transverse-field Ising chain using QuSpin.

Hamiltonian:
    H = sum_i J_i Z_i Z_{i+1} + h sum_i X_i

Observable:
    M_z(t) = (1/L) sum_i <Z_i(t)>
"""

from pathlib import Path

import numpy as np
from quspin.basis import spin_basis_1d
from quspin.operators import hamiltonian


def build_disordered_ising_hamiltonian(
    length: int,
    j_mean: float,
    disorder_strength: float,
    h_field: float,
    seed: int = 123,
):
    """
    Build a disordered transverse-field Ising Hamiltonian.

    Parameters
    ----------
    length:
        Number of spins.
    j_mean:
        Mean Ising coupling.
    disorder_strength:
        Disorder amplitude W. Couplings are sampled as J_i = J + U[-W, W].
    h_field:
        Transverse-field strength.
    seed:
        Random seed.

    Returns
    -------
    H:
        QuSpin Hamiltonian object.
    basis:
        Spin basis.
    couplings:
        Array of disordered nearest-neighbor couplings.
    """
    rng = np.random.default_rng(seed)

    basis = spin_basis_1d(length)

    couplings = j_mean + rng.uniform(
        low=-disorder_strength,
        high=disorder_strength,
        size=length - 1,
    )

    zz_terms = [[couplings[i], i, i + 1] for i in range(length - 1)]
    x_terms = [[h_field, i] for i in range(length)]

    static = [
        ["zz", zz_terms],
        ["x", x_terms],
    ]

    dynamic = []

    H = hamiltonian(
        static,
        dynamic,
        basis=basis,
        dtype=np.float64,
        check_symm=False,
        check_herm=True,
        check_pcon=False,
    )

    return H, basis, couplings


def initial_all_up_state(length: int, basis: spin_basis_1d) -> np.ndarray:
    """
    Construct the initial product state |00...0>.

    In QuSpin's spin basis convention, this corresponds to the integer state
    with all bits set to 1 for spin-up in the z basis.
    """
    state_integer = 2**length - 1
    state_index = basis.index(state_integer)

    psi0 = np.zeros(basis.Ns, dtype=np.complex128)
    psi0[state_index] = 1.0

    return psi0


def build_local_z_operators(length: int, basis: spin_basis_1d):
    """Build local Z_i operators."""
    z_ops = []

    for site in range(length):
        static = [["z", [[1.0, site]]]]
        op = hamiltonian(
            static,
            [],
            basis=basis,
            dtype=np.float64,
            check_symm=False,
            check_herm=True,
            check_pcon=False,
        )
        z_ops.append(op)

    return z_ops


def compute_local_magnetizations(states: np.ndarray, z_ops: list) -> np.ndarray:
    """
    Compute <Z_i(t)> for all sites and all times.

    Parameters
    ----------
    states:
        Array with shape (Ns, Nt), as returned by H.evolve(...).
    z_ops:
        List of local Z_i operators.

    Returns
    -------
    local_mz:
        Array with shape (Nt, L).
    """
    num_times = states.shape[1]
    length = len(z_ops)

    local_mz = np.zeros((num_times, length), dtype=np.float64)

    for t_index in range(num_times):
        psi_t = states[:, t_index]

        for site, z_op in enumerate(z_ops):
            value = z_op.expt_value(psi_t)
            local_mz[t_index, site] = np.real_if_close(value)

    return local_mz


def main() -> None:
    # Model parameters
    length = 8
    j_mean = 1.0
    disorder_strength = 2.0
    h_field = 0.6
    seed = 123

    # Time grid
    times = np.linspace(0.0, 20.0, 201)

    # Output directory
    root = Path(__file__).resolve().parents[1]
    results_dir = root / "results"
    results_dir.mkdir(exist_ok=True)

    # Build Hamiltonian
    H, basis, couplings = build_disordered_ising_hamiltonian(
        length=length,
        j_mean=j_mean,
        disorder_strength=disorder_strength,
        h_field=h_field,
        seed=seed,
    )

    # Initial state
    psi0 = initial_all_up_state(length, basis)

    # Time evolution
    states = H.evolve(
        psi0,
        t0=times[0],
        times=times,
        iterate=False,
    )

    # Observables
    z_ops = build_local_z_operators(length, basis)
    local_mz = compute_local_magnetizations(states, z_ops)
    average_mz = np.mean(local_mz, axis=1)

    # Save results
    output_path = results_dir / "quspin_dynamics_results.npz"

    np.savez(
        output_path,
        times=times,
        local_mz=local_mz,
        average_mz=average_mz,
        couplings=couplings,
        length=length,
        j_mean=j_mean,
        disorder_strength=disorder_strength,
        h_field=h_field,
        seed=seed,
    )

    print(f"Saved results to: {output_path}")
    print(f"Hilbert-space dimension: {basis.Ns}")
    print(f"Disordered couplings: {couplings}")


if __name__ == "__main__":
    main()
