# Formato de datos de entrada (estandar v1)

El proyecto usa como entrada oficial el JSON crudo generado por `src/smash_rankings/io/importer.py`.

Caso de referencia pedido: `https://www.start.gg/tournament/dungeons-and-downairs-1/event/ultimate-singles/`.

## Ubicacion y nombre de archivo

- Ruta: `data/Resultados/<anho>/<slug>.json`
- `<anho>` se obtiene desde `data.tournament.startAt`
- `<slug>` es el slug del torneo en Start.gg (ejemplo: `dungeons-and-downairs-1`)

## Estructura JSON canonica

El formato almacenado es la respuesta GraphQL completa de Start.gg para la query `GetTournamentDeep`:

```json
{
	"data": {
		"tournament": {
			"id": 0,
			"name": "string",
			"city": "string|null",
			"addrState": "string|null",
			"countryCode": "string|null",
			"venueName": "string|null",
			"venueAddress": "string|null",
			"startAt": 0,
			"endAt": 0,
			"url": "https://www.start.gg/tournament/...",
			"events": [
				{
					"id": 0,
					"name": "string",
					"slug": "string",
					"numEntrants": 0,
					"videoGame": {
						"id": 0,
						"name": "string"
					},
					"standings": {
						"pageInfo": {
							"total": 0,
							"totalPages": 0,
							"page": 1,
							"perPage": 512
						},
						"nodes": [
							{
								"placement": 1,
								"entrant": {
									"id": 0,
									"name": "string",
									"participants": [
										{
											"id": 0,
											"gamerTag": "string"
										}
									]
								}
							}
						]
					}
				}
			]
		}
	}
}
```

## Campos obligatorios para importar

`traducciones.py` y `io/validators.py` deben exigir como minimo:

- `data`
- `data.tournament`
- `data.tournament.startAt`
- `data.tournament.events`
- En cada evento: `id`, `name`, `slug`, `numEntrants`, `standings.nodes`
- En cada standing: `placement`, `entrant.id`, `entrant.name`, `entrant.participants`

## Regla de seleccion de evento (Smash Cantabria)

Para el ranking oficial solo se usa **un unico evento por torneo**:

- El bracket principal de singles.
- El resto de eventos del torneo (dobles, squad strike, side events, etc.) no se usan y deben ignorarse.

Implementacion esperada en la capa de traduccion (`traducciones.py`):

- Buscar dentro de `data.tournament.events` el evento de singles principal.
- Si hay varios candidatos de singles, elegir como principal el que tenga mayor `numEntrants`.
- Si no existe un evento de singles principal identificable, lanzar `TournamentParseError`.

## Reglas de interpretacion

- El importador guarda el JSON tal cual lo devuelve la API (sin transformaciones internas).
- Para construir `TorneoNormalizado`, solo se procesan standings del evento de singles principal seleccionado.
- Si en el futuro cambia la query, se debe versionar este documento (`v2`, `v3`, etc.).
- El parseo a `TorneoNormalizado` ocurre despues, en la capa de traduccion.
