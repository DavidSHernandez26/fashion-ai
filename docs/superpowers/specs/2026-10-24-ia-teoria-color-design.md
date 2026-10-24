# IA con teoría del color real — diseño

Fecha: 2026-10-24 · Proyecto: Be Confident (closet + asistente de moda)

## Intención y por qué

El asistente arma outfits que no son malos, pero el usuario siente que la combinación de colores **parece al azar**. Hoy la "teoría del color" son 6 viñetas dentro del prompt (`backend/prompts/fashion.js`, sección 2), y cada prenda solo tiene su color como texto libre ("café/marrón", "verde oliva"). La IA no puede calcular nada: elige a ojo.

El usuario quiere tres cosas:

1. Que **cada outfit siga una regla de color reconocible** y que la respuesta la nombre ("Look análogo en tonos tierra").
2. Poder **pedir una regla escribiéndola en el chat** con sus palabras: "solo 2 colores", "algo monocromático en azul", "solo blanco y negro", "con complementarios".
3. Que, cuando no pide nada, la IA **elija la regla que más le conviene y la vaya variando**, **aprendiendo en silencio** del estilo del usuario.

## Qué significa que funcione

- Pido "monocromático en azul" y todas las prendas con color del outfit son de la familia azul, en distintas claridades.
- Pido "solo blanco y negro" y el outfit solo tiene prendas blancas y negras.
- Pido algo que mi closet no puede cumplir y la IA me lo dice claro, por ejemplo "no tienes suficientes prendas verdes para un monocromático", y **igual** me da el mejor outfit posible con lo que tengo.
- Pido "outfit para hoy" varias veces y veo reglas distintas, cada una nombrada y coherente con el outfit que muestra.
- Con el tiempo, las reglas y paletas que elige la IA se parecen más a cómo me visto yo, según mis outfits del calendario y mis fotos de outfits completos.

## Objetivos

- **G1. Color medible por prenda.** Cada prenda guarda su color principal de forma calculable: tono (0–360°), saturación y claridad, más una **familia de color** con nombre y una marca de **neutro**. El texto libre actual se mantiene para mostrarlo.
- **G2. Reglas definidas y verificables en código.** Monocromático, dos colores, análogos, complementarios, tríada y neutros + acento, cada una definida sobre esos datos (ver "Definición de reglas").
- **G3. Pedido en lenguaje natural.** Lo que el usuario escribe se traduce a una regla, más un color opcional ("en azul") o un par de colores ("blanco y negro").
- **G4. Outfits generados por regla, no al azar.** El backend arma combinaciones que **cumplen** la regla y la IA elige entre ellas según la ocasión, el clima, el estilo y la variedad, y explica su elección. La IA no puede proponer prendas fuera de esas combinaciones válidas.
- **G5. Aviso cuando el closet no alcanza.** Si ninguna combinación cumple la regla pedida, la respuesta lo dice explícitamente y da el mejor outfit alternativo, nombrando la regla que sí usó.
- **G6. Regla nombrada en cada respuesta** de outfit (chat y maniquí), al inicio del texto y como campo estructurado `regla` en la respuesta.
- **G7. Variedad.** Sin pedido explícito, la IA no repite la misma regla que en los outfits recientes, salvo que sea la única viable.
- **G8. Aprendizaje silencioso del estilo** a partir de (a) los outfits guardados en el calendario y (b) las fotos de outfits completos subidas. El resultado sesga qué reglas y paletas se prefieren. **No se muestra** en ninguna pantalla.
- **G9. Retroactivo.** Las prendas y fotos de outfits **ya subidas** también obtienen color medible, no solo las nuevas.

## No-objetivos

- Botones, selectores o pantallas nuevas para elegir la regla: todo es por chat.
- Mostrar el perfil de estilo aprendido en el Perfil o en otro lado (más adelante, quizás).
- Cambiar el probador o maniquí más allá de que su respuesta también traiga la regla.
- Detectar varios colores por prenda para estampados complejos: se usa el color principal, y el estampado ya existe como campo `patron`.
- Cambiar el modelo de IA (`gpt-4o-mini`).

## Anti-objetivos (fallaría aunque "funcione")

- La respuesta dice "monocromático" y el outfit tiene una prenda roja y otra verde: **la regla nombrada no coincide con lo que se ve**.
- Se ignoran el clima o la ocasión para cumplir una regla de color, por ejemplo shorts con 8 °C porque eran del color correcto. Clima y ocasión siguen teniendo prioridad sobre el color.
- El usuario pide algo imposible y la IA no le da ningún outfit, o lo engaña presentando como "monocromático" algo que no lo es.
- Cada outfit es siempre la misma regla.
- El costo por mensaje se dispara: el contexto que se envía a la IA no puede crecer en proporción al número de combinaciones posibles.

## Restricciones

- Backend Node 22 ESM en Fly (`backend/server.js` más módulos puros en `backend/lib/` con tests `node:test`). La lógica de color va en módulos puros testeables.
- Supabase: los datos de color se guardan **dentro de `metadata_ia`** (JSON existente), sin migraciones de tabla (decisión mía).
- Siguen vigentes los topes de prompt del plan anterior: mensaje ≤ 1000 caracteres, historial de 10 mensajes, `outfit_ids_anteriores` ≤ 30 y `clima` sanitizado.
- Los dos endpoints (`/api/fashion` y `/api/fashion/stream`) comparten lógica (`lib/fashion.js`) y los dos deben soportar todo esto.
- El frontend lee la respuesta con los campos actuales (`outfit`, `outfit_guardado`, `cambiar_panel`, `sugerencias`). `regla` es un campo **nuevo y opcional**: el frontend actual no se rompe si no lo usa.
- Las fotos de prendas suelen venir con el fondo removido (PNG con transparencia), pero algunas quedaron **con fondo** cuando rembg falló.

## Definición de reglas (sobre el color medible)

Neutros: negro, blanco, gris, beige/crema/camel, azul marino oscuro y denim azul. Una prenda es neutra por su baja saturación o por pertenecer a esas familias; esta clasificación sale de G1.

| Regla | Se cumple cuando |
|---|---|
| Monocromático | Todas las prendas **no neutras** son de una misma familia de tono, con claridades distintas. Se permite como máximo una prenda neutra, típicamente el calzado. Con color pedido ("en azul"), esa familia es la pedida. |
| Dos colores | Todo el outfit usa exactamente dos familias de color, **contando los neutros como colores**. Así "solo blanco y negro" funciona. Con colores pedidos, son esos dos. |
| Análogos | Los tonos no neutros caen dentro de un arco de unos 60° en la rueda. Se permiten neutros. |
| Complementarios | Hay dos grupos de tono separados unos 180° (±30°). Se permiten neutros. |
| Tríada | Tres tonos separados unos 120° (±30°) entre sí. Se permiten neutros. |
| Neutros + acento | Todas las prendas son neutras menos una, que es de color. |

Las tolerancias exactas (±°, umbral de saturación para "neutro") son ajustables por el implementador. Deben ser constantes con nombre y con tests (decisión mía).

## Lo que ya decidimos sobre el cómo

- **Pedido por chat**, sin botones nuevos (decisión del usuario).
- **Si el closet no alcanza:** se avisa y se da el mejor outfit igual (decisión del usuario).
- **Aprendizaje silencioso** a partir del calendario y de las fotos de outfits completos (decisión del usuario).
- **Aplica también a lo ya subido** (decisión del usuario).
- **Color medible calculado, no solo texto:** propuesto por mí y aprobado por el usuario.

Decisiones mías dentro de eso:

1. **De dónde sale el color medible de una prenda.** De los píxeles de la imagen sin fondo: se calcula el color dominante ignorando los transparentes, con `sharp`, que ya es dependencia. Si la imagen no tiene transparencia (rembg falló), se usa un color hex estimado por la IA de visión. Para eso, el prompt de análisis de subida pide además `color_hex`.
2. **Fotos de outfits completos.** No tienen fondo removido. La IA de visión devuelve un `color_hex` por cada prenda detectada, en `metadata_ia.prendas[]`, y de ahí se calcula el color medible.
3. **Traducción del pedido a regla.** Un analizador determinista en el backend: palabras clave más una tabla de nombres de colores en español. Así es testeable y no cuesta una llamada extra a la IA. Si no reconoce ninguna regla, la elige la IA (G7 y G8).
4. **Combinaciones.** El backend genera, para la regla pedida o para cada regla viable, una **lista corta** de outfits válidos (estructura de prendas como hoy, más la regla de color). Los ordena por puntaje (estilo aprendido, variedad, prendas recientes) y le pasa a la IA solo los mejores. La IA elige uno y escribe la explicación. El backend **verifica** que los IDs elegidos sean una de esas combinaciones; si no lo son, usa la mejor de la lista.
5. **Aprendizaje.** Se calcula al vuelo, sin tabla nueva: qué reglas cumplen los outfits del calendario y de las fotos, y qué familias de color y claridades predominan. Va en caché con las prendas.
6. **Retroactivo.** Se amplía `POST /api/prendas/reanalizar`, que ya tiene botón en el Closet, para que también rellene el color medible de prendas y outfits que no lo tengan. Las prendas con fondo removido no gastan IA, porque el color sale de los píxeles.
7. **Variedad.** La regla de cada outfit se guarda en la metadata del calendario al guardarlo; el frontend agrega `regla` a lo que ya envía. Las reglas recientes salen de ahí y de la conversación en curso.

## Qué prendas cuentan para la regla (decisión del usuario)

- **Calzado y accesorios en tonos neutros** (negro, blanco, café/cuero, gris, plateado, dorado) **no rompen la regla**: quedan fuera del cálculo. Si son de color, **sí cuentan**.
- Cuando el pedido nombra un color, las variantes neutras de esa familia **cuentan como ese color**. Por ejemplo, en "en azul", el denim y el azul marino son azul y no neutros.
- La estructura del outfit cede ante la regla: se elimina "incluye TODOS los accesorios que combinen" y entran solo los que respetan la regla. Si existe al menos uno compatible, el mínimo de 1 accesorio se mantiene. Si no existe ninguno, el outfit va sin accesorio y la respuesta lo menciona.

## Más decisiones mías (tras la revisión del diseño)

8. **Clima y ocasión no se pierden.** El generador **descarta en código** las prendas que violan las reglas de clima que hoy están en el prompt. Usa los mismos umbrales actuales: abrigo obligatorio si la sensación es < 18 °C o la lluvia ≥ 40 %, sin abrigo si > 25 °C, sin shorts ni sandalias si la sensación es < 12 °C, y la temporada de la metadata. Se usa el clima ya sanitizado. La ocasión queda a cargo de la IA, pero la lista corta debe ser **variada en prendas**, no N variantes de la misma base, para que haya opciones adecuadas a la ocasión. La IA puede responder que ninguna sirve; en ese caso se usa el outfit tradicional como alternativa y la respuesta lo dice.
9. **Streaming sin contradicciones.** La IA elige una combinación **por número** (`"opcion": N`), y ese campo va **antes** de `"respuesta"` en el JSON. El backend valida el número antes de empezar a transmitir el texto. Si es inválido, no transmite el texto de la IA: envía un texto propio con la mejor combinación y su regla. El frontend no cambia.
10. **Fotos de outfits guardados.** Siguen pudiendo recomendarse: son candidatos más, y su regla se calcula a partir del `color_hex` de cada prenda detectada. Con una regla pedida, solo entran si la cumplen.
11. **Ediciones y exclusiones.** "Cambia solo X" genera combinaciones con el resto de las prendas fijo e intenta mantener la regla; si no puede, nombra la nueva regla. "Sin X / no quiero X" se detecta en el backend y excluye esa prenda o ese tipo del generador. Los chips de quitar o cambiar y el cambio manual siguen funcionando igual en el frontend. **La regla que se guarda en el calendario la recalcula el backend** a partir de los IDs, sin confiar en lo que envía el frontend. Esto reemplaza la decisión 7 en cuanto a la fuente de la regla.

## Lo que queda a criterio del implementador

- El algoritmo exacto del color dominante (cuantización, número de clusters).
- La tabla de familias de color y sus rangos de tono.
- La función de puntaje y el tamaño de la lista corta que ve la IA (debe respetar el anti-objetivo de costo).
- La redacción nueva de la sección de color del prompt.
- Cómo se reparte la generación de combinaciones entre módulos de `lib/`.
