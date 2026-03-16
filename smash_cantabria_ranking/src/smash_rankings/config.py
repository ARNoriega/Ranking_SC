"""Configuracion de temporada para el ranking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

AlcanceJugadores = Literal["all", "local"]


@dataclass(frozen=True)
class SeasonConfig:
    """Parametros de negocio por temporada.

    Nota: `score_base_por_categoria` y `tabla_reparto` se mantienen como
    estructuras configurables para permitir ajustes sin tocar la logica.
    """

    w_resultados: float
    w_h2h: float
    w_vv: float
    n_mejores: int
    min_torneos: int
    min_sets: int | None
    alcance_jugadores: AlcanceJugadores
    score_base_por_categoria: dict[str, float] = field(default_factory=dict)
    tabla_reparto: dict[str, dict[int, float]] = field(default_factory=dict)


SEASON_CONFIG_BY_ANHO: dict[int, SeasonConfig] = {
    2023: SeasonConfig(
        w_resultados=0.70,
        w_h2h=0.15,
        w_vv=0.15,
        n_mejores=3,
        min_torneos=3,
        min_sets=None,
        alcance_jugadores="all",
    ),
    2024: SeasonConfig(
        w_resultados=0.70,
        w_h2h=0.15,
        w_vv=0.15,
        n_mejores=3,
        min_torneos=3,
        min_sets=None,
        alcance_jugadores="all",
    ),
    2025: SeasonConfig(
        w_resultados=0.70,
        w_h2h=0.15,
        w_vv=0.15,
        n_mejores=3,
        min_torneos=3,
        min_sets=None,
        alcance_jugadores="all",
    ),
    2026: SeasonConfig(
        w_resultados=0.70,
        w_h2h=0.15,
        w_vv=0.15,
        n_mejores=3,
        min_torneos=3,
        min_sets=None,
        alcance_jugadores="all",
    ),
}


def get_season_config(anho: int) -> SeasonConfig:
    """Obtiene la configuracion de temporada para un anho concreto."""
    try:
        return SEASON_CONFIG_BY_ANHO[anho]
    except KeyError as exc:
        raise KeyError(f"No existe configuracion para el anho {anho}.") from exc
