# Arreglo del proyecto Be Confident — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir las fallas silenciosas, cerrar los riesgos de seguridad/costo y eliminar el código basura detectados en la revisión del 2026-10-24, sin cambiar lo que el usuario final ve salvo donde hoy está roto.

**Architecture:** `backend/server.js` (Express, un solo archivo) se mantiene como punto de entrada con las rutas, pero la lógica pura sale a módulos pequeños en `backend/lib/` para poder testearla con `node:test` sin Supabase ni OpenAI. Los dos endpoints de fashion pasan a compartir carga de datos, prompt y armado del resultado. El frontend (repo git separado en `frontend/`) solo recibe cambios puntuales y borrado de archivos muertos.

**Tech Stack:** Node 22 (ESM), Express 4, Supabase JS v2, OpenAI SDK v4, sharp, multer; React 19 + Vite 7 + Capacitor; FastAPI + rembg (backend-rembg en Railway); deploy backend en Fly.io, frontend en Vercel.

**Spec:** No hay documento de diseño aparte. La spec es la revisión hecha en la conversación del 2026-10-24, resumida aquí:

- Fallas silenciosas: (1) backend pide modelo rembg `isnet-general-use`, que rembg no permite; (2) el contexto "outfits recientes" de la IA lee la tabla `calendario` (solo racha) en vez de `calendar_outfits` (donde están los `outfit_ids`); (3) el botón del maniquí llama `/api/fashion` sin `clima`; (4) la racha usa fecha UTC; (5, nueva) `fly.toml` apunta a `internal_port = 8080` pero el server escucha en `process.env.PORT || 5001`.
- Seguridad/costo: SSRF por `imagen_url` en `/api/subir-prenda`; IDs del usuario interpolados en filtros `.or(...)`; `/api/recomendaciones-compra` sin rate limit; `mensaje`/`historial` sin tope; 401 con `details` de debug y 500 con `err.message`; `status` de amistad sin validar; multer 1.x vulnerable; outfit subido como `image/jpeg` sin convertir; imágenes huérfanas en Storage al borrar.
- Código basura: duplicación `/api/fashion` vs `/api/fashion/stream`; helpers sin uso en backend; `Subir.jsx/.css`, `ForecastStrip.jsx/.css`, `skiper40.jsx` sin importar; `console.log` sueltos; dependencias transitivas en el `package.json` raíz; `backend/uploads/*` y `.DS_Store` versionados.

## Global Constraints

- Node 22 (local v22.21.0, Docker `node:22.21.1-slim`). Backend es ESM (`"type": "module"`).
- Tests de backend con `node:test` + `node:assert/strict`, sin dependencias nuevas. Comando: `cd backend && npm test`.
- No agregar dependencias nuevas, salvo subir `multer` a `^2.0.2`.
- Modelo OpenAI se mantiene `gpt-4o-mini`.
- Modelo rembg para prendas: `birefnet-general` (decisión previa del usuario).
- Zona horaria de la app: `process.env.APP_TZ`, por defecto `"America/Bogota"`.
- Textos visibles al usuario en español.
- Commits: el backend y la raíz se commitean desde el repo raíz; para backend, `cd backend && git add . && git commit` (costumbre del usuario). El frontend es otro repo: commits dentro de `frontend/`. Push a `origin main` solo en la Task 13.
- Cada commit termina con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Reglas de auth del frontend que NO se tocan: `usuarioId` desde caché, early return en `INITIAL_SESSION`, nunca `getSession()` ni doble listener, interceptor 401 con polling de 12 s en `App.jsx`.

## Review Focus

1. **IDs como string vs número**: si la IA devuelve `"outfit_ids":["12"]` y las prendas tienen `id: 12` (o al revés), hoy `includes` no matchea y cae al outfit aleatorio. Se espera match por `String(id)`. Test en Task 3.
2. **Escapes `\uXXXX` en el streaming**: la IA puede escribir `"está"`; el extractor actual emite `u00e1` literal. Se espera `á`, incluso si el escape llega partido entre chunks. Test en Task 4.
3. **Closet solo con outfits guardados (cero prendas sueltas)**: no debe romper ni devolver fallback vacío con error. Test en Task 3.
4. **Racha cerca de medianoche**: a las 23:30 hora Bogotá (04:30 UTC del día siguiente) "hoy" es el día local. Test en Task 2.
5. **`historial` hostil**: elementos sin `text`, `text` no string o 500 mensajes no deben romper ni inflar el prompt. Test en Task 3.

---

## Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `backend/lib/outfit.js` (nuevo) | `normalizarTipo`, `subtipoAccesorio`, `deduplicarPorTipo`, `safeParseJSON` (movidos sin cambiar comportamiento) |
| `backend/lib/fechas.js` (nuevo) | Fecha local de la app y cálculo de racha |
| `backend/lib/streamRespuesta.js` (nuevo) | Extractor incremental del campo `"respuesta"` del JSON en streaming |
| `backend/lib/fashion.js` (nuevo) | `generarContextoClima`, `formatPrendaRica`, armado del mensaje de usuario y resolución del outfit |
| `backend/prompts/fashion.js` (nuevo) | `FASHION_SYSTEM_PROMPT` único |
| `backend/lib/validar.js` (nuevo) | `esUuid` |
| `backend/lib/storage.js` (nuevo) | `rutaDesdeUrlPublica` |
| `backend/test/*.test.js` (nuevos) | Un archivo por módulo de `lib/` |
| `backend/server.js` | Rutas; importa de `lib/` y `prompts/` |
| `backend/fly.toml` | Puerto y memoria |
| `backend-rembg/main.py` | Modelo precargado |
| `frontend/src/pages/Asistente.jsx` | Enviar `clima` desde el maniquí |

---

### Task 0: Dejar el repo en un estado limpio y desplegable

**Files:**
- Modify: `backend/fly.toml`
- Ya pendientes sin commit: `backend/server.js` (health check), `backend/Dockerfile`, `backend/.dockerignore`

- [ ] **Step 1: Arreglar `fly.toml`**: agregar una sección `[env]` con `PORT = "8080"` (coincide con `internal_port = 8080`). En `[[vm]]`, dejar solo `memory = '1gb'` y borrar `memory_mb = 256`, que se contradice con la línea anterior.
- [ ] **Step 2: Verificar que el server respeta el puerto**

Run: `cd backend && PORT=8080 node server.js` y, en otra terminal, `curl -s localhost:8080/api/health`
Expected: `{"ok":true}` (requiere `backend/.env` con las claves de Supabase). Detener el server.

- [ ] **Step 3: Commit de la migración a Fly pendiente**

```bash
cd backend && git add . && git commit -m "fix(deploy): PORT=8080 en fly.toml + Dockerfile y health check"
```

- [ ] **Step 4: Resolver la divergencia del frontend** (local y `origin/main` tienen 1 commit distinto cada uno; el remoto es `bdb4b47 Delete README.md`)

Run: `cd frontend && git pull --rebase origin main`
Expected: rebase sin conflictos. Si hay conflicto, detenerse y preguntarle al usuario. No commitear los cambios de `ios/`, `android/`, `capacitor.config.ts` ni `SceneDelegate.swift` en este plan: son trabajo nativo del usuario aparte.

---

### Task 1: Infraestructura de tests + extraer helpers de outfit

**Files:**
- Create: `backend/lib/outfit.js`, `backend/test/outfit.test.js`
- Modify: `backend/package.json` (script `"test": "node --test"`), `backend/server.js:189-264` (borrar las funciones movidas e importarlas)

**Interfaces:**
- Produces: `normalizarTipo(descripcion?: string, metaIa?: object) -> string`, `subtipoAccesorio(p) -> string`, `deduplicarPorTipo(prendas: object[]) -> object[]`, `safeParseJSON(content: string | {text}[]) -> object | null`. Todas con `export`, mismo código que hoy.

- [ ] **Step 1: Escribir los tests que fijan el comportamiento actual** en `backend/test/outfit.test.js`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { normalizarTipo, deduplicarPorTipo, safeParseJSON } from "../lib/outfit.js";

const p = (id, descripcion, metadata_ia = {}) => ({ id, descripcion, metadata_ia });

test("normalizarTipo: hoodie en parte superior cuenta como abrigo", () => {
  assert.equal(normalizarTipo("hoodie (gris) - parte superior"), "abrigo");
});
test("normalizarTipo: metadata_ia.tipo tiene prioridad", () => {
  assert.equal(normalizarTipo("x (negro) - accesorio", { tipo: "Calzado" }), "calzado");
});
test("deduplicarPorTipo: con vestido descarta superior e inferior", () => {
  const r = deduplicarPorTipo([p(1, "vestido (rojo) - vestido"), p(2, "camiseta (blanco) - parte superior"), p(3, "jean (azul) - parte inferior"), p(4, "tenis (blanco) - calzado")]);
  assert.deepEqual(r.map(x => x.id), [1, 4]);
});
test("deduplicarPorTipo: un accesorio por subtipo", () => {
  const r = deduplicarPorTipo([p(1, "gorra (negro) - accesorio"), p(2, "gorra (rojo) - accesorio"), p(3, "reloj (plata) - accesorio")]);
  assert.deepEqual(r.map(x => x.id), [1, 3]);
});
test("safeParseJSON: extrae JSON rodeado de texto y devuelve null si no hay", () => {
  assert.deepEqual(safeParseJSON('ok {"a":1} fin'), { a: 1 });
  assert.equal(safeParseJSON("sin json"), null);
});
```

- [ ] **Step 2: Correr y ver que falla.** Run: `cd backend && npm test`. Expected: FAIL, `Cannot find module '../lib/outfit.js'`.
- [ ] **Step 3: Mover las 4 funciones** de `server.js` a `backend/lib/outfit.js` con `export`, e importarlas en `server.js`. Agregar `"test": "node --test"` a `scripts`.
- [ ] **Step 4: Correr.** Run: `npm test`. Expected: 5 pass. Además `node --check server.js` sin error.
- [ ] **Step 5: Commit**

```bash
cd backend && git add . && git commit -m "refactor(backend): extraer helpers de outfit a lib/ con tests"
```

---

### Task 2: Racha y fechas en hora local de la app

**Files:**
- Create: `backend/lib/fechas.js`, `backend/test/fechas.test.js`
- Modify: `backend/server.js`: `registrarRachaHoy` (~1019), cálculo del `gte` de 14 días (~1047, ~1332), `/api/racha` (~2116-2165)

**Interfaces:**
- Produces:
  - `fechaHoy(ahora: Date = new Date(), tz: string = process.env.APP_TZ || "America/Bogota") -> "YYYY-MM-DD"`, implementada con `Intl.DateTimeFormat("en-CA", { timeZone: tz })`.
  - `restarDias(fecha: "YYYY-MM-DD", n: number) -> "YYYY-MM-DD"`, aritmética en UTC sobre la fecha, sin hora local.
  - `calcularRacha(fechas: string[], hoy: "YYYY-MM-DD") -> { racha: number, ultimaFecha: string | null, registroHoy: boolean }`. Acepta fechas con hora (`slice(0, 10)`), duplicadas y desordenadas.

- [ ] **Step 1: Tests**

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { fechaHoy, restarDias, calcularRacha } from "../lib/fechas.js";

test("fechaHoy: 04:30 UTC es todavía el día anterior en Bogotá", () => {
  assert.equal(fechaHoy(new Date("2026-10-25T04:30:00Z"), "America/Bogota"), "2026-10-24");
});
test("restarDias cruza meses", () => {
  assert.equal(restarDias("2026-03-01", 1), "2026-02-28");
});
test("calcularRacha: consecutiva terminando hoy", () => {
  assert.deepEqual(calcularRacha(["2026-10-24", "2026-10-23", "2026-10-23", "2026-10-22T10:00:00"], "2026-10-24"),
    { racha: 3, ultimaFecha: "2026-10-24", registroHoy: true });
});
test("calcularRacha: terminando ayer sigue viva, sin registro hoy", () => {
  assert.deepEqual(calcularRacha(["2026-10-23", "2026-10-22"], "2026-10-24"),
    { racha: 2, ultimaFecha: "2026-10-23", registroHoy: false });
});
test("calcularRacha: hueco la corta y vacío da 0", () => {
  assert.equal(calcularRacha(["2026-10-24", "2026-10-21"], "2026-10-24").racha, 1);
  assert.equal(calcularRacha(["2026-10-20"], "2026-10-24").racha, 0);
  assert.deepEqual(calcularRacha([], "2026-10-24"), { racha: 0, ultimaFecha: null, registroHoy: false });
});
```

- [ ] **Step 2: Correr.** Expected: FAIL (módulo no existe).
- [ ] **Step 3: Implementar `lib/fechas.js`** y usarlo:
  - `registrarRachaHoy` inserta `fecha: fechaHoy()`.
  - El `gte` de 14 días usa `restarDias(fechaHoy(), 14)`.
  - `/api/racha` devuelve `calcularRacha(data.map(e => e.fecha), fechaHoy())`. Esto corrige de paso que dos ramas no devolvían `registroHoy`.
- [ ] **Step 4: Correr.** Run: `npm test`. Expected: todos pass.
- [ ] **Step 5: Commit.** `cd backend && git add . && git commit -m "fix(racha): usar fecha local America/Bogota en vez de UTC"`

---

### Task 3: Unificar los dos endpoints de fashion (y leer `calendar_outfits`)

**Files:**
- Create: `backend/lib/fashion.js`, `backend/prompts/fashion.js`, `backend/test/fashion.test.js`
- Modify: `backend/server.js:974-1017` (mover `generarContextoClima` y `formatPrendaRica`), `:1029-1610` (reescribir ambos handlers sobre lo compartido)

**Interfaces:**
- Consumes: `deduplicarPorTipo`, `safeParseJSON` (Task 1); `fechaHoy`, `restarDias` (Task 2).
- Produces:
  - `FASHION_SYSTEM_PROMPT: string` en `prompts/fashion.js`. Es el prompt largo que hoy está en `/api/fashion` (líneas 1422-1554), copiado tal cual. Es la versión con teoría del color y reglas por ocasión, que el chat hoy no recibe.
  - `generarContextoClima(clima) -> string`, `formatPrendaRica(p) -> string`: movidos sin cambios.
  - `limpiarHistorial(historial: unknown) -> {role, text}[]`: si no es array, devuelve `[]`; descarta elementos cuyo `text` no sea string; se queda con los últimos 10 y corta cada `text` a 1000 caracteres.
  - `construirMensajeUsuario({ perfil, clima, prendasSueltas, outfitsGuardados, outfitIdsAnteriores, calendarioReciente, historial, mensaje }) -> string`. Arma el mismo texto que hoy (perfil, clima, prendas, outfits, actual, calendario, exclusión, historial y mensaje). Los IDs excluidos salen de `calendarioReciente[i].metadata.outfit_ids` más `outfitIdsAnteriores`.
  - `resolverOutfit(parsed: object | null, prendasSueltas, outfitsGuardados) -> { outfit: object[], outfit_guardado: object | null, cambiar_panel: boolean, sugerencias: {text, action, tipo?}[] }`.
    - Si `parsed` es `null`, devuelve el fallback aleatorio deduplicado con `cambiar_panel: true` y `sugerencias: []`.
    - Compara IDs con `String(id)`.
    - Las sugerencias quedan en máximo 3; un string se convierte en `{text, action: "chat"}`; se descartan las que no tienen `text`.
- En `server.js`:
  - `async function cargarDatosFashion(usuario_id) -> { prendas, perfil, calendarioReciente }`. Hace las 3 consultas en paralelo como hoy, pero el calendario se lee de **`calendar_outfits`** (`select("fecha, descripcion, metadata")`, `gte("fecha", restarDias(fechaHoy(), 14))`, orden desc, `limit(10)`).
  - Validación común: `mensaje` debe ser string no vacío de ≤ 1000 caracteres (si no, 400 `"Mensaje inválido"`); `outfit_ids_anteriores` debe ser array.
  - `/api/fashion` responde `{ respuesta, ...resolverOutfit(...) }`. `/api/fashion/stream` usa el mismo prompt, `resolverOutfit` y el extractor de la Task 4. Ambos llaman `registrarRachaHoy` solo si `cambiar_panel`, como hoy.
  - Las cabeceras SSE van en una función `iniciarSSE(res)`.

- [ ] **Step 1: Tests** (incluyen los puntos 1, 3 y 5 de Review Focus)

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { resolverOutfit, construirMensajeUsuario, limpiarHistorial } from "../lib/fashion.js";

const sueltas = [
  { id: 12, tipo: "prenda", descripcion: "camiseta (blanco) - parte superior", metadata_ia: {} },
  { id: 13, tipo: "prenda", descripcion: "jean (azul) - parte inferior", metadata_ia: {} },
];
const guardado = { id: 99, tipo: "outfit", descripcion: "Outfit casual", metadata_ia: { prendas: [] } };

test("resolverOutfit: matchea IDs aunque vengan como string", () => {
  const r = resolverOutfit({ outfit_ids: ["12", "13"], cambiar_panel: true }, sueltas, []);
  assert.deepEqual(r.outfit.map(p => p.id), [12, 13]);
});
test("resolverOutfit: outfit guardado tiene prioridad", () => {
  const r = resolverOutfit({ outfit_ids: [99] }, sueltas, [guardado]);
  assert.equal(r.outfit_guardado.id, 99);
  assert.deepEqual(r.outfit, []);
});
test("resolverOutfit: sin prendas sueltas no rompe", () => {
  const r = resolverOutfit({ outfit_ids: [1] }, [], [guardado]);
  assert.deepEqual(r.outfit, []);
  assert.equal(r.outfit_guardado, null);
});
test("resolverOutfit: parsed null da fallback y normaliza sugerencias", () => {
  assert.equal(resolverOutfit(null, sueltas, []).cambiar_panel, true);
  const r = resolverOutfit({ outfit_ids: [12], sugerencias: ["Más formal", {}, { text: "a", action: "swap", tipo: "calzado" }, { text: "b" }] }, sueltas, []);
  assert.deepEqual(r.sugerencias, [{ text: "Más formal", action: "chat" }, { text: "a", action: "swap", tipo: "calzado" }]);
});
test("construirMensajeUsuario: excluye IDs del calendario reciente", () => {
  const txt = construirMensajeUsuario({ perfil: null, clima: null, prendasSueltas: sueltas, outfitsGuardados: [],
    outfitIdsAnteriores: [], calendarioReciente: [{ fecha: "2026-10-23", metadata: { outfit_ids: [12] } }], historial: [], mensaje: "hola" });
  assert.match(txt, /EXCLUSIÓN OBLIGATORIA: Los IDs \[12\]/);
  assert.match(txt, /Mensaje del usuario: hola$/);
});
test("limpiarHistorial: descarta basura, limita a 10 y 1000 chars", () => {
  const h = [{ role: "user" }, { role: "user", text: 5 }, ...Array.from({ length: 15 }, () => ({ role: "user", text: "x".repeat(2000) }))];
  const r = limpiarHistorial(h);
  assert.equal(r.length, 10);
  assert.equal(r[0].text.length, 1000);
  assert.deepEqual(limpiarHistorial("no"), []);
});
```

Nota: en el test de sugerencias, `slice(0, 3)` se aplica antes de filtrar, igual que hoy. Por eso `{ text: "b" }` queda fuera.

- [ ] **Step 2: Correr.** Expected: FAIL (módulo no existe).
- [ ] **Step 3: Implementar `lib/fashion.js` y `prompts/fashion.js`**, y reescribir los dos handlers sobre ellos. `server.js` debería bajar unas 300 líneas.
- [ ] **Step 4: Correr.** Run: `npm test && node --check server.js`. Expected: todo pass.
- [ ] **Step 5: Smoke test manual** con el server local y un token real (sacarlo de la app web, en la pestaña Network):

Run: `curl -s -X POST localhost:5001/api/fashion -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"mensaje":"outfit casual"}'`
Expected: JSON con `respuesta` y `outfit` no vacío. Luego, guardar un outfit en el calendario con la fecha de hoy desde la app y repetir: los IDs de ese outfit no deberían aparecer.

- [ ] **Step 6: Commit.** `cd backend && git add . && git commit -m "refactor(fashion): unificar endpoints y leer outfits recientes de calendar_outfits"`

---

### Task 4: Extractor del streaming con tests (incluye `\uXXXX`)

Ejecutar antes o junto con la Task 3: el handler del stream la consume.

**Files:**
- Create: `backend/lib/streamRespuesta.js`, `backend/test/streamRespuesta.test.js`
- Modify: `backend/server.js` (reemplaza la máquina de estados inline, hoy ~1196-1268)

**Interfaces:**
- Produces: `crearExtractorRespuesta() -> { push(pieza: string): string, get terminado(): boolean }`. `push` devuelve el texto nuevo del campo `"respuesta"` que se debe emitir (puede ser `""`). Un escape partido entre piezas (`\` al final, o `\u00` + `e1`) se guarda hasta completarse. Soporta `\n \t \" \\ \/ \uXXXX`.

- [ ] **Step 1: Tests**

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { crearExtractorRespuesta } from "../lib/streamRespuesta.js";

const correr = (piezas) => { const ex = crearExtractorRespuesta(); return { texto: piezas.map(p => ex.push(p)).join(""), ex }; };

test("extrae solo el campo respuesta", () => {
  const { texto, ex } = correr(['{"respu', 'esta":"Hola ', 'mundo","outfit_ids":[1]}']);
  assert.equal(texto, "Hola mundo");
  assert.equal(ex.terminado, true);
});
test("escapes partidos entre chunks", () => {
  assert.equal(correr(['{"respuesta":"a\\', 'nb \\"c\\', '""}']).texto, 'a\nb "c"');
});
test("unicode escapes, también partidos", () => {
  assert.equal(correr(['{"respuesta":"est\\u00e1 ', 'bien \\u00', 'e9"}']).texto, "está bien é");
});
```

- [ ] **Step 2: Correr.** Expected: FAIL.
- [ ] **Step 3: Implementar** y usarlo en el handler del stream: `const ex = crearExtractorRespuesta();` y, por cada chunk, `const t = ex.push(rawPiece); if (t) res.write(...)`. El texto completo se sigue acumulando aparte para `safeParseJSON`.
- [ ] **Step 4: Correr.** Run: `npm test`. Expected: pass. Smoke test: en la app, el chat del Asistente escribe con efecto máquina de escribir y las tildes salen bien.
- [ ] **Step 5: Commit.** `cd backend && git add . && git commit -m "fix(stream): extractor de respuesta testeado, soporta escapes unicode"`

---

### Task 5: El maniquí envía el clima

**Files:**
- Modify: `frontend/src/pages/Asistente.jsx`: el armado de `climaPayload` (~378-381) y `handleGenerarOutfit` (~591-595)

**Interfaces:**
- Produces: `function buildClimaPayload(clima) -> object | null` en el mismo archivo, fuera del componente, con el mismo objeto que hoy se arma en la línea ~378. Lo usan el chat y `handleGenerarOutfit`; este último agrega `clima: buildClimaPayload(clima)` al body de `/api/fashion`.

- [ ] **Step 1: Implementar** la función y usarla en los dos lugares.
- [ ] **Step 2: Verificar el build.** Run: `cd frontend && npm run build`. Expected: build OK.
- [ ] **Step 3: Verificar a mano**: abrir la app, cambiar a la vista maniquí, presionar "Generar outfit" y revisar en DevTools → Network que el body de `/api/fashion` incluye `clima`.
- [ ] **Step 4: Commit** (repo frontend): `cd frontend && git add src/pages/Asistente.jsx && git commit -m "fix(asistente): el maniquí envía clima al generar outfit"`

---

### Task 6: Alinear el modelo de rembg

**Files:**
- Modify: `backend/server.js:676` → `removeBackground(imagenOriginalBuffer, "birefnet-general")`. Corregir el comentario de `removeBackground` (~282) para que diga que el servicio corre en Railway.
- Modify: `backend-rembg/main.py:22` → `get_session("birefnet-general")`

- [ ] **Step 1: Hacer los dos cambios.**
- [ ] **Step 2: Verificar.** Run: `grep -n "isnet" backend/server.js backend-rembg/main.py`. Expected: sin resultados.
- [ ] **Step 3: Commit** (desde la raíz, porque toca dos carpetas): `git add backend/server.js backend-rembg/main.py && git commit -m "fix(rembg): usar y precargar birefnet-general"`. Railway redespliega rembg al hacer push en la Task 13; anotar que la primera subida después del deploy puede tardar mientras carga el modelo.

---

### Task 7: Validar entradas y cerrar el SSRF

**Files:**
- Create: `backend/lib/validar.js`, `backend/test/validar.test.js`
- Modify: `backend/server.js`:
  - `/api/subir-prenda`: borrar el campo `imagen_url` del body y la rama `descargarImagen`; borrar también la función `descargarImagen`.
  - Validar con `esUuid` y responder 400 `"ID inválido"`: `addressee_id` en `/api/amistad/solicitar`, `uid` en `/api/amistad/amigos` (solo si viene), `otro_id` en `/api/amistad/estado`, `:amigo_id` en `/api/prendas/amigo/:amigo_id`.
  - `/api/amistad/responder`: `status` debe ser `"accepted"` o `"rejected"` (los únicos valores que envía `Amigos.jsx`); si no, 400 `"Estado inválido"`.
  - `/api/recomendaciones-compra`: agregar `aiLimiter`.

**Interfaces:**
- Produces: `esUuid(v: unknown) -> boolean`, con la regex `/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i`.

- [ ] **Step 1: Test**

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { esUuid } from "../lib/validar.js";

test("esUuid", () => {
  assert.equal(esUuid("3f2b8c1e-9a4d-4e2b-8f1a-2c3d4e5f6a7b"), true);
  assert.equal(esUuid("x),id.not.is.null,and(id.eq.x"), false);
  assert.equal(esUuid(undefined), false);
  assert.equal(esUuid(123), false);
});
```

- [ ] **Step 2: Correr.** Expected: FAIL. **Step 3: Implementar y aplicar** los cambios listados arriba.
- [ ] **Step 4: Verificar.** Run: `npm test`, y con el server local: `curl -s "localhost:5001/api/amistad/estado?otro_id=abc" -H "Authorization: Bearer $TOKEN"`. Expected: 400 `{"error":"ID inválido"}`. En la app: enviar, aceptar y rechazar una solicitud sigue funcionando.
- [ ] **Step 5: Commit.** `cd backend && git add . && git commit -m "fix(seguridad): validar UUIDs y status, quitar descarga por URL, rate limit en recomendaciones"`

---

### Task 8: Respuestas de error sin filtrar detalles internos + limpieza del backend

**Files:**
- Modify: `backend/server.js`

**Interfaces:**
- Produces: `function fallar(res, etiqueta: string, err: Error, status = 500)`. Hace `console.error(\`🔥 ${etiqueta}:\`, err.message)` y responde `res.status(status).json({ error: "Error interno" })`.

- [ ] **Step 1: Reemplazar** cada `console.error("🔥 x:", err.message); res.status(500).json({ error: err.message });` por `fallar(res, "x", err)`. Se mantienen tal cual:
  - los 400/403/404 con mensaje propio (por ejemplo "Username ya en uso", que muestran `Perfil.jsx` y `SetupPerfil.jsx`);
  - las respuestas con forma propia de `/api/fashion` y `/api/recomendaciones-compra`.
- [ ] **Step 2: En `requireAuth`**, borrar `details` de la respuesta 401 y dejar el log solo con `reason`. Borrar `getAuthDebug`, `decodeJwtPayload` y `getSupabaseProjectRef`.
- [ ] **Step 3: Borrar código muerto**:
  - la función `cleanupFile`;
  - el bloque de comentario vacío "🧠 PARSE JSON";
  - el comentario de "Railway" en `trust proxy` (cambiarlo por "proxy de Fly.io");
  - los prefijos "Fix N" en los comentarios.
- [ ] **Step 4: Verificar.** Run: `npm test && node --check server.js && grep -c "err.message })" server.js`. Expected: tests pass y el conteo da `0`. Con el server local: `curl -s localhost:5001/api/perfil/me -H "Authorization: Bearer x"` → `{"error":"Token inválido","code":"AUTH_TOKEN_INVALID"}` sin `details`.
- [ ] **Step 5: Commit.** `cd backend && git add . && git commit -m "refactor(backend): errores genéricos al cliente y borrar código muerto"`

---

### Task 9: Storage — formato correcto e imágenes huérfanas

**Files:**
- Create: `backend/lib/storage.js`, `backend/test/storage.test.js`
- Modify: `backend/server.js`:
  - rama outfit de `/api/subir-prenda` (~758): convertir con `sharp(buf).jpeg({ quality: 85 })` antes de subir;
  - `DELETE /api/prendas/:id` y `DELETE /api/posts/:id`: seleccionar también `imagen_url` y, después de borrar la fila, hacer `supabase.storage.from("prendas").remove([ruta])` si `ruta` no es `null`. Si eso falla, solo se loguea: no cambia la respuesta.

**Interfaces:**
- Produces: `rutaDesdeUrlPublica(url: string, bucket = "prendas") -> string | null`. Devuelve lo que viene después de `/storage/v1/object/public/<bucket>/`, decodificado, o `null`.

- [ ] **Step 1: Test**

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { rutaDesdeUrlPublica } from "../lib/storage.js";

test("rutaDesdeUrlPublica", () => {
  assert.equal(rutaDesdeUrlPublica("https://abc.supabase.co/storage/v1/object/public/prendas/posts/u_1.jpg"), "posts/u_1.jpg");
  assert.equal(rutaDesdeUrlPublica("https://abc.supabase.co/storage/v1/object/public/otro/x.jpg"), null);
  assert.equal(rutaDesdeUrlPublica(null), null);
});
```

- [ ] **Step 2: Correr** (FAIL). **Step 3: Implementar.** **Step 4:** `npm test` pass. Luego, en la app, subir y borrar una prenda y confirmar en el dashboard de Supabase → Storage que el archivo desapareció.
- [ ] **Step 5: Commit.** `cd backend && git add . && git commit -m "fix(storage): outfits en JPEG real y borrar imagen al eliminar prenda/post"`

---

### Task 10: Subir multer a 2.x

**Files:**
- Modify: `backend/package.json`, `backend/package-lock.json`

- [ ] **Step 1:** Run: `cd backend && npm install multer@^2.0.2`
- [ ] **Step 2: Verificar.** Run: `npm audit --omit=dev`. Expected: ninguna vulnerabilidad de multer. Luego, con el server local y la app, subir una prenda, un avatar y un post: los tres funcionan. Probar también un archivo `.txt` renombrado a `.jpg`: debe dar 415 o 500 sin tumbar el server.
- [ ] **Step 3: Commit.** `cd backend && git add . && git commit -m "chore(deps): multer 2.x"`

---

### Task 11: Limpieza del frontend

**Files:**
- Delete: `frontend/src/pages/Subir.jsx`, `frontend/src/pages/Subir.css`, `frontend/src/components/ForecastStrip.jsx`, `frontend/src/components/ForecastStrip.css`, `frontend/src/components/ui/skiper-ui/skiper40.jsx`
- Modify: archivos de `frontend/src/pages/*.jsx` que tengan `console.log`

- [ ] **Step 1: Confirmar que nada los importa.** Run: `cd frontend && grep -rn "Subir\b\|Subir\.\|ForecastStrip\|skiper40" src | grep -v "^src/pages/Subir\|^src/components/ForecastStrip\|skiper40.jsx:"`. Expected: sin resultados (si aparece algo, no borrar ese archivo y avisar).
- [ ] **Step 2: Borrar** los 5 archivos con `git rm`.
- [ ] **Step 3: Borrar las líneas `console.log(...)`** de `src/`. Los `console.error` se quedan. Run después: `grep -rn "console.log" src`. Expected: sin resultados.
- [ ] **Step 4: Verificar.** Run: `npm run build`. Expected: build OK. Luego abrir la app con `npm run dev` y recorrer Asistente, Closet, Calendario, Feed, Perfil y Amigos sin errores en consola.
- [ ] **Step 5: Commit** (repo frontend): `git add -A src && git commit -m "chore: borrar componentes sin uso y console.log"`

---

### Task 12: Limpieza del repo raíz

**Files:**
- Modify: `package.json` (raíz), `package-lock.json` (raíz), `.gitignore` (raíz)
- Untrack: `backend/uploads/*`, todos los `.DS_Store`

- [ ] **Step 1:** En el `package.json` raíz, dejar `"dependencies": {}` y en `devDependencies` solo `concurrently`. Borrar `vite` y `@vitejs/plugin-react`, que solo usa el frontend. Luego, desde la raíz, correr `rm -rf node_modules && npm install`.
- [ ] **Step 2: Verificar.** Run: `npm run dev` desde la raíz. Expected: arrancan BACKEND y FRONTEND. Detener.
- [ ] **Step 3: Agregar `uploads/`** al `.gitignore` raíz (`.DS_Store` ya está), y sacar del índice lo que no corresponde: `git rm -r --cached backend/uploads` y `git ls-files -z | grep -z "\.DS_Store$" | xargs -0 git rm --cached`. Hacer lo mismo para `.DS_Store` dentro de `frontend/`, en su propio repo, agregando `.DS_Store` a `frontend/.gitignore` si no está.
- [ ] **Step 4: Verificar.** Run: `git ls-files | grep -E "uploads/|DS_Store"`. Expected: vacío (en los dos repos).
- [ ] **Step 5: Commits.** Raíz: `git add -A && git commit -m "chore: limpiar deps raíz y dejar de versionar uploads/.DS_Store"`. Frontend: `git commit -m "chore: dejar de versionar .DS_Store"`.

---

### Task 13: Verificación final y despliegue

- [ ] **Step 1:** Run: `cd backend && npm test && node --check server.js`, y `cd frontend && npm run build`. Expected: todo verde.
- [ ] **Step 2: Recorrido completo con el server local** (`npm run dev` desde la raíz):
  - subir una prenda: sin fondo, y la metadata aparece en el Closet;
  - subir un outfit;
  - chat del Asistente con streaming;
  - "Generar outfit" del maniquí;
  - guardar el outfit en el Calendario y pedir otro: no repite prendas;
  - la racha muestra el valor correcto;
  - en el Feed: crear un post, dar like, comentar y borrar;
  - en Amigos: buscar, enviar, aceptar y eliminar.
- [ ] **Step 3: Pedirle al usuario confirmación antes de publicar.** Con su OK, hacer `git push origin main` en la raíz y en `frontend/`, y `cd backend && fly deploy`. Luego verificar con `curl -s https://closet-ia-backend.fly.dev/api/health` → `{"ok":true}` y repetir el chat desde la app desplegada en Vercel.

---

## Fuera de este plan (planes futuros)

- **CSS muerto** (~10.000 líneas): primero hay que medirlo (por ejemplo, con la cobertura de CSS de Chrome DevTools por página) y después hacer un plan propio.
- **Unificar `getAuthHeaders()` con el interceptor de axios**: toca la autenticación en todas las páginas y tiene reglas delicadas (ver Global Constraints). Va en un plan aparte, con pruebas de sesión expirada.
- **Partir `server.js` en routers por dominio** (perfil, amistad, prendas, feed, calendario): tiene sentido después de este plan, que ya saca la lógica a `lib/`.
- **Calendario y probador/maniquí**: son las features planificadas; se retoman después de este arreglo.
