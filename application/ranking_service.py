from collections.abc import Iterable

from application.contracts import Ranking, RankingProcessor, ResultRepository
from processing.ranking_engine import Torneo


class RankingService:
    """Orquesta procesado y persistencia sin conocer la interfaz visual."""

    def __init__(
        self,
        repository: ResultRepository,
        processor: RankingProcessor,
    ) -> None:
        self.repository = repository
        self.processor = processor

    def generar_ranking(self, torneos: Iterable[Torneo]) -> Ranking:
        return self.processor.calcular(torneos)

    def guardar_ranking(self, ranking: Ranking, nombre: str = "ranking") -> None:
        datos = self.repository.load()
        datos[nombre] = [
            {"jugador": jugador, "puntuacion": puntuacion}
            for jugador, puntuacion in ranking
        ]
        self.repository.save(datos)

    def generar_y_guardar(
        self,
        torneos: Iterable[Torneo],
        nombre: str = "ranking",
    ) -> Ranking:
        ranking = self.generar_ranking(torneos)
        self.guardar_ranking(ranking, nombre)
        return ranking
