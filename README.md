# Many-Body Spin-Chain Dynamics with QuSpin

This repository contains a compact example of quantum many-body spin-chain dynamics using [QuSpin](https://weinbe58.github.io/QuSpin/).

The goal is to simulate the time evolution of a disordered spin chain and compute the Néel imbalance as a dynamical diagnostic of memory retention and localization behavior.

## Physical Model

We consider a disordered transverse-field Ising-like spin chain with Hamiltonian

```math
H =
\sum_{i=0}^{L-2} J_i Z_i Z_{i+1}
+
h_x \sum_{i=0}^{L-1} X_i
+
h_z \sum_{i=0}^{L-1} Z_i.
