import json
from pathlib import Path

import pytest

from smash_rankings.io.validators import validate_bracket, validate_entrants
from smash_rankings.utils.exceptions import JSONSchemaError


@pytest.fixture
def torneo_payload() -> dict:
    path = Path("data/Resultados/2026/dungeons-and-downairs-1.json")
    if not path.exists():
        pytest.skip("No existe el fixture real esperado en data/Resultados/2026")
    return json.loads(path.read_text(encoding="utf-8"))


def test_validators_aceptan_json_con_esquema_correcto(torneo_payload: dict) -> None:
    validate_entrants(torneo_payload)
    validate_bracket(torneo_payload)


@pytest.mark.parametrize("validator", [validate_entrants, validate_bracket])
def test_validators_lanzan_error_de_esquema_si_faltan_claves(validator) -> None:
    payload_incompleto = {
        "data": {
            "tournament": {
                "events": []
            }
        }
    }

    with pytest.raises(JSONSchemaError):
        validator(payload_incompleto)
