# Plan de trabajo — Smash Cantabria Rankings

Hoja de ruta ordenada por fases. Cada tarea debe completarse **en orden** dentro de su fase antes de pasar a la siguiente.

Leyenda de estados: `[ ]` pendiente · `[~]` en curso · `[x]` completado

---

## FASE 0 — Arreglar problemas de diseño existentes

> Objetivo: que el diagrama de clases, la documentación y el esqueleto de código sean coherentes entre sí antes de tomar ninguna decisión de negocio.

### 0.1 Conflictos entre `diagrama_clases.svg` y `ARQUITECTURA.md`

| # | Problema | Ficheros afectados |
|---|----------|--------------------|
| [x] | `Player` se ha alineado con el contrato actual y ahora usa solo `gamer_tag` como identidad estable. | `core/models.py`, `ARQUITECTURA.md`, `diagrama_clases.svg` |
| [x] | `SetResult` se ha alineado con el diagrama y la arquitectura ahora documenta solo `winner_id`, `loser_id` y `score`. | `core/models.py`, `ARQUITECTURA.md` |
| [x] | `TorneoNormalizado.placements` se ha alineado con el diagrama y la arquitectura ya no define un modelo `Placement` separado. | `core/models.py`, `ARQUITECTURA.md` |
| [x] | `RankingEntry` se ha alineado con el contrato actual y ahora documenta valores `raw` y `normalized` por componente. | `core/models.py`, `ARQUITECTURA.md`, `diagrama_clases.svg` |
| [x] | `RankingTable` se ha alineado con el diagrama y la arquitectura ya no documenta `year` ni `generated_at`. | `core/models.py`, `ARQUITECTURA.md` |
| [x] | `ARQUITECTURA.md` se ha reescrito para reflejar de forma canónica los módulos, métodos, modelos y dependencias exactas del `diagrama_clases.svg`. | `ARQUITECTURA.md`, `diagrama_clases.svg` |

### 0.2 Problemas de responsabilidades en las firmas del esqueleto

| # | Problema | Ficheros afectados |
|---|----------|--------------------|
| [x] | `scoring.integrar_h2h()` se ha eliminado del módulo de scoring y la integración de componentes se ha movido a `ranking.py`. | `core/scoring.py`, `ranking.py` |
| [x] | `scoring.calcular_puntos(torneos)` ya devuelve un tipo intermedio de resultados por jugador (`dict[int, float]`), no `RankingEntry` completo. | `core/scoring.py` |
| [x] | `scoring.seleccionar_mejores(...)` y `normalizar_resultados(...)` ya tienen tipos de retorno explícitos. | `core/scoring.py` |
| [x] | `h2h.normalizar_h2h(...)` ya tiene tipo de retorno explícito coherente con la orquestación en `ranking.py`. | `core/h2h.py`, `ranking.py` |

### 0.3 Módulo `io/normalizers.py` — estado ambiguo

| # | Problema | Ficheros afectados |
|---|----------|--------------------|
| [x] | La arquitectura ya no trata `io/normalizers.py` como parte de la estructura canónica porque no aparece en el diagrama. Cualquier uso futuro deberá considerarse detalle interno, no elemento estructural. | `io/normalizers.py`, `ARQUITECTURA.md`, `diagrama_clases.svg` |

---

## FASE 1 — Definir todo antes de codificar

> Objetivo: que todas las reglas de negocio, contratos de datos y configuración estén documentados y acordados. Nada de lógica todavía.

### 1.1 Responder las preguntas abiertas de `REGLAS_RANKING.md`

Cada pregunta desbloquea una parte del código. Se pueden resolver en paralelo pero todas deben estar cerradas antes de empezar la Fase 3.

| # | Pregunta | Desbloquea |
|---|----------|------------|
| [x] | ¿Cómo se define el score base del torneo? → Se fija en `traducciones.py` durante la importación JSON de cada torneo (valor del JSON o entrada manual en traducción). | `traducciones.py`, `core/scoring.py` |
| [x] | ¿Cómo se reparte por placement? → Reparto proporcional por posición entre puestos beneficiarios, con suma total igual a `ScoreTorneo_t`. | `config.py`, `core/scoring.py` |
| [x] | ¿Cuántos mejores resultados se cuentan por jugador (N)? ¿Varía por temporada? → `N = 3` constante (ajustable) y solo torneos del anho indicado. | `config.py`, `core/scoring.py` |
| [x] | ¿Qué método de ponderación de oponente se usa para H2H? → **Multiplicativo**: $w(i)=w_2(i)\cdot w_3(i)$; $w_2=3$ si Cantabria X-1, $w_3=8$ si España X-1, base = 1. Pesos en `SeasonConfig`. | `core/h2h.py`, `config.py` |
| [x] | ¿Cuáles son los pesos `w_R`, `w_H2H` y `w_vv` para 2025 y 2026? → 70% / 15% / 15% para cualquier anho calculado. | `config.py`, `ranking.py` |
| [x] | ¿Hay un tercer componente en 2023? ¿Qué es? ¿Afecta a la estructura de modelos? → 2023 no se recalcula; se usa como baseline histórico. | `core/models.py`, `config.py`, `ranking.py` |
| [x] | ¿Cuántos torneos/sets mínimos se requieren para aparecer en el ranking? → Mínimo 3 torneos y sin mínimo de sets. | `config.py`, `ranking.py` |
| [x] | ¿Se incluyen torneos fuera de Cantabria? ¿Con el mismo peso? → No, solo torneos celebrados en Cantabria. | `config.py`, `FORMATO_DATOS.md` |
| [x] | ¿Existe categoría de torneo especial (p. ej. Major) con multiplicador de puntos? → No; Ventisca veraniega va como componente separado. | `config.py`, `core/scoring.py` |

### 1.2 Definir la estructura de `config.py`

| # | Tarea |
|---|-------|
| [x] | Crear el esqueleto de `SeasonConfig` (Pydantic o dataclass): campos `w_resultados`, `w_h2h`, `n_mejores`, `score_base_por_categoria`, `tabla_reparto`, `min_torneos`, `min_sets`, `alcance_jugadores` (`all`/`local`). |
| [x] | Definir cómo se instancia `SeasonConfig` para cada temporada (constantes en código, YAML externo, o dict indexado por `anho`). Documentar la decisión en `ARQUITECTURA.md`. |

### 1.3 Cerrar las firmas definitivas de `scoring.py` y `h2h.py`

| # | Tarea |
|---|-------|
| [x] | Actualizar la firma de `calcular_puntos` con el tipo de retorno correcto tras resolver 0.2. |
| [x] | Actualizar las firmas de `seleccionar_mejores` y `normalizar_resultados` con los tipos correctos. |
| [x] | Actualizar las firmas de `calcular_matriz_h2h` y `normalizar_h2h` con los tipos correctos. |
| [x] | Documentar en `ARQUITECTURA.md` el flujo exacto de datos entre `scoring.py`, `h2h.py` y `ranking.py` (qué entra, qué sale, en qué formato). |

### 1.4 Confirmar el formato de los JSON de entrada

| # | Tarea |
|---|-------|
| [x] | Definir el esquema JSON real de entrada y validar que coincide con `FORMATO_DATOS.md`. |
| [x] | Colocar JSON reales de ejemplo en `data/Resultados/` como **fixtures de referencia** para tests. |

---

## FASE 2 — Tests

> Objetivo: escribir los tests *antes* de la implementación (TDD). Cada test debe poder ejecutarse (y fallar) desde el momento en que se escribe.

### 2.1 Tests de contratos de datos — `test_ranking_contracts.py`

| # | Test |
|---|------|
| [x] | `Player` acepta `gamer_tag` válido y rechaza campos extra (por ejemplo `name`). |
| [x] | `Player` rechaza `gamer_tag` de tipo incorrecto. |
| [x] | `SetResult` acepta campos válidos. |
| [x] | `TorneoNormalizado` se construye correctamente con listas de jugadores, sets y placements. |
| [x] | `RankingEntry` permite guardar `raw` y `normalized`, con `normalized = None` si no se ha calculado. |
| [x] | `RankingTable` ordena entradas por `score_total_raw` descendente (el mayor score va primero). |

### 2.2 Tests de utilidades — nuevos archivos en `tests/`

| # | Test | Archivo |
|---|------|---------|
| [x] | `parse_fecha("2025-03-15_Cantabria-Open.json")` devuelve `date(2025, 3, 15)`. | `test_dates.py` |
| [x] | `parse_fecha` lanza `TournamentParseError` con nombre mal formado. | `test_dates.py` |
| [x] | `JSONSchemaError` y `TournamentParseError` son subclases de `Exception`. | `test_exceptions.py` |

### 2.3 Tests de IO — nuevos archivos en `tests/`

| # | Test | Archivo |
|---|------|---------|
| [x] | `readers` carga un JSON de fixture y devuelve una estructura válida. | `test_io_readers.py` |
| [x] | `readers` lanza error controlado con ruta inexistente o JSON inválido. | `test_io_readers.py` |
| [x] | `validators` acepta JSON con esquema correcto. | `test_io_validators.py` |
| [x] | `validators` lanza error de esquema cuando faltan claves requeridas. | `test_io_validators.py` |

### 2.4 Tests de traducción — `test_traducciones_structure.py`

| # | Test |
|---|------|
| [x] | `cargar_torneos(ruta_con_fixtures)` devuelve una lista de `TorneoNormalizado`. |
| [x] | La lista está ordenada por fecha ascendente. |
| [x] | `cargar_torneos` ignora jugadores con `checkedIn = false`. |
| [x] | `cargar_torneos` lanza `TournamentParseError` si falta información requerida en el JSON del torneo. |

### 2.5 Tests de scoring — `tests/test_scoring.py`

| # | Test |
|---|------|
| [x] | `calcular_puntos` devuelve una entrada por jugador activo. |
| [x] | El jugador con placement 1 recibe más puntos que el de placement 2 en el mismo torneo. |
| [x] | `seleccionar_mejores` devuelve exactamente N torneos por jugador. |
| [x] | `normalizar_resultados` escala de 0 a 100; el máximo es exactamente 100. |
| [x] | Torneos con 0 entrants no entran en el cálculo. |

### 2.6 Tests de H2H — `tests/test_h2h.py`

| # | Test |
|---|------|
| [x] | `calcular_matriz_h2h` devuelve un dict con clave por cada jugador ganador. |
| [x] | Un set DQ no aparece en la matriz. |
| [x] | `normalizar_h2h` devuelve valores entre 0 y 100; el máximo es exactamente 100. |

### 2.7 Test de integración — `tests/test_ranking_integration.py`

| # | Test |
|---|------|
| [x] | `generar_ranking(anho)` sobre fixtures reales devuelve un `RankingTable` no vacío. |
| [x] | El jugador con más puntos en todos los torneos ocupa la posición 1. |
| [x] | `export_json` crea un fichero JSON con las claves esperadas. |

---

## FASE 3 — Codificación principal

> Orden de implementación: de capas internas (sin dependencias) hacia capas externas.

### 3.1 Utilidades base

| # | Módulo | Tarea |
|---|--------|-------|
| [x] | `utils/exceptions.py` | *(esqueleto ya listo)* — sin cambios funcionales; excepciones base confirmadas y validadas por tests. |
| [x] | `utils/dates.py` | Implementar `parse_fecha`: extraer `YYYY-MM-DD` del nombre de archivo con regex; lanzar `TournamentParseError` si no coincide. |

### 3.2 Capa IO

| # | Módulo | Tarea |
|---|--------|-------|
| [x] | `io/readers.py` | Implementar lectura JSON y manejo de errores de parseo. |
| [x] | `io/validators.py` | Implementar validación de esquema JSON y tipos requeridos, con errores descriptivos. |

### 3.3 Traducción

| # | Módulo | Tarea |
|---|--------|-------|
| [x] | `traducciones.py` | Implementar `cargar_torneos`: escanear directorio, seleccionar el evento principal de singles, invocar IO y devolver lista ordenada. |

### 3.4 Configuración

| # | Módulo | Tarea |
|---|--------|-------|
| [x] | `config.py` | Implementar `SeasonConfig` y las instancias por temporada (2023, 2024, 2025, 2026). |
| [x] | `ranking.py`, `core/scoring.py`, `core/h2h.py` | Cablear `SeasonConfig` al flujo real de cálculo (pesos, `n_mejores`, mínimos y `alcance_jugadores`). |

### 3.5 Núcleo de negocio

| # | Módulo | Tarea |
|---|--------|-------|
| [ ] | `core/scoring.py` | Implementar `calcular_puntos`, `seleccionar_mejores`, `normalizar_resultados`. |
| [ ] | `core/h2h.py` | Implementar `calcular_matriz_h2h`, `normalizar_h2h`. |

### 3.6 Orquestación y salida

| # | Módulo | Tarea |
|---|--------|-------|
| [x] | `ranking.py` | Implementar `generar_ranking`: invocar traducciones → scoring → h2h → agregación ponderada → `RankingTable`. Añadir CLI con Typer. |
| [x] | `services/exporter.py` | Implementar `export_json` y `export_excel`. |

---

## Resumen de bloqueos actuales

| Bloqueo | Qué impide | Responsable |
|---------|-----------|-------------|
| Cablear `SeasonConfig` al flujo completo de cálculo (`scoring`, `h2h`, `ranking`) | Implementación consistente de configuración en tiempo de ejecución | Equipo técnico |
| Aportar más JSON reales representativos (mínimo 3 casos) | Fixtures para tests de IO y traducción | Organización Smash Cantabria |
