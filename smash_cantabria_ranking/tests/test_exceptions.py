from smash_rankings.utils.exceptions import JSONSchemaError, TournamentParseError


def test_json_schema_error_es_subclase_de_exception() -> None:
    assert issubclass(JSONSchemaError, Exception)


def test_tournament_parse_error_es_subclase_de_exception() -> None:
    assert issubclass(TournamentParseError, Exception)
