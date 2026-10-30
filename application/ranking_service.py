from collections.abc import Iterable
import math

from application.contracts import Ranking, RankingProcessor, ResultRepository
from database.json_repository import JsonRepositoryError
from processing.ranking_engine import Torneo


class RankingService:
    """Orquesta procesado y persistencia sin conocer la interfaz visual."""

    PREFIJO_NOMBRE = "ranking_"

    def __init__(
        self,
        repository: ResultRepository,
        processor: RankingProcessor,
    ) -> None:
        self.repository = repository
        self.processor = processor

    def generar_ranking(self, torneos: Iterable[Torneo]) -> Ranking:
        return self.processor.calcular(torneos)

    @staticmethod
    def validar_ranking(ranking: Ranking) -> None:
        if not ranking:
            raise ValueError("El ranking no puede estar vacio")
        jugadores: set[str] = set()
        puntuacion_anterior = math.inf
        for puesto, resultado in enumerate(ranking, 1):
            if not isinstance(resultado, tuple) or len(resultado) != 2:
                raise ValueError(f"El resultado {puesto} no es valido")
            jugador, puntuacion = resultado
            if not isinstance(jugador, str) or not jugador.strip():
                raise ValueError(f"El jugador del puesto {puesto} no es valido")
            if jugador in jugadores:
                raise ValueError(f"El jugador '{jugador}' esta repetido")
            try:
                puntuacion = float(puntuacion)
            except (TypeError, ValueError) as error:
                raise ValueError(f"La puntuacion del puesto {puesto} no es valida") from error
            if not math.isfinite(puntuacion):
                raise ValueError(f"La puntuacion del puesto {puesto} no es finita")
            if puntuacion > puntuacion_anterior:
                raise ValueError("Las puntuaciones deben estar ordenadas de mayor a menor")
            jugadores.add(jugador)
            puntuacion_anterior = puntuacion

    def guardar_ranking(
        self,
        ranking: Ranking,
        nombre: str = "ranking",
        *,
        sobrescribir: bool = False,
    ) -> None:
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El ranking necesita un nombre")
        self.validar_ranking(ranking)
        datos = self.repository.load()
        if nombre in datos and not sobrescribir:
            raise FileExistsError(
                f"El ranking '{nombre}' ya existe. Confirma la sobrescritura para reemplazarlo."
            )
        datos[nombre] = [
            {"jugador": jugador, "puntuacion": puntuacion}
            for jugador, puntuacion in ranking
        ]
        self.repository.save(datos)

    def listar_rankings(self) -> list[str]:
        """Devuelve los nombres de los rankings guardados."""
        datos = self.repository.load()
        return sorted(
            nombre
            for nombre, contenido in datos.items()
            if nombre.startswith(self.PREFIJO_NOMBRE)
        )

    def cargar_ranking(self, nombre: str) -> Ranking:
        """Carga y valida un ranking guardado."""
        datos = self.repository.load()
        contenido = datos.get(nombre)
        if not isinstance(contenido, list):
            raise JsonRepositoryError(
                f"El ranking '{nombre}' no existe o no tiene un formato valido."
            )

        ranking: Ranking = []
        jugadores: set[str] = set()
        for indice, resultado in enumerate(contenido, 1):
            if not isinstance(resultado, dict):
                raise JsonRepositoryError(
                    f"El resultado {indice} del ranking '{nombre}' no es valido."
                )
            try:
                jugador = resultado["jugador"]
                puntuacion = float(resultado["puntuacion"])
            except (KeyError, TypeError, ValueError) as error:
                raise JsonRepositoryError(
                    f"El resultado {indice} del ranking '{nombre}' esta incompleto."
                ) from error
            if (
                not isinstance(jugador, str)
                or not jugador.strip()
                or jugador in jugadores
                or not math.isfinite(puntuacion)
            ):
                raise JsonRepositoryError(
                    f"El resultado {indice} del ranking '{nombre}' contiene datos invalidos."
                )
            jugador = jugador.strip()
            jugadores.add(jugador)
            ranking.append((jugador, puntuacion))
        try:
            self.validar_ranking(ranking)
        except ValueError as error:
            raise JsonRepositoryError(
                f"El ranking '{nombre}' contiene datos invalidos: {error}."
            ) from error
        return ranking

    def eliminar_ranking(self, nombre: str) -> None:
        """Elimina un ranking guardado por su nombre."""
        datos = self.repository.load()
        if nombre not in datos or not nombre.startswith(self.PREFIJO_NOMBRE):
            raise ValueError(f"El ranking '{nombre}' no existe")
        del datos[nombre]
        self.repository.save(datos)

    def generar_y_guardar(
        self,
        torneos: Iterable[Torneo],
        nombre: str = "ranking",
    ) -> Ranking:
        ranking = self.generar_ranking(torneos)
        self.guardar_ranking(ranking, nombre)
        return ranking
