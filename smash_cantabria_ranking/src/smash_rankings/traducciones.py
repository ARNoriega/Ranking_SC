"""Carga y traduccion de torneos al contrato interno."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zlib import crc32

from smash_rankings.core.models import Player, SetResult, TorneoNormalizado
from smash_rankings.io.readers import read_json
from smash_rankings.io.validators import validate_bracket, validate_entrants
from smash_rankings.utils.dates import parse_fecha
from smash_rankings.utils.exceptions import JSONSchemaError, TournamentParseError


def _is_singles_event(event: dict[str, Any]) -> bool:
    name = str(event.get("name", "")).lower()
    slug = str(event.get("slug", "")).lower()
    return "single" in name or "single" in slug


def _select_main_event(events: list[dict[str, Any]]) -> dict[str, Any]:
    singles_events = [event for event in events if _is_singles_event(event)]
    if not singles_events:
        raise TournamentParseError("No se ha encontrado un evento principal de singles.")

    return max(singles_events, key=lambda event: int(event.get("numEntrants", 0)))


def _build_entrants_and_placements(event: dict[str, Any]) -> tuple[list[Player], dict[int, int]]:
    entrants: list[Player] = []
    placements: dict[int, int] = {}

    for node in event["standings"]["nodes"]:
        entrant = node["entrant"]
        participants = entrant["participants"]
        if not participants:
            raise TournamentParseError("Un entrant no tiene participantes asociados.")

        participant = participants[0]
        gamer_tag = participant.get("gamerTag")
        if not gamer_tag:
            raise TournamentParseError("Falta `gamerTag` en un participante del torneo.")

        if participant.get("checkedIn", True) is False:
            continue

        placement = node.get("placement")
        if not isinstance(placement, int):
            raise TournamentParseError("Entrant o placement invalido en standings del torneo.")

        player_id = crc32(gamer_tag.casefold().encode("utf-8"))

        entrants.append(Player(gamer_tag=gamer_tag))
        placements[player_id] = placement

    return entrants, placements


def _resolve_tournament_date(file_path: Path, tournament: dict[str, Any]):
    try:
        return parse_fecha(file_path.name)
    except TournamentParseError:
        start_at = tournament.get("startAt")
        if not isinstance(start_at, int):
            raise
        return datetime.fromtimestamp(start_at, tz=timezone.utc).date()


def cargar_torneos(ruta) -> list[TorneoNormalizado]:
    base_path = Path(ruta)
    files = sorted(base_path.glob("*.json"), key=lambda path: path.name)

    torneos: list[TorneoNormalizado] = []
    for file_path in files:
        try:
            payload = read_json(str(file_path))
            validate_entrants(payload)
            validate_bracket(payload)

            tournament = payload["data"]["tournament"]
            event = _select_main_event(tournament["events"])
            entrants, placements = _build_entrants_and_placements(event)
            tournament_date = _resolve_tournament_date(file_path, tournament)

            torneos.append(
                TorneoNormalizado(
                    fecha=tournament_date,
                    nombre=str(tournament.get("name", file_path.stem)),
                    entrants=entrants,
                    sets=[],
                    placements=placements,
                )
            )
        except (JSONSchemaError, KeyError, TypeError, ValueError) as exc:
            raise TournamentParseError(
                f"No se pudo traducir el torneo '{file_path.name}'."
            ) from exc

    return sorted(torneos, key=lambda torneo: torneo.fecha)