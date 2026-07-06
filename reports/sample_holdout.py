#!/usr/bin/env python
"""Reproducible holdout sampler (audit C2). Usage:
    python reports/sample_holdout.py --source <ticker-list.txt> --n 16 --seed 20260706 --out reports/holdout_universe_next.json
Writes {"_meta": {"seed":…, "source":…, "sha256":…, "generated":…}, "tickers":[…]}.
The source file must be a point-in-time listing snapshot (one ticker per line);
its sha256 is recorded so the draw is verifiable."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


def _read_tickers(source: Path) -> List[str]:
    """One ticker per line; blanks and '#' comments ignored, order preserved."""
    out: List[str] = []
    for line in source.read_text().splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            out.append(s)
    return out


def sample(source: Path, n: int, seed: int) -> Dict:
    """Draw `n` tickers from a listing snapshot with a fixed seed.

    The draw is `random.Random(seed).sample` over the de-duplicated, order-stable
    ticker list, so (source, n, seed) fully determines the result. The source's
    sha256 is recorded in `_meta` so the exact input can be verified later.
    """
    source = Path(source)
    tickers = _read_tickers(source)
    # De-duplicate while preserving first-seen order (stable input to the RNG).
    seen: set = set()
    pool = [t for t in tickers if not (t in seen or seen.add(t))]
    if n > len(pool):
        raise ValueError(f"requested n={n} exceeds pool size {len(pool)} in {source}")
    drawn = random.Random(seed).sample(pool, n)
    return {
        "_meta": {
            "seed": seed,
            "source": str(source),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "generated": datetime.now(timezone.utc).isoformat(),
        },
        "tickers": drawn,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, help="point-in-time listing snapshot, one ticker per line")
    ap.add_argument("--n", type=int, default=16)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    result = sample(Path(a.source), n=a.n, seed=a.seed)
    Path(a.out).write_text(json.dumps(result, indent=1))
    print(f"drew {len(result['tickers'])} tickers (seed={a.seed}) -> {a.out}")
    print(f"  source sha256 = {result['_meta']['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
