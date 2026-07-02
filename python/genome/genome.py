"""Genome definition and genetic operators.

A genome encodes the *controller* for a creature — the parameters of a central
pattern generator (CPG) that drives the motorised hinges between its body
segments. The body plan (morphology) is fixed for every creature (see
``utils.config``), which isolates the learning problem to "find a gait that
crawls forward" and makes evolutionary progress easy to observe.

Gene layout
-----------
* ``frequency``            one shared gait frequency (Hz)
* ``amplitude[i]``         swing amplitude of joint ``i`` (rad)
* ``phase[i]``             phase offset of joint ``i`` (rad)
* ``center[i]``            rest-angle offset of joint ``i`` (rad)

The parameters are stored in a flat NumPy vector so crossover and mutation are
simple, vectorised array operations.
"""
from __future__ import annotations

import random

import numpy as np

from utils import config


# Index layout of the flat gene vector.
_N = config.NUM_JOINTS
FREQ_IDX = 0
AMP_SLICE = slice(1, 1 + _N)
PHASE_SLICE = slice(1 + _N, 1 + 2 * _N)
CENTER_SLICE = slice(1 + 2 * _N, 1 + 3 * _N)
GENE_COUNT = 1 + 3 * _N

# Per-gene lower/upper bounds, aligned with the flat vector layout.
_LOWER = np.empty(GENE_COUNT)
_UPPER = np.empty(GENE_COUNT)
_LOWER[FREQ_IDX], _UPPER[FREQ_IDX] = config.FREQ_RANGE
_LOWER[AMP_SLICE], _UPPER[AMP_SLICE] = config.AMPLITUDE_RANGE
_LOWER[PHASE_SLICE], _UPPER[PHASE_SLICE] = config.PHASE_RANGE
_CENTER_LO, _CENTER_HI = config.CENTER_RANGE
_LOWER[CENTER_SLICE], _UPPER[CENTER_SLICE] = _CENTER_LO, _CENTER_HI

# Relative mutation scale per gene group (phases roam more freely than offsets).
_SIGMA_SCALE = np.empty(GENE_COUNT)
_SIGMA_SCALE[FREQ_IDX] = 0.30
_SIGMA_SCALE[AMP_SLICE] = 0.20
_SIGMA_SCALE[PHASE_SLICE] = 0.35
_SIGMA_SCALE[CENTER_SLICE] = 0.15
_SPAN = _UPPER - _LOWER


class Genome:
    """A creature controller expressed as a flat vector of CPG parameters."""

    __slots__ = ("genes",)

    def __init__(self, genes: np.ndarray | None = None):
        self.genes = np.asarray(genes, dtype=float) if genes is not None else self.random_genes()

    # -- construction -------------------------------------------------------- #
    @staticmethod
    def random_genes(rng: random.Random | None = None) -> np.ndarray:
        """Draw a uniformly random genome inside the configured bounds."""
        r = np.random.default_rng(None if rng is None else rng.randint(0, 2**31 - 1))
        return _LOWER + r.random(GENE_COUNT) * _SPAN

    @classmethod
    def random(cls, rng: random.Random | None = None) -> "Genome":
        return cls(cls.random_genes(rng))

    # -- structured accessors ----------------------------------------------- #
    @property
    def frequency(self) -> float:
        return float(self.genes[FREQ_IDX])

    @property
    def amplitudes(self) -> np.ndarray:
        return self.genes[AMP_SLICE]

    @property
    def phases(self) -> np.ndarray:
        return self.genes[PHASE_SLICE]

    @property
    def centers(self) -> np.ndarray:
        return self.genes[CENTER_SLICE]

    # -- genetic operators --------------------------------------------------- #
    def clone(self) -> "Genome":
        return Genome(self.genes.copy())

    def mutate(self, sigma: float, rng: random.Random) -> "Genome":
        """Return a mutated copy using bounded Gaussian perturbations.

        ``sigma`` scales the global mutation strength (annealed over the run).
        Each gene is perturbed with probability ``GENE_MUTATION_RATE`` by noise
        proportional to its own range, then clamped back inside its bounds.
        """
        genes = self.genes.copy()
        for i in range(GENE_COUNT):
            if rng.random() < config.GENE_MUTATION_RATE:
                step = rng.gauss(0.0, sigma * _SIGMA_SCALE[i] * _SPAN[i])
                genes[i] += step
        np.clip(genes, _LOWER, _UPPER, out=genes)
        return Genome(genes)

    @staticmethod
    def crossover(a: "Genome", b: "Genome", rng: random.Random) -> "Genome":
        """Uniform crossover: each gene is inherited from either parent."""
        mask = np.array([rng.random() < 0.5 for _ in range(GENE_COUNT)])
        genes = np.where(mask, a.genes, b.genes)
        return Genome(genes)
