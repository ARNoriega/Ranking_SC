from datetime import date

import pytest

from smash_rankings.utils.dates import parse_fecha
from smash_rankings.utils.exceptions import TournamentParseError


def test_parse_fecha_devuelve_date_valida() -> None:
    assert parse_fecha("2025-03-15_Cantabria-Open.json") == date(2025, 3, 15)


def test_parse_fecha_lanza_tournament_parse_error_con_nombre_invalido() -> None:
    with pytest.raises(TournamentParseError):
        parse_fecha("Cantabria-Open-2025.json")
