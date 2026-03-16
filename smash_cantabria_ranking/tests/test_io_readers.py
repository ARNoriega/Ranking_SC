import json
from pathlib import Path

import pytest

from smash_rankings.io.readers import read_json


@pytest.fixture
def torneo_fixture_path() -> Path:
    path = Path("data/Resultados/2026/dungeons-and-downairs-1.json")
    if not path.exists():
        pytest.skip("No existe el fixture real esperado en data/Resultados/2026")
    return path


def test_readers_carga_json_fixture_y_devuelve_estructura_valida(
    torneo_fixture_path: Path,
) -> None:
    payload = read_json(str(torneo_fixture_path))

    assert isinstance(payload, dict)
    assert "data" in payload
    assert "tournament" in payload["data"]
    assert isinstance(payload["data"]["tournament"].get("events", []), list)


@pytest.mark.parametrize("scenario", ["missing_path", "invalid_json"])
def test_readers_lanza_error_controlado_ruta_inexistente_o_json_invalido(
    tmp_path: Path,
    scenario: str,
) -> None:
    if scenario == "missing_path":
        target = tmp_path / "no-existe.json"
        with pytest.raises(FileNotFoundError):
            read_json(str(target))
        return

    target = tmp_path / "invalido.json"
    target.write_text('{"data": ', encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        read_json(str(target))
