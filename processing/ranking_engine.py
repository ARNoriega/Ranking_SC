from dataclasses import dataclass, field
from itertools import islice
from collections import defaultdict
from typing import Final, Iterable


PAGERANK_CONSTANT: Final[float] = 1.0
factor_torneo: Final[float] = 0.8
factor_head2head: Final[float] = 0.2
factor_historial: Final[float] = 0.6
factor_recencia: Final[float] = 0.4
suelo_historial: Final[float] = 0.5


@dataclass
class Torneo:
    """Torneo con puntuacion externa y participantes (seed, jugador)."""

    puntuacion: float
    participantes: list[tuple[int, str]] = field(default_factory=list)
    nombre: str = ""
    anho: int = 0

    @property
    def puntuación(self) -> float:
        """Alias compatible para el nombre original del atributo."""
        return self.puntuacion

    def ordenar_participantes(self) -> None:
        self.participantes.sort(key=lambda participante: participante[0])

    def _limite_top(self) -> int:
        jugadores = len(self.participantes)
        puntos = self.puntuacion
        top = 0
        if jugadores >= 16:
            top = 8
            if jugadores > 24 and puntos >= 800:
                top = 16
                if puntos >= 1300:
                    top = 24
                    if jugadores > 64 and puntos >= 1800:
                        top = 32
                        if puntos >= 2800:
                            top = 48
                            if jugadores > 96 and puntos >= 3500:
                                top = 64
                                if puntos >= 4200:
                                    top = 96
                                    if puntos >= 5000:
                                        top = 128
        return top

    def Top(self) -> list[tuple[int, str]]:
        """Devuelve los participantes que puntuan."""
        return self.participantes[:self._limite_top()]


def _normaliza(valores: dict[str, float]) -> dict[str, float]:
    if not valores:
        return {}
    minimo = min(valores.values())
    maximo = max(valores.values())
    intervalo = maximo - minimo
    if intervalo == 0:
        return {nombre: 1.0 for nombre in valores}
    return {nombre: (valor - minimo) / intervalo for nombre, valor in valores.items()}


def puntua(torneo: Torneo, participante: str | None = None):
    """Calcula puntos por puesto para uno o todos los participantes del top."""
    top = torneo._limite_top()
    if participante is not None:
        for puesto, (_, nombre) in enumerate(islice(torneo.participantes, top), 1):
            if nombre == participante:
                return participante, torneo.puntuacion / puesto
        return None
    return [
        (nombre, torneo.puntuacion / puesto)
        for puesto, (_, nombre) in enumerate(islice(torneo.participantes, top), 1)
    ]


def TopAcumulativo(torneos: Iterable[Torneo]) -> list[tuple[str, float]]:
    """Ranking acumulativo: puntuacion de torneo mas factor upset."""
    puntuaciones: dict[str, float] = defaultdict(float)
    factores_upset: dict[str, float] = defaultdict(float)
    for torneo in torneos:
        for puesto, (seed, jugador) in enumerate(torneo.Top(), 1):
            puntuaciones[jugador] += torneo.puntuacion / puesto
            factores_upset[jugador] += seed - puesto
    normalizadas = _normaliza(dict(puntuaciones))
    upsets_normalizados = _normaliza(dict(factores_upset))
    return sorted(
        [
            (
                jugador,
                factor_torneo * normalizadas[jugador]
                + factor_head2head * upsets_normalizados[jugador],
            )
            for jugador in normalizadas
        ],
        key=lambda resultado: (-resultado[1], resultado[0]),
    )


def TopAcumulativoConservador(
    torneos: Iterable[Torneo],
    torneos_por_anho: int = 4,
    factor_torneo_local: float = factor_torneo,
    factor_head2head_local: float = factor_head2head,
) -> list[tuple[str, float]]:
    """Ranking acumulativo con proteccion del historial y constancia."""
    if torneos_por_anho < 1:
        raise ValueError("torneos_por_anho debe ser positivo")
    if not 0 <= factor_torneo_local <= 1 or not 0 <= factor_head2head_local <= 1:
        raise ValueError("los factores deben estar entre 0 y 1")
    if abs(factor_torneo_local + factor_head2head_local - 1) > 1e-9:
        raise ValueError("factor_torneo + factor_head2head debe ser 1")

    torneos_lista = list(torneos)
    resultados: dict[str, list[float]] = defaultdict(list)
    upsets: dict[str, float] = defaultdict(float)
    participaciones: dict[str, int] = defaultdict(int)
    for torneo in torneos_lista:
        for puesto, (seed, jugador) in enumerate(torneo.Top(), 1):
            resultados[jugador].append(torneo.puntuacion / puesto)
            upsets[jugador] += seed - puesto
            participaciones[jugador] += 1
    if not resultados:
        return []

    recientes: dict[str, list[float]] = defaultdict(list)
    for torneo in torneos_lista[-torneos_por_anho:]:
        for puesto, (_, jugador) in enumerate(torneo.Top(), 1):
            recientes[jugador].append(torneo.puntuacion / puesto)

    puntuaciones = {}
    for jugador, valores in resultados.items():
        historial = sum(valores) / len(valores)
        valores_recientes = recientes.get(jugador, valores)
        reciente = sum(valores_recientes) / len(valores_recientes)
        reciente_protegido = max(reciente, historial * suelo_historial)
        puntuaciones[jugador] = factor_historial * historial + factor_recencia * reciente_protegido

    normalizadas = _normaliza(puntuaciones)
    upsets_normalizados = _normaliza(dict(upsets))
    constancia = {jugador: participaciones[jugador] / len(torneos_lista) for jugador in resultados}
    return sorted(
        [
            (
                jugador,
                (factor_torneo_local * normalizadas[jugador] + factor_head2head_local * upsets_normalizados[jugador])
                * (0.75 + 0.25 * constancia[jugador]),
            )
            for jugador in resultados
        ],
        key=lambda resultado: (-resultado[1], resultado[0]),
    )
