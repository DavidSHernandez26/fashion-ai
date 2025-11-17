import express from "express";
import multer from "multer";
import cors from "cors";
import dotenv from "dotenv";
import OpenAI from "openai";
import fs from "fs";
import fetch from "node-fetch";
import FormData from "form-data";
import { createClient } from "@supabase/supabase-js";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

// 📂 Subida temporal
const upload = multer({ dest: "uploads/" });

// ⚙️ Configuración de OpenAI y Supabase
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);

// ───────────────────────────────
// 🧼 FUNCIÓN remove.bg (corregida)
// ───────────────────────────────
async function removeBackground(imageUrl) {
  try {
    const formData = new FormData();
    formData.append("image_url", imageUrl);
    formData.append("size", "auto");

    const headers = {
      "X-Api-Key": process.env.REMOVEBG_API_KEY,
      ...formData.getHeaders(),
    };

    const res = await fetch("https://api.remove.bg/v1.0/removebg", {
      method: "POST",
      headers,
      body: formData,
    });

    if (!res.ok) {
      const errTxt = await res.text();
      throw new Error(`Remove.bg error ${res.status}: ${errTxt}`);
    }

    // ✅ CORREGIDO: leer como binario, no texto
    const arrayBuffer = await res.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    return buffer;
  } catch (err) {
    console.error("❌ Error en removeBackground:", err.message);
    throw err;
  }
}

// ───────────────────────────────
// 📸 SUBIR Y ANALIZAR PRENDA
// ───────────────────────────────
app.post("/api/subir-prenda", upload.single("imagen"), async (req, res) => {
  try {
    const { usuario_id, genero = "unisex", tipo = "prenda", imagen_url } = req.body;
    if (!usuario_id) return res.status(400).json({ error: "Falta usuario_id" });

    let imagenUrl = imagen_url || null;

    // 🖼️ Subir a Supabase si viene un archivo
    if (req.file) {
      const tempPath = req.file.path;
      const ext = req.file.originalname.split(".").pop();
      const fileName = `${usuario_id}_${Date.now()}.${ext}`;
      const fileBuffer = fs.readFileSync(tempPath);

      const { error: uploadError } = await supabase.storage
        .from("prendas")
        .upload(fileName, fileBuffer, {
          contentType: req.file.mimetype,
          cacheControl: "3600",
          upsert: false,
        });

      fs.unlinkSync(tempPath);
      if (uploadError) throw uploadError;

      const { data: publicData } = supabase.storage.from("prendas").getPublicUrl(fileName);
      imagenUrl = publicData?.publicUrl;
    }

    if (!imagenUrl) {
      return res.status(400).json({ error: "No se recibió imagen ni imagen_url." });
    }

    console.log("🧼 Quitando fondo de:", imagenUrl);
    const cleanBuffer = await removeBackground(imagenUrl);

    // 📤 Subir imagen sin fondo
    const cleanName = `${usuario_id}_${Date.now()}_clean.png`;
    const { error: cleanUploadError } = await supabase.storage
      .from("prendas")
      .upload(cleanName, cleanBuffer, {
        contentType: "image/png",
        cacheControl: "3600",
        upsert: false,
      });

    if (cleanUploadError) throw cleanUploadError;
    const { data: cleanData } = supabase.storage.from("prendas").getPublicUrl(cleanName);
    const cleanImageUrl = cleanData?.publicUrl;
    console.log("✅ Imagen limpia subida:", cleanImageUrl);

    // 🔍 Análisis IA
    const prompt = `Devuelve JSON {"prendas":[{"nombre":"","color":"","tipo":""}]} según la imagen.`;
    const aiResponse = await openai.chat.completions.create({
      model: process.env.OPENAI_MODEL || "gpt-4o-mini",
      messages: [
        {
          role: "user",
          content: [
            { type: "text", text: prompt },
            { type: "image_url", image_url: { url: cleanImageUrl } },
          ],
        },
      ],
      max_tokens: 300,
      temperature: 0,
    });

    const raw = aiResponse.choices?.[0]?.message?.content || "";
    let prendasDetectadas = [];

    try {
      const jsonStr = raw.slice(raw.indexOf("{"), raw.lastIndexOf("}") + 1);
      const parsed = JSON.parse(jsonStr);
      prendasDetectadas = parsed.prendas || [];
    } catch {
      console.warn("⚠️ Error parseando JSON IA:", raw);
      prendasDetectadas = [];
    }

    // 🧥 Guardar resultados
    if (prendasDetectadas.length > 1) {
      await Promise.all(
        prendasDetectadas.map(async (p) => {
          await supabase.from("prendas").insert([
            {
              usuario_id,
              tipo: "prenda",
              genero,
              imagen_url: cleanImageUrl,
              descripcion: `${p.nombre || "Prenda"} (${p.color || "desconocido"}) - ${
                p.tipo || "sin tipo"
              }`,
              metadata_ia: p,
              created_at: new Date().toISOString(),
            },
          ]);
        })
      );
      return res.json({
        mensaje: "✅ Outfit detectado, prendas guardadas individualmente.",
        prendasDetectadas,
      });
    }

    const descripcion =
      prendasDetectadas.length === 1
        ? `${prendasDetectadas[0].nombre} (${prendasDetectadas[0].color}) - ${prendasDetectadas[0].tipo}`
        : "No se detectó prenda clara.";

    const { error: dbError } = await supabase.from("prendas").insert([
      {
        usuario_id,
        tipo,
        genero,
        imagen_url: cleanImageUrl,
        descripcion,
        metadata_ia: prendasDetectadas,
        created_at: new Date().toISOString(),
      },
    ]);
    if (dbError) throw dbError;

    res.json({
      mensaje: "✅ Prenda analizada correctamente.",
      descripcion,
      prendasDetectadas,
      imagen_url: cleanImageUrl,
    });
  } catch (err) {
    console.error("🔥 Error /api/subir-prenda:", err.message);
    res.status(500).json({ error: err.message });
  }
});

// ───────────────────────────────
// 📋 OBTENER PRENDAS
// ───────────────────────────────
app.get("/api/prendas", async (req, res) => {
  try {
    const { usuario_id, tipo } = req.query;
    if (!usuario_id) return res.status(400).json({ error: "Falta usuario_id" });

    let query = supabase
      .from("prendas")
      .select("*")
      .eq("usuario_id", usuario_id)
      .order("created_at", { ascending: false });

    if (tipo && tipo !== "Todos") query = query.eq("tipo", tipo);

    const { data, error } = await query;
    if (error) throw error;

    res.json(data || []);
  } catch (err) {
    console.error("🔥 Error /api/prendas:", err.message);
    res.status(500).json({ error: err.message });
  }
});

// ───────────────────────────────
// ❌ ELIMINAR PRENDA
// ───────────────────────────────
app.delete("/api/prendas/:id", async (req, res) => {
  try {
    const { id } = req.params;
    const { data: prenda } = await supabase
      .from("prendas")
      .select("imagen_url")
      .eq("id", id)
      .single();

    if (prenda?.imagen_url) {
      const fileName = prenda.imagen_url.split("/").pop();
      await supabase.storage.from("prendas").remove([fileName]);
    }

    await supabase.from("prendas").delete().eq("id", id);
    res.json({ mensaje: "🗑️ Prenda eliminada correctamente" });
  } catch (err) {
    console.error("🔥 Error eliminando prenda:", err.message);
    res.status(500).json({ error: err.message });
  }
});

// ───────────────────────────────
// 👗 RECOMENDACIONES
// ───────────────────────────────
app.post("/api/fashion", async (req, res) => {
  try {
    const { usuario_id, mensaje } = req.body;
    if (!usuario_id || !mensaje)
      return res.status(400).json({ error: "Faltan datos." });

    const { data: prendas } = await supabase
      .from("prendas")
      .select("tipo, descripcion, genero")
      .eq("usuario_id", usuario_id);

    const contexto = (prendas || [])
      .map((p) => `• (${p.tipo || "sin tipo"}) ${p.descripcion}`)
      .join("\n");

    const chat = await openai.chat.completions.create({
      model: process.env.OPENAI_MODEL || "gpt-4o-mini",
      messages: [
        { role: "system", content: "Eres un asesor de moda profesional." },
        {
          role: "user",
          content: `Estas son las prendas del usuario:\n${contexto}\n\nPregunta: ${mensaje}`,
        },
      ],
      max_tokens: 300,
      temperature: 0.7,
    });

    res.json({ respuesta: chat.choices[0]?.message?.content || "Sin respuesta" });
  } catch (err) {
    console.error("🔥 Error /api/fashion:", err.message);
    res.status(500).json({ error: err.message });
  }
});

// ───────────────────────────────
// 🚀 INICIAR SERVIDOR
// ───────────────────────────────
const PORT = process.env.PORT || 5001;
app.listen(PORT, () =>
  console.log(`🚀 Backend corriendo en http://localhost:${PORT}`)
);
