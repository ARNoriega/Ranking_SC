import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from smash_rankings import ranking as ranking_module
from smash_rankings.core.models import Player, RankingEntry, RankingTable, TorneoNormalizado
from smash_rankings.services.exporter import export_json


@pytest.fixture
def torneos_ficticios() -> list[TorneoNormalizado]:
    return [
        TorneoNormalizado(
            fecha=date(2025, 1, 10),
            nombre="Torneo A",
            entrants=[Player(gamer_tag="P1"), Player(gamer_tag="P2")],
            sets=[],
            placements={1: 1, 2: 2},
        )
    ]


def test_generar_ranking_sobre_fixtures_reales_devuelve_rankingtable_no_vacio() -> None:
    year_path = Path("data/Resultados/2025")
    if not year_path.exists() or not any(year_path.glob("*.json")):
        pytest.skip("No hay fixtures reales disponibles para 2025")

    ranking = ranking_module.generar_ranking(2025)

    assert isinstance(ranking, RankingTable)
    assert ranking.entries


def test_jugador_con_mas_puntos_en_todos_los_torneos_ocupa_posicion_1(
    monkeypatch: pytest.MonkeyPatch,
    torneos_ficticios: list[TorneoNormalizado],
) -> None:
    monkeypatch.setattr(
        ranking_module,
        "traducciones",
        SimpleNamespace(cargar_torneos=lambda ruta: torneos_ficticios),
        raising=False,
    )
    monkeypatch.setattr(ranking_module.scoring, "calcular_puntos", lambda torneos: {1: 100.0, 2: 50.0})
    monkeypatch.setattr(ranking_module.scoring, "seleccionar_mejores", lambda puntos, n_mejores=3: puntos)
    monkeypatch.setattr(ranking_module.scoring, "normalizar_resultados", lambda puntos: puntos)
    monkeypatch.setattr(ranking_module.h2h, "calcular_matriz_h2h", lambda torneos: {1: {2: 1}, 2: {1: 0}})
    monkeypatch.setattr(ranking_module.h2h, "normalizar_h2h", lambda puntos: {1: 10.0, 2: 0.0})

    ranking = ranking_module.generar_ranking(2025)

    assert isinstance(ranking, RankingTable)
    assert ranking.entries[0].player.gamer_tag == "P1"


def test_export_json_crea_fichero_json_con_claves_esperadas(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    ranking = RankingTable(
        entries=[
            RankingEntry(
                player=Player(gamer_tag="P1"),
                score_total_raw=100.0,
                score_total_normalized=100.0,
                score_results_raw=80.0,
                score_results_normalized=80.0,
                score_h2h_raw=20.0,
                score_h2h_normalized=20.0,
            )
        ]
    )

    export_json(ranking)

    json_files = list(tmp_path.rglob("*.json"))
    assert json_files

    payload = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert "entries" in payload
    assert "player" in payload["entries"][0]
    assert "score_total_raw" in payload["entries"][0]
