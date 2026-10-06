from typing import Dict

import pandas as pd

LOOKBACK = 252
TOP_N = 5


class SignalEngine:
    """52週高値モメンタム: 終値 / 252日最高値 が高い上位N銘柄を等金額で保有する。"""

    def generate(self, data_map: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        close = pd.DataFrame({c: df["close"] for c, df in data_map.items()}).sort_index()
        score = close / close.rolling(LOOKBACK, min_periods=LOOKBACK).max()
        rank = score.rank(axis=1, ascending=False, method="first")
        selected = (rank <= TOP_N) & score.notna()
        weight = selected.astype(float) / TOP_N
        return {c: weight[c].reindex(df.index).fillna(0.0) for c, df in data_map.items()}
