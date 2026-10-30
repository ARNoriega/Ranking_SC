from application.contracts import Ranking, RankingView


class ConsoleRankingView:
    """Presentacion por consola; puede sustituirse por GUI o web."""

    def mostrar_ranking(self, ranking: Ranking) -> None:
        for puesto, (jugador, puntuacion) in enumerate(ranking, start=1):
            print(f"{puesto}. {jugador}: {puntuacion:.4f}")


class RankingPresenter:
    """Presentador que mantiene la vista fuera de la logica de negocio."""

    def __init__(self, view: RankingView) -> None:
        self.view = view

    def presentar(self, ranking: Ranking) -> None:
        self.view.mostrar_ranking(ranking)
