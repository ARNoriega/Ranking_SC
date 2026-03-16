"""Excepciones de dominio definidas por el diagrama de clases."""


class JSONSchemaError(Exception):
    """Error lanzado cuando un JSON no cumple el esquema esperado."""

    pass


class TournamentParseError(Exception):
    """Error lanzado cuando no se puede traducir correctamente un torneo."""

    pass