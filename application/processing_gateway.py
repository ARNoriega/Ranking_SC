from collections.abc import Iterable

from application.contracts import Ranking
from processing.ranking_engine import TopAcumulativo, Torneo


class TopAcumulativoProcessor:
    """Puerta de entrada de la aplicacion al motor TopAcumulativo."""

    def calcular(self, torneos: Iterable[Torneo]) -> Ranking:
        return TopAcumulativo(torneos)
