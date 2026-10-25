# Chat estilo WhatsApp — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el chat del Asistente se vea y se mueva como WhatsApp (opción B, ventana Mac, oscuro/claro), con mensajes de outfit tipo "foto", pop up del maniquí en escritorio con confirmación por prenda, y animaciones Motion livianas.

**Architecture:** La lógica pura del chat (mensajes con hora, foto del outfit, agrupación por día) va en módulos `.mjs` testeados con `node:test`. La UI se separa en componentes pequeños (burbuja, escribiendo, separador, mensaje de outfit, pop up), todos con los mismos tokens de movimiento de Motion. `Asistente.jsx` queda como orquestador.

**Tech Stack:** React 19, Vite 7, `framer-motion` 12 (Motion, ya instalado), CSS, Capacitor 8.

**Spec:** `docs/superpowers/specs/2026-10-25-chat-estilo-whatsapp-design.md`

## Global Constraints

- Sin dependencias nuevas. Los tests del frontend corren con `node --test`: script `"test": "node --test test/"` en `frontend/package.json`. Los módulos testeados son `.mjs` en `frontend/src/lib/chat/`.
- Breakpoint: **≤ 900 px es celular, > 900 px es escritorio** (el `@media (max-width: 900px)` existente).
- Colores: oscuro `#0F0326` / lavanda `#C4B5E8`, burbuja propia en degradado `#7c5cd6 → #9b7fe0`, burbuja de la IA `rgba(196,181,232,.10)` con borde `rgba(196,181,232,.12)`. Claro: tarjeta `rgba(255,255,255,.82)`, texto `#0F0326`, burbuja propia `#5a3d9e`, burbuja de la IA blanca con borde `rgba(15,3,38,.08)`. Modo claro = `body.light-mode`.
- Textos exactos: "en línea", "escribiendo…", "Hoy", "Ayer", "Tócalo para verlo en el maniquí", "← Volver", "Cambiar", "Cancelar". La confirmación dice `¿Cambiar <etiqueta en minúscula>?` (por ejemplo "¿Cambiar calzado?").
- Animaciones: solo `transform` y `opacity`, entre 150 y 400 ms. `<MotionConfig reducedMotion="user">` envuelve el chat.
- Esquema de mensaje: `{ role: "user" | "assistant", text: string, ts?: number, outfit?: Snapshot, streaming?: boolean }`. Se persiste en `asistente_chat_${usuarioId}` como hoy, con un máximo de 100 mensajes.
- Reglas de autenticación que no se tocan: `usuarioId` desde caché, early return en `INITIAL_SESSION`, nunca `getSession()` ni doble listener.
- Commits dentro de `frontend/`, solo los archivos de cada tarea. Nunca el WIP nativo (ios/, android/, `capacitor.config.ts`, `.DS_Store`). Trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Sin push.
- Verificación de cada tarea: `cd frontend && npm test && npm run build`. Lo que necesita navegador queda como pendiente manual para el usuario.

## Review Focus

1. **Chats guardados antes del cambio** (mensajes sin `ts` ni `outfit` en localStorage): se ven sin romper, sin hora y arriba sin separador. Test en la Task 1.
2. **El texto en vivo de la IA:** cada fragmento que llega no debe volver a animar ni re-montar los mensajes anteriores. Solo anima el mensaje nuevo al montarse, con `key` estable. Lo revisa el revisor de la Task 2.
3. **Outfit guardado** (`outfit_guardado`) frente a un outfit de prendas sueltas: la foto del mensaje cubre los dos casos y al abrirse restaura el correcto. Test en la Task 1.
4. **Tamaño en localStorage:** la foto guarda solo `id`, `imagen_url` y `descripcion` de cada prenda, no la metadata completa. Test en la Task 1.
5. **Cambiar el ancho de la ventana cruzando los 900 px** con el pop up abierto: se cierra y el outfit se conserva. Verificación manual en la Task 4.

---

## Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `frontend/src/lib/chat/mensajes.mjs` (nuevo) | Crear mensajes, foto del outfit, hora, día, agrupación y actualizar la foto |
| `frontend/test/mensajes.test.mjs` (nuevo) | Tests de lo anterior |
| `frontend/src/lib/chat/movimiento.js` (nuevo) | Tokens de transición de Motion compartidos |
| `frontend/src/components/chat/ChatBubble.jsx`, `TypingIndicator.jsx`, `DaySeparator.jsx`, `OutfitMessage.jsx`, `ChatWhatsapp.css` (nuevos) | Piezas visuales del chat |
| `frontend/src/components/chat/MannequinModal.jsx`, `MannequinModal.css` (nuevos) | Pop up de escritorio |
| `frontend/src/hooks/useEsEscritorio.js` (nuevo) | `matchMedia("(min-width: 901px)")` |
| `frontend/src/components/VirtualMannequin.jsx`, `.css` | Prendas como botones y confirmación |
| `frontend/src/pages/Asistente.jsx`, `Asistente.css` | Orquestación y limpieza de animaciones duplicadas |

---

### Task 1: Lógica pura de mensajes

**Files:** Create `frontend/src/lib/chat/mensajes.mjs`, `frontend/test/mensajes.test.mjs`. Modify `frontend/package.json` (script `test`).

**Interfaces — Produces:**
- `Snapshot = { prendas: Array<{ id, imagen_url, descripcion }> } | { guardado: { id, imagen_url, descripcion } }`
- `snapshotOutfit({ outfit, outfitGuardado }) -> Snapshot | null`. Si hay outfit guardado tiene prioridad; con `outfit` vacío y sin guardado devuelve null. Solo copia esos 3 campos.
- `restaurarOutfit(snapshot) -> { outfit: object[], outfitIds: any[], outfitGuardado: object | null }`
- `crearMensaje(role, text, { ts = Date.now(), outfit = null } = {}) -> Mensaje`. Omite `outfit` si es null.
- `formatearHora(ts, locale?) -> string`. Usa `new Date(ts).toLocaleTimeString(locale, { hour: "numeric", minute: "2-digit" })`, y devuelve `""` si `ts` no es un número.
- `etiquetaDia(ts, ahora = Date.now(), locale?) -> "Hoy" | "Ayer" | string`. Compara días locales; para otros días usa `toLocaleDateString(locale, { day: "numeric", month: "long" })`.
- `agruparPorDia(mensajes, ahora = Date.now()) -> Array<{ tipo: "dia", etiqueta, key } | { tipo: "msg", msg, index }>`. Los mensajes sin `ts` van sin separador; antes del primer mensaje de cada día con `ts` va un separador.
- `actualizarSnapshot(mensajes, index, snapshot) -> Mensaje[]` (copia inmutable; si el índice no tiene `outfit`, devuelve el mismo array).
- `ultimoIndiceOutfit(mensajes) -> number` (-1 si no hay).
- `recortarHistorial(mensajes, max = 100) -> Mensaje[]` (se queda con los últimos `max`).

- [ ] **Step 1: Tests**

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import * as m from "../src/lib/chat/mensajes.mjs";

const p = (id) => ({ id, imagen_url: `u${id}`, descripcion: `d${id}`, metadata_ia: { grande: "x".repeat(500) } });

test("snapshot de prendas guarda solo 3 campos", () => {
  assert.deepEqual(m.snapshotOutfit({ outfit: [p(1)], outfitGuardado: null }),
    { prendas: [{ id: 1, imagen_url: "u1", descripcion: "d1" }] });
});
test("snapshot de outfit guardado tiene prioridad y se restaura", () => {
  const s = m.snapshotOutfit({ outfit: [p(1)], outfitGuardado: p(9) });
  assert.deepEqual(s, { guardado: { id: 9, imagen_url: "u9", descripcion: "d9" } });
  assert.deepEqual(m.restaurarOutfit(s), { outfit: [], outfitIds: [], outfitGuardado: { id: 9, imagen_url: "u9", descripcion: "d9" } });
  assert.deepEqual(m.restaurarOutfit({ prendas: [{ id: 1 }, { id: 2 }] }).outfitIds, [1, 2]);
  assert.equal(m.snapshotOutfit({ outfit: [], outfitGuardado: null }), null);
});
test("agruparPorDia: viejos sin ts arriba sin separador, luego Ayer y Hoy", () => {
  const ahora = new Date(2026, 9, 25, 12).getTime();
  const ayer = new Date(2026, 9, 24, 20).getTime();
  const r = m.agruparPorDia([{ role: "user", text: "viejo" }, m.crearMensaje("user", "a", { ts: ayer }), m.crearMensaje("assistant", "b", { ts: ahora - 1000 }), m.crearMensaje("user", "c", { ts: ahora })], ahora);
  assert.deepEqual(r.map(x => x.tipo === "dia" ? x.etiqueta : x.msg.text), ["viejo", "Ayer", "a", "Hoy", "b", "c"]);
});
test("formatearHora sin ts", () => { assert.equal(m.formatearHora(undefined), ""); });
test("actualizarSnapshot, ultimoIndiceOutfit, recortarHistorial", () => {
  const chat = [m.crearMensaje("assistant", "", { ts: 1, outfit: { prendas: [{ id: 1 }] } }), m.crearMensaje("user", "x", { ts: 2 })];
  assert.equal(m.ultimoIndiceOutfit(chat), 0);
  const nuevo = m.actualizarSnapshot(chat, 0, { prendas: [{ id: 2 }] });
  assert.notEqual(nuevo, chat);
  assert.deepEqual(nuevo[0].outfit, { prendas: [{ id: 2 }] });
  assert.equal(m.actualizarSnapshot(chat, 1, { prendas: [] }), chat);
  assert.equal(m.recortarHistorial(Array.from({ length: 150 }, (_, i) => ({ text: String(i) }))).length, 100);
});
```

- [ ] **Step 2:** `cd frontend && npm test`. Esperado: FAIL (el módulo no existe).
- [ ] **Step 3:** Implementar y agregar el script `test`. **Step 4:** pass, y `npm run build` OK.
- [ ] **Step 5: Commit:** `feat(chat): lógica de mensajes con hora y foto del outfit`

---

### Task 2: Piezas visuales tipo WhatsApp y animaciones unificadas

**Files:** Create `frontend/src/lib/chat/movimiento.js`, `frontend/src/components/chat/{ChatBubble,TypingIndicator,DaySeparator,OutfitMessage}.jsx`, `frontend/src/components/chat/ChatWhatsapp.css`. Modify `frontend/src/pages/Asistente.jsx` (render del chat ~840-935, cabecera ~725-760), `Asistente.css`.

**Interfaces:**
- Consumes: `agruparPorDia` y `formatearHora` (Task 1).
- Produces:
  - `TRANS` en `movimiento.js` con `TRANS.mensaje` (spring corto, unos 250 ms), `TRANS.aparecer` (fundido de 180 ms) y `TRANS.popup` (unos 220 ms).
  - `<ChatBubble role text ts streaming>{children}</ChatBubble>`: hora abajo a la derecha, y `✓✓` si `role === "user"`. Esquina de cola: abajo a la derecha para los propios, abajo a la izquierda para la IA.
  - `<TypingIndicator />`: los tres puntitos.
  - `<DaySeparator etiqueta />`.
  - `<OutfitMessage snapshot ts onOpen />`: miniaturas en grilla de 3 (una sola imagen si es un outfit guardado), el texto "Tócalo para verlo en el maniquí" y la hora. Es un `<button>`.

- [ ] **Step 1:** Crear los componentes y el CSS con los colores de Global Constraints, en oscuro y en `body.light-mode`.
- [ ] **Step 2:** En `Asistente.jsx`:
  - Envolver el chat en `<MotionConfig reducedMotion="user">`.
  - Renderizar con `agruparPorDia(chat)`. Cada mensaje es un `motion` con `initial` solo al montar, `key` estable (el índice) y **sin `layout`**: los fragmentos del texto en vivo no deben volver a animar nada.
  - Los mensajes con `outfit` se renderizan con `OutfitMessage`; el resto con `ChatBubble`. La lógica actual de formato del texto de la IA (párrafos e items) se mantiene como hijo de la burbuja.
  - La cabecera muestra "en línea" con punto verde, o "escribiendo…" mientras `loading` o hay un mensaje en `streaming`, con un fundido entre ambos (`TRANS.aparecer`).
  - `TypingIndicator` se muestra donde hoy está el indicador de carga.
- [ ] **Step 3:** Borrar del CSS las animaciones que quedan duplicadas por Motion (`messageIn`, `dotBounce` y el cursor si se reemplaza) y verificar con `grep` que nada más las use.
- [ ] **Step 4: Verificar.** `npm test && npm run build`. Pendiente manual: mirar oscuro y claro a 375 px y a 1280 px.
- [ ] **Step 5: Commit:** `feat(chat): burbujas estilo WhatsApp y animaciones unificadas`

---

### Task 3: Mensajes con hora y foto del outfit en el flujo del chat

**Files:** Modify `frontend/src/pages/Asistente.jsx` (`enviarMensaje`/`processEvent` ~370-470, `handleSeleccionarPrenda` ~640, acciones de chips ~905-925, persistencia del chat).

**Interfaces:**
- Consumes: Task 1 (`crearMensaje`, `snapshotOutfit`, `restaurarOutfit`, `actualizarSnapshot`, `ultimoIndiceOutfit`, `recortarHistorial`) y `OutfitMessage.onOpen` (Task 2).
- Produces:
  - estado `indiceOutfitAbierto: number | null`;
  - `abrirOutfitDeMensaje(index)`: restaura el outfit de ese mensaje como actual (`restaurarOutfit`), guarda el índice y luego, en celular, `setShowOutfitSheet(true)`; en escritorio, `setModalAbierto(true)`, que la Task 4 conecta. Agrega en esta tarea el estado `modalAbierto` (false) para que exista.

- [ ] **Step 1: Crear mensajes con `ts`.** Los mensajes del usuario y de la IA se crean con `crearMensaje` (el mensaje en vivo recibe `ts` cuando se agrega). Al persistir se usa `recortarHistorial`.
- [ ] **Step 2: Mensaje de outfit.** En el evento `done` (y en la respuesta de `/api/fashion` del Probador), si `cambiar_panel` es true y hay outfit, se agrega después del texto `crearMensaje("assistant", "", { outfit: snapshotOutfit(...) })`.
- [ ] **Step 3: Actualizar la foto.** Al cambiar o quitar una prenda (selección manual, chip `remove` o chip `swap`), se actualiza la foto del mensaje abierto (`indiceOutfitAbierto`), o la de `ultimoIndiceOutfit(chat)` si no hay uno abierto. No se crea un mensaje nuevo, y el texto que hoy se agrega al cambiar se mantiene.
- [ ] **Step 4: Verificar.** `npm test && npm run build`. Pendiente manual: en celular, pedir un outfit, tocar el mensaje y ver que se abre la hoja; recargar la página y ver que el chat restaura las fotos.
- [ ] **Step 5: Commit:** `feat(chat): mensajes de outfit tipo foto con hora`

---

### Task 4: Escritorio — pop up del maniquí, sin botón ni panel lateral

**Files:** Create `frontend/src/hooks/useEsEscritorio.js`, `frontend/src/components/chat/MannequinModal.jsx`, `MannequinModal.css`. Modify `frontend/src/pages/Asistente.jsx` (botón ~793-808, `outfit-panel` ~1065-1125, `modo`), `Asistente.css`.

**Interfaces:**
- Consumes: `modalAbierto` y `abrirOutfitDeMensaje` (Task 3); `handleSwap`, `swapPrendas`, `handleSeleccionarPrenda`, el selector de calendario y `handleGuardarCalendario` (existentes).
- Produces:
  - `useEsEscritorio() -> boolean`, con `matchMedia("(min-width: 901px)")` y su listener de `change`.
  - `<MannequinModal abierto onClose outfit outfitGuardado onPedirCambio(tipo) swap={{ tipo, prendas, loading, onElegir, onVolver }} calendario={{ abierto, onAbrir, onVolver, ...props del selector actual }} />`, con pasos internos `"maniqui" | "cambiar" | "calendario"`.

- [ ] **Step 1: Escritorio sin modo Probador.** Si `useEsEscritorio()` es true, no se renderizan el botón chat↔maniquí ni el panel lateral del maniquí, y se fuerza `modo = "chat"`. En celular todo queda como hoy.
- [ ] **Step 2: Pop up.**
  - Usa `AnimatePresence` + `TRANS.popup`, con fondo oscurecido.
  - Se cierra con ✕, con Escape o tocando fuera; Escape cierra primero el paso interno.
  - Paso "maniquí": `VirtualMannequin` con confirmación (Task 5) y el botón "Guardar en calendario".
  - Paso "cambiar": la lista actual de prendas para cambiar, con "← Volver"; al elegir una vuelve al maniquí y el pop up sigue abierto.
  - Paso "calendario": el selector actual, con "← Volver"; al confirmar vuelve al maniquí.
  - Foco: al abrir va al pop up; al cerrar vuelve al mensaje.
- [ ] **Step 3: Chip "Cambiar X" en escritorio.** Abre el pop up directamente en el paso "cambiar", sin confirmación.
- [ ] **Step 4: Cruce de 900 px.** Al pasar de escritorio a celular se cierra el pop up; al pasar de celular a escritorio se colapsa la hoja y `modo` vuelve a "chat". El outfit actual se conserva.
- [ ] **Step 5: Verificar.** `npm test && npm run build`. Pendiente manual (Review Focus 5): con el pop up abierto, achicar la ventana por debajo de 900 px y volver a agrandarla; el outfit sigue ahí.
- [ ] **Step 6: Commit:** `feat(chat): maniquí en pop up en escritorio`

---

### Task 5: Confirmación por prenda en el maniquí

**Files:** Modify `frontend/src/components/VirtualMannequin.jsx`, `VirtualMannequin.css`.

**Interfaces:**
- Consumes: las props actuales de `VirtualMannequin` (`outfit`, `onSwap`, etc.).
- Produces: una prop nueva, `confirmarCambio: boolean = true`.
  - Las tres zonas que hoy llaman a `onSwap(tipo)` (la prenda en el maniquí, el accesorio lateral y el chip de prenda) pasan a ser `<button type="button">`.
  - Con `confirmarCambio`, al tocarlas aparece una confirmación pequeña, animada con Motion, con el texto `¿Cambiar <etiqueta en minúscula>?` y los botones **Cambiar** / **Cancelar**. Solo "Cambiar" llama a `onSwap(tipo)`, y no aparece más de una confirmación a la vez.
  - Con `confirmarCambio={false}`, se comporta como hoy.

- [ ] **Step 1:** Implementar. Si alguna variante del maniquí no debe confirmar (solo chips o calendario), pasarle `confirmarCambio={false}`; revisar todos los usos con `grep -n "<VirtualMannequin" src`.
- [ ] **Step 2: Verificar.** `npm run build`. Pendiente manual: tocar una prenda muestra la confirmación, "Cancelar" no cambia nada y "Cambiar" abre el selector, tanto en celular como en el pop up.
- [ ] **Step 3: Commit:** `feat(maniqui): confirmar antes de cambiar una prenda`

---

### Task 6: Sincronizar con iOS y Android

- [ ] **Step 1:** `cd frontend && npm run build && npx cap sync ios && npx cap sync android`. Los dos deben terminar con "Sync finished".
- [ ] **Step 2:** Commitear solo los archivos versionados que cambie el sync y que no estuvieran ya modificados antes. Si no hay ninguno, no se hace commit.
- [ ] **Step 3:** Pedirle al usuario el OK para el push del frontend (Vercel). Este plan no toca el backend.
