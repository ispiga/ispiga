from pathlib import Path
import xml.etree.ElementTree as ET
import math
import html


# ============================================================
# CONFIGURACIÓN
# ============================================================

INPUT_DIR = Path("assets/technologies")
OUTPUT_FILE = Path("assets/technologies.svg")

WIDTH = 900
HEIGHT = 460

CENTER_X = WIDTH / 2
CENTER_Y = HEIGHT / 2

# Tamaño máximo aproximado de la esfera.
SPHERE_RADIUS = 155

# Tamaño máximo de cada logo.
ICON_SIZE = 64

# Duración de una vuelta completa.
ANIMATION_DURATION = 20

# Fondo.
BACKGROUND = "#0d1117"

# Línea/esfera decorativa.
SPHERE_LINE = "#30363d"

# Color de los textos.
TEXT_COLOR = "#ffffff"


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def get_svg_root(svg_text):
    return ET.fromstring(svg_text)


def get_viewbox(root):
    """
    Obtiene el viewBox del SVG original.
    Si no existe, utiliza width y height.
    """

    viewbox = root.attrib.get("viewBox")

    if viewbox:
        values = viewbox.replace(",", " ").split()

        if len(values) == 4:
            return [float(value) for value in values]

    width = root.attrib.get("width", "100")
    height = root.attrib.get("height", "100")

    def parse_number(value):
        value = str(value).replace("px", "")

        try:
            return float(value)
        except ValueError:
            return 100.0

    return [
        0,
        0,
        parse_number(width),
        parse_number(height),
    ]


def get_svg_content(root):
    """
    Obtiene el contenido interno del SVG original.
    """

    content = []

    for child in list(root):
        content.append(
            ET.tostring(
                child,
                encoding="unicode"
            )
        )

    return "\n".join(content)


def escape_xml(text):
    return html.escape(text, quote=True)


# ============================================================
# LEER LOS SVG
# ============================================================

svg_files = sorted(
    INPUT_DIR.glob("*.svg")
)

if not svg_files:
    raise SystemExit(
        f"No se encontraron SVG en {INPUT_DIR}"
    )


icons = []

for svg_file in svg_files:

    try:

        svg_text = svg_file.read_text(
            encoding="utf-8"
        )

        root = get_svg_root(svg_text)

        viewbox = get_viewbox(root)

        content = get_svg_content(root)

        icons.append(
            {
                "name": svg_file.stem,
                "viewbox": viewbox,
                "content": content,
            }
        )

    except Exception as error:

        print(
            f"WARNING: No se pudo procesar "
            f"{svg_file}: {error}"
        )


if not icons:
    raise SystemExit(
        "No se pudo procesar ningún SVG."
    )


print(
    f"Encontrados {len(icons)} iconos:"
)

for icon in icons:
    print(
        f"  - {icon['name']}.svg"
    )


# ============================================================
# DISTRIBUCIÓN SOBRE UNA ESFERA
# ============================================================

def fibonacci_sphere(count):
    """
    Distribuye puntos aproximadamente de forma uniforme
    sobre la superficie de una esfera.

    Devuelve:
        [(x, y, z), ...]
    """

    points = []

    if count == 1:
        return [(0, 0, 1)]

    golden_angle = math.pi * (
        3 - math.sqrt(5)
    )

    for index in range(count):

        y = 1 - (
            2 * index / (count - 1)
        )

        radius = math.sqrt(
            max(
                0,
                1 - y * y
            )
        )

        theta = (
            golden_angle * index
        )

        x = (
            math.cos(theta)
            * radius
        )

        z = (
            math.sin(theta)
            * radius
        )

        points.append(
            (
                x,
                y,
                z
            )
        )

    return points


sphere_points = fibonacci_sphere(
    len(icons)
)


# ============================================================
# TRANSFORMACIÓN 3D
# ============================================================

def rotate_y(point, angle):
    """
    Rotación alrededor del eje Y.
    """

    x, y, z = point

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    new_x = (
        x * cos_a
        + z * sin_a
    )

    new_z = (
        -x * sin_a
        + z * cos_a
    )

    return (
        new_x,
        y,
        new_z
    )


def rotate_x(point, angle):
    """
    Rotación alrededor del eje X.
    """

    x, y, z = point

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    new_y = (
        y * cos_a
        - z * sin_a
    )

    new_z = (
        y * sin_a
        + z * cos_a
    )

    return (
        x,
        new_y,
        new_z
    )


# ============================================================
# CREAR SVG
# ============================================================

svg = []

svg.append(
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
# DEFINICIONES
# ============================================================

svg.append(
    f'''
<defs>

    <filter
        id="technology-shadow"
        x="-50%"
        y="-50%"
        width="200%"
        height="200%"
    >
        <feDropShadow
            dx="0"
            dy="3"
            stdDeviation="4"
            flood-color="#000000"
            flood-opacity="0.45"
        />
    </filter>

    <radialGradient
        id="sphere-gradient"
        cx="35%"
        cy="30%"
    >
        <stop
            offset="0%"
            stop-color="#21262d"
            stop-opacity="0.45"
        />

        <stop
            offset="70%"
            stop-color="#0d1117"
            stop-opacity="0.1"
        />

        <stop
            offset="100%"
            stop-color="#0d1117"
            stop-opacity="0"
        />
    </radialGradient>

</defs>
'''
)


# ============================================================
# ESTILOS
# ============================================================

svg.append(
    f'''
<style>

    .technology-label {{
        font-family:
            Arial,
            Helvetica,
            sans-serif;

        fill: {TEXT_COLOR};

        font-size: 20px;

        font-weight: 600;

        text-anchor: middle;
    }}

    .technology-name {{
        font-family:
            Arial,
            Helvetica,
            sans-serif;

        fill: {TEXT_COLOR};

        font-size: 11px;

        font-weight: 500;

        text-anchor: middle;
    }}

    .sphere {{
        transform-origin:
            {CENTER_X}px {CENTER_Y}px;
    }}

    @media (prefers-reduced-motion: reduce) {{
        .sphere {{
            animation: none;
        }}
    }}

</style>
'''
)


# ============================================================
# FONDO
# ============================================================

svg.append(
    f'''
<rect
    x="0"
    y="0"
    width="{WIDTH}"
    height="{HEIGHT}"
    rx="20"
    fill="{BACKGROUND}"
/>
'''
)


# ============================================================
# TÍTULO
# ============================================================

svg.append(
    f'''
<text
    x="{CENTER_X}"
    y="38"
    class="technology-label"
>
    Technologies &amp; Tools
</text>
'''
)


# ============================================================
# ESFERA DECORATIVA
# ============================================================

svg.append(
    f'''
<circle
    cx="{CENTER_X}"
    cy="{CENTER_Y + 8}"
    r="{SPHERE_RADIUS}"
    fill="url(#sphere-gradient)"
    stroke="{SPHERE_LINE}"
    stroke-width="1"
    opacity="0.35"
/>
'''
)


# ============================================================
# GRUPO DE ANIMACIÓN
# ============================================================

svg.append(
    f'''
<g
    class="sphere"
>
'''
)


# ============================================================
# ANIMACIÓN PRINCIPAL
# ============================================================

svg.append(
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
# GENERAR LOS LOGOS
# ============================================================

elements = []


for index, icon in enumerate(icons):

    x3d, y3d, z3d = sphere_points[index]

    # --------------------------------------------------------
    # Posición inicial
    # --------------------------------------------------------

    x = (
        CENTER_X
        + x3d * SPHERE_RADIUS
    )

    y = (
        CENTER_Y
        + y3d * SPHERE_RADIUS
    )

    # --------------------------------------------------------
    # Profundidad
    #
    # z =  1 -> delante
    # z =  0 -> lateral
    # z = -1 -> detrás
    # --------------------------------------------------------

    depth = (
        z3d + 1
    ) / 2

    # --------------------------------------------------------
    # Escala según profundidad
    # --------------------------------------------------------

    scale = (
        0.58
        + depth * 0.42
    )

    # --------------------------------------------------------
    # Opacidad según profundidad
    # --------------------------------------------------------

    opacity = (
        0.35
        + depth * 0.65
    )

    # --------------------------------------------------------
    # Tamaño
    # --------------------------------------------------------

    icon_size = (
        ICON_SIZE * scale
    )

    # --------------------------------------------------------
    # ViewBox original
    # --------------------------------------------------------

    vb_x, vb_y, vb_width, vb_height = (
        icon["viewbox"]
    )

    if vb_width <= 0:
        vb_width = 100

    if vb_height <= 0:
        vb_height = 100

    icon_scale = min(
        icon_size / vb_width,
        icon_size / vb_height
    )

    rendered_width = (
        vb_width * icon_scale
    )

    rendered_height = (
        vb_height * icon_scale
    )

    icon_x = (
        x
        - rendered_width / 2
    )

    icon_y = (
        y
        - rendered_height / 2
    )

    # --------------------------------------------------------
    # Crear elemento
    # --------------------------------------------------------

    element = f'''
<g
    opacity="{opacity:.3f}"
    filter="url(#technology-shadow)"
    data-depth="{z3d:.4f}"
    data-index="{index}"
    transform="
        translate({icon_x:.2f} {icon_y:.2f})
    "
>

    <circle
        cx="{rendered_width / 2:.2f}"
        cy="{rendered_height / 2:.2f}"
        r="{min(rendered_width, rendered_height) * 0.48:.2f}"
        fill="#161b22"
        stroke="#30363d"
        stroke-width="1"
    />

    <svg
        x="0"
        y="0"
        width="{rendered_width:.2f}"
        height="{rendered_height:.2f}"
        viewBox="{vb_x} {vb_y} {vb_width} {vb_height}"
        preserveAspectRatio="xMidYMid meet"
    >
        {icon["content"]}
    </svg>

</g>
'''

    elements.append(
        (
            z3d,
            element
        )
    )


# ============================================================
# ORDENAR POR PROFUNDIDAD
# ============================================================

# Los elementos traseros se dibujan primero.
elements.sort(
    key=lambda item: item[0]
)


for _, element in elements:
    svg.append(element)


# ============================================================
# CERRAR ESFERA
# ============================================================

svg.append("</g>")


# ============================================================
# TEXTO INFERIOR
# ============================================================

svg.append(
    f'''
<text
    x="{CENTER_X}"
    y="{HEIGHT - 22}"
    class="technology-name"
    opacity="0.7"
>
    C# · .NET · SQL Server · Docker · JavaScript · Python · Dart · Flutter · Git · Postman · VS Code
</text>
'''
)


# ============================================================
# CERRAR SVG
# ============================================================

svg.append("</svg>")


# ============================================================
# GUARDAR
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE.write_text(
    "\n".join(svg),
    encoding="utf-8"
)


print()
print(
    "============================================"
)

print(
    "Technologies & Tools generado correctamente."
)

print(
    f"Archivo: {OUTPUT_FILE}"
)

print(
    f"Iconos utilizados: {len(icons)}"
)

print(
    "============================================"
)
