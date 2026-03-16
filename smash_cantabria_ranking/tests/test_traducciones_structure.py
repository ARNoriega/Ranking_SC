import json
from pathlib import Path

import pytest

from smash_rankings.core.models import TorneoNormalizado
from smash_rankings.traducciones import cargar_torneos
from smash_rankings.utils.exceptions import TournamentParseError


def _single_event_payload(*, entrants: list[dict], placements: list[tuple[int, int]]) -> dict:
	nodes = []
	for placement, entrant_id in placements:
		gamer_tag = next(e["gamer_tag"] for e in entrants if e["id"] == entrant_id)
		checked_in = next(e["checked_in"] for e in entrants if e["id"] == entrant_id)
		nodes.append(
			{
				"placement": placement,
				"entrant": {
					"id": entrant_id,
					"name": gamer_tag,
					"participants": [
						{
							"id": entrant_id,
							"gamerTag": gamer_tag,
							"checkedIn": checked_in,
						}
					],
				},
			}
		)

	return {
		"data": {
			"tournament": {
				"id": 1,
				"name": "Torneo de prueba",
				"startAt": 1736467200,
				"events": [
					{
						"id": 10,
						"name": "Ultimate Singles",
						"slug": "tournament/test/event/ultimate-singles",
						"numEntrants": len(entrants),
						"videoGame": {"id": 1386, "name": "Super Smash Bros. Ultimate"},
						"standings": {
							"pageInfo": {
								"total": len(nodes),
								"totalPages": 1,
								"page": 1,
								"perPage": 512,
							},
							"nodes": nodes,
						},
					}
				],
			}
		}
	}


def _write_fixture(path: Path, payload: dict) -> None:
	path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_cargar_torneos_devuelve_lista_de_torneo_normalizado(tmp_path: Path) -> None:
	payload = _single_event_payload(
		entrants=[
			{"id": 1, "gamer_tag": "A", "checked_in": True},
			{"id": 2, "gamer_tag": "B", "checked_in": True},
		],
		placements=[(1, 1), (2, 2)],
	)
	_write_fixture(tmp_path / "2025-01-10_torneo-a.json", payload)

	torneos = cargar_torneos(str(tmp_path))

	assert isinstance(torneos, list)
	assert torneos
	assert all(isinstance(t, TorneoNormalizado) for t in torneos)


def test_cargar_torneos_devuelve_lista_ordenada_por_fecha_ascendente(tmp_path: Path) -> None:
	payload = _single_event_payload(
		entrants=[
			{"id": 1, "gamer_tag": "A", "checked_in": True},
			{"id": 2, "gamer_tag": "B", "checked_in": True},
		],
		placements=[(1, 1), (2, 2)],
	)
	_write_fixture(tmp_path / "2025-02-10_torneo-b.json", payload)
	_write_fixture(tmp_path / "2025-01-10_torneo-a.json", payload)

	torneos = cargar_torneos(str(tmp_path))
	fechas = [t.fecha for t in torneos]

	assert fechas == sorted(fechas)


def test_cargar_torneos_ignora_jugadores_con_checked_in_false(tmp_path: Path) -> None:
	payload = _single_event_payload(
		entrants=[
			{"id": 1, "gamer_tag": "A", "checked_in": True},
			{"id": 2, "gamer_tag": "B", "checked_in": False},
		],
		placements=[(1, 1), (2, 2)],
	)
	_write_fixture(tmp_path / "2025-01-10_torneo-a.json", payload)

	torneos = cargar_torneos(str(tmp_path))
	gamer_tags = {player.gamer_tag for player in torneos[0].entrants}

	assert "A" in gamer_tags
	assert "B" not in gamer_tags


def test_cargar_torneos_lanza_tournament_parse_error_si_falta_info_requerida(
	tmp_path: Path,
) -> None:
	payload = {
		"data": {
			"tournament": {
				"id": 1,
				"name": "Invalido",
				"startAt": 1736467200,
				"events": [],
			}
		}
	}
	_write_fixture(tmp_path / "2025-01-10_torneo-invalido.json", payload)

	with pytest.raises(TournamentParseError):
		cargar_torneos(str(tmp_path))
