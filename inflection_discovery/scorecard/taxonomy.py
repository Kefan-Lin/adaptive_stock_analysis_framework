"""Numerically specified scorecard taxonomy (resolves review SC3).

Single source of truth for both engines. Thresholds are explicit constants, not
"percentile-based" hand-waving. Percentiles, where used, are self-relative
(versus the name's own trailing history) and point-in-time (data <= T only).
"""
from __future__ import annotations

# --- Dimension A: depressed base (HARD GATE) ---
A_GATE_MIN_DRAWDOWN = 0.30      # must be >=30% below its 3y high to count as depressed
A_DRAWDOWN_FULL = 0.60         # 60%+ drawdown -> full depressedness on that sub-signal
A_HIGH_WINDOW_DAYS = 1095      # 3 CALENDAR years for the "high" reference (sliced by date)
A_LOW_WINDOW_DAYS = 365        # 52 weeks for the "low" reference (sliced by date)
A_LOW_PROX_NEAR = 0.10         # within 10% of the 52w low -> full
A_LOW_PROX_FAR = 1.00          # 100%+ above the low -> zero
VAL_MIN_QUARTERS = 8           # need >=8 quarters to compute a P/S-vs-history percentile

# --- Dimension B: earnings second derivative ---
B_ACCEL_SCALE = 0.05           # YoY-growth acceleration scale for the logistic
B_MARGIN_DELTA_SCALE = 0.02    # gross-margin QoQ delta scale
B_MARGIN_TROUGH_WINDOW = 8     # quarters to define the margin trough
B_MARGIN_TROUGH_FULL = 0.10    # +10pp off the trough -> full off-trough credit
MIN_QUARTERS_SEASONAL = 5      # need >=5 quarters for YoY-of-YoY accel; below this it is suppressed
YOY_TOLERANCE_DAYS = 45        # how close to 365d-ago a quarter match must be
DAYS_PER_QUARTER = 91.25

# --- Dimension C: narrative re-rating (lightweight text features) ---
INFLECTION_KEYWORDS = [
    "artificial intelligence", "data center", "datacenter", "hbm",
    "high bandwidth memory", "design win", "record revenue", "record quarter",
    "demand recovery", "strong demand", "strategic alternatives",
    "strategic review", "restructuring", "cost reduction", "new chief executive",
    "spin-off", "spinoff", "share repurchase", "return to growth", "inflection",
    "ramp", "backlog", "book-to-bill", "bookings", "5g", "optical",
    "transceiver", "accelerating", "turnaround",
]
# Cover-page / glossary boilerplate stripped before keyword matching so it does
# not inflate C (e.g. "large accelerated filer", "FedRAMP") — review A-vs-B finding.
C_BOILERPLATE = [
    "large accelerated filer", "non-accelerated filer", "accelerated filer",
    "smaller reporting company", "emerging growth company",
    "well-known seasoned issuer",
]
C_KEYWORD_FULL = 8             # distinct keywords present for full "presence" credit
C_DELTA_SCALE = 5.0            # change in total keyword hits vs prior filing

# --- Trap / head-fake filter ---
TRAP_DILUTION_YOY = 0.20       # >20% YoY share growth is dilutive
TRAP_DILUTION_FULL = 0.50      # 50%+ -> full dilution flag
TRAP_RUNWAY_QUARTERS = 4.0     # < 4 quarters of cash at current burn is risky
TRAP_SECULAR_CAGR = -0.05      # 3y revenue CAGR below this, with no acceleration, = secular
TRAP_CEILING = 0.70            # candidates above this trap_risk are not surfaced

# Spec §Metrics liquidity haircut: names whose trailing-60-session median
# dollar volume at the as-of date is below this are not costlessly investable;
# they are excluded from top-N eligibility and counted as excluded_illiquid.
MIN_ADV_USD = 1_000_000.0

# --- D (ranker) and composite weights ---
D_W_A = 0.4                    # weight on depressedness (reduced: rank on the turn, not raw cheapness)
D_W_TURN = 0.5                 # weight on max(B, C)
D_W_MOM = 0.1                  # weight on early price-reclaim momentum
D_TRAP_PENALTY = 0.4          # D is scaled down by up to this fraction by trap_risk
SMA_FAST = 50                  # fast moving average for the early-momentum check
