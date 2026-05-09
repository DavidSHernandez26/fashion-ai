from pathlib import Path


OUT = Path("diagrams/section4_professional")
OUT.mkdir(parents=True, exist_ok=True)

PALETTE = {
    "bg": "#f8fafc",
    "panel": "#ffffff",
    "ink": "#111827",
    "muted": "#475569",
    "line": "#334155",
    "blue": "#2563eb",
    "blue_fill": "#dbeafe",
    "cyan": "#0891b2",
    "cyan_fill": "#ecfeff",
    "green": "#16a34a",
    "green_fill": "#f0fdf4",
    "violet": "#4f46e5",
    "violet_fill": "#eef2ff",
    "orange": "#ea580c",
    "orange_fill": "#fff7ed",
    "slate": "#cbd5e1",
}


def svg_start(width, height, title):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <style>
      .title{{font:700 30px Arial,sans-serif;fill:{PALETTE["ink"]}}}
      .subtitle{{font:14px Arial,sans-serif;fill:{PALETTE["muted"]}}}
      .h{{font:700 17px Arial,sans-serif;fill:{PALETTE["ink"]}}}
      .t{{font:14px Arial,sans-serif;fill:{PALETTE["ink"]}}}
      .s{{font:13px Arial,sans-serif;fill:{PALETTE["muted"]}}}
      .bg{{fill:{PALETTE["bg"]};stroke:{PALETTE["slate"]};stroke-width:1.5;rx:22}}
      .pkg{{fill:{PALETTE["panel"]};stroke:{PALETTE["slate"]};stroke-width:2;rx:18}}
      .class{{fill:{PALETTE["panel"]};stroke:{PALETTE["blue"]};stroke-width:2;rx:10}}
      .classHead{{fill:{PALETTE["blue_fill"]};stroke:{PALETTE["blue"]};stroke-width:2}}
      .front{{fill:{PALETTE["cyan_fill"]};stroke:{PALETTE["cyan"]};stroke-width:2;rx:10}}
      .back{{fill:{PALETTE["green_fill"]};stroke:{PALETTE["green"]};stroke-width:2;rx:10}}
      .ext{{fill:{PALETTE["violet_fill"]};stroke:{PALETTE["violet"]};stroke-width:2;rx:12}}
      .db{{fill:{PALETTE["orange_fill"]};stroke:{PALETTE["orange"]};stroke-width:2;rx:12}}
      .act{{fill:{PALETTE["cyan_fill"]};stroke:{PALETTE["cyan"]};stroke-width:2;rx:18}}
      .decision{{fill:{PALETTE["orange_fill"]};stroke:{PALETTE["orange"]};stroke-width:2}}
      .lane{{fill:#ffffff;stroke:{PALETTE["slate"]};stroke-width:1.5;rx:12}}
      .line{{stroke:{PALETTE["line"]};stroke-width:2.1;fill:none}}
      .dash{{stroke:{PALETTE["line"]};stroke-width:2;fill:none;stroke-dasharray:8 6}}
      .actor{{stroke:{PALETTE["ink"]};stroke-width:2;fill:none}}
      .start{{fill:{PALETTE["ink"]};stroke:{PALETTE["ink"]};stroke-width:2}}
      .endOuter{{fill:#ffffff;stroke:{PALETTE["ink"]};stroke-width:2}}
      .endInner{{fill:{PALETTE["ink"]}}}
    </style>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="{PALETTE["line"]}"/>
    </marker>
  </defs>
  <rect x="25" y="25" width="{width - 50}" height="{height - 50}" class="bg"/>
  <text x="{width / 2}" y="70" text-anchor="middle" class="title">{title}</text>
'''


def svg_end():
    return "</svg>\n"


def text(x, y, value, cls="t", anchor="start"):
    return f'  <text x="{x}" y="{y}" text-anchor="{anchor}" class="{cls}">{value}</text>\n'


def rect(x, y, w, h, cls="front"):
    return f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" class="{cls}"/>\n'


def line(x1, y1, x2, y2, label=None, lx=None, ly=None, dashed=False):
    cls = "dash" if dashed else "line"
    out = f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}" marker-end="url(#arrow)"/>\n'
    if label:
        out += text(lx or (x1 + x2) / 2, ly or (y1 + y2) / 2 - 8, label, "s", "middle")
    return out


def poly(points, label=None, lx=None, ly=None, dashed=False):
    cls = "dash" if dashed else "line"
    pts = " ".join(f"{x},{y}" for x, y in points)
    out = f'  <polyline points="{pts}" class="{cls}" marker-end="url(#arrow)"/>\n'
    if label:
        out += text(lx or points[len(points) // 2][0], ly or points[len(points) // 2][1] - 8, label, "s", "middle")
    return out


def class_box(x, y, w, name, attrs):
    row_h = 24
    h = 46 + len(attrs) * row_h + 16
    out = rect(x, y, w, h, "class")
    out += f'  <rect x="{x}" y="{y}" width="{w}" height="42" class="classHead"/>\n'
    out += text(x + w / 2, y + 27, name, "h", "middle")
    for i, a in enumerate(attrs):
        out += text(x + 18, y + 70 + i * row_h, a, "t")
    return out, h


def component(x, y, w, h, name, desc="", cls="front"):
    out = rect(x, y, w, h, cls)
    out += text(x + w / 2, y + 28, name, "h", "middle")
    if desc:
        lines = desc.split("\n")
        for i, d in enumerate(lines):
            out += text(x + w / 2, y + 54 + i * 20, d, "s", "middle")
    return out


def actor(x, y, label):
    out = f'''  <circle cx="{x}" cy="{y}" r="18" class="actor"/>
  <line x1="{x}" y1="{y + 18}" x2="{x}" y2="{y + 76}" class="actor"/>
  <line x1="{x - 35}" y1="{y + 42}" x2="{x + 35}" y2="{y + 42}" class="actor"/>
  <line x1="{x}" y1="{y + 76}" x2="{x - 32}" y2="{y + 122}" class="actor"/>
  <line x1="{x}" y1="{y + 76}" x2="{x + 32}" y2="{y + 122}" class="actor"/>
'''
    out += text(x, y + 156, label, "h", "middle")
    return out


def write(name, content):
    (OUT / name).write_text(content, encoding="utf-8")


def diagram_classes():
    s = svg_start(1800, 1180, "Figura 4.1. Diagrama de clases")
    s += text(900, 98, "Modelo conceptual de las entidades principales de Be: Confident", "subtitle", "middle")
    boxes = {}
    definitions = [
        ("Usuario", 90, 160, 260, ["id: uuid", "email: string"]),
        ("Perfil", 470, 125, 320, ["id: uuid", "username: string", "nombre: string", "bio: string", "avatar_url: string", "setup_completo: boolean"]),
        ("Prenda", 930, 110, 350, ["id: uuid", "usuario_id: uuid", "tipo: prenda | outfit", "genero: string", "imagen_url: string", "descripcion: string", "metadata_ia: json"]),
        ("CalendarOutfit", 1390, 125, 320, ["id: uuid", "usuario_id: uuid", "fecha: date", "imagen_url: string", "descripcion: string", "metadata: json"]),
        ("Post", 90, 470, 320, ["id: uuid", "usuario_id: uuid", "imagen_url: string", "descripcion: string", "prendas: json", "created_at: timestamp"]),
        ("Like", 500, 470, 260, ["id: uuid", "post_id: uuid", "usuario_id: uuid"]),
        ("Comment", 830, 455, 300, ["id: uuid", "post_id: uuid", "usuario_id: uuid", "texto: string", "created_at: timestamp"]),
        ("Wishlist", 1230, 455, 320, ["id: uuid", "usuario_id: uuid", "post_id: uuid", "imagen_url: string", "descripcion: string"]),
        ("Friendship", 450, 810, 360, ["id: uuid", "requester_id: uuid", "addressee_id: uuid", "status: pending | accepted | rejected"]),
        ("Notification", 980, 790, 350, ["id: uuid", "usuario_id: uuid", "from_user_id: uuid", "tipo: string", "mensaje: string", "leida: boolean"]),
    ]
    for name, x, y, w, attrs in definitions:
        box, h = class_box(x, y, w, name, attrs)
        boxes[name] = (x, y, w, h)
        s += box
    # Main relationships
    s += line(350, 215, 470, 215, "1 a 1", 410, 200)
    s += line(350, 230, 930, 230, "1 a *", 640, 216)
    s += poly([(220, 285), (220, 385), (1550, 385), (1550, 125)], "1 a *", 1450, 374)
    s += line(220, 285, 250, 470, "1 a *", 260, 380)
    s += poly([(220, 285), (220, 735), (630, 735), (630, 810)], "1 a *", 420, 724)
    s += poly([(220, 285), (220, 1040), (1155, 1040), (1155, 790)], "1 a *", 680, 1028)
    s += line(410, 540, 500, 540, "1 a *", 455, 526)
    s += line(410, 585, 830, 520, "1 a *", 620, 532)
    s += line(410, 635, 1230, 540, "1 a *", 820, 566)
    s += text(90, 1100, "Nota. El diagrama representa las relaciones persistentes principales usadas por Supabase/PostgreSQL.", "subtitle")
    s += svg_end()
    write("4_1_1_diagrama_clases_profesional.svg", s)


def diagram_components():
    s = svg_start(1800, 1120, "Figura 4.2. Diagrama de componentes")
    s += text(900, 98, "Distribución lógica de componentes frontend, backend y servicios externos", "subtitle", "middle")
    s += rect(70, 125, 470, 860, "pkg") + text(305, 162, "Frontend React/Vite/Capacitor", "h", "middle")
    s += rect(665, 125, 470, 860, "pkg") + text(900, 162, "Backend Node.js Express", "h", "middle")
    s += rect(1260, 125, 470, 860, "pkg") + text(1495, 162, "Servicios externos", "h", "middle")
    # Frontend
    front = [
        (115, 210, "Auth", "login, sesión"),
        (325, 210, "Closet", "inventario y filtros"),
        (115, 320, "Asistente", "chat y outfits"),
        (325, 320, "Calendario", "planificación"),
        (115, 430, "Feed/Amigos/Perfil", "comunidad"),
        (325, 430, "UploadModal", "cámara/galería"),
        (115, 540, "VirtualMannequin", "visualiza outfit"),
        (325, 540, "WeatherService", "clima local"),
    ]
    for x, y, n, d in front:
        s += component(x, y, 175, 74, n, d, "front")
    # Backend
    back = [
        (815, 210, "API REST", "rutas HTTP/JSON"),
        (710, 330, "Auth Middleware", "verifica JWT"),
        (920, 330, "Upload + Multer", "multipart images"),
        (710, 450, "Sharp", "procesamiento imagen"),
        (920, 450, "Motor prompts IA", "clasifica/recomienda"),
        (710, 570, "Cache memoria", "TTL prendas/users"),
        (920, 570, "Notificaciones", "eventos sociales"),
    ]
    for x, y, n, d in back:
        s += component(x, y, 175, 74, n, d, "back")
    # External
    ext = [
        (1310, 210, "Supabase Auth", "sesión/JWT", "ext"),
        (1510, 210, "PostgreSQL", "datos", "db"),
        (1310, 330, "Storage", "imágenes", "db"),
        (1510, 330, "OpenAI", "Vision/Chat", "ext"),
        (1310, 450, "FastAPI rembg", "remove-bg", "ext"),
        (1510, 450, "Clima/Geo", "pronóstico", "ext"),
    ]
    for x, y, n, d, c in ext:
        s += component(x, y, 170, 74, n, d, c)
    # Lines
    s += line(500, 247, 1310, 247, "autenticación", 905, 235)
    s += line(500, 357, 815, 247, "chat/outfits", 640, 285)
    s += line(500, 467, 815, 247, "feed/closet", 640, 398)
    s += line(500, 467, 920, 367, "multipart", 690, 440)
    s += line(410, 614, 1510, 487, "pronóstico", 950, 664)
    s += line(815, 284, 797, 330)
    s += line(815, 284, 1007, 330)
    s += line(1007, 404, 797, 450)
    s += line(1095, 487, 1510, 367, "prompts", 1295, 414)
    s += line(797, 487, 1310, 487, "remove-bg", 1060, 474)
    s += line(900, 284, 1510, 247, "consultas", 1210, 228)
    s += line(900, 284, 1310, 367, "archivos", 1100, 348)
    s += line(1007, 607, 1510, 247, "guardar eventos", 1245, 560)
    s += text(70, 1045, "Nota. El frontend consume la API Express y también se comunica con Supabase Auth y servicios de clima cuando el flujo lo requiere.", "subtitle")
    s += svg_end()
    write("4_1_2_diagrama_componentes_profesional.svg", s)


def activity_box(x, y, w, h, title):
    return rect(x, y, w, h, "act") + text(x + w / 2, y + h / 2 + 5, title, "t", "middle")


def diagram_activity():
    s = svg_start(1500, 1680, "Figura 4.3. Diagrama de actividades")
    s += text(750, 98, "Flujo principal de subida, análisis y persistencia de prendas u outfits", "subtitle", "middle")
    lanes = [("Usuario", 70, 150, 300), ("Frontend", 370, 150, 330), ("Backend Express", 700, 150, 420), ("Servicios externos", 1120, 150, 310)]
    for name, x, y, w in lanes:
        s += rect(x, y, w, 1420, "lane")
        s += text(x + w / 2, y + 34, name, "h", "middle")
    s += f'  <circle cx="220" cy="230" r="18" class="start"/>\n'
    steps = [
        (105, 290, 230, 56, "Abre modal de subida"),
        (105, 390, 230, 56, "Selecciona prenda/outfit"),
        (405, 390, 250, 56, "Captura o elige imagen"),
        (405, 500, 250, 56, "Comprime imagen"),
        (405, 610, 250, 56, "Obtiene JWT"),
        (405, 720, 250, 56, "Envía FormData"),
        (770, 720, 280, 56, "Valida JWT"),
        (770, 830, 280, 56, "Multer recibe archivo"),
        (770, 940, 280, 56, "Sharp optimiza imagen"),
    ]
    for x, y, w, h, label in steps:
        s += activity_box(x, y, w, h, label)
    # decisions
    s += f'  <polygon points="910,1045 1045,1115 910,1185 775,1115" class="decision"/>\n'
    s += text(910, 1112, "¿Tipo prenda?", "t", "middle")
    # prenda branch
    prenda = [
        (1190, 1045, 190, 56, "FastAPI rembg"),
        (770, 1230, 280, 56, "Sube imagen a Storage"),
        (1190, 1230, 190, 56, "OpenAI Vision"),
    ]
    for x, y, w, h, label in prenda:
        s += activity_box(x, y, w, h, label)
    s += f'  <polygon points="910,1335 1045,1405 910,1475 775,1405" class="decision"/>\n'
    s += text(910, 1402, "¿Prenda válida?", "t", "middle")
    s += activity_box(770, 1510, 280, 56, "Inserta registro")
    s += activity_box(1135, 1510, 250, 56, "Responde 422")
    # outfit branch
    s += activity_box(510, 1230, 160, 56, "Outfit: sube imagen")
    s += activity_box(510, 1335, 160, 56, "Detecta prendas")
    s += activity_box(510, 1440, 160, 56, "Inserta outfit")
    # finish
    s += activity_box(405, 1560, 250, 56, "Refresca closet")
    s += f'  <circle cx="220" cy="1588" r="18" class="endOuter"/><circle cx="220" cy="1588" r="11" class="endInner"/>\n'
    # lines
    s += line(220, 248, 220, 290)
    s += line(220, 346, 220, 390)
    s += line(335, 418, 405, 418)
    s += line(530, 446, 530, 500)
    s += line(530, 556, 530, 610)
    s += line(530, 666, 530, 720)
    s += line(655, 748, 770, 748)
    s += line(910, 776, 910, 830)
    s += line(910, 886, 910, 940)
    s += line(910, 996, 910, 1045)
    s += line(1045, 1115, 1190, 1073, "Sí", 1115, 1075)
    s += line(910, 1185, 910, 1230)
    s += line(1050, 1258, 1190, 1258, "analiza", 1120, 1244)
    s += line(910, 1286, 910, 1335)
    s += line(910, 1475, 910, 1510, "Sí", 930, 1492)
    s += line(1045, 1405, 1135, 1510, "No", 1110, 1450)
    s += poly([(775, 1115), (590, 1115), (590, 1230)], "No, outfit", 650, 1098)
    s += line(590, 1286, 590, 1335)
    s += line(590, 1391, 590, 1440)
    s += poly([(590, 1496), (590, 1540), (530, 1540), (530, 1560)])
    s += poly([(910, 1566), (910, 1628), (530, 1628), (530, 1616)])
    s += line(405, 1588, 238, 1588)
    s += text(70, 1645, "Nota. El flujo contempla los caminos de éxito, rechazo por imagen no válida y carga de outfit completo.", "subtitle")
    s += svg_end()
    write("4_1_3_diagrama_actividades_profesional.svg", s)


def diagram_deployment():
    s = svg_start(1700, 1050, "Figura 4.4. Diagrama de despliegue")
    s += text(850, 98, "Vista física de ejecución, hosting y servicios administrados", "subtitle", "middle")
    s += rect(80, 140, 390, 270, "pkg") + text(275, 176, "Dispositivo usuario", "h", "middle")
    s += component(125, 225, 300, 62, "Web App React", "navegador", "front")
    s += component(125, 315, 300, 62, "App Android/iOS Capacitor", "WebView nativo", "front")
    s += rect(80, 570, 390, 210, "pkg") + text(275, 606, "Hosting estático", "h", "middle")
    s += component(125, 665, 300, 62, "Frontend build", "Vercel o hosting estático", "front")
    s += rect(650, 360, 360, 210, "pkg") + text(830, 396, "Railway", "h", "middle")
    s += component(700, 460, 260, 62, "Node.js Express API", "backend REST", "back")
    s += rect(1200, 120, 380, 330, "ext") + text(1390, 156, "Supabase", "h", "middle")
    s += component(1250, 215, 280, 58, "Auth", "JWT/sesión", "ext")
    s += component(1250, 290, 280, 58, "PostgreSQL", "base de datos", "db")
    s += component(1250, 365, 280, 58, "Storage bucket prendas", "archivos", "db")
    s += rect(1200, 560, 380, 160, "ext") + text(1390, 596, "OpenAI API", "h", "middle")
    s += component(1250, 640, 280, 58, "Chat/Vision model", "IA multimodal", "ext")
    s += rect(650, 730, 360, 160, "pkg") + text(830, 766, "Servicio rembg", "h", "middle")
    s += component(700, 810, 260, 58, "FastAPI + rembg models", "segmentación", "back")
    s += line(275, 665, 275, 287, "entrega app", 340, 490)
    s += line(425, 256, 700, 482, "HTTPS", 520, 340)
    s += line(425, 346, 700, 505, "HTTPS", 520, 430)
    s += poly([(425, 256), (1110, 256), (1250, 244)], "sesión/JWT", 760, 240)
    s += line(960, 475, 1250, 320, "consultas", 1110, 372)
    s += line(960, 492, 1250, 392, "imágenes", 1110, 452)
    s += line(960, 510, 1250, 668, "análisis", 1110, 610)
    s += line(830, 522, 830, 810, "remove-bg", 890, 676)
    s += text(80, 970, "Nota. El backend centraliza las reglas de negocio y se integra con servicios externos mediante HTTPS.", "subtitle")
    s += svg_end()
    write("4_1_4_diagrama_despliegue_profesional.svg", s)


def diagram_c4_level1():
    s = svg_start(1450, 900, "Figura 4.5. Modelo C4 - Nivel 1: Contexto")
    s += text(725, 98, "Relación entre usuarios, sistema principal y servicios externos", "subtitle", "middle")
    s += actor(150, 300, "Usuario")
    s += component(535, 330, 330, 130, "Be: Confident", "Closet inteligente con IA", "front")
    s += component(1060, 160, 260, 80, "Supabase", "auth, datos y archivos", "ext")
    s += component(1060, 310, 260, 80, "OpenAI API", "análisis y recomendaciones", "ext")
    s += component(1060, 460, 260, 80, "Clima/Geolocalización", "contexto climático", "ext")
    s += component(1060, 610, 260, 80, "Servicio rembg", "remoción de fondo", "ext")
    s += line(185, 385, 535, 395, "usa", 355, 372)
    s += line(865, 360, 1060, 200, "auth/datos", 950, 250)
    s += line(865, 395, 1060, 350, "IA", 955, 362)
    s += line(865, 430, 1060, 500, "clima", 955, 480)
    s += line(740, 460, 1060, 650, "remove-bg", 910, 585)
    s += svg_end()
    write("4_4_c4_nivel_1_contexto_profesional.svg", s)


def diagram_c4_level2():
    s = svg_start(1550, 940, "Figura 4.6. Modelo C4 - Nivel 2: Contenedores")
    s += text(775, 98, "Contenedores ejecutables y servicios usados por la solución", "subtitle", "middle")
    s += actor(120, 335, "Usuario")
    s += component(310, 340, 290, 120, "App React/Capacitor", "SPA web + app móvil", "front")
    s += component(735, 340, 260, 120, "API Express", "rutas y reglas de negocio", "back")
    s += component(1165, 150, 270, 105, "Supabase Auth/Postgres/Storage", "persistencia administrada", "db")
    s += component(1165, 340, 270, 105, "OpenAI API", "prompts y visión", "ext")
    s += component(1165, 535, 270, 105, "FastAPI rembg", "segmentación de imágenes", "ext")
    s += component(310, 620, 290, 105, "Servicio de clima", "consumido desde frontend", "ext")
    s += line(155, 420, 310, 400, "interactúa", 225, 392)
    s += line(600, 400, 735, 400, "HTTPS/JSON", 668, 384)
    s += line(995, 365, 1165, 205, "datos/auth/storage", 1085, 260)
    s += line(995, 400, 1165, 395, "prompts", 1080, 386)
    s += line(920, 460, 1165, 585, "remove-bg", 1040, 535)
    s += line(455, 460, 455, 620, "pronóstico", 520, 548)
    s += svg_end()
    write("4_4_c4_nivel_2_contenedores_profesional.svg", s)


def diagram_c4_level3():
    s = svg_start(1650, 1080, "Figura 4.7. Modelo C4 - Nivel 3: Componentes Backend")
    s += text(825, 98, "Componentes internos del backend Express y dependencias principales", "subtitle", "middle")
    s += rect(265, 135, 1000, 780, "pkg") + text(765, 172, "API Express", "h", "middle")
    comps = [
        (330, 230, "requireAuth", "valida JWT"),
        (660, 230, "upload / multer", "recibe imágenes"),
        (990, 230, "Sharp", "optimiza imagen"),
        (330, 390, "removeBackground", "consume rembg"),
        (660, 390, "OpenAI prompts", "análisis/outfits"),
        (990, 390, "Supabase client", "datos/storage"),
        (330, 550, "aiLimiter", "rate limit IA"),
        (660, 550, "Cache", "TTL prendas/users"),
        (990, 550, "Notificaciones", "eventos sociales"),
    ]
    for x, y, n, d in comps:
        s += component(x, y, 220, 82, n, d, "back")
    s += component(60, 230, 170, 82, "Frontend", "React/Capacitor", "front")
    s += component(1350, 230, 220, 82, "Supabase", "SQL/storage/auth", "db")
    s += component(1350, 420, 220, 82, "OpenAI API", "Vision/Chat", "ext")
    s += component(1350, 610, 220, 82, "FastAPI rembg", "remove-bg", "ext")
    s += line(230, 271, 330, 271, "JWT", 280, 255)
    s += line(550, 271, 660, 271)
    s += line(880, 271, 990, 271)
    s += line(990, 312, 440, 390, "imagen", 715, 340)
    s += line(550, 431, 660, 431)
    s += line(880, 431, 1350, 461)
    s += line(1210, 431, 1350, 271)
    s += line(440, 472, 1350, 651)
    s += line(440, 312, 440, 550)
    s += line(770, 472, 770, 550)
    s += line(1100, 472, 1100, 550)
    s += svg_end()
    write("4_4_c4_nivel_3_componentes_profesional.svg", s)


def diagram_c4_level4():
    s = svg_start(1750, 1160, "Figura 4.8. Modelo C4 - Nivel 4: Código Backend")
    s += text(875, 98, "Funciones y módulos clave implementados en server.js", "subtitle", "middle")
    s += component(735, 135, 280, 100, "server.js", "Express app, CORS, Helmet,\naiLimiter, multer", "back")
    routes = [
        (90, 330, "POST /api/subir-prenda", "procesa imágenes\nguarda prendas"),
        (450, 330, "POST /api/fashion", "genera outfits\ncon OpenAI"),
        (810, 330, "GET/POST calendario", "consulta y guarda\noutfits por fecha"),
        (1170, 330, "Feed/Social", "posts, likes,\ncomments, wishlist"),
        (1170, 515, "Perfil/Amistades", "profiles,\nfriendships, notifications"),
    ]
    for x, y, n, d in routes:
        s += component(x, y, 280, 98, n, d, "front")
    helpers = [
        (90, 735, "requireAuth", "valida JWT"),
        (400, 735, "safeParseJSON", "parsea salida IA"),
        (710, 735, "removeBackground", "llama FastAPI"),
        (1020, 735, "Cache", "Map con TTL"),
        (1330, 735, "crearNotificacion", "guarda eventos"),
        (400, 900, "generarContextoClima", "reglas climáticas"),
        (710, 900, "formatPrendaRica", "metadata a prompt"),
        (1020, 900, "deduplicarPorTipo", "evita repetidos"),
    ]
    for x, y, n, d in helpers:
        s += component(x, y, 250, 90, n, d, "back")
    s += component(90, 1035, 250, 70, "Supabase", "datos/storage/auth", "db")
    s += component(750, 1035, 250, 70, "OpenAI API", "visión/chat", "ext")
    s += component(1360, 1035, 250, 70, "FastAPI rembg", "segmentación", "ext")
    for x, y, _, _ in routes:
        s += line(875, 235, x + 140, y)
    s += line(230, 428, 215, 735)
    s += line(230, 428, 525, 735)
    s += line(230, 428, 835, 735)
    s += line(590, 428, 525, 735)
    s += line(590, 428, 835, 900)
    s += line(590, 428, 1145, 900)
    s += line(1310, 428, 1455, 735)
    s += line(1310, 613, 1455, 735)
    s += line(215, 825, 215, 1035)
    s += line(525, 825, 875, 1035)
    s += line(835, 825, 1485, 1035)
    s += line(1145, 825, 215, 1035)
    s += svg_end()
    write("4_4_c4_nivel_4_codigo_profesional.svg", s)


def diagram_data_model():
    s = svg_start(1650, 1020, "Figura 4.9. Modelo de datos / Persistencia")
    s += text(825, 98, "Vista relacional de tablas principales en Supabase PostgreSQL", "subtitle", "middle")
    defs = [
        ("profiles", 90, 160, 280, ["id PK", "username", "nombre", "avatar_url", "setup_completo"]),
        ("prendas", 500, 120, 300, ["id PK", "usuario_id FK", "tipo", "imagen_url", "metadata_ia JSON"]),
        ("calendar_outfits", 930, 150, 310, ["id PK", "usuario_id FK", "fecha", "imagen_url", "metadata JSON"]),
        ("posts", 90, 500, 280, ["id PK", "usuario_id FK", "imagen_url", "descripcion", "prendas JSON"]),
        ("likes", 500, 485, 240, ["id PK", "post_id FK", "usuario_id FK"]),
        ("comments", 810, 485, 280, ["id PK", "post_id FK", "usuario_id FK", "texto"]),
        ("wishlist", 1160, 485, 280, ["id PK", "usuario_id FK", "post_id FK", "imagen_url"]),
        ("friendships", 500, 780, 310, ["id PK", "requester_id FK", "addressee_id FK", "status"]),
        ("notifications", 930, 780, 320, ["id PK", "usuario_id FK", "from_user_id FK", "tipo", "leida"]),
    ]
    for name, x, y, w, attrs in defs:
        b, _ = class_box(x, y, w, name, attrs)
        s += b
    s += line(370, 230, 500, 230, "1 a *")
    s += line(370, 260, 930, 240, "1 a *")
    s += line(230, 330, 230, 500, "1 a *")
    s += line(370, 565, 500, 550, "1 a *")
    s += line(370, 590, 810, 550, "1 a *")
    s += line(370, 620, 1160, 550, "1 a *")
    s += line(640, 650, 640, 780, "1 a *")
    s += poly([(230, 330), (230, 940), (1090, 940), (1090, 780)], "1 a *")
    s += text(90, 970, "Nota. El almacenamiento de imágenes se realiza en Supabase Storage y las URLs públicas se referencian desde estas tablas.", "subtitle")
    s += svg_end()
    write("4_3_modelo_datos_persistencia_profesional.svg", s)


def write_puml_files():
    puml_map = {
        "4_1_1_diagrama_clases_profesional.puml": """@startuml
skinparam classAttributeIconSize 0
class Usuario { id: uuid\nemail: string }
class Perfil { id: uuid\nusername: string\nnombre: string\nbio: string\navatar_url: string\nsetup_completo: boolean }
class Prenda { id: uuid\nusuario_id: uuid\ntipo: prenda|outfit\ngenero: string\nimagen_url: string\ndescripcion: string\nmetadata_ia: json }
class CalendarOutfit { id: uuid\nusuario_id: uuid\nfecha: date\nimagen_url: string\ndescripcion: string\nmetadata: json }
class Post { id: uuid\nusuario_id: uuid\nimagen_url: string\ndescripcion: string\nprendas: json\ncreated_at: timestamp }
class Like { id: uuid\npost_id: uuid\nusuario_id: uuid }
class Comment { id: uuid\npost_id: uuid\nusuario_id: uuid\ntexto: string\ncreated_at: timestamp }
class Wishlist { id: uuid\nusuario_id: uuid\npost_id: uuid\nimagen_url: string\ndescripcion: string }
class Friendship { id: uuid\nrequester_id: uuid\naddressee_id: uuid\nstatus: pending|accepted|rejected }
class Notification { id: uuid\nusuario_id: uuid\nfrom_user_id: uuid\ntipo: string\nmensaje: string\nleida: boolean }
Usuario "1" -- "1" Perfil
Usuario "1" -- "*" Prenda
Usuario "1" -- "*" CalendarOutfit
Usuario "1" -- "*" Post
Usuario "1" -- "*" Wishlist
Usuario "1" -- "*" Friendship
Usuario "1" -- "*" Notification
Post "1" -- "*" Like
Post "1" -- "*" Comment
Post "1" -- "*" Wishlist
@enduml
""",
        "4_1_2_diagrama_componentes_profesional.puml": """@startuml
skinparam componentStyle rectangle
package "Frontend React/Vite/Capacitor" {
  component Auth
  component Closet
  component Asistente
  component Calendario
  component "Feed/Amigos/Perfil" as SocialUI
  component UploadModal
  component VirtualMannequin
  component WeatherService
}
package "Backend Node.js Express" {
  component "API REST" as API
  component "Auth Middleware" as AuthMid
  component "Upload + Multer" as Upload
  component Sharp
  component "Motor prompts IA" as Prompts
  component Cache
  component Notificaciones
}
package "Servicios externos" {
  component "Supabase Auth" as SupaAuth
  database "Supabase Postgres" as DB
  storage "Supabase Storage" as Storage
  component "OpenAI Vision/Chat" as OpenAI
  component "FastAPI rembg" as Rembg
  component "Clima/Geolocalización" as Weather
}
Auth --> SupaAuth
Closet --> API
Asistente --> API
Calendario --> API
SocialUI --> API
UploadModal --> API
Asistente --> VirtualMannequin
WeatherService --> Weather
API --> AuthMid
API --> Upload
Upload --> Sharp
Sharp --> Rembg
API --> Prompts
Prompts --> OpenAI
API --> DB
API --> Storage
AuthMid --> SupaAuth
API --> Cache
API --> Notificaciones
@enduml
""",
        "4_1_3_diagrama_actividades_profesional.puml": """@startuml
|Usuario|
start
:Abre modal de subida;
:Selecciona prenda u outfit;
|Frontend|
:Captura o elige imagen;
:Comprime imagen;
:Obtiene JWT de Supabase;
:Envía FormData;
|Backend Express|
:Valida JWT;
if (¿JWT válido?) then (Sí)
  :Multer recibe archivo;
  :Sharp optimiza imagen;
  if (¿Tipo = prenda?) then (Sí)
    |Servicios externos|
    :FastAPI rembg remueve fondo;
    |Backend Express|
    :Sube imagen a Storage;
    |Servicios externos|
    :OpenAI analiza prenda;
    |Backend Express|
    if (¿Prenda válida?) then (Sí)
      :Inserta registro en prendas;
      |Frontend|
      :Refresca closet;
    else (No)
      :Responde error 422;
    endif
  else (Outfit)
    :Sube outfit a Storage;
    |Servicios externos|
    :OpenAI detecta prendas;
    |Backend Express|
    :Inserta outfit;
    |Frontend|
    :Refresca closet;
  endif
else (No)
  :Responde 401;
endif
stop
@enduml
""",
    }
    for name, content in puml_map.items():
        write(name, content)


def write_section_text():
    section = """4.1 Diseño detallado del software

Figura 4.1. Diagrama de clases.
El diagrama de clases presenta las entidades conceptuales más importantes de Be: Confident: usuario, perfil, prendas, calendario, publicaciones, interacciones sociales, wishlist, amistades y notificaciones. Esta vista permite reconocer cómo se relacionan los datos principales del sistema antes de pasar al diseño físico de persistencia.

Figura 4.2. Diagrama de componentes.
El diagrama de componentes muestra la separación lógica entre frontend, backend y servicios externos. El frontend concentra la experiencia de usuario en React/Vite/Capacitor; el backend Express centraliza reglas de negocio, autenticación, procesamiento de imágenes, prompts de IA y notificaciones; y los servicios externos aportan autenticación, base de datos, almacenamiento, inteligencia artificial, clima y remoción de fondo.

Figura 4.3. Diagrama de actividades.
El diagrama de actividades describe el flujo principal de subida y análisis de una prenda u outfit. El proceso inicia cuando el usuario selecciona una imagen, continúa con compresión, validación del JWT, procesamiento con Sharp, remoción de fondo, análisis con OpenAI, almacenamiento en Supabase y actualización del closet en la interfaz.

Figura 4.4. Diagrama de despliegue.
El diagrama de despliegue representa la distribución física de la solución. La aplicación puede ejecutarse como web app o como app móvil híbrida con Capacitor. El backend Express se despliega como API en Railway, mientras Supabase administra autenticación, base de datos y storage. OpenAI y FastAPI rembg funcionan como servicios externos especializados.

4.3 Diseño del modelo de datos / Persistencia

Figura 4.9. Modelo de datos / Persistencia.
La persistencia se organiza alrededor de tablas de usuario, prendas, calendario, publicaciones e interacciones sociales. Las imágenes se almacenan en Supabase Storage y las tablas guardan las URL y la metadata asociada a cada recurso.

4.4 Diseño de la arquitectura de software (Modelo C4)

Figura 4.5. Modelo C4 Nivel 1: Contexto.
Este nivel ubica a Be: Confident frente a sus actores y dependencias principales: el usuario, Supabase, OpenAI, el servicio de clima/geolocalización y el servicio de remoción de fondo.

Figura 4.6. Modelo C4 Nivel 2: Contenedores.
Este nivel separa la solución en contenedores ejecutables: App React/Capacitor, API Express, Supabase, OpenAI, FastAPI rembg y servicio de clima.

Figura 4.7. Modelo C4 Nivel 3: Componentes Backend.
Este nivel detalla los componentes internos del backend Express, incluyendo middleware de autenticación, carga de imágenes, procesamiento con Sharp, motor de prompts, cache, notificaciones y cliente Supabase.

Figura 4.8. Modelo C4 Nivel 4: Código Backend.
Este nivel baja al detalle de funciones y rutas clave dentro de server.js, mostrando cómo las rutas principales se apoyan en helpers como requireAuth, safeParseJSON, removeBackground, cache, generación de contexto climático y deduplicación de prendas.
"""
    write("SECCION_4_TEXTO_PARA_PAGES.txt", section)


def main():
    diagram_classes()
    diagram_components()
    diagram_activity()
    diagram_deployment()
    diagram_c4_level1()
    diagram_c4_level2()
    diagram_c4_level3()
    diagram_c4_level4()
    diagram_data_model()
    write_puml_files()
    write_section_text()
    print(OUT.resolve())


if __name__ == "__main__":
    main()
