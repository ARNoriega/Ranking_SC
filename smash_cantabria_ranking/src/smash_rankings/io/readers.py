"""Lectores de JSON de torneos."""

import json
from pathlib import Path
from typing import Any


def read_json(path: str) -> dict[str, Any]:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise TypeError("El JSON del torneo debe tener un objeto en la raiz.")

    return payload