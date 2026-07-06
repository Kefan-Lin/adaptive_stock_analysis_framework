"""Offline tests for the reproducible holdout sampler (audit C2).

Same seed + source must yield an identical draw; the recorded sha256 must match
the source file; a different seed must change the draw. No network.
"""
from __future__ import annotations

import hashlib
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SAMPLER = ROOT / "reports" / "sample_holdout.py"


def _load():
    spec = importlib.util.spec_from_file_location("sample_holdout", SAMPLER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _source(tmp_path):
    p = tmp_path / "listing.txt"
    p.write_text("\n".join(f"TK{i:03d}" for i in range(60)) + "\n")
    return p


def test_same_seed_same_draw(tmp_path):
    m = _load()
    src = _source(tmp_path)
    a = m.sample(src, n=16, seed=20260706)
    b = m.sample(src, n=16, seed=20260706)
    assert a["tickers"] == b["tickers"]
    assert len(a["tickers"]) == 16


def test_meta_sha256_matches_source(tmp_path):
    m = _load()
    src = _source(tmp_path)
    out = m.sample(src, n=16, seed=20260706)
    expect = hashlib.sha256(src.read_bytes()).hexdigest()
    assert out["_meta"]["sha256"] == expect
    assert out["_meta"]["seed"] == 20260706
    assert out["_meta"]["source"] == str(src)
    assert out["_meta"]["generated"]  # ISO timestamp present


def test_different_seed_different_draw(tmp_path):
    m = _load()
    src = _source(tmp_path)
    a = m.sample(src, n=16, seed=20260706)
    b = m.sample(src, n=16, seed=1)
    assert a["tickers"] != b["tickers"]
