import json

import pytest

from application.processing_gateway import TopAcumulativoProcessor
from application.presentation import RankingPresenter
from application.ranking_service import RankingService
from application.torneo_service import TorneoService
from application.visual import RankingApp
from database.json_repository import JsonRepository, JsonRepositoryError
from processing.ranking_engine import (
    TopAcumulativo,
    TopAcumulativoConservador,
    Torneo,
    puntua,
)
from simulation.runner import crear_demo_torneos, crear_muestras


def torneo_prueba() -> Torneo:
    participantes = [(seed, f"Jugador{seed}") for seed in range(1, 18)]
    return Torneo(799.0, participantes)


def torneo_con(jugadores: int, puntuacion: float) -> Torneo:
    participantes = [(seed, f"Jugador{seed}") for seed in range(1, jugadores + 1)]
    return Torneo(puntuacion, participantes)


def test_motor_top_acumulativo() -> None:
    torneo = torneo_prueba()
    assert len(torneo.Top()) == 8
    assert torneo.puntuación == 799.0
    assert TopAcumulativo([torneo])[0][0] == "Jugador1"


def test_top_respeta_limites_de_participantes_y_puntuacion() -> None:
    assert len(torneo_con(16, 799).Top()) == 8
    assert len(torneo_con(17, 0).Top()) == 8
    assert len(torneo_con(24, 800).Top()) == 8
    assert len(torneo_con(25, 800).Top()) == 16
    assert len(torneo_con(25, 1300).Top()) == 24


def test_puntua_devuelve_puesto_y_puntuacion() -> None:
    torneo = torneo_prueba()
    assert puntua(torneo, "Jugador1") == ("Jugador1", 799.0)
    assert puntua(torneo, "Jugador8") == ("Jugador8", 799.0 / 8)
    assert puntua(torneo, "Jugador9") is None
    assert len(puntua(torneo)) == 8


def test_top_acumulativo_ordena_por_puntuacion() -> None:
    torneo = torneo_prueba()
    ranking = TopAcumulativo([torneo])
    assert ranking == sorted(ranking, key=lambda resultado: (-resultado[1], resultado[0]))
    assert ranking[0][0] == "Jugador1"


def test_factor_upset_favorece_mejorar_la_seed() -> None:
    participantes = [(8, "Upset"), (1, "Favorito")]
    participantes.extend((seed, f"Jugador{seed}") for seed in range(3, 18))
    ranking = TopAcumulativo([Torneo(799.0, participantes)])
    assert ranking[0][0] == "Upset"


def test_top_acumulativo_conservador_valida_factores() -> None:
    torneo = torneo_prueba()
    assert TopAcumulativoConservador([torneo], 4, 0.8, 0.2)
    with pytest.raises(ValueError):
        TopAcumulativoConservador([torneo], 4, 0.7, 0.7)
    with pytest.raises(ValueError):
        TopAcumulativoConservador([torneo], 0, 0.8, 0.2)


def test_simulacion_crea_doce_torneos() -> None:
    torneos = crear_muestras()
    assert len(torneos) == 12
    assert all(len(torneo.participantes) < 40 for torneo in torneos)


def test_crear_demo_torneos_es_reproducible() -> None:
    demos = crear_demo_torneos(seed=10, cantidad=3)
    assert [torneo.nombre for torneo in demos] == ["Demo 1", "Demo 2", "Demo 3"]
    assert all(16 <= len(torneo.participantes) < 40 for torneo in demos)
    assert crear_demo_torneos(seed=10, cantidad=3)[0].participantes == demos[0].participantes


def test_aplicacion_guarda_json(tmp_path) -> None:
    repository = JsonRepository(tmp_path / "resultados.json")
    service = RankingService(repository, TopAcumulativoProcessor())
    ranking = service.generar_y_guardar([torneo_prueba()])
    assert ranking
    contenido = json.loads((tmp_path / "resultados.json").read_text(encoding="utf-8"))
    assert contenido["ranking"][0]["jugador"] == "Jugador1"


def test_json_corrupto_da_un_error_controlable(tmp_path) -> None:
    ruta = tmp_path / "resultados.json"
    ruta.write_text('{"torneos": [', encoding="utf-8")

    with pytest.raises(JsonRepositoryError, match="parece estar dañado"):
        JsonRepository(ruta).load()


def test_json_con_formato_invalido_da_un_error_controlable(tmp_path) -> None:
    ruta = tmp_path / "resultados.json"
    ruta.write_text("[]", encoding="utf-8")

    with pytest.raises(JsonRepositoryError, match="formato de datos valido"):
        JsonRepository(ruta).load()


@pytest.mark.parametrize(
    ("contenido", "mensaje"),
    [
        ('{"torneos": {}}', "'torneos' debe ser una lista"),
        ('{"torneos": [{"participantes": []}]}', "puntuacion o año validos"),
        ('{"torneos": [{"puntuacion": 800, "participantes": {}}]}', "lista de participantes"),
        ('{"torneos": [{"puntuacion": 800, "participantes": [{"seed": 1}]}]}', "esta incompleto"),
        ('{"torneos": [{"puntuacion": 800, "participantes": [{"seed": 0, "jugador": "Ana"}]}]}', "seed o jugador invalido"),
    ],
)
def test_json_parcialmente_invalido_da_error_amigable(tmp_path, contenido, mensaje) -> None:
    ruta = tmp_path / "resultados.json"
    ruta.write_text(contenido, encoding="utf-8")

    with pytest.raises(JsonRepositoryError, match=mensaje):
        TorneoService(JsonRepository(ruta)).cargar_torneos()


def test_json_corrupto_se_aparta_y_permite_guardar_datos_nuevos(tmp_path) -> None:
    ruta = tmp_path / "resultados.json"
    ruta.write_text('{"torneos": [', encoding="utf-8")
    repository = JsonRepository(ruta)

    respaldo = repository.apartar_archivo_corrupto()

    assert respaldo is not None
    assert respaldo.exists()
    assert not ruta.exists()
    repository.save({"torneos": []})
    assert repository.load() == {"torneos": []}


def test_guardado_con_datos_no_serializables_da_error_amigable(tmp_path) -> None:
    repository = JsonRepository(tmp_path / "resultados.json")

    with pytest.raises(JsonRepositoryError, match="no se puede convertir a JSON"):
        repository.save({"datos": object()})


def test_error_de_escritura_da_error_amigable(tmp_path, monkeypatch) -> None:
    ruta = tmp_path / "resultados.json"
    repository = JsonRepository(ruta)

    def escritura_fallida(*_args, **_kwargs):
        raise OSError("permiso denegado")

    monkeypatch.setattr(type(ruta), "write_text", escritura_fallida)
    with pytest.raises(JsonRepositoryError, match="Comprueba los permisos"):
        repository.save({"torneos": []})


def test_torneos_se_pueden_guardar_cargar_y_eliminar(tmp_path) -> None:
    repository = JsonRepository(tmp_path / "resultados.json")
    service = TorneoService(repository)
    torneo = Torneo(799.0, [(seed, f"Jugador{seed}") for seed in range(1, 17)], "Regional", 2026)

    service.guardar_torneos([torneo])
    cargados = service.cargar_torneos()
    assert len(cargados) == 1
    assert cargados[0].nombre == "Regional"
    assert cargados[0].anho == 2026
    assert len(cargados[0].Top()) == 8

    assert service.eliminar_torneo(0) == []
    assert service.cargar_torneos() == []


def test_presentacion_es_independiente_del_procesado() -> None:
    mostrado = []

    class VistaFalsa:
        def mostrar_ranking(self, ranking) -> None:
            mostrado.extend(ranking)

    ranking = [("Jugador1", 1.0)]
    RankingPresenter(VistaFalsa()).presentar(ranking)
    assert mostrado == ranking


def test_ranking_generado_se_puede_parsear_y_validar() -> None:
    texto = "1. Ana: 0.9500\n2. Luis: 0.7000\n"
    assert RankingApp._parsear_ranking(texto) == [
        ("Ana", 0.95),
        ("Luis", 0.7),
    ]
    with pytest.raises(ValueError):
        RankingApp._parsear_ranking("1. Ana: 0.9500\n2. Ana: 0.7000")
    with pytest.raises(ValueError):
        RankingApp._parsear_ranking("")
