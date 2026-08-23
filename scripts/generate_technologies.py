from pathlib import Path
import xml.etree.ElementTree as ET
import math


# ============================================================
# CONFIGURACIÓN
# ============================================================

INPUT_DIR = Path("assets/technologies")
OUTPUT_FILE = Path("assets/technologies.svg")

WIDTH = 900
HEIGHT = 460

CENTER_X = WIDTH / 2
CENTER_Y = HEIGHT / 2

SPHERE_RADIUS_X = 155
SPHERE_RADIUS_Y = 145

ICON_SIZE = 58

# Más puntos de animación para conseguir un movimiento fluido.
FRAME_COUNT = 180

# Una vuelta completa.
ANIMATION_DURATION = 18


# ============================================================
# CARGAR SVG
# ============================================================

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
# LEER TECNOLOGÍAS
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

        source = svg_file.read_text(
            encoding="utf-8"
        )

        root = ET.fromstring(source)

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
            f"{svg_file.name}: {error}"
        )


if not icons:

    raise SystemExit(
        "No se pudo cargar ningún icono."
    )


# ============================================================
# ESFERA DE FIBONACCI
# ============================================================

def fibonacci_sphere(count):

    points = []

    if count == 1:

        return [
            [0.0, 0.0, 1.0]
        ]

    golden_angle = (
        math.pi *
        (3.0 - math.sqrt(5.0))
    )

    for i in range(count):

        y = 1.0 - (
            2.0 * i /
            (count - 1)
        )

        radius = math.sqrt(
            max(
                0.0,
                1.0 - y * y
            )
        )

        theta = (
            golden_angle * i
        )

        x = (
            math.cos(theta) *
            radius
        )

        z = (
            math.sin(theta) *
            radius
        )

        points.append(
            [x, y, z]
        )

    return points


base_points = fibonacci_sphere(
    len(icons)
)


# ============================================================
# ROTACIONES 3D
# ============================================================

def rotate_y(point, angle):

    x, y, z = point

    c = math.cos(angle)
    s = math.sin(angle)

    return [
        x * c + z * s,
        y,
        -x * s + z * c
    ]


def rotate_x(point, angle):

    x, y, z = point

    c = math.cos(angle)
    s = math.sin(angle)

    return [
        x,
        y * c - z * s,
        y * s + z * c
    ]


def rotate_z(point, angle):

    x, y, z = point

    c = math.cos(angle)
    s = math.sin(angle)

    return [
        x * c - y * s,
        x * s + y * c,
        z
    ]


# ============================================================
# GENERAR VALORES DE ANIMACIÓN
# ============================================================

def generate_animation_values(point, phase):

    x_values = []
    y_values = []
    scale_values = []
    opacity_values = []

    for frame in range(FRAME_COUNT):

        progress = (
            frame /
            FRAME_COUNT
        )

        # Rotación principal.
        angle_y = (
            progress *
            math.pi *
            2
            + phase
        )

        # Inclinación vertical.
        #
        # Al contrario que la versión anterior,
        # la inclinación no es fija.
        # Esto hace que incluso los puntos situados
        # inicialmente arriba y abajo se desplacen.
        angle_x = (
            math.radians(22)
            * math.sin(
                progress *
                math.pi *
                2
            )
        )

        # Rotación secundaria.
        angle_z = (
            math.radians(9)
            * math.sin(
                progress *
                math.pi *
                2
                + phase
            )
        )

        rotated = rotate_y(
            point,
            angle_y
        )

        rotated = rotate_x(
            rotated,
            angle_x
        )

        rotated = rotate_z(
            rotated,
            angle_z
        )

        x3d, y3d, z3d = rotated

        # ----------------------------------------------------
        # POSICIÓN
        # ----------------------------------------------------

        x = (
            CENTER_X
            + x3d *
            SPHERE_RADIUS_X
        )

        y = (
            CENTER_Y
            + y3d *
            SPHERE_RADIUS_Y
        )

        # ----------------------------------------------------
        # PROFUNDIDAD
        # ----------------------------------------------------

        depth = (
            z3d + 1.0
        ) / 2.0

        # ----------------------------------------------------
        # PERSPECTIVA
        # ----------------------------------------------------

        scale = (
            0.55
            + depth * 0.45
        )

        # ----------------------------------------------------
        # OPACIDAD
        # ----------------------------------------------------

        opacity = (
            0.28
            + depth * 0.72
        )

        # Los elementos muy alejados se atenúan.
        if z3d < -0.65:

            opacity *= 0.72

        x_values.append(
            f"{x:.2f}"
        )

        y_values.append(
            f"{y:.2f}"
        )

        scale_values.append(
            f"{scale:.4f}"
        )

        opacity_values.append(
            f"{opacity:.4f}"
        )

    return (
        ";".join(x_values),
        ";".join(y_values),
        ";".join(scale_values),
        ";".join(opacity_values)
    )


# ============================================================
# KEY TIMES
# ============================================================

key_times = []

for frame in range(FRAME_COUNT):

    key_times.append(
        f"{frame / FRAME_COUNT:.6f}"
    )

key_times = ";".join(
    key_times
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
    '''
<defs>

    <filter
        id="technology-shadow"
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
            flood-opacity="0.40"
        />

    </filter>

</defs>
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
    fill="#0d1117"
/>
'''
)


# ============================================================
# LOGOS
# ============================================================

for index, icon in enumerate(icons):

    point = base_points[index]

    # Cada logo tiene una fase diferente.
    phase = (
        index *
        0.43
    )

    (
        x_values,
        y_values,
        scale_values,
        opacity_values
    ) = generate_animation_values(
        point,
        phase
    )

    # --------------------------------------------------------
    # VIEWBOX
    # --------------------------------------------------------

    vb_x, vb_y, vb_width, vb_height = (
        icon["viewbox"]
    )

    if vb_width <= 0:
        vb_width = 100

    if vb_height <= 0:
        vb_height = 100


    # --------------------------------------------------------
    # POSICIÓN INICIAL
    # --------------------------------------------------------

    initial_point = point.copy()

    initial_point = rotate_y(
        initial_point,
        phase
    )

    initial_point = rotate_x(
        initial_point,
        0
    )

    initial_point = rotate_z(
        initial_point,
        0
    )

    initial_x3d, initial_y3d, initial_z3d = (
        initial_point
    )

    initial_x = (
        CENTER_X
        + initial_x3d *
        SPHERE_RADIUS_X
    )

    initial_y = (
        CENTER_Y
        + initial_y3d *
        SPHERE_RADIUS_Y
    )

    initial_depth = (
        initial_z3d + 1
    ) / 2

    initial_scale = (
        0.55
        + initial_depth * 0.45
    )

    initial_opacity = (
        0.28
        + initial_depth * 0.72
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
    opacity="{initial_opacity:.4f}"
    filter="url(#technology-shadow)"
>
'''
    )


    # --------------------------------------------------------
    # FONDO DEL ICONO
    # --------------------------------------------------------

    svg.append(
        f'''
<circle
    cx="0"
    cy="0"
    r="{ICON_SIZE * 0.52:.2f}"
    fill="#161b22"
    stroke="#30363d"
    stroke-width="1"
    opacity="0.92"
/>
'''
    )


    # --------------------------------------------------------
    # ICONO
    # --------------------------------------------------------

    svg.append(
        f'''
<svg
    x="{-ICON_SIZE / 2:.2f}"
    y="{-ICON_SIZE / 2:.2f}"
    width="{ICON_SIZE}"
    height="{ICON_SIZE}"
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
        '''
</svg>
'''
    )


    # ========================================================
    # ANIMACIÓN DE POSICIÓN X
    # ========================================================

    svg.append(
        f'''
<animate
    attributeName="x"
    values="{x_values}"
    keyTimes="{key_times}"
    dur="{ANIMATION_DURATION}s"
    repeatCount="indefinite"
    calcMode="spline"
    keySplines="
        0.42 0 0.58 1;
        0.42 0 0.58 1;
        0.42 0 0.58 1;
        0.42 0 0.58 1
    "
/>
'''
    )


    # ========================================================
    # ANIMACIÓN DE POSICIÓN Y
    # ========================================================

    svg.append(
        f'''
<animate
    attributeName="y"
    values="{y_values}"
    keyTimes="{key_times}"
    dur="{ANIMATION_DURATION}s"
    repeatCount="indefinite"
    calcMode="linear"
/>
'''
    )


    # ========================================================
    # ESCALA
    # ========================================================

    svg.append(
        f'''
<animateTransform
    attributeName="transform"
    type="scale"
    values="{scale_values}"
    keyTimes="{key_times}"
    dur="{ANIMATION_DURATION}s"
    repeatCount="indefinite"
    calcMode="linear"
/>
'''
    )


    # ========================================================
    # OPACIDAD
    # ========================================================

    svg.append(
        f'''
<animate
    attributeName="opacity"
    values="{opacity_values}"
    keyTimes="{key_times}"
    dur="{ANIMATION_DURATION}s"
    repeatCount="indefinite"
    calcMode="linear"
/>
'''
    )


    svg.append(
        '''
</g>
'''
    )


# ============================================================
# CERRAR SVG
# ============================================================

svg.append(
    '''
</svg>
'''
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
    f"Iconos: {len(icons)}"
)

print(
    f"Frames de movimiento: {FRAME_COUNT}"
)

print(
    f"Duración: {ANIMATION_DURATION}s"
)

print(
    f"Salida: {OUTPUT_FILE}"
)

print(
    "Animación: esfera 3D continua por icono"
)

print(
    "=============================================="
)
