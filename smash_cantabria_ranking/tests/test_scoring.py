from datetime import date

from smash_rankings.core.models import Player, TorneoNormalizado
from smash_rankings.core.scoring import calcular_puntos, normalizar_resultados, seleccionar_mejores


def _build_torneo(
    *,
    nombre: str,
    entrants_count: int,
    placements: dict[int, int],
) -> TorneoNormalizado:
    entrants = [Player(gamer_tag=f"P{idx}") for idx in range(1, entrants_count + 1)]
    return TorneoNormalizado(
        fecha=date(2025, 1, 1),
        nombre=nombre,
        entrants=entrants,
        sets=[],
        placements=placements,
    )


def test_calcular_puntos_devuelve_entrada_por_jugador_activo() -> None:
    torneos = [
        _build_torneo(
            nombre="Torneo A",
            entrants_count=2,
            placements={1: 1, 2: 2},
        )
    ]

    puntos = calcular_puntos(torneos)

    assert set(puntos.keys()) == {1, 2}


def test_placement_1_recibe_mas_puntos_que_placement_2_mismo_torneo() -> None:
    torneos = [
        _build_torneo(
            nombre="Torneo A",
            entrants_count=2,
            placements={1: 1, 2: 2},
        )
    ]

    puntos = calcular_puntos(torneos)

    assert puntos[1] > puntos[2]


def test_seleccionar_mejores_devuelve_exactamente_n_torneos_por_jugador() -> None:
    puntos_por_torneo = {
        1: [100.0, 80.0, 60.0, 40.0],
        2: [90.0, 70.0, 50.0, 30.0],
    }

    seleccion = seleccionar_mejores(puntos_por_torneo, n_mejores=3)

    assert seleccion[1] == 240.0
    assert seleccion[2] == 210.0


def test_normalizar_resultados_escala_0_a_100_y_maximo_es_100() -> None:
    puntos_resultados = {1: 50.0, 2: 25.0, 3: 0.0}

    normalizados = normalizar_resultados(puntos_resultados)

    assert max(normalizados.values()) == 100.0
    assert all(0.0 <= value <= 100.0 for value in normalizados.values())


def test_torneos_con_0_entrants_no_entran_en_calculo() -> None:
    torneos = [
        _build_torneo(
            nombre="Torneo Vacio",
            entrants_count=0,
            placements={},
        ),
        _build_torneo(
            nombre="Torneo Con Datos",
            entrants_count=2,
            placements={1: 1, 2: 2},
        ),
    ]

    puntos = calcular_puntos(torneos)

    assert set(puntos.keys()) == {1, 2}
