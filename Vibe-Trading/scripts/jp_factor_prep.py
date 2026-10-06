"""日本株の主要銘柄で Alpha Zoo のファクターを計算し、factor_analysis 用の CSV を作る。

- 価格: yfinance の調整後終値（配当・分割反映）
- ファクター: Vibe-Trading 同梱の Alpha Zoo をそのまま使う（Registry.compute）
- リターン: factor_analysis は内部でシフトしないため、「翌日以降のリターン」を自前で作る
"""
from pathlib import Path

import pandas as pd
import yfinance as yf

from src.factors.registry import get_default_registry

OUT = Path(__file__).resolve().parent.parent / "data"
OUT.mkdir(exist_ok=True)

TICKERS = [
    "7203.T", "6758.T", "9984.T", "8306.T", "6861.T", "9432.T", "8035.T", "6098.T",
    "4063.T", "8058.T", "8031.T", "9983.T", "7974.T", "6501.T", "7267.T", "8316.T",
    "4502.T", "2914.T", "6367.T", "6902.T", "9433.T", "8001.T", "8766.T", "6594.T",
    "7741.T", "4519.T", "6954.T", "7751.T", "5108.T", "9434.T",
]
START, END = "2018-01-01", "2026-10-02"
ALPHAS = ["academic_carhart_mom", "academic_high52w", "academic_bab"]
# 評価期間: 252営業日のウォームアップを避けるため 2020 年以降
EVAL_START = "2020-01-01"

raw = yf.download(TICKERS, start=START, end=END, auto_adjust=True, progress=False)
panel = {
    "close": raw["Close"],
    "open": raw["Open"],
    "high": raw["High"],
    "low": raw["Low"],
    "volume": raw["Volume"],
}
close = panel["close"].dropna(axis=1, how="all")
panel = {k: v[close.columns] for k, v in panel.items()}
print("銘柄数:", close.shape[1], " 期間:", close.index[0].date(), "〜", close.index[-1].date(), " 日数:", len(close))

reg = get_default_registry()
for aid in ALPHAS:
    f = reg.compute(aid, panel).loc[EVAL_START:]
    f.to_csv(OUT / f"{aid}.csv")
    print(aid, "->", f.shape, " NaN率:", round(float(f.isna().mean().mean()), 3))

# 翌日リターン / 20営業日先リターン（ファクター日付 t に対して、t より後の値動き）
for h, name in [(1, "ret_fwd1"), (20, "ret_fwd20")]:
    r = (close.shift(-h) / close - 1).loc[EVAL_START:]
    r.to_csv(OUT / f"{name}.csv")
    print(name, r.shape)
