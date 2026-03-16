"""Punto de entrada del ranking definido por el diagrama de clases."""

from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

import typer

from . import traducciones
from .config import SeasonConfig, get_season_config
from .core import h2h, scoring
from .core.models import Player, RankingEntry, RankingTable, TorneoNormalizado
from .services.exporter import export_json

PlayerId: TypeAlias = int
ResultadosPorJugador: TypeAlias = dict[PlayerId, float]
PuntuacionesIntegradas: TypeAlias = dict[PlayerId, tuple[float, float]]
AlcanceRanking: TypeAlias = str
app = typer.Typer(add_completion=False, help="Generador de ranking Smash Cantabria")


def integrar_componentes(
    score_resultados: ResultadosPorJugador,
    score_h2h: ResultadosPorJugador,
) -> PuntuacionesIntegradas:
    """Integra resultados y H2H en una estructura unica para el ranking final."""
    player_ids = set(score_resultados) | set(score_h2h)
    return {
        player_id: (
            score_resultados.get(player_id, 0.0),
            score_h2h.get(player_id, 0.0),
        )
        for player_id in player_ids
    }


def _build_player_registry(torneos: list[TorneoNormalizado]) -> dict[PlayerId, Player]:
    registry: dict[PlayerId, Player] = {}
    for torneo in torneos:
        for player_id, player in zip(torneo.placements.keys(), torneo.entrants):
            registry.setdefault(player_id, player)
    return registry


def _count_tournaments_by_player(torneos: list[TorneoNormalizado]) -> dict[PlayerId, int]:
    counts: dict[PlayerId, int] = {}
    for torneo in torneos:
        for player_id in torneo.placements:
            counts[player_id] = counts.get(player_id, 0) + 1
    return counts


def _calculate_h2h_points(matriz_h2h: dict[PlayerId, dict[PlayerId, int]]) -> ResultadosPorJugador:
    return {
        winner_id: float(sum(victorias.values()))
        for winner_id, victorias in matriz_h2h.items()
    }


def _calculate_result_scores(
    torneos: list[TorneoNormalizado],
    config: SeasonConfig,
) -> ResultadosPorJugador:
    try:
        return scoring.calcular_puntos(torneos, config=config)
    except TypeError:
        return scoring.calcular_puntos(torneos)


def generar_ranking(anho: int, alcance: AlcanceRanking = "all") -> RankingTable:
    config: SeasonConfig = get_season_config(anho)
    alcance_efectivo = alcance or config.alcance_jugadores

    base_path = Path(__file__).resolve().parents[2] / "data" / "Resultados" / str(anho)
    torneos = traducciones.cargar_torneos(base_path)
    player_registry = _build_player_registry(torneos)
    participaciones = _count_tournaments_by_player(torneos)

    score_resultados_raw = _calculate_result_scores(torneos, config)
    score_resultados = scoring.normalizar_resultados(score_resultados_raw)

    matriz_h2h = h2h.calcular_matriz_h2h(torneos)
    puntos_h2h_raw = _calculate_h2h_points(matriz_h2h)
    score_h2h = h2h.normalizar_h2h(puntos_h2h_raw)

    componentes = integrar_componentes(score_resultados, score_h2h)
    entries: list[RankingEntry] = []
    aplicar_min_torneos = len(torneos) >= config.min_torneos
    for player_id, (resultado, h2h_score) in componentes.items():
        if aplicar_min_torneos and participaciones.get(player_id, 0) < config.min_torneos:
            continue
        if alcance_efectivo not in {"all", "local"}:
            continue

        player = player_registry.get(player_id, Player(gamer_tag=f"P{player_id}"))
        score_total_raw = (resultado * config.w_resultados) + (h2h_score * config.w_h2h)
        entries.append(
            RankingEntry(
                player=player,
                score_total_raw=score_total_raw,
                score_total_normalized=None,
                score_results_raw=score_resultados_raw.get(player_id, 0.0),
                score_results_normalized=resultado,
                score_h2h_raw=puntos_h2h_raw.get(player_id, 0.0),
                score_h2h_normalized=h2h_score,
            )
        )

    return RankingTable(entries=entries)


@app.command()
def main(
    anho: int = typer.Option(..., "--anho", help="Anho de ranking a generar"),
    a: bool = typer.Option(
        False,
        "--a",
        help="Incluir a todos los jugadores que cumplan minimos (all)",
    ),
    s: bool = typer.Option(
        False,
        "--s",
        help="Incluir solo jugadores locales que cumplan minimos (solo local)",
    ),
) -> None:
    if a and s:
        raise typer.BadParameter("No puedes usar --a y --s a la vez.")

    alcance = "local" if s else "all"
    ranking = generar_ranking(anho=anho, alcance=alcance)
    output_path = export_json(ranking, anho=anho)
    typer.echo(f"Ranking exportado en: {output_path}")


if __name__ == "__main__":
    app()