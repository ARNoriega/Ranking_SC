from datetime import date

from smash_rankings.core.h2h import calcular_matriz_h2h, normalizar_h2h
from smash_rankings.core.models import Player, SetResult, TorneoNormalizado


def _build_torneo(sets: list[SetResult]) -> TorneoNormalizado:
    return TorneoNormalizado(
        fecha=date(2025, 1, 1),
        nombre="Torneo H2H",
        entrants=[
            Player(gamer_tag="P1"),
            Player(gamer_tag="P2"),
            Player(gamer_tag="P3"),
        ],
        sets=sets,
        placements={},
    )


def test_calcular_matriz_h2h_devuelve_dict_con_clave_por_cada_ganador() -> None:
    torneos = [
        _build_torneo(
            [
                SetResult(winner_id=1, loser_id=2, score="2-0"),
                SetResult(winner_id=2, loser_id=3, score="2-1"),
            ]
        )
    ]

    matriz = calcular_matriz_h2h(torneos)

    assert set(matriz.keys()) == {1, 2}
    assert matriz[1][2] == 1
    assert matriz[2][3] == 1


def test_set_dq_no_aparece_en_matriz() -> None:
    torneos = [
        _build_torneo(
            [
                SetResult(winner_id=1, loser_id=2, score="DQ"),
                SetResult(winner_id=2, loser_id=3, score="2-1"),
            ]
        )
    ]

    matriz = calcular_matriz_h2h(torneos)

    assert 1 not in matriz or 2 not in matriz.get(1, {})
    assert matriz[2][3] == 1


def test_normalizar_h2h_devuelve_valores_entre_0_y_100_y_maximo_100() -> None:
    puntos_h2h = {1: 10.0, 2: 5.0, 3: 0.0}

    normalizados = normalizar_h2h(puntos_h2h)

    assert max(normalizados.values()) == 100.0
    assert all(0.0 <= valor <= 100.0 for valor in normalizados.values())
