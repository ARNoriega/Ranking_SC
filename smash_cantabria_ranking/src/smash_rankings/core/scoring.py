"""Funciones de scoring definidas por el diagrama de clases."""

from __future__ import annotations

from typing import TypeAlias

from smash_rankings.config import SeasonConfig

from .models import TorneoNormalizado

PlayerId: TypeAlias = int
ResultadosPorJugador: TypeAlias = dict[PlayerId, float]
PuntosPorTorneoJugador: TypeAlias = dict[PlayerId, list[float]]


def calcular_puntos_por_torneo(
    torneos: list[TorneoNormalizado],
    config: SeasonConfig | None = None,
) -> PuntosPorTorneoJugador:
    _ = config
    puntos_por_torneo: PuntosPorTorneoJugador = {}

    for torneo in torneos:
        if not torneo.entrants or not torneo.placements:
            continue

        participantes = max(len(torneo.entrants), len(torneo.placements))
        for player_id, placement in torneo.placements.items():
            puntos = max(float(participantes - placement + 1), 0.0)
            puntos_por_torneo.setdefault(player_id, []).append(puntos)

    return puntos_por_torneo


def calcular_puntos(
    torneos: list[TorneoNormalizado],
    config: SeasonConfig | None = None,
) -> ResultadosPorJugador:
    puntos_por_torneo = calcular_puntos_por_torneo(torneos, config=config)
    if config is not None:
        return seleccionar_mejores(puntos_por_torneo, n_mejores=config.n_mejores)
    return {player_id: sum(puntos) for player_id, puntos in puntos_por_torneo.items()}


def seleccionar_mejores(
    puntos_por_torneo: PuntosPorTorneoJugador,
    n_mejores: int = 3,
) -> ResultadosPorJugador:
    seleccionados: ResultadosPorJugador = {}
    for player_id, puntos in puntos_por_torneo.items():
        mejores = sorted(puntos, reverse=True)[:n_mejores]
        seleccionados[player_id] = sum(mejores)
    return seleccionados


def normalizar_resultados(puntos_resultados: ResultadosPorJugador) -> ResultadosPorJugador:
    if not puntos_resultados:
        return {}

    maximo = max(puntos_resultados.values())
    if maximo <= 0:
        return {player_id: 0.0 for player_id in puntos_resultados}

    return {
        player_id: (puntos / maximo) * 100.0
        for player_id, puntos in puntos_resultados.items()
    }