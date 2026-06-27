"""The shared scorecard IP: the A/B/C/D taxonomy and its scoring.

Both engines read the SAME taxonomy and scoring so A and B are comparable.
"""
from .score import compute_dimensions, score_A, score_B, score_C, trap_risk, score_D  # noqa: F401
