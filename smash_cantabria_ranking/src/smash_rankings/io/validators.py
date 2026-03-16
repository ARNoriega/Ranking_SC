"""Validadores de JSON definidos por el diagrama de clases."""

from __future__ import annotations

from typing import Any

from smash_rankings.utils.exceptions import JSONSchemaError


def _require_dict(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise JSONSchemaError(f"Se esperaba un objeto JSON en '{path}'.")
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise JSONSchemaError(f"Se esperaba una lista en '{path}'.")
    return value


def _require_key(container: dict[str, Any], key: str, path: str) -> Any:
    if key not in container:
        raise JSONSchemaError(f"Falta la clave requerida '{path}.{key}'.")
    return container[key]


def _get_tournament(payload: Any) -> dict[str, Any]:
    root = _require_dict(payload, "root")
    data = _require_dict(_require_key(root, "data", "root"), "data")
    tournament = _require_dict(
        _require_key(data, "tournament", "data"),
        "data.tournament",
    )

    _require_key(tournament, "startAt", "data.tournament")
    return tournament


def _get_events(payload: Any) -> list[dict[str, Any]]:
    tournament = _get_tournament(payload)
    events = _require_list(
        _require_key(tournament, "events", "data.tournament"),
        "data.tournament.events",
    )
    if not events:
        raise JSONSchemaError("La lista 'data.tournament.events' no puede estar vacia.")

    normalized_events: list[dict[str, Any]] = []
    for index, event in enumerate(events):
        event_dict = _require_dict(event, f"data.tournament.events[{index}]")
        normalized_events.append(event_dict)
    return normalized_events


def validate_entrants(payload):
    events = _get_events(payload)

    for index, event in enumerate(events):
        event_path = f"data.tournament.events[{index}]"
        _require_key(event, "id", event_path)
        _require_key(event, "name", event_path)
        _require_key(event, "slug", event_path)
        _require_key(event, "numEntrants", event_path)

        standings = _require_dict(_require_key(event, "standings", event_path), f"{event_path}.standings")
        nodes = _require_list(_require_key(standings, "nodes", f"{event_path}.standings"), f"{event_path}.standings.nodes")

        for node_index, node in enumerate(nodes):
            node_path = f"{event_path}.standings.nodes[{node_index}]"
            node_dict = _require_dict(node, node_path)
            entrant = _require_dict(_require_key(node_dict, "entrant", node_path), f"{node_path}.entrant")
            _require_key(entrant, "id", f"{node_path}.entrant")
            _require_key(entrant, "name", f"{node_path}.entrant")
            _require_list(
                _require_key(entrant, "participants", f"{node_path}.entrant"),
                f"{node_path}.entrant.participants",
            )


def validate_bracket(payload):
    events = _get_events(payload)

    for index, event in enumerate(events):
        event_path = f"data.tournament.events[{index}]"
        _require_key(event, "id", event_path)
        _require_key(event, "name", event_path)
        _require_key(event, "slug", event_path)
        _require_key(event, "numEntrants", event_path)

        standings = _require_dict(_require_key(event, "standings", event_path), f"{event_path}.standings")
        nodes = _require_list(_require_key(standings, "nodes", f"{event_path}.standings"), f"{event_path}.standings.nodes")

        for node_index, node in enumerate(nodes):
            node_path = f"{event_path}.standings.nodes[{node_index}]"
            node_dict = _require_dict(node, node_path)
            _require_key(node_dict, "placement", node_path)
            entrant = _require_dict(_require_key(node_dict, "entrant", node_path), f"{node_path}.entrant")
            _require_key(entrant, "id", f"{node_path}.entrant")
            _require_key(entrant, "name", f"{node_path}.entrant")
            _require_list(
                _require_key(entrant, "participants", f"{node_path}.entrant"),
                f"{node_path}.entrant.participants",
            )