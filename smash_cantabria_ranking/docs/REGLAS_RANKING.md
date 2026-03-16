# Reglas del ranking

## Visión general

El score final de cada jugador es una **suma ponderada de componentes** normalizados a 100:

$$ \mathrm{Score}_{total} = w_{R} \cdot \text{Score}_{Resultados} + w_{H2H} \cdot \text{Score}_{H2H} + w_{vv} \cdot \text{Score}_{vv} $$

donde:

- $w_R = 0.70$
- $w_{H2H} = 0.15$
- $w_{vv} = 0.15$

y por tanto $w_R + w_{H2H} + w_{vv} = 1$.

Cada componente se normaliza de forma independiente a escala 0–100 antes de agregar.

---

## Componente Resultados

### 1. Score del torneo y cálculo de tier

Cada torneo tiene un **score variable** definido en la fase de traducción (`traducciones.py`) al importar torneos JSON del anho correspondiente.

Regla vigente:

1. `ScoreTorneo_t` se asigna durante la importación/traducción de cada torneo.
2. El valor puede venir del propio JSON o de una entrada manual en el traductor durante la carga.
3. El cálculo de ranking usa el `ScoreTorneo_t` ya resuelto por `traducciones.py`; no se recalcula dentro de `core/scoring.py`.

$$
	\text{ScoreTorneo}_t =
\begin{cases}
	\text{score\_json}_t, & \text{si existe en JSON} \\
	\text{score\_manual}_t, & \text{si se introduce por consola}
\end{cases}
$$

Formato JSON sugerido:

```json
{
	"torneos": {
		"2026-03-15_Cantabria-Open": 1825,
		"2026-05-10_Ventisca-Veraniega": 3560
	}
}
```

> Posible expansion futura: calcular automaticamente `ScoreTorneo_t` a partir de participantes y jugadores top.

Una vez calculado ese score, se asigna un tier usando la siguiente tabla:

| Rango de score del torneo | Tier | Restricción adicional |
|---------------------------|------|-----------------------|
| < 800                     | C    | - |
| 800 - 1299                | B    | Mínimo 24 participantes |
| 1300 - 1799               | B+   | - |
| 1800 - 2799               | A    | Mínimo 64 participantes |
| 2800 - 3499               | A+   | - |
| 3500 - 4499               | S    | Mínimo 96 participantes |
| 4500 - 4999               | S+   | - |
| >= 5000                   | SS   | - |

Para asignar tier, se toma `ScoreTorneo_t` (manual o JSON) y se aplica la tabla de rangos.

No existe categoría especial tipo *Major*: el tratamiento diferencial ya se modela con el componente separado de `Ventisca veraniega`.

### 2. Reglas de computo de torneos por jugador

La primera parte de la puntuación final se calcula a partir de las posiciones de los jugadores en los torneos en los que participan.

Se fija la constante:

$$
N_{mejores} = 3
$$

Reglas de cómputo:

1. Para calcular `Score_Resultados` de un anho X, solo se consideran torneos del anho X.
2. De esos torneos válidos, computan los **3 mejores resultados** de cada jugador.
3. Si un jugador tiene menos de 3 resultados válidos, computan solo los disponibles.

Ademas, para incentivar torneos altos:

1. El `Ventisca veraniega` computa por separado
2. No acudir a este torneo implica **0 puntos** en esa plaza computable.
3. Solo computan torneos celebrados en Cantabria. Los torneos de fuera no entran en el ranking.

### 3. Reparto por placement segun tier

La puntuacion en un torneo se calcula en funcion de:

1. Tier del torneo.
2. Score del torneo.
3. Posicion final del jugador.

Segun la tier, solo reciben puntos estos puestos:

| Tier | Puestos con puntos |
|------|---------------------|
| C    | Top 8 |
| B    | Top 16 |
| B+   | Top 24 |
| A    | Top 32 |
| A+   | Top 48 |
| S    | Top 64 |
| S+   | Top 96 |
| SS   | Top 128 |

El **score de un jugador en un torneo** es:
$$
\text{puntos}_{j,t} = \text{ScoreTorneo}_{t} \cdot w_{\text{pos}_{j,t},\,\text{tier}_{t}},
\qquad
\sum_{r \in \text{puestos puntuables}(\text{tier}_{t})} w_{r,\text{tier}_{t}} = 1
$$

Condiciones del reparto por placement:

1. Para un mismo torneo, mejor posición implica mayor o igual peso: si $r_1 < r_2$, entonces $w_{r_1,\text{tier}_t} \ge w_{r_2,\text{tier}_t}$.
2. Solo reciben puntos los puestos beneficiarios del corte de su tier (tabla anterior).
3. La suma total otorgada en el torneo coincide con su score:

$$
\sum_{j \in J_t} \text{puntos}_{j,t} = \text{ScoreTorneo}_t
$$

donde $J_t$ es el conjunto de jugadores que quedan en puestos puntuables en el torneo $t$.

Si el placement del jugador queda fuera del corte de su tier, entonces:
$$
\mathrm{puntos}_{j,t} = 0
$$




### 4. Suma de puntos de resultados

$$
\mathrm{PuntosResultados}_j = \sum_{k=1}^{N_{mejores}} \text{puntos}_{j, \text{top-k torneo}}
$$



### 5. Normalizacion a 100

$$
\text{Score}_{Resultados,j} = 100 \cdot \frac{\text{PuntosResultados}_j}{\max_i(\text{PuntosResultados}_i)}
$$

El jugador con más puntos acumulados recibe 100; el resto se escala proporcionalmente.

---

## Componente H2H

### 1. Registro de enfrentamientos directos

Para cada set disputado entre jugadores A y B:
- Se registra como una victoria para el ganador y una derrota para el perdedor.
- Los sets DQ (descalificación) **no cuentan**.
- Si se disputaron múltiples sets entre el mismo par en la misma temporada, todos cuentan.

### 2. Valoración por calidad del oponente

El peso de un oponente se calcula de forma **multiplicativa** consultando los **rankings del año anterior** (año X-1):

$$
w(i) = w_2(i) \cdot w_3(i)
$$

donde:

$$
w_2(i) = \begin{cases} 3 & \text{si } i \in \text{ranking Cantabria}_{X-1} \\ 1 & \text{en caso contrario} \end{cases}
\qquad
w_3(i) = \begin{cases} 8 & \text{si } i \in \text{ranking España}_{X-1} \\ 1 & \text{en caso contrario} \end{cases}
$$

Esto produce cuatro niveles efectivos de peso:

| Situación del oponente | $w_2(i)$ | $w_3(i)$ | $w(i)$ |
|------------------------|----------|----------|--------|
| Ni Cantabria ni España | 1 | 1 | **1** |
| Solo Cantabria         | 3 | 1 | **3** |
| Solo España            | 1 | 8 | **8** |
| Cantabria **y** España | 3 | 8 | **24** |

Reglas de aplicación:
- Para el cálculo del ranking del año X, el sistema carga los rankings de España y Cantabria del año X-1.
- Los pesos se aplican de forma independiente y multiplicativa; un oponente en ambos rankings puntúa como el producto de ambos factores.
- Los valores de $w_2$ y $w_3$ se configurarán en `SeasonConfig` y podrán ajustarse por temporada.

> **Posible expansión**: modificar $w_2$ y $w_3$ para que sean funciones del puesto dentro del ranking (cuanto más cerca del top 1, mayor peso).

> **Posible expansión**: introducir un $w_4(i)$ para jugadores europeos/extranjeros.

### 3. Score H2H por jugador

$$
H2H(j) = \sum_{\substack{i \in J \\ j \text{ venció a } i}} w_2(i) \cdot w_3(i)
$$

### 4. Normalización a 100

#### Pesos por temporada

| Temporada | $w_R$ (Resultados) | $w_{H2H}$ (H2H) | $w_{vv}$ |
|-----------|--------------------|-----------------|-------|
| Cualquier anho calculado | 70% | 15% | 15% *(Ventisca Veraniega)* |


Se suman los puntos normalizado a 100 con los pesos relativos
$$
\text{Score}_{H2H,j} = 100 \cdot \frac{\text{PuntosH2H}_j}{\max_i(\text{PuntosH2H}_i)}
$$

El componente de Ventisca tambien se normaliza a 100:
$$
\text{Score}_{vv,j} = 100 \cdot \frac{\text{PuntosVV}_j}{\max_i(\text{PuntosVV}_i)}
$$

La suma final por temporada queda:

$$ Score_{Total,j}^{temp} = w_{R}^{temp} \cdot \text{Score}_{R,j} + w_{H2H}^{(temp)} \cdot \text{Score}_{H2H,j} + w_{vv}^{(temp)} \cdot \text{Score}_{vv,j}
$$

con la restriccion:
$$
w_{R}^{(temp)} + w_{H2H}^{(temp)} + w_{vv}^{(temp)} = 1
$$

Por construccion, si cada componente esta en [0, 100] y los pesos suman 1,
entonces \(\text{Score}_{total,j}^{(temp)} \in [0, 100]\).

## Temporada 2023

El ranking 2023 se considera **cerrado y ya calculado**.

- No se recalcula con este sistema.
- Se usa como ranking base para arrancar las iteraciones de temporadas posteriores.
- En particular, sirve como referencia histórica para la ponderación H2H de 2024.

---

## Bonificaciones geográficas

No se aplica fórmula de bonificación insular (Baleares/Canarias) en este proyecto.

La mención previa provenía de una copia de normativa española y se considera descartada para Smash Cantabria.

---

## Agregación final

$$ \text{Score}_{total,j}^{(temp)} = w_{R}^{(temp)} \cdot \text{Score}_{R,j} + w_{H2H}^{(temp)} \cdot \text{Score}_{H2H,j} + w_{vv}^{(temp)} \cdot \text{Score}_{vv,j} $$

El ranking final se ordena por `Score_total` de mayor a menor.

---

## Requisitos mínimos de participación

Para aparecer en el ranking publicado:

| Parámetro                   | Valor                  |
|-----------------------------|------------------------|
| Torneos mínimos disputados  | 3                      |
| Sets mínimos disputados     | No aplica              |

Los jugadores que no cumplan los mínimos se excluyen del ranking final pero sus resultados siguen contando para el cálculo del H2H de los demás.

### Alcance de jugadores en el ranking

El sistema debe permitir dos modos de elegibilidad en CLI:

- `--a`: incluye a cualquier jugador que cumpla los mínimos (all).
- `--s`: incluye solo jugadores locales que cumplan los mínimos (solo local).

### Variante Exclusión Selectiva

Se deberá añadir una función en la que el sistema pregunte por consola uno por uno los participantes del ranking a excluir, dichos participantes que se excluyan no aparecerán para el ranking, pero sí contarán para el H2H de los demás.

---

## Desempates

Cuando dos jugadores tienen el mismo `Score_total`, el desempate se resuelve en este orden:

1. Mayor `Score_Resultados`.
2. Mayor `Score_H2H`.
3. Mayor número de torneos disputados.
4. Resultado del enfrentamiento directo entre ambos en la temporada.

## Preguntas abiertas

Estos puntos deben resolverse **antes de implementar** `core/scoring.py`, `core/h2h.py` y la orquestación final en `ranking.py`:

| # | Pregunta |
|---|----------|
| ~~1~~ | ~~¿Cuáles son los valores numéricos de $w_1$, $w_2$ y $w_3$?~~ → **Resuelto**: $w_2 = 3$ (Cantabria), $w_3 = 8$ (España), base = 1; fórmula multiplicativa. |
| ~~2~~ | ~~¿Cuáles son los pesos exactos $w_R$, $w_{H2H}$, $w_{vv}$ para 2025 y 2026?~~ → **Resuelto**: 70% / 15% / 15% para cualquier anho calculado. |
| ~~3~~ | ~~¿Hay un tercer componente en 2023? ¿Qué es?~~ → **Resuelto**: 2023 no se recalcula; se usa como baseline histórico. |
| ~~4~~ | ~~¿Se tienen en cuenta solo torneos de Cantabria o también torneos fuera de la región?~~ → **Resuelto**: solo torneos de Cantabria. |
| ~~5~~ | ~~¿Existe categoría de torneo especial (p. ej. *Major* regional con multiplicador de puntos)?~~ → **Resuelto**: no; `Ventisca veraniega` ya va como componente separado. |
| ~~6~~ | ~~¿Cuál es la fórmula de bonificación para Baleares/Canarias y cuándo la decide el equipo?~~ → **Resuelto**: no aplica; descartada para este proyecto. |
