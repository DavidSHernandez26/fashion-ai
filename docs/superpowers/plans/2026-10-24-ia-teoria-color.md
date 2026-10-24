# IA con teoría del color — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que cada outfit siga una regla de color verificable (monocromático, dos colores, análogos, complementarios, tríada, neutros + acento), pedible por chat, nombrada en la respuesta, variada y sesgada por el estilo aprendido del usuario, con el color medible también para lo ya subido.

**Architecture:** La lógica de color es pura y testeable en `backend/lib/` y queda repartida en estos módulos:
- color medible;
- reglas;
- intérprete del pedido;
- generador de combinaciones;
- estilo aprendido.

Los endpoints de fashion generan una lista corta de combinaciones válidas y la IA elige una por número (`opcion`). El backend valida esa elección antes de transmitir el texto. El color de cada prenda se guarda en `metadata_ia.color_medible`. El Closet gana un botón y un aviso visibles para completar lo ya subido.

**Tech Stack:** Node 22 ESM + Express, `sharp` (ya instalado), Supabase, OpenAI `gpt-4o-mini`, `node:test`; React 19 + Vite + Capacitor 8.

**Spec:** `docs/superpowers/specs/2026-10-24-ia-teoria-color-design.md`

## Global Constraints

- Sin dependencias nuevas en el backend. El color dominante se calcula con `sharp`.
- Sin migraciones: todo dato nuevo va en JSON existente (`prendas.metadata_ia`, `calendar_outfits.metadata`).
- Modelo `gpt-4o-mini`; se mantienen `max_tokens: 900` y `temperature: 0.7` en fashion.
- Siguen los topes actuales: mensaje ≤ 1000 caracteres, historial de 10, `outfit_ids_anteriores` ≤ 30 y `clima` sanitizado.
- `regla` es un campo **nuevo y opcional** en las respuestas de fashion. Se mantienen los campos `outfit`, `outfit_guardado`, `cambiar_panel` y `sugerencias`, con su forma actual.
- Nombres visibles de las reglas (exactos): `Monocromático`, `Dos colores`, `Análogos`, `Complementarios`, `Tríada`, `Neutros + acento`.
- Neutros generales: `negro`, `blanco`, `gris`, `beige`, `azul marino`, `denim`. En calzado y accesorios también son neutros `café` y los tonos metálicos (que se detectan como gris o beige).
- Si se pide una familia, sus variantes neutras cuentan como ella: `azul marino` y `denim` cuentan como `azul`, y `beige` como `café`.
- Umbrales de clima (los mismos del prompt actual): abrigo obligatorio si la sensación es < 18 °C o la lluvia ≥ 40 %; sin abrigo si la sensación es > 25 °C; sin shorts, bermudas ni sandalias si la sensación es < 12 °C.
- Botón de análisis: visible en las pestañas de prendas **y** outfits, con el texto **"Analizar colores"**. En pantallas ≤ 768 px va en su propia línea, a lo ancho, con al menos 44 px de alto.
- Repos: el backend se commitea dentro de `backend/`, el frontend dentro de `frontend/` y los docs en la raíz. Nunca se hace push ni deploy sin el OK del usuario. Trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Tests: `cd backend && npm test` (`node --test`). Frontend: `cd frontend && npm run build`.

## Review Focus

1. **Closet todavía sin analizar** (prendas sin `color_medible`): el chat debe seguir funcionando como hoy (flujo actual), no quedarse sin outfit. Test en la Task 4.
2. **Closet incompleto** (sin calzado o sin accesorios): el generador arma outfits sin esa categoría en vez de devolver nada. Test en la Task 4.
3. **Palabras de color dentro de un pedido de edición o exclusión** ("sin la chaqueta negra", "cambia la camisa blanca"): no deben convertirse en un pedido de regla de color. Test en la Task 3.
4. **Tonos que cruzan el 0°** (rojo 350° con naranja 20°): son análogos. Test en la Task 2.
5. **La IA devuelve una `opcion` inexistente o la omite durante el streaming:** no debe transmitirse un texto que contradiga el outfit mostrado. Test en la Task 6.

---

## Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `backend/lib/color.js` (nuevo) | hex → HSL, familia y neutro; nombres de color en español → familia; `faltaColorMedible` |
| `backend/lib/colorImagen.js` (nuevo) | color dominante de una imagen con transparencia (`sharp`) |
| `backend/lib/reglas.js` (nuevo) | qué prendas cuentan, `cumpleRegla`, `detectarRegla`, nombres visibles |
| `backend/lib/pedidoColor.js` (nuevo) | traduce el mensaje del usuario a regla, familias, exclusiones y edición |
| `backend/lib/generador.js` (nuevo) | filtro de clima, combinaciones válidas por regla, lista corta variada |
| `backend/lib/estilo.js` (nuevo) | estilo aprendido del calendario y de los outfits guardados; puntaje |
| `backend/lib/fashion.js` | mensaje con opciones, `resolverEleccion`, `leerOpcion` |
| `backend/prompts/fashion.js` | sección de color y formato JSON con `opcion` y `regla` |
| `backend/server.js` | captura de color al subir, reanálisis, `pendientes-color`, endpoints de fashion, regla en el calendario |
| `frontend/src/pages/Closet.jsx`, `Closet.css` | botón "Analizar colores" y aviso de pendientes |

---

### Task 1: Color medible

**Files:**
- Create: `backend/lib/color.js`, `backend/lib/colorImagen.js`, `backend/test/color.test.js`

**Interfaces:**
- Produces:
  - `hexAHsl(hex: string) -> { h: number, s: number, l: number } | null`, con h en 0–360, s y l en 0–100. Devuelve null si el hex es inválido.
  - `colorMedible(hex: string) -> { hex: string, h, s, l, familia: string, neutro: boolean } | null`.
    - Familias cromáticas: `rojo`, `naranja`, `amarillo`, `verde`, `turquesa`, `azul`, `morado`, `rosa`, `café`.
    - Familias neutras: `negro`, `blanco`, `gris`, `beige`, `azul marino`, `denim`.
    - Los umbrales son constantes con nombre, a criterio del implementador.
  - `familiaDeNombre(texto: string) -> string | null`, para nombres en español. Mínimo debe reconocer:
    - azul; marino → `azul marino`; negro; blanco; gris;
    - beige, crema y camel → `beige`;
    - café y marrón → `café`; rojo, burdeos y vino → `rojo`;
    - verde y oliva → `verde`; amarillo y mostaza → `amarillo`;
    - rosa; morado y lila → `morado`; naranja; turquesa;
    - denim → `denim`.
  - `faltaColorMedible(item) -> boolean`:
    - si `item.tipo === "prenda"`: true cuando no existe `metadata_ia.color_medible`;
    - si `item.tipo === "outfit"`: true cuando alguna de `metadata_ia.prendas[]` no tiene `color_medible`.
  - `colorDominante(buffer: Buffer) -> Promise<string | null>` (en `colorImagen.js`). Devuelve el hex del color más frecuente entre los píxeles con alfa ≥ 128, o `null` si menos del 5 % de los píxeles son transparentes (imagen con fondo).

- [ ] **Step 1: Tests**

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import sharp from "sharp";
import { hexAHsl, colorMedible, familiaDeNombre, faltaColorMedible } from "../lib/color.js";
import { colorDominante } from "../lib/colorImagen.js";

test("hexAHsl", () => {
  assert.deepEqual(hexAHsl("#ff0000"), { h: 0, s: 100, l: 50 });
  assert.equal(hexAHsl("nope"), null);
});
test("colorMedible: familias y neutros", () => {
  const f = (hex) => { const c = colorMedible(hex); return [c.familia, c.neutro]; };
  assert.deepEqual(f("#000000"), ["negro", true]);
  assert.deepEqual(f("#FFFFFF"), ["blanco", true]);
  assert.deepEqual(f("#808080"), ["gris", true]);
  assert.deepEqual(f("#D2B48C"), ["beige", true]);
  assert.deepEqual(f("#1B2A4A"), ["azul marino", true]);
  assert.deepEqual(f("#FF0000"), ["rojo", false]);
  assert.deepEqual(f("#0057FF"), ["azul", false]);
  assert.deepEqual(f("#2E8B57"), ["verde", false]);
  assert.deepEqual(f("#FFD700"), ["amarillo", false]);
  assert.deepEqual(f("#800080"), ["morado", false]);
  assert.deepEqual(f("#6B3E1F"), ["café", false]);
});
test("familiaDeNombre", () => {
  assert.equal(familiaDeNombre("Verde Oliva"), "verde");
  assert.equal(familiaDeNombre("mostaza"), "amarillo");
  assert.equal(familiaDeNombre("azul marino"), "azul marino");
  assert.equal(familiaDeNombre("camel"), "beige");
  assert.equal(familiaDeNombre("xyz"), null);
});
test("faltaColorMedible", () => {
  assert.equal(faltaColorMedible({ tipo: "prenda", metadata_ia: {} }), true);
  assert.equal(faltaColorMedible({ tipo: "prenda", metadata_ia: { color_medible: { familia: "rojo" } } }), false);
  assert.equal(faltaColorMedible({ tipo: "outfit", metadata_ia: { prendas: [{ color_medible: {} }, {}] } }), true);
});
test("colorDominante: prenda roja con fondo transparente", async () => {
  const roja = await sharp({ create: { width: 40, height: 40, channels: 4, background: "#ff0000ff" } }).png().toBuffer();
  const img = await sharp({ create: { width: 100, height: 100, channels: 4, background: "#00000000" } })
    .composite([{ input: roja, top: 30, left: 30 }]).png().toBuffer();
  assert.equal(colorMedible(await colorDominante(img)).familia, "rojo");
});
test("colorDominante: imagen sin transparencia devuelve null", async () => {
  const opaca = await sharp({ create: { width: 50, height: 50, channels: 3, background: "#00ff00" } }).png().toBuffer();
  assert.equal(await colorDominante(opaca), null);
});
```

- [ ] **Step 2:** `cd backend && npm test`. Esperado: FAIL (los módulos no existen).
- [ ] **Step 3: Implementar** los dos módulos. `colorDominante`: `sharp(buf).ensureAlpha().resize(64, 64, { fit: "inside" }).raw()`, agrupar los píxeles opacos en cubos de 32 niveles por canal y promediar el cubo más poblado.
- [ ] **Step 4:** `npm test`. Esperado: todo pass.
- [ ] **Step 5: Commit** (repo backend): `feat(color): color medible de prendas`

---

### Task 2: Reglas de color

**Files:**
- Create: `backend/lib/reglas.js`, `backend/test/reglas.test.js`

**Interfaces:**
- Consumes: `normalizarTipo` (`lib/outfit.js`).
- Produces:
  - `REGLAS = ["monocromatico", "dos_colores", "analogos", "complementarios", "triada", "neutros_acento"]` y `NOMBRE_REGLA` con los nombres visibles de Global Constraints.
  - `colorDe(prenda) -> colorMedible | null`. Lee `prenda.metadata_ia.color_medible`, o `prenda.color_medible` para las prendas dentro de un outfit guardado.
  - `cuentaParaRegla(prenda) -> boolean`. Es false si no hay color, o si el tipo es calzado o accesorio y el color es neutro o `café`.
  - `cumpleRegla(prendas: object[], regla: string, familias: string[] = []) -> boolean`. Definiciones sobre las prendas que cuentan, con las familias ajustadas según las variantes pedidas de Global Constraints:
    - `monocromatico`: todas son de una misma familia (que, si se pidió, es `familias[0]`), con a lo sumo 1 prenda de otra familia neutra.
    - `dos_colores`: el conjunto de familias tiene exactamente 2 (los neutros cuentan). Si se pidieron, ese conjunto es igual a `familias`.
    - `analogos`: hay 2 o más prendas no neutras y su arco de tono (circular) es ≤ `ARCO_ANALOGO = 60`.
    - `complementarios`: los tonos no neutros forman 2 grupos, cada tono a ≤ 30° del centro de su grupo, y los centros están separados 180 ± `TOL_COMPLEMENTO = 30`.
    - `triada`: 3 grupos separados 120 ± 30.
    - `neutros_acento`: exactamente 1 prenda no neutra.
  - `detectarRegla(prendas, familias = []) -> string | null`. Prueba en este orden: monocromatico, neutros_acento, dos_colores, complementarios, triada, analogos.

- [ ] **Step 1: Tests.** Usar un helper `p(tipoTexto, hex)` que arme `{ descripcion: \`x (c) - ${tipoTexto}\`, metadata_ia: { color_medible: colorMedible(hex) } }`.
  - monocromático azul: superior `#1E50C8`, inferior `#0A2F80`, calzado `#000000`, accesorio `#C0C0C0` → `cumpleRegla(..., "monocromatico", ["azul"])` es true.
  - monocromático azul con jean: superior `#1E50C8`, inferior denim `#5B7FA6` → true con `["azul"]`.
  - monocromático roto: superior rojo `#E02020` e inferior verde `#2E8B57` → false.
  - solo blanco y negro: superior `#FFFFFF`, inferior `#000000`, calzado `#6B3E1F` (café, no cuenta) → `cumpleRegla(..., "dos_colores", ["blanco","negro"])` es true.
  - accesorio de color cuenta: lo mismo que el anterior más un accesorio rojo `#E02020` → false.
  - **(Review Focus 4)** análogos cruzando 0°: superior `#FF0040` (≈345°) e inferior `#FF6A00` (≈25°) → `"analogos"` es true.
  - complementarios: superior azul `#0057FF` e inferior naranja `#FF8C00` → true.
  - neutros + acento: superior `#808080`, inferior `#000000` y abrigo `#E02020` → `detectarRegla` es `"neutros_acento"`.
  - sin color: si a una prenda le falta `color_medible`, no cuenta, y `detectarRegla` funciona igual con el resto.
- [ ] **Step 2:** FAIL. **Step 3:** implementar. **Step 4:** pass.
- [ ] **Step 5: Commit:** `feat(color): reglas de teoría del color`

---

### Task 3: Intérprete del pedido

**Files:**
- Create: `backend/lib/pedidoColor.js`, `backend/test/pedidoColor.test.js`

**Interfaces:**
- Consumes: `familiaDeNombre` (Task 1).
- Produces: `interpretarPedido(mensaje: string) -> { regla: string | null, familias: string[], excluirTipos: string[], editarTipo: string | null }`. Los tipos son los de `normalizarTipo`: `parte superior`, `parte inferior`, `calzado`, `abrigo`, `accesorio`, `vestido`.
  - Palabras de prenda → tipo:
    - camisa, camiseta, polo, blusa, top → parte superior;
    - pantalón, jean(s), short(s), falda, bermuda → parte inferior;
    - zapatos, tenis, botas, calzado, zapatillas, sandalias → calzado;
    - chaqueta, abrigo, sudadera, hoodie, saco, blazer → abrigo;
    - gorra, bolso, reloj, collar, cinturón, lentes, accesorio(s) → accesorio;
    - vestido → vestido.
  - Exclusión: `sin <prenda>` y `no quiero <prenda>`. Edición: `cambia(r) (solo) <prenda>`. Los artículos se ignoran.
  - **Una palabra de color que va dentro de una frase de exclusión o edición no se suma a `familias`.**

- [ ] **Step 1: Tests**

```js
const t = (m) => interpretarPedido(m);
assert.deepEqual(t("quiero algo monocromático en azul"), { regla: "monocromatico", familias: ["azul"], excluirTipos: [], editarTipo: null });
assert.deepEqual(t("solo blanco y negro"), { regla: "dos_colores", familias: ["blanco", "negro"], excluirTipos: [], editarTipo: null });
assert.equal(t("un look con 2 colores").regla, "dos_colores");
assert.equal(t("algo con complementarios").regla, "complementarios");
assert.equal(t("colores análogos porfa").regla, "analogos");
assert.equal(t("una tríada").regla, "triada");
assert.equal(t("todo neutro con un toque de color").regla, "neutros_acento");
assert.deepEqual(t("outfit para hoy"), { regla: null, familias: [], excluirTipos: [], editarTipo: null });
// Review Focus 3
assert.deepEqual(t("sin la chaqueta negra"), { regla: null, familias: [], excluirTipos: ["abrigo"], editarTipo: null });
assert.deepEqual(t("cambia solo los zapatos"), { regla: null, familias: [], excluirTipos: [], editarTipo: "calzado" });
assert.deepEqual(t("cambia la camisa blanca"), { regla: null, familias: [], excluirTipos: [], editarTipo: "parte superior" });
```

- [ ] **Step 2:** FAIL. **Step 3:** implementar. Normalizar el texto quitando tildes y pasando a minúsculas antes de buscar palabras clave. **Step 4:** pass.
- [ ] **Step 5: Commit:** `feat(color): interpretar pedido de color en el chat`

---

### Task 4: Generador de combinaciones y estilo aprendido

**Files:**
- Create: `backend/lib/generador.js`, `backend/lib/estilo.js`, `backend/test/generador.test.js`, `backend/test/estilo.test.js`

**Interfaces:**
- Consumes: Task 2 (`cumpleRegla`, `detectarRegla`, `colorDe`, `REGLAS`); `normalizarTipo` y `subtipoAccesorio`.
- Produces:
  - `aptaParaClima(prenda, clima) -> boolean`, con los umbrales de Global Constraints; con `clima` null siempre es true. Además excluye `temporada` "verano" si la sensación es < 12 °C, e "invierno" si es > 25 °C.
  - `generarCandidatos({ prendas, regla, familias = [], clima = null, excluirIds = [], excluirTipos = [], fijas = [], max = 6, estilo = null, idsRecientes = [] }) -> Candidato[]`.
    - `Candidato = { ids: string[], prendas: object[], regla: string, puntaje: number }`.
    - Solo usa prendas con `color_medible` que pasen `aptaParaClima`.
    - Estructura: superior + inferior, o vestido; calzado si hay; abrigo según el clima (obligatorio si corresponde y existe, prohibido si > 25 °C, opcional si no); de 1 a 2 accesorios que respeten la regla si existen.
    - `fijas` son prendas que deben estar en todos los candidatos.
    - Con `regla` null, genera para cada regla y etiqueta cada candidato con `detectarRegla`.
    - Devuelve hasta `max` candidatos ordenados por puntaje. Cada candidato nuevo debe diferir en ≥ 2 prendas de los ya elegidos.
    - Si el producto cartesiano supera 20 000 combinaciones, se muestrea al azar hasta 20 000.
  - `candidatosGuardados(outfitsGuardados, regla, familias) -> Candidato[]`. Los outfits guardados cuya `detectarRegla` (sobre `metadata_ia.prendas`) coincide con la regla, o todos los que tengan regla detectable si `regla` es null. Usa `ids: [String(outfit.id)]`.
  - `aprenderEstilo({ calendario, prendasSueltas, outfitsGuardados }) -> { reglas: Record<string, number>, familias: Record<string, number> }`. Frecuencias normalizadas (suman 1) de reglas y familias en los outfits del calendario (`metadata.outfit_ids` → prendas) y en los outfits guardados.
  - `puntuarCandidato(candidato, estilo, idsRecientes) -> number`. Suma el peso de su regla y de sus familias en el estilo, y resta por cada prenda que esté en `idsRecientes`.

- [ ] **Step 1: Tests de generador.** Con un closet de fixture: 3 superiores (azul, blanco, rojo), 2 inferiores (denim, negro), 2 calzados (negro, blanco), 1 abrigo (gris), 2 accesorios (negro, rojo), 1 short azul de temporada verano.
  - Con `regla: "monocromatico", familias: ["azul"]`, todo candidato cumple `cumpleRegla(c.prendas, "monocromatico", ["azul"])`.
  - Con clima `{ temp: 8, feels: 6 }`: ningún candidato incluye el short y todos incluyen el abrigo.
  - Con clima `{ temp: 30, feels: 31 }`: ningún candidato incluye el abrigo.
  - Con `excluirTipos: ["abrigo"]`: ningún candidato incluye un abrigo.
  - Con `fijas` = [inferior negro]: todos lo incluyen.
  - Variedad: en el resultado, cada par de candidatos difiere en ≥ 2 IDs.
  - **(Review Focus 1)** Un closet sin ningún `color_medible` devuelve `[]`.
  - **(Review Focus 2)** Un closet sin calzado devuelve candidatos sin calzado (no `[]`).
  - Una regla imposible (`monocromatico` con `["verde"]`) devuelve `[]`.
- [ ] **Step 2: Tests de estilo:**
  - un calendario con 3 outfits monocromáticos y 1 análogo da `reglas.monocromatico === 0.75`;
  - `puntuarCandidato` de un candidato monocromático es mayor que el de uno análogo con ese estilo;
  - un candidato con una prenda reciente puntúa menos que el mismo sin ella.
- [ ] **Step 3:** FAIL. **Step 4:** implementar. **Step 5:** pass.
- [ ] **Step 6: Commit:** `feat(color): generador de combinaciones y estilo aprendido`

---

### Task 5: Capturar el color al subir, reanalizar y contar pendientes

**Files:**
- Modify: `backend/server.js`:
  - `/api/subir-prenda`: los prompts de prenda y de outfit;
  - `/api/prendas/reanalizar`;
  - un endpoint nuevo `GET /api/prendas/pendientes-color`.

**Interfaces:**
- Consumes: `colorDominante`, `colorMedible` y `faltaColorMedible` (Task 1).
- Produces:
  - `metadata_ia.color_medible` en prendas y `metadata_ia.prendas[i].color_medible` en outfits.
  - `GET /api/prendas/pendientes-color` → `{ pendientes: number }`, que cuenta los ítems del usuario con `faltaColorMedible`.
  - `POST /api/prendas/reanalizar` → `{ mensaje, actualizadas, total, pendientes }`.

- [ ] **Step 1: Subida de prenda.**
  - El prompt agrega `"color_hex": "#RRGGBB"` (color principal) al JSON pedido.
  - Después de rembg: `hex = sinFondo ? await colorDominante(sinFondo) : null`, y si da null se usa `parsed.color_hex`.
  - Guardar `color_medible: colorMedible(hex)` dentro de `metadata_ia`, solo si no es null.
- [ ] **Step 2: Subida de outfit.**
  - El prompt pide `color_hex` en cada elemento de `prendas`.
  - Guardar `color_medible: colorMedible(x.color_hex)` en cada uno.
- [ ] **Step 3: Reanalizar.** Además de lo que ya hace:
  - Prendas con `faltaColorMedible`: descargar `imagen_url` (siempre es una URL de nuestro Storage; usar `fetch` con timeout de 15 s) y calcular `colorDominante`. Si da null, pedir `color_hex` a la IA con el prompt de reanálisis ampliado.
  - Outfits con `faltaColorMedible`: una llamada de visión que devuelva `prendas[]` con `color_hex`, conservando `nombre`, `color` y `tipo`.
  - Lotes de 5 como hoy. Invalidar la caché. Devolver `pendientes`, recalculado al final.
- [ ] **Step 4: Verificar.** `npm test && node --check server.js`. Arrancar el server y probar `curl -s localhost:5001/api/prendas/pendientes-color` sin token → 401.
- [ ] **Step 5: Commit:** `feat(color): guardar color medible al subir y en el reanálisis`

---

### Task 6: Prompt, opciones y resolución de la elección

**Files:**
- Modify: `backend/prompts/fashion.js`, `backend/lib/fashion.js`, `backend/test/fashion.test.js`

**Interfaces:**
- Consumes: `Candidato` (Task 4), `NOMBRE_REGLA` (Task 2).
- Produces:
  - En `FASHION_SYSTEM_PROMPT`:
    - la sección "2. TEORÍA DEL COLOR" se reescribe: la IA debe elegir **una** de las OPCIONES listadas y explicarla según la regla;
    - el formato JSON exigido pasa a ser `{"opcion":N,"regla":"<nombre visible>","respuesta":"...","outfit_ids":[...],"cambiar_panel":true,"sugerencias":[...]}`, con `opcion` **antes** de `respuesta`;
    - se elimina "Incluye TODOS los accesorios";
    - `respuesta` empieza nombrando la regla;
    - si recibe `AVISO_REGLA`, debe decir que el closet no alcanza para lo pedido.
  - `construirMensajeUsuario({...actual, candidatos: Candidato[] = [], avisoRegla: string | null = null})`: cuando hay candidatos, agrega un bloque `OPCIONES (elige una por número):` con líneas del tipo `N) [Regla] desc1 + desc2 + ...`. Si viene `avisoRegla`, agrega `AVISO_REGLA: ...`. Sin candidatos, el texto queda igual que hoy.
  - `leerOpcion(acumulado: string) -> number | null`. Lee `"opcion": N` del JSON parcial.
  - `resolverEleccion(parsed, candidatos, prendasSueltas, outfitsGuardados) -> { outfit, outfit_guardado, cambiar_panel, sugerencias, regla, valida: boolean }`. Si `parsed.opcion` es un índice válido (empieza en 1), usa ese candidato. Si no, usa `candidatos[0]` con `valida: false`. Sin candidatos, delega en `resolverOutfit` y deja `regla` en `null` y `valida: true`. Un candidato que sea un outfit guardado devuelve `outfit_guardado`.

- [ ] **Step 1: Tests**
  - `leerOpcion('{"opcion": 3, "resp')` es 3; `leerOpcion('{"respuesta":"x')` es null.
  - `resolverEleccion({ opcion: 2 }, [c1, c2], ...)` devuelve las prendas de c2, `regla: NOMBRE_REGLA[c2.regla]` y `valida: true`.
  - **(Review Focus 5)** `resolverEleccion({ opcion: 9 }, [c1, c2], ...)` devuelve c1 con `valida: false`; `resolverEleccion({}, [c1], ...)` devuelve c1 con `valida: false`.
  - `resolverEleccion(parsed, [], ...)` equivale a `resolverOutfit` y además trae `regla: null`.
  - `construirMensajeUsuario` con candidatos contiene `OPCIONES (elige una por número):` y `1) [Monocromático]`; con `avisoRegla` contiene `AVISO_REGLA:`.
- [ ] **Step 2:** FAIL. **Step 3:** implementar. **Step 4:** pass.
- [ ] **Step 5: Commit:** `feat(color): elegir entre opciones validadas`

---

### Task 7: Conectar los endpoints de fashion y la regla del calendario

**Files:**
- Modify: `backend/server.js` (`cargarDatosFashion`, `mensajesFashion`, los dos handlers de fashion y `POST /api/calendario`)

**Interfaces:**
- Consumes: Tasks 2, 3, 4 y 6.
- Produces:
  - `cargarDatosFashion` agrega `calendarioEstilo`: las últimas 60 entradas de `calendar_outfits` (`fecha, metadata`), sin filtro de fecha.
  - Función `prepararOpciones({ datos, prendasSueltas, outfitsGuardados, peticion }) -> { candidatos, avisoRegla }` en server.js. Pasos:
    1. `pedido = interpretarPedido(mensaje)`.
    2. `fijas`: si `pedido.editarTipo` y hay `outfitIdsAnteriores`, son las prendas actuales menos las de ese tipo.
    3. `estilo = aprenderEstilo(...)`.
    4. `idsRecientes` salen del calendario de 14 días.
    5. `candidatos = [...generarCandidatos(...), ...candidatosGuardados(...)]`, ordenados por puntaje y recortados a 6.
    6. Si `pedido.regla` existe y no hay candidatos, se generan con `regla: null` y se arma `avisoRegla = "No hay suficientes prendas para <regla><' en ' + familias> — dilo y elige la mejor alternativa"`.
    7. Variedad: si `pedido.regla` es null, se ordenan primero los candidatos cuya regla no esté en las 2 reglas más recientes del calendario (`metadata.regla`).
  - Los dos endpoints usan `resolverEleccion`, y las respuestas incluyen `regla`.
  - **Streaming:**
    - antes del primer chunk de texto, `leerOpcion(fullAccumulated)`;
    - si hay candidatos y la opción es null o inválida, **no** se transmite texto de la IA;
    - al final se envía un solo chunk con `Te propongo este look (<regla>): <descs>`.
  - `POST /api/calendario`: si `metadata.outfit_ids` existe, el backend calcula `metadata.regla = detectarRegla(prendas del usuario con esos ids)` y la guarda. Si el frontend mandó `metadata.regla`, se sobrescribe.

- [ ] **Step 1: Implementar.**
- [ ] **Step 2: Verificar.** `npm test && node --check server.js`. Arrancar el server: POST `/api/fashion` sin token → 401. Revisar a mano que los dos endpoints llamen a `prepararOpciones` y a `resolverEleccion`, sin lógica duplicada entre ellos.
- [ ] **Step 3: Commit:** `feat(color): outfits por regla de color en el asistente`

---

### Task 8: Botón y aviso de análisis en el Closet

**Files:**
- Modify: `frontend/src/pages/Closet.jsx` (toolbar ~408-445, `handleReanalizar` ~130-150), `frontend/src/pages/Closet.css`

**Interfaces:**
- Consumes: `GET /api/prendas/pendientes-color` → `{ pendientes }`; `POST /api/prendas/reanalizar` → `{ mensaje, actualizadas, total, pendientes }`.

- [ ] **Step 1: Botón.**
  - Se muestra en las dos pestañas (quitar la condición `tabActiva === "prenda"`), con el texto `Analizar colores` y `Analizando…` mientras corre.
  - Clase nueva `closet-analizar-btn`. En `@media (max-width: 768px)` va en su propia fila, `width: 100%`, `min-height: 44px`.
- [ ] **Step 2: Aviso.**
  - Al montar y después de cada subida (evento `prendas-updated`, que ya existe), pedir `pendientes-color`.
  - Si `pendientes > 0`, mostrar arriba de la grilla `"{n} prendas sin analizar · Analizar ahora"` (singular si n = 1), con un botón que llama a `handleReanalizar`.
  - Después de reanalizar, actualizar con el `pendientes` de la respuesta.
  - Si falla, mostrar `"No se pudo analizar. Reintentar"`.
- [ ] **Step 3: Verificar** con `cd frontend && npm run build`. Verificación manual (pendiente para el usuario): el botón y el aviso se ven en el navegador a 375 px y a 1280 px de ancho.
- [ ] **Step 4: Commit** (repo frontend): `feat(closet): botón y aviso para analizar colores`

---

### Task 9: Sincronizar con iOS y Android

- [ ] **Step 1:** `cd frontend && npm run build && npx cap sync ios && npx cap sync android`. Esperado: los dos terminan sin error, copiando `build/` a los proyectos nativos.
- [ ] **Step 2:** `git -C frontend status --short`. Revisar qué archivos nativos cambió el sync y commitear **solo** los generados por el sync (por ejemplo `ios/App/App/public`, `android/app/src/main/assets/public` y `capacitor.config.json` si están versionados), sin mezclar el trabajo nativo sin commitear del usuario: `chore: cap sync`.
- [ ] **Step 3:** Pedirle al usuario el OK para el push de los tres repos y `fly deploy`. El frontend nuevo depende del endpoint `pendientes-color`, así que el backend se despliega antes o al mismo tiempo.
