# Rankings

## Estructura

- `application/`: casos de uso y orquestacion.
- `processing/`: motor del ranking y modelo `Torneo`.
- `database/`: persistencia de resultados en JSON.
- `simulation/`: muestras, simulaciones y graficas aisladas.
- `tests/`: pruebas del motor, la aplicacion y la persistencia.

## Ejecutar una simulacion

```powershell
python -m simulation.runner
```

La simulacion genera una grafica en `data/simulacion.png`.

## Usar la aplicacion

```python
from application.ranking_service import RankingService
from application.processing_gateway import TopAcumulativoProcessor
from database.json_repository import JsonRepository

repositorio = JsonRepository("data/resultados.json")
servicio = RankingService(repositorio, TopAcumulativoProcessor())
resultado = servicio.generar_y_guardar(torneos, "ranking_2026")
```

El motor seleccionado es `TopAcumulativo`. Los resultados se guardan como JSON con el nombre del ranking y una lista de jugadores con su puntuacion. El servicio valida que el ranking no este vacio, que no haya jugadores repetidos, que las puntuaciones sean finitas y que esten ordenadas de mayor a menor.

Por seguridad, guardar un ranking con un nombre ya existente produce un error. Para reemplazarlo desde codigo hay que indicarlo explicitamente:

```python
servicio.guardar_ranking(
    resultado,
    "ranking_2026",
    sobrescribir=True,
)
```

Los rankings guardados se pueden consultar, cargar y eliminar:

```python
servicio.listar_rankings()
ranking = servicio.cargar_ranking("ranking_2026")
servicio.eliminar_ranking("ranking_2026")
```

## Prototipo visual

```powershell
python -m application.visual
```

La interfaz permite:

- Introducir, editar y eliminar torneos.
- Cargar torneos demo sin duplicarlos.
- Filtrar torneos por año.
- Calcular y editar el ranking acumulativo.
- Guardar rankings con confirmacion antes de sobrescribirlos.
- Seleccionar, cargar y eliminar rankings guardados.

Los participantes se introducen uno por linea usando el formato `seed, jugador`.

## Ejecutar el proyecto

Desde PowerShell:

```powershell
.\run_project.ps1
```

El script compila el proyecto, ejecuta las pruebas con `pytest` y solo si ambas fases terminan correctamente inicia la aplicacion visual. Tambien puedes abrir `run_project.bat` con doble clic.

Para ejecutar solo las pruebas:

```powershell
python -m pytest -q
```
