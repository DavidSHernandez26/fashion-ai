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

    /* ── Si viene archivo, subirlo a Supabase ── */
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

    /* ── Descargar imagen si vino como URL ── */
    if (!imagenOriginalBuffer) {
      imagenOriginalBuffer = await descargarImagen(imagenOriginalUrl);
      if (!imagenOriginalBuffer) throw new Error("No se pudo descargar la imagen");
    }

    /* ── Corregir rotación EXIF ── */
    imagenOriginalBuffer = await sharp(imagenOriginalBuffer).rotate().toBuffer();

    /* ════════════════════════════════════════
       🟢 FLUJO A: PRENDA INDIVIDUAL
       remove.bg directo → guardar sin fondo
    ════════════════════════════════════════ */
    if (tipo === "prenda") {
      console.log("👕 Modo: prenda individual");

      const sinFondo = await removeBackground(imagenOriginalBuffer);
      const bufferFinal = sinFondo || imagenOriginalBuffer;

      /* ── Detectar nombre y color con IA ── */
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

      /* ── Subir imagen sin fondo ── */
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
       Guardar foto tal como está + analizar
       prendas para recomendaciones
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
    const { usuario_id, mensaje } = req.body;

    if (!usuario_id || !mensaje) return res.status(400).json({ error: "Faltan datos" });

    const { data: prendas, error } = await supabase
      .from("prendas")
      .select("id, descripcion, imagen_url, tipo, metadata_ia")
      .eq("usuario_id", usuario_id);

    if (error) throw error;

    if (!prendas || prendas.length === 0) {
      return res.json({ respuesta: "No tienes prendas registradas.", outfit: [] });
    }

    const contexto = prendas.map((p) => {
      if (p.tipo === "outfit" && p.metadata_ia?.prendas) {
        const lista = p.metadata_ia.prendas
          .map((x) => `${x.nombre} (${x.color})`)
          .join(", ");
        return `(${p.id}) Outfit: ${p.descripcion} — contiene: ${lista}`;
      }
      return `(${p.id}) ${p.descripcion}`;
    }).join("\n");

    const ai = await openai.chat.completions.create({
      model: MODEL,
      messages: [
        {
          role: "system",
          content: 'Eres un asistente de moda. Devuelve SOLO JSON {"respuesta":"","outfit_ids":[id,id]}',
        },
        {
          role: "user",
          content: `Estas son las prendas y outfits disponibles:\n${contexto}\n\n${mensaje}`,
        },
      ],
      max_completion_tokens: 500,
    });

    const parsed = safeParseJSON(ai.choices[0].message.content);

    if (!parsed) {
      return res.json({ respuesta: "Te armé un outfit con lo disponible.", outfit: prendas.slice(0, 4) });
    }

    const outfit = prendas.filter((p) => parsed.outfit_ids?.includes(p.id));

    res.json({
      respuesta: parsed.respuesta || "Aquí tienes un outfit",
      outfit: outfit.length ? outfit : prendas.slice(0, 4),
    });
  } catch (err) {
    console.error("🔥 fashion:", err.message);
    res.status(500).json({ respuesta: "Error generando outfit", outfit: [] });
  }
});

/* ───────────────────────────────
   🚀 START
─────────────────────────────── */
const PORT = process.env.PORT || 5001;
app.listen(PORT, () => {
  console.log(`🚀 Backend corriendo en http://localhost:${PORT}`);
});