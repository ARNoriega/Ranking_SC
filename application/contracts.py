from collections.abc import Iterable
from pathlib import Path
from typing import Any, Protocol

from processing.ranking_engine import Torneo


Ranking = list[tuple[str, float]]


class RankingProcessor(Protocol):
    """Contrato que necesita la aplicacion para calcular rankings."""

    def calcular(self, torneos: Iterable[Torneo]) -> Ranking:
        ...


class ResultRepository(Protocol):
    """Contrato de persistencia que usa la aplicacion."""

    def load(self) -> dict[str, Any]:
        ...

    def save(self, data: dict[str, Any]) -> None:
        ...

    def apartar_archivo_corrupto(self) -> Path | None:
        ...


class RankingView(Protocol):
    """Contrato de presentacion independiente de la interfaz concreta."""

    def mostrar_ranking(self, ranking: Ranking) -> None:
        ...
