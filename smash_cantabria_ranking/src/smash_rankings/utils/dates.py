"""Utilidades de fechas definidas por el diagrama de clases."""

import re
from datetime import date

from smash_rankings.utils.exceptions import TournamentParseError


def parse_fecha(nombre_archivo: str) -> date:
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})_.*\.json$", nombre_archivo)
    if not match:
        raise TournamentParseError(
            "Nombre de archivo invalido: se esperaba 'YYYY-MM-DD_<torneo>.json'."
        )

    year, month, day = map(int, match.groups())
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise TournamentParseError(f"Fecha invalida en nombre de archivo: {nombre_archivo}") from exc