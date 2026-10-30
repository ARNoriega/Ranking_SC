from pathlib import Path
from random import Random
from time import perf_counter
from datetime import date
from typing import Any

from processing.ranking_engine import TopAcumulativo, Torneo


def crear_muestras(seed: int = 42, torneos_count: int = 12) -> list[Torneo]:
    """Genera torneos reproducibles para pruebas, fuera de la aplicacion."""
    random = Random(seed)
    jugadores = [f"Jugador{i}" for i in range(1, 36)]
    torneos = []
    for indice in range(torneos_count):
        asistentes = [jugador for jugador in jugadores if random.random() < 0.75]
        while len(asistentes) < 17:
            candidato = jugadores[len(asistentes)]
            if candidato not in asistentes:
                asistentes.append(candidato)
        asistentes = asistentes[:39]
        semillas = {jugador: puesto + 1 for puesto, jugador in enumerate(asistentes)}
        orden = sorted(asistentes, key=lambda jugador: semillas[jugador])
        if indice in (4, 9) and len(orden) > 8:
            orden[0], orden[7] = orden[7], orden[0]
        participantes = [(semillas[jugador], jugador) for jugador in orden]
        torneos.append(Torneo(800.0 + indice * 100.0, participantes))
    return torneos


def crear_demo_torneos(seed: int = 1234, cantidad: int = 4) -> list[Torneo]:
    """Crea una demo pequena y reproducible para probar la aplicacion visual."""
    if cantidad < 1:
        raise ValueError("cantidad debe ser positiva")

    random = Random(seed)
    jugadores = [f"DemoJugador{i}" for i in range(1, 25)]
    torneos = []
    for indice in range(cantidad):
        asistentes = jugadores[:]
        random.shuffle(asistentes)
        asistentes = asistentes[:16 + indice % 9]
        semillas = {jugador: puesto + 1 for puesto, jugador in enumerate(asistentes)}
        resultado = sorted(
            asistentes,
            key=lambda jugador: semillas[jugador] + random.randint(-4, 4),
        )
        participantes = [(semillas[jugador], jugador) for jugador in resultado]
        torneos.append(
            Torneo(
                800.0 + indice * 350.0,
                participantes,
                f"Demo {indice + 1}",
                date.today().year,
            )
        )
    return torneos


def ejecutar_simulacion(torneos: list[Torneo]) -> dict[str, Any]:
    """Ejecuta TopAcumulativo y mide su coste temporal."""
    inicio = perf_counter()
    ranking = TopAcumulativo(torneos)
    return {
        "ranking": ranking,
        "tiempo_segundos": perf_counter() - inicio,
        "torneos": len(torneos),
        "jugadores_maximos": max((len(t.participantes) for t in torneos), default=0),
    }


def guardar_grafica(resultado: dict[str, Any], path: str | Path = "data/simulacion.png") -> None:
    """Guarda una grafica de puntuaciones del ranking simulado."""
    import matplotlib.pyplot as plt

    ranking = resultado["ranking"]
    figura, eje = plt.subplots(figsize=(10, 5))
    eje.plot(range(1, len(ranking) + 1), [valor for _, valor in ranking], marker="o")
    eje.set_title("TopAcumulativo")
    eje.set_xlabel("Puesto")
    eje.set_ylabel("Puntuacion")
    eje.grid(True, alpha=0.3)
    figura.tight_layout()
    figura.savefig(path, dpi=150)
    plt.close(figura)


if __name__ == "__main__":
    datos = ejecutar_simulacion(crear_muestras())
    guardar_grafica(datos)
    print(datos)
