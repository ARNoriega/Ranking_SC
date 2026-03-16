"""Exportadores definidos por el diagrama de clases."""

from __future__ import annotations

import json
from pathlib import Path

from ..core.models import RankingTable


def _default_json_path(anho: int | None = None) -> Path:
    if anho is None:
        return Path("data") / "Rankings" / "ranking.json"
    return Path("data") / "Rankings" / str(anho) / f"ranking_{anho}.json"


def _default_excel_path(anho: int | None = None) -> Path:
    if anho is None:
        return Path("data") / "Rankings" / "ranking.xlsx"
    return Path("data") / "Rankings" / str(anho) / f"ranking_{anho}.xlsx"


def export_json(
    ranking: RankingTable,
    output_path: str | Path | None = None,
    anho: int | None = None,
) -> Path:
    path = Path(output_path) if output_path is not None else _default_json_path(anho)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(ranking.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def export_excel(
    ranking: RankingTable,
    output_path: str | Path | None = None,
    anho: int | None = None,
) -> Path:
    import pandas as pd

    path = Path(output_path) if output_path is not None else _default_excel_path(anho)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for entry in ranking.entries:
        rows.append(
            {
                "gamer_tag": entry.player.gamer_tag,
                "score_total_raw": entry.score_total_raw,
                "score_total_normalized": entry.score_total_normalized,
                "score_results_raw": entry.score_results_raw,
                "score_results_normalized": entry.score_results_normalized,
                "score_h2h_raw": entry.score_h2h_raw,
                "score_h2h_normalized": entry.score_h2h_normalized,
            }
        )

    pd.DataFrame(rows).to_excel(path, index=False)
    return path