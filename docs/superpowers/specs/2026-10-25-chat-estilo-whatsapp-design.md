# Chat estilo WhatsApp con animaciones fluidas — diseño

Fecha: 2026-10-25 · Proyecto: Be Confident · Maquetas aprobadas: `.superpowers/brainstorm/84713-1792896363/content/chat-b-mac.html` (opción B)

## Intención y por qué

El usuario quiere que hablar con el Asistente **se sienta como hablar por WhatsApp con una estilista que te recomienda un outfit**: un chat con ritmo humano, animaciones fluidas y nada recargado. Hoy el chat mezcla animaciones de Motion (`framer-motion`) con varias animaciones CSS sueltas (`messageIn`, `dotBounce`, `cursorBlink`, etc.), cada una con su propio tiempo, así que no se siente como un solo movimiento.

## Qué significa que funcione

- Al escribir, mi mensaje "sale" a la derecha con la hora y ✓✓. La cabecera cambia de "en línea" a "escribiendo…", aparecen los tres puntitos y luego llega la respuesta.
- La respuesta de la IA llega con la etiqueta de la regla de color y el texto se va escribiendo en vivo, como hoy. Después aparece el outfit como si fuera una foto enviada y debajo las sugerencias.
- En el computador, toco el outfit y se abre el maniquí en un pop up donde puedo cambiar prendas (con confirmación) y guardarlo en el calendario.
- En el celular, ya sea en la app o en el navegador, todo sigue funcionando como hoy desde la parte de abajo.
- Nada se siente lento ni pesado: no hay tirones al hacer scroll ni al llegar el texto.

## Objetivos

- **G1. Aspecto WhatsApp (opción B)** dentro de la **ventana estilo Mac actual** (los tres puntitos y la tarjeta), con los **colores actuales** en modo oscuro y claro:
  - Oscuro: fondo `#0F0326`, acento lavanda `#C4B5E8`. Burbuja propia en degradado morado (como la maqueta `#7c5cd6 → #9b7fe0`); burbuja de la IA translúcida lavanda.
  - Claro: fondo de página verde `#84A07C`, tarjeta blanca (`rgba(255,255,255,.82)`), texto `#0F0326`. Burbuja propia morada sólida (`#5a3d9e`); burbuja de la IA blanca con borde suave.
- **G2. Burbujas tipo WhatsApp:**
  - mensajes propios a la derecha y de la IA a la izquierda, con la esquina "de cola" más cerrada;
  - hora en cada mensaje, y ✓✓ en los propios;
  - separador de día ("Hoy", "Ayer" o fecha).
- **G3. Presencia:** la cabecera muestra "en línea" con punto verde y cambia a "escribiendo…" mientras la IA responde. Dentro del chat aparecen los tres puntitos hasta que llega el primer texto.
- **G4. Mensaje de outfit como "foto enviada":** el outfit recomendado aparece como un mensaje propio de la IA con las miniaturas de las prendas y el texto "Tócalo para verlo en el maniquí". La etiqueta de la regla de color va en el mensaje de texto, igual que en la maqueta.
- **G5. Animaciones unificadas con Motion:**
  - entrada de mensajes con un pequeño "salto" (spring corto);
  - puntitos de "escribiendo…";
  - aparición de las sugerencias;
  - apertura y cierre del pop up.
  Todo debe compartir los mismos tiempos y curvas. Las animaciones CSS sueltas del chat que hagan lo mismo se reemplazan, para que no se dupliquen.
- **G6. Escritorio (pantalla ancha) — maniquí en pop up:**
  - Se **quitan** el botón chat↔maniquí y el **maniquí del panel lateral**. El chat ocupa todo el ancho de la ventana.
  - Tocar el mensaje del outfit abre un **pop up** con el maniquí (`VirtualMannequin`).
  - Dentro del pop up:
    - **cada prenda es un botón**; al tocarla aparece una **confirmación** ("¿Cambiar la chaqueta?"), y solo si se confirma se abre la elección de otra prenda (el flujo de cambio actual);
    - un botón para **guardar en el calendario** (el flujo actual de elegir fecha y confirmar).
  - El pop up se cierra con ✕, con Escape o tocando fuera, y nunca pierde el outfit.
- **G7. Celular (pantalla angosta, sea app iOS/Android o navegador):** el comportamiento actual se mantiene, viendo el outfit desde la parte de abajo (la hoja `outfit-sheet`). El celular gana el mismo estilo WhatsApp del chat (G1–G5).
- **G8. Liviano:** las animaciones solo usan `transform` y `opacity`; nada anima tamaños ni sombras en bucle. Se respeta "reducir movimiento" del sistema: con esa opción activa, las animaciones se vuelven fundidos breves o desaparecen.

## No-objetivos

- Cambiar otras pantallas (Closet, Feed, Calendario…). Este diseño es solo para el chat del Asistente.
- Sonidos o vibraciones nuevas.
- Cambiar la lógica de la IA, los endpoints o el formato de las respuestas.
- Una librería nueva: se usa Motion (`framer-motion`, ya instalada).
- Rediseñar el maniquí (`VirtualMannequin`) por dentro, más allá de lo necesario para el botón y la confirmación por prenda.

## Anti-objetivos (fallaría aunque "funcione")

- Que se sienta pesado: tirones al hacer scroll, al escribir o mientras llega el texto en vivo, o animaciones largas que hagan esperar.
- Cambiar una prenda por un toque accidental, sin confirmación.
- Perder el outfit o el historial del chat al abrir o cerrar el pop up, o al cambiar el tamaño de la ventana.
- Romper el modo claro, o que el texto quede ilegible en alguno de los dos modos.
- Que en el celular deje de funcionar la forma actual de ver el outfit.

## Restricciones

- React 19 + Vite + Capacitor 8. Archivos principales: `frontend/src/pages/Asistente.jsx` (unas 1340 líneas), `Asistente.css` (unas 2060 líneas) y `frontend/src/components/VirtualMannequin.jsx`.
- **Corte entre celular y escritorio: el breakpoint actual de 900 px** (`@media (max-width: 900px)` en `Asistente.css`). Hasta 900 px es la versión celular; por encima, la de escritorio. Decisión mía: reutiliza el corte que ya existe.
- Reglas de autenticación del frontend que no se tocan: `usuarioId` desde caché, early return en `INITIAL_SESSION`, nunca `getSession()` ni doble listener.
- Se mantienen el streaming de la respuesta (efecto máquina de escribir), los chips de sugerencias y sus acciones (`remove`, `swap`, `chat`) y la etiqueta de regla de color que ya viene del backend.
- El frontend se commitea dentro de `frontend/` (su propio repo); al final se hace `npx cap sync ios` y `npx cap sync android`.

## Lo que ya decidimos sobre el cómo

- Librería: **Motion** (decisión del usuario).
- Estilo: **opción B** (WhatsApp con los colores de Be Confident) dentro de la ventana Mac, en oscuro y claro (decisión del usuario).
- Celular igual que la app; escritorio con pop up (decisión del usuario).
- En escritorio se quitan el botón chat↔maniquí y el maniquí lateral (decisión del usuario).
- En el pop up: cada prenda es un botón y cambiarla pide confirmación, y se puede guardar en el calendario (decisión del usuario).

Decisiones mías:
1. **La confirmación por prenda también se aplica en el celular**, donde hoy se cambian prendas desde el maniquí. Es la misma protección contra toques accidentales y se reutiliza el mismo componente.
2. **El pop up de escritorio no trae "Generar otro outfit"**: para eso está el chat ("dame otro"). El modo "Probador" con ocasiones sigue existiendo en el celular, como hoy.
3. **La hora del mensaje** es la hora local en que se envió o recibió. Los mensajes guardados de antes, que no tienen hora, se muestran sin hora.
4. **✓✓** se muestra fijo en los mensajes propios, como adorno de estilo; no indica "leído" de verdad.
5. Las animaciones duran entre **150 y 400 ms**, con un spring corto para la entrada de mensajes.

Decisiones mías tras la revisión del diseño:

6. **Cada mensaje de outfit guarda su propia "foto".** El mensaje del chat guarda una copia del outfit (ids más los datos mínimos de cada prenda, o el outfit guardado), igual que una foto enviada por WhatsApp que no cambia sola. El esquema de mensajes pasa a `{ role, text, ts?, outfit? }` y se persiste igual que hoy (límite de 100 mensajes).
   - **Al tocar un mensaje de outfit**, ese outfit pasa a ser el actual y se abre: el pop up en escritorio, la hoja expandida en celular.
   - **Si se cambia o quita una prenda** desde el pop up, la hoja o un chip, se actualiza el outfit actual y la copia del mensaje que se abrió (o, para los chips, la del último mensaje de outfit). No se crea un mensaje nuevo; el texto que ya se agrega hoy al hacer un cambio se mantiene.
   - Los mensajes viejos, guardados antes de este cambio, no tienen outfit y se muestran solo como texto.
7. **El mensaje de outfit aparece también en el celular**, para que el chat se vea igual en todas partes. En celular, tocarlo abre la hoja de abajo expandida. Se agrega al chat cuando llega una respuesta con `cambiar_panel` en true y un outfit, justo después del texto de la IA.
8. **Celular (≤ 900 px):** se mantienen el modo Probador (`modo`), sus ocasiones y su botón chat↔maniquí. **Escritorio (> 900 px):** no hay modo Probador ni botón; el chat queda fijo en modo chat.
   - **Si la ventana cruza los 900 px**, el pop up se cierra o la hoja se colapsa y el outfit actual se conserva.
   - Si estabas en modo Probador y la ventana pasa a escritorio, vuelve a modo chat.
9. **Dentro del pop up**, el selector para cambiar prenda **reemplaza la vista del maniquí** (un segundo paso con botón "← Volver"), y lo mismo pasa con el selector de fecha del calendario.
   - Después de confirmar un cambio o de guardar, se vuelve a la vista del maniquí y el pop up **sigue abierto**.
   - Escape o ✕ cierran primero el paso interno y luego el pop up. Tocar fuera cierra el pop up.
10. **La confirmación vive dentro de `VirtualMannequin`**, con una prop (por ejemplo `confirmarCambio`), para que las tres zonas tocables la tengan: la prenda en el maniquí, el accesorio lateral y el chip de prenda. Esas zonas pasan a ser `<button>` reales, que también funcionan con teclado. No debe haber doble confirmación: la variante de solo chips o de calendario no la repite.
11. **El chip de sugerencia "Cambiar X" no pide confirmación**, porque ya es un toque explícito. En escritorio abre el pop up directamente en el paso de elegir prenda; en celular, el flujo actual.
12. **Hora:** se guarda `ts` en milisegundos y se muestra con la hora local del dispositivo (`toLocaleTimeString` con hora y minutos). El separador de día ("Hoy", "Ayer" o fecha) solo agrupa mensajes con `ts`; los viejos, sin hora, van arriba sin separador.

## Lo que queda a criterio del implementador

- Si conviene separar en componentes nuevos (por ejemplo `ChatBubble`, `TypingIndicator`, `OutfitMessage`, `MannequinModal`, `ConfirmSwap`) para que `Asistente.jsx` no crezca. Se recomienda hacerlo.
- Los valores exactos del spring y la curva de aceleración, dentro del rango de 150–400 ms.
- Qué animaciones CSS existentes se eliminan por duplicadas.
- Cómo se ve la confirmación: un diálogo pequeño, o una tarjeta que aparece sobre la prenda con "Cambiar / Cancelar".
