from pathlib import Path
import xml.etree.ElementTree as ET
import html
import math


# ============================================================
# CONFIGURACIÓN
# ============================================================

INPUT_DIR = Path("assets/technologies")
OUTPUT_FILE = Path("assets/technologies.svg")

WIDTH = 900
HEIGHT = 420

CENTER_X = WIDTH / 2
CENTER_Y = HEIGHT / 2

ICON_SIZE = 72

# Número de vueltas completas de los iconos.
# Cuanto mayor sea, más rápida será la animación.
ANIMATION_DURATION = 18

# Radio horizontal y vertical del círculo.
RADIUS_X = 300
RADIUS_Y = 135

# Tecnologías que aparecerán más cerca del centro.
# Si quieres que todas estén en círculo, puedes dejarlo vacío.
CENTER_ICON = None


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def local_name(tag):
    """Obtiene el nombre de una etiqueta XML eliminando namespaces."""
    return tag.split("}")[-1]


def get_svg_root(svg_text):
    """Carga un SVG y devuelve su raíz XML."""
    return ET.fromstring(svg_text)


def get_viewbox(root):
    """
    Obtiene el viewBox del SVG.
    Si no existe, intenta obtener width y height.
    """
    viewbox = root.attrib.get("viewBox")

    if viewbox:
        values = viewbox.replace(",", " ").split()

        if len(values) == 4:
            return [float(v) for v in values]

    width = root.attrib.get("width", "100")
    height = root.attrib.get("height", "100")

    def number(value):
        value = value.replace("px", "")
        try:
            return float(value)
        except ValueError:
            return 100.0

    return [0, 0, number(width), number(height)]


def serialize_children(root):
    """
    Extrae el contenido interno del SVG original.
    Se eliminan algunos atributos del SVG raíz porque
    el generador crea su propio contenedor.
    """
    parts = []

    for child in list(root):
        parts.append(
            ET.tostring(
                child,
                encoding="unicode"
            )
        )

    return "\n".join(parts)


def escape_xml(text):
    return html.escape(text, quote=True)


# ============================================================
# LEER LOS ICONOS
# ============================================================

svg_files = sorted(INPUT_DIR.glob("*.svg"))

if not svg_files:
    raise SystemExit(
        "ERROR: No se han encontrado archivos SVG en "
        f"{INPUT_DIR}"
    )


icons = []

for svg_file in svg_files:
    try:
        svg_text = svg_file.read_text(
            encoding="utf-8"
        )

        root = get_svg_root(svg_text)

        viewbox = get_viewbox(root)

        inner_content = serialize_children(root)

        icons.append(
            {
                "name": svg_file.stem,
                "viewbox": viewbox,
                "content": inner_content,
            }
        )

    except Exception as error:
        print(
            f"WARNING: No se pudo procesar "
            f"{svg_file}: {error}"
        )


if not icons:
    raise SystemExit(
        "ERROR: Ningún SVG pudo ser procesado."
    )


# ============================================================
# POSICIONES
# ============================================================

positions = []

count = len(icons)

for index in range(count):

    angle = (
        -math.pi / 2
        + (2 * math.pi * index / count)
    )

    x = CENTER_X + RADIUS_X * math.cos(angle)
    y = CENTER_Y + RADIUS_Y * math.sin(angle)

    positions.append(
        {
            "x": x,
            "y": y,
            "angle": math.degrees(angle),
        }
    )


# ============================================================
# CREAR SVG
# ============================================================

svg_parts = []

svg_parts.append(
    f'''<?xml version="1.0" encoding="UTF-8"?>
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
>
'''
)


# ============================================================
# ESTILOS
# ============================================================

svg_parts.append(
    """
<style>
    .technology-label {
        font-family: Arial, Helvetica, sans-serif;
        fill: #ffffff;
        font-size: 13px;
        font-weight: 600;
        text-anchor: middle;
    }

    .technology-icon {
        transform-box: fill-box;
        transform-origin: center;
    }

    .technology-orbit {
        transform-origin: 450px 210px;
    }

    @media (prefers-reduced-motion: reduce) {
        .technology-orbit {
            animation: none;
        }
    }
</style>
"""
)


# ============================================================
# FONDO
# ============================================================

svg_parts.append(
    """
<rect
    x="0"
    y="0"
    width="900"
    height="420"
    rx="20"
    fill="#0d1117"
/>
"""
)


# ============================================================
# CÍRCULO ORBITAL DECORATIVO
# ============================================================

svg_parts.append(
    f'''
<ellipse
    cx="{CENTER_X}"
    cy="{CENTER_Y}"
    rx="{RADIUS_X}"
    ry="{RADIUS_Y}"
    fill="none"
    stroke="#30363d"
    stroke-width="1.5"
    stroke-dasharray="5 8"
    opacity="0.8"
/>
'''
)


# ============================================================
# GRUPO PRINCIPAL
# ============================================================

svg_parts.append(
    f'''
<g
    class="technology-orbit"
>
'''
)

# Animación mediante SMIL.
svg_parts.append(
    f'''
<animateTransform
    attributeName="transform"
    type="rotate"
    from="0 {CENTER_X} {CENTER_Y}"
    to="360 {CENTER_X} {CENTER_Y}"
    dur="{ANIMATION_DURATION}s"
    repeatCount="indefinite"
/>
'''
)


# ============================================================
# ICONOS
# ============================================================

for index, icon in enumerate(icons):

    position = positions[index]

    x = position["x"]
    y = position["y"]

    viewbox = icon["viewbox"]

    vb_x, vb_y, vb_width, vb_height = viewbox

    # Evitamos divisiones por cero.
    if vb_width <= 0:
        vb_width = 100

    if vb_height <= 0:
        vb_height = 100

    # Calculamos una escala que permita que todos
    # los logos tengan aproximadamente el mismo tamaño.
    scale = min(
        ICON_SIZE / vb_width,
        ICON_SIZE / vb_height
    )

    # Convertimos el centro del icono a coordenadas.
    icon_x = x - (vb_width * scale) / 2
    icon_y = y - (vb_height * scale) / 2

    svg_parts.append(
        f'''
<g
    transform="
        translate({icon_x:.2f} {icon_y:.2f})
        scale({scale:.5f})
    "
>
'''
    )

    # Fondo circular detrás del icono.
    svg_parts.append(
        f'''
<circle
    cx="{vb_width / 2:.2f}"
    cy="{vb_height / 2:.2f}"
    r="{min(vb_width, vb_height) * 0.46:.2f}"
    fill="#161b22"
    stroke="#30363d"
    stroke-width="{1 / scale:.3f}"
    opacity="0.95"
/>
'''
    )

    # SVG anidado para conservar el viewBox original.
    svg_parts.append(
        f'''
<svg
    x="0"
    y="0"
    width="{vb_width}"
    height="{vb_height}"
    viewBox="{vb_x} {vb_y} {vb_width} {vb_height}"
    preserveAspectRatio="xMidYMid meet"
>
'''
    )

    svg_parts.append(icon["content"])

    svg_parts.append(
        """
</svg>
</g>
"""
    )


svg_parts.append("</g>")


# ============================================================
# TÍTULO
# ============================================================

svg_parts.append(
    f'''
<text
    x="{CENTER_X}"
    y="35"
    class="technology-label"
    font-size="20"
>
    Technologies &amp; Tools
</text>
'''
)


# ============================================================
# CERRAR SVG
# ============================================================

svg_parts.append("</svg>")


# ============================================================
# ESCRIBIR ARCHIVO
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE.write_text(
    "\n".join(svg_parts),
    encoding="utf-8"
)

print(
    f"Generated {OUTPUT_FILE} "
    f"using {len(icons)} technology icons."
)

for icon in icons:
    print(f"  - {icon['name']}.svg")
