from datetime import date

import pytest
from pydantic import ValidationError

from smash_rankings.core.models import Player, RankingEntry, RankingTable, SetResult, TorneoNormalizado


def test_player_acepta_gamer_tag_valido_y_rechaza_campos_extra() -> None:
	player = Player(gamer_tag="AND")

	assert player.gamer_tag == "AND"

	with pytest.raises(ValidationError):
		Player(gamer_tag="AND", name="Patrocinado")


def test_player_rechaza_gamer_tag_tipo_incorrecto() -> None:
	with pytest.raises(ValidationError):
		Player(gamer_tag=123)


def test_set_result_acepta_campos_validos() -> None:
	result = SetResult(winner_id=1, loser_id=2, score="2-1")

	assert result.winner_id == 1
	assert result.loser_id == 2
	assert result.score == "2-1"


def test_torneo_normalizado_se_construye_correctamente() -> None:
	torneo = TorneoNormalizado(
		fecha=date(2025, 3, 15),
		nombre="Cantabria Open",
		entrants=[Player(gamer_tag="A"), Player(gamer_tag="B")],
		sets=[SetResult(winner_id=1, loser_id=2, score="2-0")],
		placements={1: 1, 2: 2},
	)

	assert torneo.fecha == date(2025, 3, 15)
	assert torneo.nombre == "Cantabria Open"
	assert len(torneo.entrants) == 2
	assert len(torneo.sets) == 1
	assert torneo.placements[1] == 1


def test_ranking_entry_permite_raw_y_normalized_none() -> None:
	entry = RankingEntry(
		player=Player(gamer_tag="A"),
		score_total_raw=100.0,
		score_total_normalized=None,
		score_results_raw=70.0,
		score_results_normalized=None,
		score_h2h_raw=30.0,
		score_h2h_normalized=None,
	)

	assert entry.score_total_raw == 100.0
	assert entry.score_total_normalized is None
	assert entry.score_results_raw == 70.0
	assert entry.score_h2h_normalized is None


def test_ranking_table_ordena_por_score_total_raw_descendente() -> None:
	ranking = RankingTable(
		entries=[
			RankingEntry(player=Player(gamer_tag="B"), score_total_raw=80.0),
			RankingEntry(player=Player(gamer_tag="A"), score_total_raw=100.0),
		]
	)

	assert [entry.player.gamer_tag for entry in ranking.entries] == ["A", "B"]
