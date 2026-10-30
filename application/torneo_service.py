from collections.abc import Iterable
from datetime import date
import math
from pathlib import Path

from application.contracts import Ranking, RankingProcessor, ResultRepository
from database.json_repository import JsonRepositoryError
from processing.ranking_engine import Torneo


class TorneoService:
    """Caso de uso de entrada y almacenamiento de torneos."""

    def __init__(self, repository: ResultRepository) -> None:
        self.repository = repository

    @staticmethod
    def validar_torneo(torneo: Torneo) -> None:
        if not torneo.nombre.strip():
            raise ValueError("El torneo necesita un nombre")
        if not math.isfinite(torneo.puntuacion) or torneo.puntuacion < 0:
            raise ValueError("La puntuacion del torneo no es valida")
        if torneo.anho < 1:
            raise ValueError("El año del torneo no es valido")
        if not torneo.participantes:
            raise ValueError("El torneo necesita al menos un participante")

        seeds: set[int] = set()
        jugadores: set[str] = set()
        for seed, jugador in torneo.participantes:
            if seed < 1 or not isinstance(jugador, str) or not jugador.strip():
                raise ValueError("El torneo contiene un participante invalido")
            if seed in seeds or jugador in jugadores:
                raise ValueError("El torneo contiene seeds o jugadores repetidos")
            seeds.add(seed)
            jugadores.add(jugador)

    def guardar_torneos(self, torneos: Iterable[Torneo]) -> None:
        torneos = list(torneos)
        for torneo in torneos:
            self.validar_torneo(torneo)
        datos = self.repository.load()
        datos["torneos"] = [
            {
                "nombre": torneo.nombre,
                "anho": torneo.anho,
                "puntuacion": torneo.puntuacion,
                "participantes": [
                    {"seed": seed, "jugador": jugador}
                    for seed, jugador in torneo.participantes
                ],
            }
            for torneo in torneos
        ]
        self.repository.save(datos)

    @staticmethod
    def quitar_duplicados(torneos: Iterable[Torneo]) -> list[Torneo]:
        """Conserva la primera aparición de cada torneo idéntico."""
        resultado: list[Torneo] = []
        vistos: set[tuple[float, int, str, tuple[tuple[int, str], ...]]] = set()
        for torneo in torneos:
            clave = (
                torneo.puntuacion,
                torneo.anho,
                torneo.nombre,
                tuple(torneo.participantes),
            )
            if clave in vistos:
                continue
            vistos.add(clave)
            resultado.append(torneo)
        return resultado

    def cargar_torneos(self) -> list[Torneo]:
        """Carga los torneos guardados y reconstruye sus objetos de dominio."""
        datos = self.repository.load()
        datos_torneos = datos.get("torneos", [])
        if not isinstance(datos_torneos, list):
            raise JsonRepositoryError(
                "Los datos guardados no son validos: 'torneos' debe ser una lista."
            )

        torneos = []
        for indice, datos_torneo in enumerate(datos_torneos, 1):
            if not isinstance(datos_torneo, dict):
                raise JsonRepositoryError(
                    f"Los datos del torneo {indice} no son validos: debe ser un objeto."
                )

            try:
                puntuacion = float(datos_torneo["puntuacion"])
                anho = int(datos_torneo.get("anho", date.today().year))
            except (KeyError, TypeError, ValueError) as error:
                raise JsonRepositoryError(
                    f"El torneo {indice} no tiene una puntuacion o año validos."
                ) from error
            if not math.isfinite(puntuacion) or anho < 1:
                raise JsonRepositoryError(
                    f"El torneo {indice} contiene una puntuacion o año invalidos."
                )

            datos_participantes = datos_torneo.get("participantes")
            if not isinstance(datos_participantes, list):
                raise JsonRepositoryError(
                    f"El torneo {indice} no tiene una lista de participantes valida."
                )

            participantes = []
            seeds: set[int] = set()
            jugadores: set[str] = set()
            for numero, datos_participante in enumerate(datos_participantes, 1):
                if not isinstance(datos_participante, dict):
                    raise JsonRepositoryError(
                        f"El participante {numero} del torneo {indice} no es valido."
                    )
                try:
                    seed = int(datos_participante["seed"])
                    jugador = str(datos_participante["jugador"]).strip()
                except (KeyError, TypeError, ValueError) as error:
                    raise JsonRepositoryError(
                        f"El participante {numero} del torneo {indice} esta incompleto."
                    ) from error
                if seed < 1 or not jugador or seed in seeds or jugador in jugadores:
                    raise JsonRepositoryError(
                        f"El participante {numero} del torneo {indice} tiene un seed o jugador invalido."
                    )
                seeds.add(seed)
                jugadores.add(jugador)
                participantes.append((seed, jugador))

            torneos.append(
                Torneo(
                    puntuacion,
                    participantes,
                    str(datos_torneo.get("nombre", "")).strip(),
                    anho,
                )
            )
        return torneos

    def apartar_archivo_corrupto(self) -> Path | None:
        """Aparta el archivo de datos dañado para permitir continuar usando la app."""
        return self.repository.apartar_archivo_corrupto()

    def eliminar_torneo(self, indice: int) -> list[Torneo]:
        """Elimina un torneo por indice, lo guarda y devuelve la lista resultante."""
        torneos = self.cargar_torneos()
        if not 0 <= indice < len(torneos):
            raise IndexError("Indice de torneo no valido")
        del torneos[indice]
        self.guardar_torneos(torneos)
        return torneos


class TorneoProcessor:
    """Adaptador de la capa de procesado al contrato de aplicacion."""

    def __init__(self, processor: RankingProcessor) -> None:
        self.processor = processor

    def calcular(self, torneos: Iterable[Torneo]) -> Ranking:
        return self.processor.calcular(torneos)
