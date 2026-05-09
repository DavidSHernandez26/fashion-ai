from html import escape
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


OUT = Path("Entrega_opcion_de_grado_Be_Confident.docx")

NS = (
    'xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:o="urn:schemas-microsoft-com:office:office" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
    'xmlns:v="urn:schemas-microsoft-com:vml" '
    'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:w10="urn:schemas-microsoft-com:office:word" '
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
    'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
    'xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" '
    'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
    'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
    'mc:Ignorable="w14 wp14"'
)


class Doc:
    def __init__(self):
        self.body = []

    def p(self, text="", style=None, bold=False, italic=False):
        ppr = f"<w:pPr><w:pStyle w:val=\"{style}\"/></w:pPr>" if style else ""
        rpr = ""
        if bold or italic:
            rpr = "<w:rPr>" + ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "") + "</w:rPr>"
        parts = str(text).split("\n")
        runs = []
        for i, part in enumerate(parts):
            if i:
                runs.append("<w:r><w:br/></w:r>")
            runs.append(f"<w:r>{rpr}<w:t xml:space=\"preserve\">{escape(part)}</w:t></w:r>")
        self.body.append(f"<w:p>{ppr}{''.join(runs)}</w:p>")

    def h(self, text, level=1):
        self.p(text, f"Heading{level}")

    def bullet(self, text):
        self.p("• " + text)

    def code(self, text):
        for line in text.strip("\n").split("\n"):
            self.p(line, "Code")

    def page_break(self):
        self.body.append("<w:p><w:r><w:br w:type=\"page\"/></w:r></w:p>")

    def table(self, rows):
        grid_cols = "".join("<w:gridCol w:w=\"4500\"/>" for _ in rows[0])
        xml = [
            '<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
            '<w:tblW w:w="0" w:type="auto"/></w:tblPr>',
            f"<w:tblGrid>{grid_cols}</w:tblGrid>",
        ]
        for row in rows:
            xml.append("<w:tr>")
            for cell in row:
                xml.append(
                    "<w:tc><w:tcPr><w:tcW w:w=\"4500\" w:type=\"dxa\"/></w:tcPr>"
                    f"<w:p><w:r><w:t xml:space=\"preserve\">{escape(str(cell))}</w:t></w:r></w:p></w:tc>"
                )
            xml.append("</w:tr>")
        xml.append("</w:tbl>")
        self.body.append("".join(xml))

    def build(self):
        sect = (
            '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
            '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
            'w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:document {NS}><w:body>{"".join(self.body)}{sect}</w:body></w:document>'
        )


def content_types():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""


def rels():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""


def doc_rels():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>"""


def styles():
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:after="0" w:line="480" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:jc w:val="center"/><w:spacing w:after="240" w:line="480" w:lineRule="auto"/></w:pPr><w:rPr><w:b/><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:jc w:val="center"/><w:spacing w:before="240" w:after="0" w:line="480" w:lineRule="auto"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="240" w:after="0" w:line="480" w:lineRule="auto"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="240" w:after="0" w:line="480" w:lineRule="auto"/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:i/><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/><w:sz w:val="18"/></w:rPr></w:style>
  <w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/><w:tblPr><w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/></w:tblBorders></w:tblPr></w:style>
</w:styles>"""


doc = Doc()

doc.p("Be: Confident: aplicación híbrida para la organización inteligente del vestuario mediante inteligencia artificial", "Title")
doc.p("Documento de especificación, diseño e implementación del proyecto de software")
doc.p("Autor: [Nombre del estudiante]")
doc.p("Institución: [Nombre de la institución]")
doc.p("Programa académico: [Nombre del programa]")
doc.p("Asignatura / opción de grado: [Nombre de la asignatura]")
doc.p("Docente: [Nombre del docente]")
doc.p("Fecha: 8 de mayo de 2026")
doc.page_break()

doc.h("Introducción")
doc.p("Este documento presenta la evolución técnica y funcional de Be: Confident, una propuesta de software que nace de una necesidad cotidiana: elegir qué ponerse sin perder tiempo, sin repetir siempre las mismas prendas y sin comprar ropa que realmente no hace falta. A partir de esa situación, el proyecto plantea una solución híbrida que combina organización personal, inteligencia artificial, planificación y comunidad.")
doc.p("La documentación se estructura con base en criterios de especificación de requisitos, diseño de software e implementación. Para la parte de requisitos se toma como referencia el enfoque de IEEE 830, mientras que el diseño se organiza considerando principios del ciclo de vida de software descritos por ISO/IEC/IEEE 12207. En la arquitectura se utiliza el modelo C4 como recurso para explicar el sistema desde diferentes niveles de abstracción (Brown, s. f.; IEEE, 1998; ISO/IEC/IEEE, 2017).")

doc.h("1. Datos Informativos Del Proyecto")
doc.h("1.1 Título Del Proyecto De Software", 2)
doc.p("Be: Confident — Desarrollo de una aplicación híbrida para la organización inteligente de vestuario, recomendación de outfits y planificación semanal usando inteligencia artificial.")
doc.h("1.2 Breve Síntesis Del Proyecto", 2)
doc.p("Be: Confident es una aplicación web y móvil híbrida pensada para convertir el closet físico de una persona en un espacio digital fácil de consultar. La aplicación permite subir fotografías de prendas u outfits, analizarlas con inteligencia artificial, clasificarlas por características de moda y generar recomendaciones de outfits de acuerdo con la ocasión, el clima, el historial de uso y el estilo personal.")
doc.p("Más que funcionar como un simple inventario de ropa, el proyecto intenta acompañar una decisión diaria que muchas veces se vuelve repetitiva o estresante. La idea es que el usuario pueda abrir la aplicación, ver lo que realmente tiene, recibir una recomendación razonada y planificar sus combinaciones sin depender únicamente de la memoria o de la inspiración del momento. En su versión actual, la solución se construye con React/Vite, Capacitor, Node.js/Express, Supabase, OpenAI y un microservicio FastAPI para remoción de fondo.")

doc.h("2. Planificación Del Proyecto")
doc.h("2.1 Planteamiento Del Problema", 2)
doc.p("En la vida diaria, elegir ropa puede parecer una actividad menor, pero para muchas personas implica tiempo, dudas y repetición de decisiones. Es común tener prendas guardadas que se olvidan, comprar artículos parecidos a otros que ya se tienen o sentir que “no hay nada que ponerse” aunque el closet esté lleno. Esta dificultad no solo afecta la organización personal, sino también la manera en que se aprovechan los recursos ya adquiridos.")
doc.p("El problema se hace más evidente cuando el usuario debe vestirse para estudiar, trabajar, asistir a una reunión, salir con amigos o responder a cambios de clima. En esos casos, la decisión debe ser rápida, pero también coherente con la ocasión. A esto se suma que el consumo impulsivo de ropa puede relacionarse con dinámicas de moda rápida, acumulación innecesaria y bajo uso de prendas. Por esa razón, una solución tecnológica que ayude a ver, clasificar y recombinar el propio closet puede aportar valor práctico y también fomentar hábitos de consumo más conscientes.")
doc.h("2.2 Objetivos Del Proyecto", 2)
doc.h("2.2.1 Objetivo General", 3)
doc.p("Diseñar, desarrollar e implementar una aplicación híbrida que permita organizar digitalmente el vestuario del usuario y generar recomendaciones personalizadas de outfits mediante inteligencia artificial, integrando análisis de imágenes, clima, planificación semanal y funciones sociales.")
doc.h("2.2.2 Objetivos Específicos", 3)
for item in [
    "Definir los requisitos funcionales y no funcionales de una solución de closet inteligente.",
    "Diseñar una arquitectura modular compuesta por frontend híbrido, backend API, persistencia en la nube, servicios de IA y microservicio de procesamiento de imagen.",
    "Implementar autenticación, perfil de usuario, carga de prendas, clasificación automática, closet digital, asistente conversacional, calendario y comunidad.",
    "Aplicar procesamiento de imágenes para optimizar fotografías, remover fondos y almacenar recursos visuales en la nube.",
    "Generar recomendaciones de outfits considerando ocasión, clima, historial, metadata de prendas y preferencias del usuario.",
    "Validar la solución mediante pruebas de construcción, revisión funcional y documentación técnica conforme a IEEE 830, ISO 12207-1 y modelo C4.",
]:
    doc.bullet(item)
doc.h("2.3 Alcance De La Solución", 2)
doc.p("El alcance incluye una aplicación híbrida funcional con módulos de autenticación, onboarding de perfil, closet digital, carga de prendas y outfits, análisis con IA, asistente de moda, maniquí virtual, calendario de outfits, feed social, amistades, likes, comentarios, guardados, notificaciones y recomendaciones de compra.")
doc.p("No se contempla en esta fase un sistema de pagos, marketplace propio, entrenamiento de modelos personalizados, inventario multiusuario empresarial ni integración con tiendas en tiempo real. La solución se enfoca en el uso personal del closet y en una comunidad social básica entre usuarios.")
doc.h("2.4 Metodología De Desarrollo De Software", 2)
doc.p("Para el desarrollo se adopta Extreme Programming (XP), una metodología ágil adecuada para proyectos que evolucionan con retroalimentación constante y entregas frecuentes. En Be: Confident esta elección resulta pertinente porque la experiencia de usuario, los prompts de IA, las reglas de recomendación y los flujos móviles se ajustan mejor mediante ciclos cortos de prueba, revisión y mejora. XP favorece una construcción incremental y flexible, manteniendo el foco en funcionalidades útiles para el usuario final (Beck, 2000).")
for item in [
    "Iteraciones incrementales para construir módulos independientes: autenticación, closet, asistente, calendario y comunidad.",
    "Refactorización continua para mejorar rendimiento, caching, manejo de errores y seguridad.",
    "Integración frecuente entre frontend, backend, Supabase, OpenAI y rembg.",
    "Validación temprana de interfaces y flujos de usuario en web y entorno móvil Capacitor.",
    "Diseño simple y evolutivo, evitando complejidad innecesaria antes de comprobar necesidades reales.",
]:
    doc.bullet(item)

doc.h("3. Especificación De Requisitos De Software (IEEE 830)")
doc.h("3.1 Funcionalidad Del Producto (Procesos Y Servicios)", 2)
doc.table([
    ["Proceso/Servicio", "Descripción"],
    ["Autenticación y perfil", "Inicio de sesión con Supabase Auth, registro en waitlist, recuperación de contraseña y configuración de perfil."],
    ["Carga de prendas/outfits", "Selección desde galería o cámara, compresión, subida al backend y almacenamiento en Supabase Storage."],
    ["Análisis visual con IA", "Clasificación de nombre, color, tipo, material, temporada, estilo, patrón y fit usando OpenAI."],
    ["Remoción de fondo", "Microservicio FastAPI con rembg para generar imágenes limpias de prendas individuales."],
    ["Closet digital", "Consulta, filtrado, ordenamiento, estadísticas por color/tipo, reanálisis y eliminación de prendas."],
    ["Asistente de moda", "Chat que recomienda outfits según ocasión, clima, perfil, historial y prendas disponibles."],
    ["Calendario", "Planificación de outfits por fecha, edición, detalle y eliminación de registros."],
    ["Comunidad", "Feed de outfits, publicaciones, likes, comentarios, wishlist, amistades y notificaciones."],
    ["Recomendaciones de compra", "Sugerencias cortas de prendas faltantes para completar combinaciones."],
])
doc.h("3.2 Características De Los Usuarios (Público Objetivo)", 2)
doc.p("El público objetivo son jóvenes y adultos entre 18 y 40 años, estudiantes, profesionales o usuarios interesados en moda práctica, organización personal y herramientas digitales. Se espera familiaridad básica con aplicaciones móviles, navegación web, cámara del dispositivo, inicio de sesión y publicación de contenido social.")
doc.p("Los usuarios buscan ahorrar tiempo, aprovechar mejor su ropa, mejorar su estilo diario y recibir ayuda contextual sin tener conocimientos avanzados de moda.")
doc.h("3.3 Requisitos Funcionales", 2)
requirements = [
    ("RF-01", "El sistema debe permitir iniciar sesión mediante correo y contraseña usando Supabase Auth."),
    ("RF-02", "El sistema debe permitir registrar correos en una lista de espera para beta cerrada."),
    ("RF-03", "El sistema debe solicitar completar perfil antes de acceder a las funciones privadas."),
    ("RF-04", "El sistema debe permitir subir una o varias imágenes de prendas individuales."),
    ("RF-05", "El sistema debe permitir subir una imagen de outfit completo."),
    ("RF-06", "El sistema debe remover el fondo de prendas individuales cuando el servicio esté disponible."),
    ("RF-07", "El sistema debe analizar imágenes con IA y guardar metadata estructurada de moda."),
    ("RF-08", "El sistema debe rechazar imágenes que no correspondan a ropa, calzado o accesorios."),
    ("RF-09", "El sistema debe listar prendas por usuario autenticado y filtrar por tipo/categoría/color."),
    ("RF-10", "El sistema debe permitir eliminar prendas propias."),
    ("RF-11", "El sistema debe permitir reanalizar prendas existentes para completar metadata."),
    ("RF-12", "El sistema debe generar outfits personalizados desde el asistente de moda."),
    ("RF-13", "El sistema debe usar clima/localización como contexto para la recomendación."),
    ("RF-14", "El sistema debe mostrar el outfit recomendado en un maniquí virtual."),
    ("RF-15", "El sistema debe guardar outfits en calendario por fecha."),
    ("RF-16", "El sistema debe consultar y eliminar registros del calendario."),
    ("RF-17", "El sistema debe permitir crear publicaciones con imagen, descripción y prendas asociadas."),
    ("RF-18", "El sistema debe mostrar feed propio y de amigos con paginación."),
    ("RF-19", "El sistema debe permitir dar like, comentar y guardar publicaciones en wishlist."),
    ("RF-20", "El sistema debe permitir buscar usuarios, enviar solicitudes, aceptar/rechazar amistades y eliminar amigos."),
    ("RF-21", "El sistema debe generar notificaciones por likes, comentarios y solicitudes."),
    ("RF-22", "El sistema debe calcular racha de uso de outfits registrados."),
]
doc.table([["ID", "Requisito funcional"]] + requirements)
doc.h("3.4 Diagrama De Casos De Uso", 2)
doc.code("""
@startuml
left to right direction
actor Usuario
actor "Usuario amigo" as Amigo
actor "Servicio IA OpenAI" as OpenAI
actor "Servicio Clima/Geolocalización" as Clima
actor "Servicio rembg" as Rembg

rectangle "Be: Confident" {
  Usuario --> (Iniciar sesión)
  Usuario --> (Completar perfil)
  Usuario --> (Subir prenda/outfit)
  (Subir prenda/outfit) --> (Analizar imagen con IA)
  (Subir prenda/outfit) --> (Remover fondo)
  Usuario --> (Consultar closet)
  Usuario --> (Solicitar outfit al asistente)
  (Solicitar outfit al asistente) --> (Consultar clima)
  Usuario --> (Guardar outfit en calendario)
  Usuario --> (Publicar outfit)
  Usuario --> (Dar like/comentar/guardar)
  Usuario --> (Buscar usuarios y gestionar amistades)
  Amigo --> (Ver closet autorizado)
  OpenAI --> (Analizar imagen con IA)
  OpenAI --> (Generar recomendación de outfit)
  Clima --> (Consultar clima)
  Rembg --> (Remover fondo)
}
@enduml
""")
doc.h("3.5 Especificaciones De Los Casos De Uso", 2)
doc.table([
    ["Caso de uso", "Actor", "Flujo principal", "Resultado"],
    ["CU-01 Iniciar sesión", "Usuario", "Ingresa correo y contraseña; Supabase valida credenciales; la app guarda sesión y redirige.", "Usuario autenticado."],
    ["CU-02 Subir prenda", "Usuario", "Selecciona tipo prenda, adjunta imágenes, backend procesa, remueve fondo, IA clasifica y almacena.", "Prenda disponible en closet."],
    ["CU-03 Solicitar outfit", "Usuario", "Escribe ocasión o necesidad; app envía closet, historial y clima; IA devuelve respuesta y IDs de prendas.", "Outfit recomendado en chat y maniquí."],
    ["CU-04 Planificar outfit", "Usuario", "Selecciona fecha en calendario, elige prenda/outfit o guarda recomendación.", "Registro guardado por fecha."],
    ["CU-05 Publicar outfit", "Usuario", "Carga imagen, descripción y etiquetas; backend almacena post y recursos.", "Post visible en feed propio/amigos."],
    ["CU-06 Gestionar amistad", "Usuario", "Busca usuario, envía solicitud; destinatario acepta o rechaza.", "Relación de amistad actualizada."],
    ["CU-07 Interactuar en feed", "Usuario", "Da like, comenta o guarda publicación.", "Interacción persistida y notificación generada."],
])
doc.h("3.6 Restricciones Y Atributos De Calidad", 2)
for item in [
    "Seguridad: endpoints privados protegidos con JWT de Supabase; validación de propiedad antes de eliminar recursos; Helmet, CORS configurable y rate limit en endpoints de IA.",
    "Rendimiento: lazy loading de páginas React, compresión de imágenes en cliente, resize con Sharp, caching temporal de prendas y usernames en backend.",
    "Disponibilidad: backend desplegable en Railway; frontend compatible con web y Capacitor; Supabase como servicio administrado.",
    "Usabilidad: interfaz responsive, navegación inferior, modales de carga, estados de progreso, haptics y adaptación a teclado móvil.",
    "Escalabilidad: arquitectura separada en frontend, API, base de datos/almacenamiento, IA externa y microservicio rembg.",
    "Compatibilidad: navegadores modernos y empaquetado Android/iOS mediante Capacitor.",
    "Privacidad: closets de otros usuarios solo visibles bajo relación de amistad aceptada.",
]:
    doc.bullet(item)

doc.h("4. Diseño Del Software (ISO 12207-1)")
doc.h("4.1 Diseño Detallado Del Software", 2)
doc.p("El sistema se organiza en una arquitectura cliente-servidor con servicios externos. El frontend React gestiona navegación, estado visual y consumo de API; el backend Express centraliza reglas de negocio, autenticación, procesamiento de imágenes e integración con OpenAI/Supabase; el microservicio FastAPI encapsula remoción de fondo.")
doc.h("4.1.1 Diagrama De Clases", 3)
doc.code("""
@startuml
class Usuario {
  id: uuid
  email: string
}
class Perfil {
  id: uuid
  username: string
  nombre: string
  bio: string
  avatar_url: string
  setup_completo: boolean
}
class Prenda {
  id: uuid
  usuario_id: uuid
  tipo: prenda|outfit
  genero: string
  imagen_url: string
  descripcion: string
  metadata_ia: json
}
class CalendarOutfit {
  id: uuid
  usuario_id: uuid
  fecha: date
  imagen_url: string
  descripcion: string
  metadata: json
}
class Post {
  id: uuid
  usuario_id: uuid
  imagen_url: string
  descripcion: string
  prendas: json
}
class Friendship {
  id: uuid
  requester_id: uuid
  addressee_id: uuid
  status: pending|accepted|rejected
}
class Like
class Comment
class Wishlist
class Notification

Usuario "1" -- "1" Perfil
Usuario "1" -- "*" Prenda
Usuario "1" -- "*" CalendarOutfit
Usuario "1" -- "*" Post
Post "1" -- "*" Like
Post "1" -- "*" Comment
Usuario "1" -- "*" Wishlist
Usuario "1" -- "*" Notification
Usuario "1" -- "*" Friendship
@enduml
""")
doc.h("4.1.2 Diagrama De Componentes", 3)
doc.code("""
@startuml
package "Frontend React/Vite/Capacitor" {
  [Auth]
  [Closet]
  [Asistente]
  [Calendario]
  [Feed/Amigos/Perfil]
  [UploadModal]
}
package "Backend Node.js Express" {
  [API REST]
  [Auth Middleware]
  [Procesamiento Sharp]
  [Motor de Prompts IA]
  [Cache en memoria]
}
package "Servicios externos" {
  [Supabase Auth]
  [Supabase Postgres]
  [Supabase Storage]
  [OpenAI Vision/Chat]
  [FastAPI rembg]
  [Geolocalización/Clima]
}
[Frontend React/Vite/Capacitor] --> [API REST]
[Frontend React/Vite/Capacitor] --> [Supabase Auth]
[API REST] --> [Supabase Postgres]
[API REST] --> [Supabase Storage]
[API REST] --> [OpenAI Vision/Chat]
[API REST] --> [FastAPI rembg]
[Asistente] --> [Geolocalización/Clima]
@enduml
""")
doc.h("4.1.3 Diagrama De Actividades", 3)
doc.code("""
@startuml
start
:Usuario abre modal de subida;
:Selecciona prenda u outfit;
:Selecciona/captura imagen;
:Cliente comprime imagen;
:Envía FormData con JWT al backend;
if (¿JWT válido?) then (sí)
  :Backend rota y optimiza imagen con Sharp;
  if (Tipo = prenda) then (sí)
    :Solicita remoción de fondo a rembg;
    :Sube imagen PNG a Supabase Storage;
    :OpenAI analiza la prenda;
    if (¿Es prenda válida?) then (sí)
      :Inserta registro en tabla prendas;
    else (no)
      :Elimina archivo y responde 422;
    endif
  else (outfit)
    :Sube imagen JPG a Supabase Storage;
    :OpenAI detecta prendas visibles;
    :Inserta outfit en tabla prendas;
  endif
  :Invalida cache;
  :Frontend actualiza closet;
else (no)
  :Responde 401;
endif
stop
@enduml
""")
doc.h("4.1.4 Diagrama De Despliegue", 3)
doc.code("""
@startuml
node "Dispositivo usuario" {
  artifact "Web App React"
  artifact "App Android/iOS Capacitor"
}
node "Vercel/Hosting estático" {
  artifact "Frontend build"
}
node "Railway" {
  node "Node.js Express API"
}
node "Servicio rembg" {
  node "FastAPI + rembg models"
}
cloud "Supabase" {
  database "PostgreSQL"
  storage "Storage bucket prendas"
  component "Auth"
}
cloud "OpenAI API" {
  component "Chat/Vision model"
}
"Web App React" --> "Node.js Express API" : HTTPS
"App Android/iOS Capacitor" --> "Node.js Express API" : HTTPS
"Node.js Express API" --> "PostgreSQL"
"Node.js Express API" --> "Storage bucket prendas"
"Node.js Express API" --> "OpenAI API"
"Node.js Express API" --> "FastAPI + rembg models"
@enduml
""")

doc.h("4.2 Diseño De La Interfaz", 2)
doc.h("4.2.1 Interfaz De Usuario (Hardware, Software Y Comunicaciones)", 3)
doc.p("La interfaz está diseñada para web responsive y app móvil híbrida. En hardware requiere cámara o galería para capturar prendas, pantalla táctil o mouse/teclado y conexión a internet. En software utiliza navegador moderno o WebView de Capacitor. Las comunicaciones se realizan por HTTPS hacia el backend y Supabase, con JWT en cabecera Authorization.")
doc.h("4.2.2 Interfaces De Entrada (Formularios, Login)", 3)
for item in [
    "Login: correo, contraseña, recordar correo y recuperación de contraseña.",
    "Waitlist/registro: correo electrónico para beta cerrada.",
    "Setup/Perfil: username, nombre, biografía y avatar.",
    "UploadModal: tipo prenda/outfit, cámara/galería, múltiples archivos, estado de carga.",
    "Asistente: caja de chat, entrada por texto y voz, selección de ocasión y fecha.",
    "Calendario: selección de día/mes/año, modal para elegir prenda u outfit.",
    "Feed: imagen, descripción, hashtags, comentarios y búsqueda de usuarios.",
]:
    doc.bullet(item)
doc.h("4.2.3 Interfaces De Salida (Reportes, Consultas, Impresiones)", 3)
for item in [
    "Closet visual con tarjetas de prendas, filtros por categoría/color y estadísticas.",
    "Respuesta conversacional del asistente con explicación de cada prenda recomendada.",
    "Maniquí virtual con la composición del outfit sugerido.",
    "Calendario mensual/semanal con collage de prendas registradas por día.",
    "Feed social con likes, comentarios, guardados y publicaciones populares.",
    "Panel de notificaciones y contador de eventos no leídos.",
    "Recomendaciones de compra basadas en brechas del closet.",
]:
    doc.bullet(item)

doc.h("4.3 Diseño Del Modelo De Datos / Persistencia", 2)
doc.table([
    ["Entidad/Tabla", "Campos principales", "Propósito"],
    ["profiles", "id, username, nombre, bio, avatar_url, genero, setup_completo", "Datos públicos y configuración inicial del usuario."],
    ["prendas", "id, usuario_id, tipo, genero, imagen_url, descripcion, metadata_ia, created_at", "Prendas individuales y outfits guardados."],
    ["calendar_outfits", "id, usuario_id, fecha, imagen_url, descripcion, metadata", "Planificación de outfits por fecha."],
    ["posts", "id, usuario_id, imagen_url, descripcion, prendas, created_at", "Publicaciones del feed social."],
    ["likes", "id, post_id, usuario_id", "Interacciones de me gusta."],
    ["comments", "id, post_id, usuario_id, texto, created_at", "Comentarios de publicaciones."],
    ["wishlist", "id, usuario_id, post_id, imagen_url, descripcion", "Publicaciones guardadas por el usuario."],
    ["friendships", "id, requester_id, addressee_id, status", "Relaciones de amistad y solicitudes."],
    ["notifications", "id, usuario_id, from_user_id, tipo, mensaje, post_id, leida", "Eventos sociales y solicitudes."],
    ["waitlist", "email, created_at", "Lista de espera de beta cerrada."],
])
doc.h("4.4 Diseño De La Arquitectura De Software (Modelo C4)", 2)
doc.h("Nivel 1: Contexto", 3)
doc.code("""
Usuario -> Be: Confident -> Supabase
Usuario -> Be: Confident -> OpenAI
Usuario -> Be: Confident -> Servicio de clima/geolocalización
Be: Confident -> Servicio rembg
""")
doc.h("Nivel 2: Contenedores", 3)
doc.code("""
[App React/Capacitor] -> [API Express]
[API Express] -> [Supabase Auth/Postgres/Storage]
[API Express] -> [OpenAI API]
[API Express] -> [FastAPI rembg]
[App React/Capacitor] -> [Servicio de clima desde frontend]
""")
doc.h("Nivel 3: Componentes Backend", 3)
doc.code("""
API Express
├─ requireAuth: valida JWT de Supabase
├─ upload/multer: recibe imágenes
├─ sharp: rota, redimensiona y comprime
├─ removeBackground: consume FastAPI rembg
├─ OpenAI prompts: análisis visual, outfits, recomendaciones de compra
├─ Supabase client: persistencia y storage
├─ aiLimiter: rate limit para endpoints costosos
└─ cache prendas/usernames: reduce consultas repetidas
""")

doc.h("5. Implementación")
doc.h("5.1 Herramientas Utilizadas En El Desarrollo Del Proyecto", 2)
doc.table([
    ["Categoría", "Herramientas"],
    ["Frontend", "React 19, Vite 7, React Router DOM 7, Axios, Framer Motion, Lucide React, Swiper, date-fns."],
    ["Móvil híbrido", "Capacitor 8, Android/iOS, plugins Camera, Geolocation, Haptics, Keyboard, StatusBar, Local Notifications."],
    ["Backend", "Node.js, Express, ESM, Multer, Helmet, CORS, express-rate-limit, Sharp, node-fetch, FormData."],
    ["Inteligencia artificial", "OpenAI Chat/Vision para análisis de imagen y recomendación de outfits."],
    ["Persistencia", "Supabase Auth, PostgreSQL, Storage y cliente supabase-js."],
    ["Procesamiento de fondo", "FastAPI, rembg, modelos birefnet-general, u2net_cloth_seg y u2net."],
    ["Despliegue/configuración", "Railway para backend, Vercel/hosting estático para frontend, variables de entorno, npm, concurrently."],
    ["Diseño UI", "CSS modular por página, componentes propios, shadcn/base-ui/cmdk como soporte de UI."],
])
doc.p("La selección de estas herramientas se fundamenta en la revisión del código del proyecto y en la documentación oficial de cada tecnología. React se utiliza por su modelo de interfaces basadas en componentes; Vite, por su enfoque de construcción rápida para aplicaciones frontend; Express, por su capacidad para crear APIs en Node.js; Supabase, por integrar autenticación, base de datos PostgreSQL y almacenamiento; Capacitor, por permitir empaquetar la experiencia web como aplicación móvil; OpenAI, por ofrecer APIs de análisis y generación; y FastAPI, por facilitar la creación del microservicio Python de remoción de fondo (Capacitor, s. f.; Express, s. f.; FastAPI, s. f.; OpenAI, s. f.; React, s. f.; Supabase, s. f.; Vite, s. f.).")
doc.h("5.2 Requisitos Del Hardware", 2)
doc.table([
    ["Entorno", "Requisito mínimo recomendado"],
    ["Desarrollo", "Equipo macOS, Windows o Linux; procesador 2 núcleos; 8 GB RAM; 2 GB libres; Node.js 18+; navegador moderno."],
    ["Pruebas móviles", "Dispositivo o emulador Android/iOS con cámara/galería y conexión a internet."],
    ["Usuario final web", "Navegador Chrome, Edge, Safari o Firefox; pantalla mínima 360 px; conexión estable."],
    ["Usuario final móvil", "Android/iOS compatible con Capacitor; cámara y permisos de galería/localización/notificaciones opcionales."],
    ["Servidor backend", "Instancia Node.js con acceso HTTPS, variables OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, CORS_ORIGIN y REMBG_SERVICE_URL."],
    ["Servicio rembg", "Servidor Python con CPU suficiente; para mejor rendimiento se recomienda GPU o instancia optimizada para inferencia."],
])

doc.h("Conclusiones")
doc.p("Be: Confident demuestra cómo una necesidad cotidiana puede convertirse en una solución de software con componentes reales de frontend, backend, inteligencia artificial, persistencia en la nube y experiencia móvil. El proyecto no se limita a recomendar ropa de forma genérica; utiliza el closet propio del usuario, su historial, el clima y su perfil para construir sugerencias más contextualizadas.")
doc.p("Desde el punto de vista académico, el desarrollo permite aplicar especificación de requisitos, diseño arquitectónico, modelado de datos, integración de servicios externos y construcción de interfaces. Como trabajo de opción de grado, la propuesta tiene un valor práctico porque aborda un problema cercano al usuario y lo resuelve mediante una arquitectura moderna, modular y escalable.")

doc.h("Fuentes Consultadas")
doc.p("Para construir el documento se usaron dos tipos de fuentes. Primero, se revisó el proyecto local Be: Confident, especialmente los archivos del frontend, backend, configuración de Capacitor y microservicio de remoción de fondo. Segundo, se consultaron fuentes oficiales en internet para respaldar la descripción de tecnologías, estándares y arquitectura. Las fuentes externas se incluyen en la lista de referencias en formato APA 7.")

doc.h("Referencias")
doc.p("American Psychological Association. (2020). Publication manual of the American Psychological Association (7th ed.). American Psychological Association.")
doc.p("Beck, K. (2000). Extreme programming explained: Embrace change. Addison-Wesley.")
doc.p("Brown, S. (s. f.). The C4 model for visualising software architecture. https://c4model.com/")
doc.p("Capacitor. (s. f.). Capacitor documentation. Ionic. https://capacitorjs.com/docs")
doc.p("Express. (s. f.). Express: Node.js web application framework. https://expressjs.com/")
doc.p("FastAPI. (s. f.). FastAPI documentation. https://fastapi.tiangolo.com/")
doc.p("IEEE. (1998). IEEE recommended practice for software requirements specifications (IEEE Std 830-1998). IEEE.")
doc.p("ISO/IEC/IEEE. (2017). Systems and software engineering: Software life cycle processes (ISO/IEC/IEEE 12207:2017). International Organization for Standardization.")
doc.p("OpenAI. (s. f.). OpenAI API documentation. https://platform.openai.com/docs")
doc.p("React. (s. f.). React documentation. Meta Open Source. https://react.dev/")
doc.p("Supabase. (s. f.). Supabase documentation. https://supabase.com/docs")
doc.p("Vite. (s. f.). Vite guide. https://vite.dev/guide/")

with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", content_types())
    z.writestr("_rels/.rels", rels())
    z.writestr("word/_rels/document.xml.rels", doc_rels())
    z.writestr("word/styles.xml", styles())
    z.writestr("word/document.xml", doc.build())

print(OUT.resolve())
