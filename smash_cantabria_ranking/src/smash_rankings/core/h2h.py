"""Funciones auxiliares de H2H definidas por el diagrama de clases."""

from __future__ import annotations

from typing import TypeAlias

from .models import TorneoNormalizado

PlayerId: TypeAlias = int
MatrizH2H: TypeAlias = dict[PlayerId, dict[PlayerId, int]]
PuntosH2H: TypeAlias = dict[PlayerId, float]


def calcular_matriz_h2h(torneos: list[TorneoNormalizado]) -> MatrizH2H:
    matriz: MatrizH2H = {}

    for torneo in torneos:
        for set_result in torneo.sets:
            if set_result.score.strip().upper() == "DQ":
                continue
            matriz.setdefault(set_result.winner_id, {})
            matriz[set_result.winner_id][set_result.loser_id] = (
                matriz[set_result.winner_id].get(set_result.loser_id, 0) + 1
            )

    return matriz


def normalizar_h2h(puntos_h2h: PuntosH2H) -> PuntosH2H:
    if not puntos_h2h:
        return {}

    maximo = max(puntos_h2h.values())
    if maximo <= 0:
        return {player_id: 0.0 for player_id in puntos_h2h}

    return {
        player_id: (puntos / maximo) * 100.0
        for player_id, puntos in puntos_h2h.items()
    }