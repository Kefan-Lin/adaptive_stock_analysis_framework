"""China A-share variant (LIVE discovery).

IMPORTANT — why this is LIVE, not a point-in-time backtest: we verified that
akshare's A-share earnings (`stock_yjbb_em`) carry only the *latest* disclosure
date (最新公告日期) — for a 2021-Q1 snapshot, 97% of rows show a 2022 date because
the next annual report re-disclosed the period — and the values are
current-restated. So, exactly like the US akshare path, A-share fundamentals
cannot be reconstructed as-originally-reported on free data. hfq prices ARE
point-in-time-safe, but with restated fundamentals a clean A-share PIT backtest
is not achievable on free data. This module therefore extends the mechanism to
the A-share market for LIVE discovery only.
"""
