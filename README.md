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
from database.json_repository import JsonRepository
from processing.ranking_engine import Torneo

servicio = RankingService(JsonRepository("data/resultados.json"))
resultado = servicio.generar_y_guardar(torneos)
```

El motor seleccionado es `TopAcumulativo`. Los resultados se guardan como JSON con el nombre del ranking y una lista de jugadores con su puntuacion.

## Prototipo visual

```powershell
python -m application.visual
```

La interfaz permite introducir el nombre y los puntos de cada torneo, pegar los participantes ordenados por resultado usando el formato `seed, jugador`, calcular el ranking acumulativo y guardar el resultado en `data/resultados.json`.

## Ejecutar el proyecto

Desde PowerShell:

```powershell
.\run_project.ps1
```

También puedes abrir `run_project.bat` con doble clic. El script compila primero las capas del proyecto y las pruebas; solo si no hay errores inicia la aplicación visual.
