from typing import Dict

import pandas as pd


class SignalEngine:
    """比較用: 全銘柄を等金額で保有する（毎月リバランス）。"""

    def generate(self, data_map: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        n = len(data_map)
        return {c: pd.Series(1.0 / n, index=df.index) for c, df in data_map.items()}
