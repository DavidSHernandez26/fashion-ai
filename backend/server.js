import express from "express";
import multer from "multer";
import cors from "cors";
import dotenv from "dotenv";
import OpenAI from "openai";
import fs from "fs";
import fetch from "node-fetch";
import FormData from "form-data";
import sharp from "sharp";
import { createClient } from "@supabase/supabase-js";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const upload = multer({ dest: "uploads/" });

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
);

const MODEL = "gpt-5.4-mini";

/* ───────────────────────────────
   🧠 PARSE JSON IA (ROBUSTO)
─────────────────────────────── */
function safeParseJSON(content) {
  try {
    const text = Array.isArray(content)
      ? content.map((c) => c.text || "").join("")
      : content;
    const jsonStr = text.slice(text.indexOf("{"), text.lastIndexOf("}") + 1);
    return JSON.parse(jsonStr);
  } catch {
    return null;
  }
}

/* ───────────────────────────────
   📥 DESCARGAR IMAGEN DESDE URL
─────────────────────────────── */
async function descargarImagen(url) {
  try {
    console.log("📥 Descargando imagen:", url);
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const buffer = Buffer.from(await res.arrayBuffer());
    console.log("📥 Buffer size:", buffer.length, "bytes");
    return buffer;
  } catch (err) {
    console.error("⚠️ Error descargando imagen:", err.message);
    return null;
  }
}

/* ───────────────────────────────
   🧼 REMOVE BACKGROUND
─────────────────────────────── */
async function removeBackground(imageBuffer) {
  try {
    console.log("🧼 Enviando a remove.bg...");
    const formData = new FormData();
    formData.append("image_file", imageBuffer, {
      filename: "prenda.png",
      contentType: "image/png",
    });
    formData.append("size", "auto");

    const res = await fetch("https://api.remove.bg/v1.0/removebg", {
      method: "POST",
      headers: {
        "X-Api-Key": process.env.REMOVEBG_API_KEY,
        ...formData.getHeaders(),
      },
      body: formData,
    });

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt);
    }

    const buffer = Buffer.from(await res.arrayBuffer());
    console.log("🧼 remove.bg OK, size:", buffer.length);
    return buffer;
  } catch (err) {
    console.error("⚠️ remove.bg falló:", err.message);
    return null;
  }
}

/* ───────────────────────────────
   📸 SUBIR PRENDA / OUTFIT
─────────────────────────────── */
app.post("/api/subir-prenda", upload.single("imagen"), async (req, res) => {
  try {
    const { usuario_id, genero = "unisex", tipo = "prenda", imagen_url } = req.body;

    if (!usuario_id) return res.status(400).json({ error: "Falta usuario_id" });
    if (!req.file && !imagen_url) return res.status(400).json({ error: "No se envió imagen" });

    let imagenOriginalUrl = imagen_url;
    let imagenOriginalBuffer = null;

    if (req.file) {
      const ext = req.file.originalname.split(".").pop();
      const fileName = `${usuario_id}_${Date.now()}.${ext}`;
      imagenOriginalBuffer = fs.readFileSync(req.file.path);

      const { error: uploadError } = await supabase.storage
        .from("prendas")
        .upload(fileName, imagenOriginalBuffer, { contentType: req.file.mimetype });

      fs.unlinkSync(req.file.path);
      if (uploadError) throw uploadError;

      imagenOriginalUrl = supabase.storage
        .from("prendas")
        .getPublicUrl(fileName).data.publicUrl;

      console.log("📤 Archivo subido:", imagenOriginalUrl);
    }

    if (!imagenOriginalBuffer) {
      imagenOriginalBuffer = await descargarImagen(imagenOriginalUrl);
      if (!imagenOriginalBuffer) throw new Error("No se pudo descargar la imagen");
    }

    imagenOriginalBuffer = await sharp(imagenOriginalBuffer).rotate().toBuffer();

    /* ════════════════════════════════════════
       🟢 FLUJO A: PRENDA INDIVIDUAL
    ════════════════════════════════════════ */
    if (tipo === "prenda") {
      console.log("👕 Modo: prenda individual");

      const sinFondo = await removeBackground(imagenOriginalBuffer);
      const bufferFinal = sinFondo || imagenOriginalBuffer;

      const ai = await openai.chat.completions.create({
        model: MODEL,
        messages: [
          {
            role: "user",
            content: [
              {
                type: "text",
                text: `Eres un experto en moda y retail con visión detallada.
Analiza esta prenda con mucho cuidado y devuelve SOLO este JSON:
{
  "nombre": "tenis",
  "color": "café/marrón",
  "tipo": "calzado"
}

Reglas estrictas:
- Para el color: sé muy específico y usa el nombre exacto del color que ves (café, marrón, beige, crema, burdeos, mostaza, camel, terracota, etc). NO uses colores genéricos si puedes ser más preciso.
- Si hay varios colores menciona el principal: "café con blanco".
- Para el nombre: usa el término correcto de la prenda (tenis, botines, mocasines, chaqueta, sudadera, hoodie, etc).
- Para el tipo: usa únicamente uno de estos valores: calzado, parte superior, parte inferior, accesorio, abrigo.`,
              },
              {
                type: "image_url",
                image_url: { url: imagenOriginalUrl, detail: "high" },
              },
            ],
          },
        ],
        temperature: 0,
        max_completion_tokens: 200,
      });

      const parsed = safeParseJSON(ai.choices[0].message.content);
      const nombre = parsed?.nombre || "prenda";
      const color = parsed?.color || "?";
      const tipoPrenda = parsed?.tipo || "?";
      const descripcion = `${nombre} (${color}) - ${tipoPrenda}`;

      console.log("👕 Detectado:", descripcion);

      const cleanName = `${usuario_id}_${Date.now()}_${nombre.replace(/\s/g, "_")}.png`;
      const { error: cleanError } = await supabase.storage
        .from("prendas")
        .upload(cleanName, bufferFinal, { contentType: "image/png" });

      const imagenFinalUrl = cleanError
        ? imagenOriginalUrl
        : supabase.storage.from("prendas").getPublicUrl(cleanName).data.publicUrl;

      await supabase.from("prendas").insert([{
        usuario_id,
        tipo: "prenda",
        genero,
        imagen_url: imagenFinalUrl,
        descripcion,
        metadata_ia: parsed || {},
        created_at: new Date().toISOString(),
      }]);

      return res.json({ mensaje: "✅ Prenda guardada sin fondo" });
    }

    /* ════════════════════════════════════════
       🟣 FLUJO B: OUTFIT COMPLETO
    ════════════════════════════════════════ */
    if (tipo === "outfit") {
      console.log("🧥 Modo: outfit completo");

      const ai = await openai.chat.completions.create({
        model: MODEL,
        messages: [
          {
            role: "user",
            content: [
              {
                type: "text",
                text: `Eres un experto en moda y retail con visión detallada.
Analiza este outfit con mucho cuidado y devuelve SOLO este JSON:
{
  "prendas": [
    { "nombre": "camiseta", "color": "blanco", "tipo": "parte superior" },
    { "nombre": "pantalón cargo", "color": "verde oliva", "tipo": "parte inferior" }
  ],
  "descripcion_outfit": "Outfit casual con camiseta blanca y pantalón cargo verde oliva"
}

Reglas estrictas:
- Para el color: sé muy específico (café, marrón, beige, crema, burdeos, mostaza, camel, terracota, verde oliva, etc). NO uses colores genéricos.
- Si hay varios colores menciona el principal: "café con blanco".
- Para el nombre: usa el término correcto (tenis, botines, chaqueta, sudadera, hoodie, etc).
- Para el tipo: usa únicamente: calzado, parte superior, parte inferior, accesorio, abrigo.
- Incluye TODAS las prendas y accesorios visibles.`,
              },
              {
                type: "image_url",
                image_url: { url: imagenOriginalUrl, detail: "high" },
              },
            ],
          },
        ],
        temperature: 0,
        max_completion_tokens: 800,
      });

      const respuestaIA = ai.choices[0].message.content;
      console.log("🧠 Respuesta IA:", respuestaIA);

      const parsed = safeParseJSON(respuestaIA);
      const prendasDetectadas = parsed?.prendas || [];
      const descripcionOutfit = parsed?.descripcion_outfit || "Outfit completo";

      console.log("👕 Prendas detectadas:", prendasDetectadas.length);

      await supabase.from("prendas").insert([{
        usuario_id,
        tipo: "outfit",
        genero,
        imagen_url: imagenOriginalUrl,
        descripcion: descripcionOutfit,
        metadata_ia: { prendas: prendasDetectadas },
        created_at: new Date().toISOString(),
      }]);

      return res.json({
        mensaje: `✅ Outfit guardado con ${prendasDetectadas.length} prenda(s) detectadas`,
      });
    }

    res.status(400).json({ error: "Tipo inválido, usa 'prenda' o 'outfit'" });

  } catch (err) {
    console.error("🔥 subir-prenda:", err.message);
    res.status(500).json({ error: err.message });
  }
});

/* ───────────────────────────────
   📋 OBTENER PRENDAS
─────────────────────────────── */
app.get("/api/prendas", async (req, res) => {
  try {
    const { usuario_id, tipo } = req.query;

    if (!usuario_id) return res.status(400).json({ error: "Falta usuario_id" });

    let query = supabase
      .from("prendas")
      .select("*")
      .eq("usuario_id", usuario_id)
      .order("created_at", { ascending: false });

    if (tipo && tipo !== "todos") query = query.eq("tipo", tipo);

    const { data, error } = await query;
    if (error) throw error;

    res.json(data || []);
  } catch (err) {
    console.error("🔥 get prendas:", err.message);
    res.status(500).json({ error: err.message });
  }
});

/* ───────────────────────────────
   ❌ ELIMINAR PRENDA
─────────────────────────────── */
app.delete("/api/prendas/:id", async (req, res) => {
  try {
    const { id } = req.params;
    const { error } = await supabase.from("prendas").delete().eq("id", id);
    if (error) throw error;
    res.json({ mensaje: "🗑️ Eliminado" });
  } catch (err) {
    console.error("🔥 delete:", err.message);
    res.status(500).json({ error: err.message });
  }
});

/* ───────────────────────────────
   👗 FASHION IA
─────────────────────────────── */
app.post("/api/fashion", async (req, res) => {
  try {
    const { usuario_id, mensaje, historial = [], outfit_ids_anteriores = [] } = req.body;

    if (!usuario_id || !mensaje) return res.status(400).json({ error: "Faltan datos" });

    const { data: prendas, error } = await supabase
      .from("prendas")
      .select("id, descripcion, imagen_url, tipo, metadata_ia")
      .eq("usuario_id", usuario_id);

    if (error) throw error;

    if (!prendas || prendas.length === 0) {
      return res.json({
        respuesta: "No tienes prendas registradas aún. ¡Sube algunas fotos de tu closet!",
        outfit: [],
        outfit_guardado: null,
      });
    }

    const prendasSueltas = prendas.filter((p) => p.tipo === "prenda");
    const outfitsGuardados = prendas.filter((p) => p.tipo === "outfit");

    const contextoPrendas = prendasSueltas.length > 0
      ? "PRENDAS SUELTAS DISPONIBLES:\n" +
        prendasSueltas.map((p) => `[ID:${p.id}] ${p.tipo?.toUpperCase()}: ${p.descripcion}`).join("\n")
      : "No hay prendas sueltas.";

    const contextoOutfits = outfitsGuardados.length > 0
      ? "\n\nOUTFITS GUARDADOS (puedes recomendarlos por su ID, o usarlos como referencia de estilo):\n" +
        outfitsGuardados.map((p) => {
          const lista = p.metadata_ia?.prendas?.map((x) => `${x.nombre} (${x.color})`).join(", ") || "";
          return `[ID:${p.id}] OUTFIT: ${p.descripcion}${lista ? ` — contiene: ${lista}` : ""}`;
        }).join("\n")
      : "";

    const prendasActuales = prendasSueltas.filter((p) =>
      outfit_ids_anteriores.includes(p.id)
    );
    const contextoActual = prendasActuales.length > 0
      ? "\n\nOUTFIT ACTUAL EN EL MANIQUÍ:\n" +
        prendasActuales.map((p) => `[ID:${p.id}] ${p.descripcion}`).join("\n")
      : "";

    const historialTexto = historial.length > 0
      ? "\n\nHISTORIAL DE CONVERSACIÓN:\n" +
        historial
          .map((h) => `${h.role === "user" ? "Usuario" : "Asistente"}: ${h.text}`)
          .join("\n")
      : "";

    const ai = await openai.chat.completions.create({
      model: MODEL,
      messages: [
        {
          role: "system",
          content: `Eres un estilista personal experto. Armas outfits con las prendas del closet del usuario.

REGLAS ESTRICTAS:
1. Si el usuario pide prendas sueltas o un outfit armado por ti, usa SOLO IDs de PRENDAS SUELTAS en outfit_ids. Máximo 1 parte superior, 1 parte inferior, 1 calzado, 1-2 accesorios.
2. Si el usuario pide un OUTFIT GUARDADO específico (ej: "muéstrame el outfit casual", "dame ese look que subí"), usa el ID del outfit guardado en outfit_ids.
3. Si el usuario dice "sin X prenda", NUNCA la incluyas. Regla absoluta.
4. Si el usuario pide COMPLEMENTAR el outfit actual del maniquí, mantén las prendas actuales y agrega solo lo pedido.
5. Si el usuario pide algo NUEVO, propón combinaciones completamente distintas.
6. Mantén el hilo de la conversación.
7. Explica brevemente por qué combinan las prendas.
8. Responde en español con calidez y personalidad.
9. Devuelve SOLO este JSON:
{"respuesta":"explicación","outfit_ids":[id1,id2]}

REGLA DE ORO: outfit_ids puede tener IDs de prendas sueltas O un solo ID de outfit guardado, nunca ambos mezclados.`,
        },
        {
          role: "user",
          content: `${contextoPrendas}${contextoOutfits}${contextoActual}${historialTexto}\n\nMensaje del usuario: ${mensaje}`,
        },
      ],
      max_completion_tokens: 600,
      temperature: 0.75,
    });

    const parsed = safeParseJSON(ai.choices[0].message.content);

    if (!parsed) {
      const fallback = [...prendasSueltas].sort(() => Math.random() - 0.5).slice(0, 3);
      return res.json({
        respuesta: "Te armé una combinación con lo que tienes disponible.",
        outfit: fallback,
        outfit_guardado: null,
      });
    }

    /* ── Verificar si recomienda un outfit guardado ── */
    const outfitGuardadoRecomendado = outfitsGuardados.find((p) =>
      parsed.outfit_ids?.includes(p.id)
    );

    if (outfitGuardadoRecomendado) {
      return res.json({
        respuesta: parsed.respuesta || "Aquí tienes el outfit",
        outfit: [],
        outfit_guardado: outfitGuardadoRecomendado,
      });
    }

    /* ── Prendas sueltas en maniquí ── */
    const outfit = prendasSueltas.filter((p) => parsed.outfit_ids?.includes(p.id));
    const fallback = [...prendasSueltas].sort(() => Math.random() - 0.5).slice(0, 3);

    res.json({
      respuesta: parsed.respuesta || "Aquí tienes un outfit",
      outfit: outfit.length ? outfit : fallback,
      outfit_guardado: null,
    });

  } catch (err) {
    console.error("🔥 fashion:", err.message);
    res.status(500).json({ respuesta: "Error generando outfit", outfit: [], outfit_guardado: null });
  }
});

/* ───────────────────────────────
   🚀 START
─────────────────────────────── */
const PORT = process.env.PORT || 5001;
app.listen(PORT, () => {
  console.log(`🚀 Backend corriendo en http://localhost:${PORT}`);
});