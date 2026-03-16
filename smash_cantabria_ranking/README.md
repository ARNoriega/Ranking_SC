# Smash Cantabria — Rankings

Pipeline modular para el cálculo de rankings de Smash Bros. Ultimate de Smash Cantabria.
Lee los resultados de torneos en formato JSON, los valida, los normaliza y produce una tabla de ranking final por temporada.

---

## Índice

1. [Descripción general](#descripción-general)
2. [Estructura del proyecto](#estructura-del-proyecto)
3. [Instalación](#instalación)
4. [Uso rápido](#uso-rápido)
5. [Datos de entrada](#datos-de-entrada)
6. [Arquitectura](#arquitectura)
7. [Reglas del ranking](#reglas-del-ranking)
8. [Tests](#tests)
9. [Comandos de desarrollo](#comandos-de-desarrollo)

---

## Descripción general

El sistema toma JSON de cada torneo y produce un ranking acumulado por temporada. El pipeline está dividido en fases independientes:

```
JSONs de torneos
	   │
	   ▼
   io/readers     ← lectura y validación de formato JSON
	   │
	   ▼
   io/validators  ← comprobación de columnas y tipos
	   │
	   ▼
   io/normalizers ← mapeo a modelos internos (Pydantic)
	   │
	   ▼
  core/scoring    ← puntos por placement y tamaño
	   │
	   ▼
   core/h2h       ← componente H2H (direct confrontation)
	   │
	   ▼
 ranking.py       ← orquestación y agregación final
	   │
	   ▼
services/exporter ← JSON / XLSX de salida
```

---

## Estructura del proyecto

```
smash_cantabria_ranking/
├── data/
│   └── Resultados/
│       ├── 2023/          ← JSON de torneos 2023
│       ├── 2024/          ← JSON de torneos 2024
│       ├── 2025/          ← JSON de torneos 2025
│       └── 2026/          ← JSON de torneos 2026
├── src/
│   └── smash_rankings/
│       ├── ranking.py          ← punto de entrada / CLI
│       ├── traducciones.py     ← carga y entrega de torneos normalizados
│       ├── core/
│       │   ├── models.py       ← contratos de datos (Pydantic)
│       │   ├── scoring.py      ← puntuación por resultados
│       │   ├── h2h.py          ← cálculo H2H
│       │   └── __init__.py
│       ├── io/
│       │   ├── readers.py      ← lectura de JSON
│       │   └── validators.py   ← validación de esquema
│       ├── services/
│       │   ├── exporter.py     ← exportación de resultados
│       │   └── __init__.py
│       └── utils/
│           ├── dates.py        ← parseo y utilidades de fechas
│           ├── exceptions.py   ← excepciones del dominio
│           └── __init__.py
├── tests/
│   ├── test_ranking_contracts.py
│   └── test_traducciones_structure.py
├── pyproject.toml
├── Makefile
└── README.md
```

---

## Instalación

> Requiere Python ≥ 3.10.

```bash
# 1. Crear entorno virtual
python -m venv .venv

# 2. Activar entorno
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS

# 3. Instalar dependencias (incluye herramientas de desarrollo)
pip install -e ".[dev]"
```

---

## Uso rápido

```bash
# Ranking del anho para cualquier jugador elegible (all)
python -m smash_rankings.ranking --anho 2025 --a

# Ranking del anho solo para jugadores locales
python -m smash_rankings.ranking --anho 2025 --s
```

Flags de alcance del ranking:

- `--a`: incluye a cualquier jugador que cumpla minimos.
- `--s`: incluye solo jugadores locales que cumplan minimos.

Los resultados se guardarán en `data/Rankings/<anho>/ranking_<anho>.json` (y `.xlsx` opcionalmente).

---

## Datos de entrada

Los torneos se importan en formato **JSON**.

Consulta [docs/FORMATO_DATOS.md](docs/FORMATO_DATOS.md) para el contrato de entrada y el esquema definitivo (pendiente de definición final).

---

## Arquitectura

Consulta [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) para una descripción detallada del diseño modular, las responsabilidades de cada capa y los contratos de datos.

---

## Reglas del ranking

Consulta [docs/REGLAS_RANKING.md](docs/REGLAS_RANKING.md) para la fórmula de puntuación, las tablas de reparto por placement, las categorías de torneo y los pesos por temporada.

---

## Tests

```bash
pytest -q
```

Los tests se ubican en `tests/` y cubren:
- Contratos de datos (Pydantic models).
- Estructura y salidas de `traducciones.py`.

---

## Comandos de desarrollo

| Comando       | Descripción                         |
|---------------|-------------------------------------|
| `make install`| Instala dependencias en el venv     |
| `make test`   | Ejecuta todos los tests             |
| `make lint`   | Linting con Ruff                    |
| `make format` | Formateo automático con Black       |
| `make type`   | Comprobación de tipos con mypy      |
