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

SPHERE_RADIUS = 155
ICON_SIZE = 64

ANIMATION_DURATION = 18

BACKGROUND = "#0d1117"
TEXT_COLOR = "#ffffff"


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def get_svg_root(svg_text):
    return ET.fromstring(svg_text)


def get_viewbox(root):
    viewbox = root.attrib.get("viewBox")

    if viewbox:
        values = viewbox.replace(",", " ").split()

        if len(values) == 4:
            return [float(v) for v in values]

    width = root.attrib.get("width", "100")
    height = root.attrib.get("height", "100")

    def number(value):
        value = str(value).replace("px", "")

        try:
            return float(value)
        except ValueError:
            return 100.0

    return [
        0,
        0,
        number(width),
        number(height)
    ]


def get_svg_content(root):
    content = []

    for child in list(root):
        content.append(
            ET.tostring(
                child,
                encoding="unicode"
            )
        )

    return "\n".join(content)


# ============================================================
# LEER SVG
# ============================================================

svg_files = sorted(
    INPUT_DIR.glob("*.svg")
)

if not svg_files:
    raise SystemExit(
        f"No se encontraron archivos SVG en {INPUT_DIR}"
    )


icons = []

for svg_file in svg_files:

    try:

        source = svg_file.read_text(
            encoding="utf-8"
        )

        root = get_svg_root(source)

        icons.append(
            {
                "name": svg_file.stem,
                "viewbox": get_viewbox(root),
                "content": get_svg_content(root)
            }
        )

    except Exception as error:

        print(
            f"WARNING: no se pudo procesar "
            f"{svg_file}: {error}"
        )


if not icons:
    raise SystemExit(
        "No se pudo procesar ningún SVG."
    )


# ============================================================
# ESFERA DE FIBONACCI
# ============================================================

def fibonacci_sphere(count):

    points = []

    if count == 1:
        return [(0, 0, 1)]

    golden_angle = math.pi * (
        3 - math.sqrt(5)
    )

    for i in range(count):

        y = 1 - (
            2 * i / (count - 1)
        )

        radius = math.sqrt(
            max(
                0,
                1 - y * y
            )
        )

        theta = golden_angle * i

        x = math.cos(theta) * radius
        z = math.sin(theta) * radius

        points.append(
            (x, y, z)
        )

    return points


sphere_points = fibonacci_sphere(
    len(icons)
)


# ============================================================
# ROTACIONES 3D
# ============================================================

def rotate_y(point, angle):

    x, y, z = point

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    return (
        x * cos_a + z * sin_a,
        y,
        -x * sin_a + z * cos_a
    )


def rotate_x(point, angle):

    x, y, z = point

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    return (
        x,
        y * cos_a - z * sin_a,
        y * sin_a + z * cos_a
    )


def rotate_z(point, angle):

    x, y, z = point

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    return (
        x * cos_a - y * sin_a,
        x * sin_a + y * cos_a,
        z
    )


# ============================================================
# PARÁMETROS DE ANIMACIÓN
# ============================================================

FRAME_COUNT = 96

key_times = []

for frame in range(FRAME_COUNT):

    key_times.append(
        frame / (FRAME_COUNT - 1)
    )

key_times_string = ";".join(
    f"{value:.5f}"
    for value in key_times
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
    """
<defs>

    <filter
        id="shadow"
        x="-100%"
        y="-100%"
        width="300%"
        height="300%"
    >
        <feDropShadow
            dx="0"
            dy="3"
            stdDeviation="4"
            flood-color="#000000"
            flood-opacity="0.45"
        />
    </filter>

</defs>
"""
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
    fill="{TEXT_COLOR}"
    font-family="Arial, Helvetica, sans-serif"
    font-size="20"
    font-weight="600"
    text-anchor="middle"
>
    Technologies &amp; Tools
</text>
'''
)


# ============================================================
# GENERAR CADA LOGO DE FORMA INDEPENDIENTE
# ============================================================

for index, icon in enumerate(icons):

    vb_x, vb_y, vb_width, vb_height = (
        icon["viewbox"]
    )

    if vb_width <= 0:
        vb_width = 100

    if vb_height <= 0:
        vb_height = 100


    # --------------------------------------------------------
    # POSICIONES DE LA ESFERA
    # --------------------------------------------------------

    x_values = []
    y_values = []
    scale_values = []
    opacity_values = []


    # Pequeña diferencia de fase para evitar que todos
    # los logos parezcan moverse exactamente igual.
    phase = (
        index * 0.37
    )


    for frame in range(FRAME_COUNT):

        progress = (
            frame / (FRAME_COUNT - 1)
        )

        angle = (
            progress * math.pi * 2
            + phase
        )


        point = sphere_points[index]


        # Rotación principal.
        point = rotate_y(
            point,
            angle
        )


        # Segunda rotación para producir una
        # sensación más tridimensional.
        tilt = (
            math.radians(14)
            * math.sin(
                angle * 0.5
            )
        )

        point = rotate_x(
            point,
            tilt
        )


        # Pequeña rotación adicional.
        point = rotate_z(
            point,
            math.radians(5)
        )


        x3d, y3d, z3d = point


        # ----------------------------------------------------
        # PROYECCIÓN 3D
        # ----------------------------------------------------

        x = (
            CENTER_X
            + x3d * SPHERE_RADIUS
        )

        y = (
            CENTER_Y
            + y3d * SPHERE_RADIUS
        )


        # ----------------------------------------------------
        # PROFUNDIDAD
        # ----------------------------------------------------

        depth = (
            z3d + 1
        ) / 2


        # ----------------------------------------------------
        # ESCALA
        # ----------------------------------------------------

        scale = (
            0.52
            + depth * 0.48
        )


        # ----------------------------------------------------
        # OPACIDAD
        # ----------------------------------------------------

        opacity = (
            0.30
            + depth * 0.70
        )


        x_values.append(
            f"{x:.2f}"
        )

        y_values.append(
            f"{y:.2f}"
        )

        scale_values.append(
            f"{scale:.3f}"
        )

        opacity_values.append(
            f"{opacity:.3f}"
        )


    # --------------------------------------------------------
    # POSICIÓN INICIAL
    # --------------------------------------------------------

    initial_x = float(
        x_values[0]
    )

    initial_y = float(
        y_values[0]
    )

    initial_scale = float(
        scale_values[0]
    )

    initial_opacity = float(
        opacity_values[0]
    )


    icon_size = (
        ICON_SIZE
        * initial_scale
    )


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


    # --------------------------------------------------------
    # GRUPO DEL LOGO
    # --------------------------------------------------------

    svg.append(
        f'''
<g
    transform="
        translate(
            {initial_x:.2f}
            {initial_y:.2f}
        )
    "
    opacity="{initial_opacity:.3f}"
    filter="url(#shadow)"
>
'''
    )


    # --------------------------------------------------------
    # CÍRCULO INDIVIDUAL DEL LOGO
    # --------------------------------------------------------

    svg.append(
        f'''
<circle
    cx="0"
    cy="0"
    r="{ICON_SIZE * 0.56:.2f}"
    fill="#161b22"
    stroke="#30363d"
    stroke-width="1"
    opacity="0.95"
/>
'''
    )


    # --------------------------------------------------------
    # CONTENEDOR DEL SVG
    # --------------------------------------------------------

    svg.append(
        f'''
<g
    transform="
        translate(
            {-rendered_width / 2:.2f}
            {-rendered_height / 2:.2f}
        )
        scale({initial_scale:.4f})
    "
>
'''
    )


    svg.append(
        f'''
<svg
    x="0"
    y="0"
    width="{vb_width}"
    height="{vb_height}"
    viewBox="
        {vb_x}
        {vb_y}
        {vb_width}
        {vb_height}
    "
    preserveAspectRatio="xMidYMid meet"
>
'''
    )


    svg.append(
        icon["content"]
    )


    svg.append(
        """
</svg>
</g>
"""
    )


    # ========================================================
    # ANIMACIÓN DE POSICIÓN
    # ========================================================

    svg.append(
        f'''
<animate
    attributeName="x"
    values="{';'.join(x_values)}"
    keyTimes="{key_times_string}"
    dur="{ANIMATION_DURATION}s"
    repeatCount="indefinite"
    calcMode="linear"
/>
'''
    )

    svg.append(
        f'''
<animate
    attributeName="y"
    values="{';'.join(y_values)}"
    keyTimes="{key_times_string}"
    dur="{ANIMATION_DURATION}s"
    repeatCount="indefinite"
    calcMode="linear"
/>
'''
    )


    # ========================================================
    # ANIMACIÓN DE ESCALA
    # ========================================================

    svg.append(
        f'''
<animateTransform
    attributeName="transform"
    type="scale"
    values="{' ; '.join(scale_values)}"
    keyTimes="{key_times_string}"
    dur="{ANIMATION_DURATION}s"
    repeatCount="indefinite"
    calcMode="linear"
/>
'''
    )


    # ========================================================
    # ANIMACIÓN DE OPACIDAD
    # ========================================================

    svg.append(
        f'''
<animate
    attributeName="opacity"
    values="{' ; '.join(opacity_values)}"
    keyTimes="{key_times_string}"
    dur="{ANIMATION_DURATION}s"
    repeatCount="indefinite"
    calcMode="linear"
/>
'''
    )


    svg.append(
        """
</g>
"""
    )


# ============================================================
# TEXTO INFERIOR
# ============================================================

svg.append(
    f'''
<text
    x="{CENTER_X}"
    y="{HEIGHT - 20}"
    fill="{TEXT_COLOR}"
    font-family="Arial, Helvetica, sans-serif"
    font-size="11"
    font-weight="500"
    text-anchor="middle"
    opacity="0.65"
>
    C# · .NET · SQL Server · Docker · JavaScript · Python · Dart · Flutter · Git · Postman · VS Code
</text>
'''
)


# ============================================================
# CERRAR SVG
# ============================================================

svg.append(
    "</svg>"
)


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
    "=============================================="
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
    "Animación: esfera 3D independiente por logo"
)

print(
    "=============================================="
)
