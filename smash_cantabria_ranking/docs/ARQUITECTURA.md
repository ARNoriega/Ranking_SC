# Arquitectura del sistema de Rankings

Este documento describe la estructura **canonica** definida por `diagrama_clases.svg`.

## Configuracion por temporada

Decision adoptada para Fase 1.2:

- Se define `SeasonConfig` en `src/smash_rankings/config.py`.
- La instanciacion por temporada se hace en codigo mediante un diccionario
    indexado por `anho`: `SEASON_CONFIG_BY_ANHO`.
- El acceso a la configuracion se centraliza con `get_season_config(anho)`.

Campos de `SeasonConfig`:

- `w_resultados`
- `w_h2h`
- `w_vv`
- `n_mejores`
- `score_base_por_categoria`
- `tabla_reparto`
- `min_torneos`
- `min_sets`
- `alcance_jugadores` (`all`/`local`)

## Modulos del diagrama

### `ranking.py`

Metodo expuesto:

- `generar_ranking(anho: int, alcance: "all"|"local" = "all"): RankingTable`
- `integrar_componentes(score_resultados: dict[int, float], score_h2h: dict[int, float]) -> dict[int, tuple[float, float]]`

Rol en el diagrama:

- Lee torneos via `traducciones.py`.
- Calcula ranking via `scoring.py` (con `h2h.py` como auxiliar).
- Exporta via `exporter.py`.

### `traducciones.py`

Metodo expuesto:

- `cargar_torneos(ruta): List[TorneoNormalizado]`

Dependencias en el diagrama:

- `readers.py`
- `validators.py`
- `dates.py`

### `readers.py`

Metodo expuesto:

- `read_json(path): dict`

### `validators.py`

Metodos expuestos:

- `validate_entrants(df)`
- `validate_bracket(df)`

### `scoring.py`

Metodos expuestos:

- `calcular_puntos(torneos: list[TorneoNormalizado]) -> dict[int, float]`
- `seleccionar_mejores(puntos_por_torneo: dict[int, list[float]], n_mejores: int = 3) -> dict[int, float]`
- `normalizar_resultados(puntos_resultados: dict[int, float]) -> dict[int, float]`

Nota: la integracion con H2H vive en `ranking.py`, no en `scoring.py`.

### `h2h.py` (auxiliar)

Metodos expuestos:

- `calcular_matriz_h2h(torneos: list[TorneoNormalizado]) -> dict[int, dict[int, int]]`
- `normalizar_h2h(puntos_h2h: dict[int, float]) -> dict[int, float]`

### `exporter.py`

Metodos expuestos:

- `export_json(ranking)`
- `export_excel(ranking)`

### `dates.py`

Metodo expuesto:

- `parse_fecha(nombre_archivo)`

### `exceptions.py`

Excepciones expuestas:

- `JSONSchemaError`
- `TournamentParseError`

## Modelos del dominio

### `Player`

- `gamer_tag: str`
- No admite campos extra (por ejemplo `name`), para evitar identidades inestables por torneo.

### `SetResult`

- `winner_id: int`
- `loser_id: int`
- `score: str`

### `TorneoNormalizado`

- `fecha: date`
- `nombre: str`
- `entrants: List[Player]`
- `sets: List[SetResult]`
- `placements: Dict[int, int]`

### `RankingEntry`

- `player: Player`
- `score_total_raw: float`
- `score_total_normalized: float | None` (`None` si todavia no se ha normalizado)
- `score_results_raw: float | None`
- `score_results_normalized: float | None`
- `score_h2h_raw: float | None`
- `score_h2h_normalized: float | None`

### `RankingTable`

- `entries: List[RankingEntry]`

## Dependencias estructurales

```
ranking.py  ──►  traducciones.py  ──►  readers.py
                                   ──►  validators.py
                                   ──►  dates.py
                                   ──►  TorneoNormalizado

ranking.py  ──►  scoring.py  ──►  h2h.py (auxiliar)
ranking.py  ──►  exporter.py

RankingTable  ──►  RankingEntry  ──►  Player
TorneoNormalizado  ──►  Player
TorneoNormalizado  ──►  SetResult
```

## Flujo de datos scoring/H2H/ranking

Flujo acordado para orquestacion:

1. `traducciones.py` entrega `list[TorneoNormalizado]`.
2. `scoring.calcular_puntos(...)` calcula resultados por jugador: `dict[int, float]`.
3. `scoring.seleccionar_mejores(...)` aplica `N=3` y devuelve `dict[int, float]`.
4. `scoring.normalizar_resultados(...)` normaliza resultados a escala 0-100: `dict[int, float]`.
5. `h2h.calcular_matriz_h2h(...)` arma matriz de enfrentamientos: `dict[int, dict[int, int]]`.
6. `h2h.normalizar_h2h(...)` entrega score H2H normalizado: `dict[int, float]`.
7. `ranking.integrar_componentes(...)` combina resultados y H2H para preparar la agregacion final.

Con esto, los formatos de entrada/salida entre `scoring.py`, `h2h.py` y `ranking.py` quedan definidos explicitamente.

Este documento debe mantenerse alineado con `diagrama_clases.svg`. Si cambia el diagrama, este archivo debe actualizarse en la misma tarea.
