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

SPHERE_RADIUS_X = 165
SPHERE_RADIUS_Y = 145

ICON_SIZE = 58

# Número de estados de la animación.
# 120 ofrece un movimiento bastante más fluido
# sin hacer el SVG excesivamente grande.
FRAME_COUNT = 120

# Tiempo de una vuelta completa.
ANIMATION_DURATION = 16


# ============================================================
# SVG
# ============================================================

def get_viewbox(root):

    viewbox = root.attrib.get("viewBox")

    if viewbox:

        values = viewbox.replace(",", " ").split()

        if len(values) == 4:

            return [
                float(v)
                for v in values
            ]

    width = root.attrib.get(
        "width",
        "100"
    )

    height = root.attrib.get(
        "height",
        "100"
    )

    def number(value):

        value = str(
            value
        ).replace(
            "px",
            ""
        )

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

    return "\n".join(
        content
    )


# ============================================================
# CARGAR ICONOS
# ============================================================

svg_files = sorted(
    INPUT_DIR.glob("*.svg")
)

if not svg_files:

    raise SystemExit(
        f"No hay SVG en {INPUT_DIR}"
    )


icons = []


for svg_file in svg_files:

    try:

        source = svg_file.read_text(
            encoding="utf-8"
        )

        root = ET.fromstring(
            source
        )

        icons.append(
            {
                "name": svg_file.stem,
                "viewbox": get_viewbox(root),
                "content": get_svg_content(root)
            }
        )

    except Exception as error:

        print(
            f"ERROR: {svg_file.name}: {error}"
        )


if not icons:

    raise SystemExit(
        "No se pudo cargar ningún SVG."
    )


print(
    f"Iconos encontrados: {len(icons)}"
)


# ============================================================
# DISTRIBUCIÓN SOBRE ESFERA
# ============================================================

def fibonacci_sphere(count):

    points = []

    golden_angle = (
        math.pi *
        (3 - math.sqrt(5))
    )

    for i in range(count):

        # Evitamos exactamente los polos.
        y = (
            1 -
            2 *
            (i + 0.5) /
            count
        )

        radius = math.sqrt(
            max(
                0,
                1 -
                y * y
            )
        )

        theta = (
            golden_angle *
            (i + 0.5)
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
            [
                x,
                y,
                z
            ]
        )

    return points


points = fibonacci_sphere(
    len(icons)
)


# ============================================================
# ROTACIÓN 3D
# ============================================================

def rotate_y(
    x,
    y,
    z,
    angle
):

    c = math.cos(angle)
    s = math.sin(angle)

    return (
        x * c + z * s,
        y,
        -x * s + z * c
    )


def rotate_x(
    x,
    y,
    z,
    angle
):

    c = math.cos(angle)
    s = math.sin(angle)

    return (
        x,
        y * c - z * s,
        y * s + z * c
    )


def rotate_z(
    x,
    y,
    z,
    angle
):

    c = math.cos(angle)
    s = math.sin(angle)

    return (
        x * c - y * s,
        x * s + y * c,
        z
    )


# ============================================================
# CALCULAR TRAYECTORIA DE CADA LOGO
# ============================================================

trajectories = []


for index, point in enumerate(points):

    trajectory = []

    x0, y0, z0 = point

    # Cada logo tiene una pequeña diferencia de fase.
    phase = (
        index *
        0.23
    )

    for frame in range(
        FRAME_COUNT
    ):

        progress = (
            frame /
            FRAME_COUNT
        )

        # ----------------------------------------------------
        # ROTACIÓN PRINCIPAL
        # ----------------------------------------------------

        angle_y = (
            progress *
            math.pi *
            2
            +
            phase
        )

        # ----------------------------------------------------
        # INCLINACIÓN DE LA ESFERA
        #
        # Cambia continuamente, evitando que los logos
        # situados inicialmente arriba/abajo se queden fijos.
        # ----------------------------------------------------

        angle_x = (
            math.radians(18)
            +
            math.sin(
                progress *
                math.pi *
                2
            )
            *
            math.radians(10)
        )

        # ----------------------------------------------------
        # PEQUEÑA ROTACIÓN SECUNDARIA
        # ----------------------------------------------------

        angle_z = (
            math.sin(
                progress *
                math.pi *
                2
                +
                phase
            )
            *
            math.radians(8)
        )

        x, y, z = rotate_y(
            x0,
            y0,
            z0,
            angle_y
        )

        x, y, z = rotate_x(
            x,
            y,
            z,
            angle_x
        )

        x, y, z = rotate_z(
            x,
            y,
            z,
            angle_z
        )

        # ----------------------------------------------------
        # PROYECCIÓN 3D
        # ----------------------------------------------------

        screen_x = (
            CENTER_X +
            x *
            SPHERE_RADIUS_X
        )

        screen_y = (
            CENTER_Y +
            y *
            SPHERE_RADIUS_Y
        )

        # ----------------------------------------------------
        # PROFUNDIDAD
        # ----------------------------------------------------

        depth = (
            z + 1
        ) / 2

        # ----------------------------------------------------
        # PERSPECTIVA
        # ----------------------------------------------------

        scale = (
            0.55 +
            depth *
            0.45
        )

        # ----------------------------------------------------
        # OPACIDAD
        # ----------------------------------------------------

        opacity = (
            0.30 +
            depth *
            0.70
        )

        trajectory.append(
            {
                "x": screen_x,
                "y": screen_y,
                "z": z,
                "scale": scale,
                "opacity": opacity
            }
        )

    trajectories.append(
        trajectory
    )


# ============================================================
# KEY TIMES
# ============================================================

key_times = ";".join(
    f"{i / FRAME_COUNT:.6f}"
    for i in range(
        FRAME_COUNT
    )
)


# ============================================================
# GENERAR SVG
# ============================================================

svg = []


svg.append(
    '''<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width="900"
    height="460"
    viewBox="0 0 900 460"
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
        id="tech-shadow"
        x="-100%"
        y="-100%"
        width="300%"
        height="300%"
    >

        <feDropShadow
            dx="0"
            dy="3"
            stdDeviation="3"
            flood-color="#000000"
            flood-opacity="0.45"
        />

    </filter>

</defs>
'''
)


# ============================================================
# FONDO
# ============================================================

svg.append(
    '''
<rect
    x="0"
    y="0"
    width="900"
    height="460"
    rx="20"
    fill="#0d1117"
/>
'''
)


# ============================================================
# CREAR LOGOS
# ============================================================

for index, icon in enumerate(icons):

    trajectory = trajectories[index]

    vb_x, vb_y, vb_width, vb_height = (
        icon["viewbox"]
    )

    # --------------------------------------------------------
    # VALORES
    # --------------------------------------------------------

    x_values = ";".join(
        f"{p['x']:.2f}"
        for p in trajectory
    )

    y_values = ";".join(
        f"{p['y']:.2f}"
        for p in trajectory
    )

    scale_values = ";".join(
        f"{p['scale']:.4f}"
        for p in trajectory
    )

    opacity_values = ";".join(
        f"{p['opacity']:.4f}"
        for p in trajectory
    )


    first = trajectory[0]


    # ========================================================
    # GRUPO EXTERIOR
    #
    # Este grupo SOLO controla la posición.
    # ========================================================

    svg.append(
        f'''
<g
    transform="
        translate(
            {first['x']:.2f}
            {first['y']:.2f}
        )
    "
    opacity="{first['opacity']:.4f}"
    filter="url(#tech-shadow)"
>
'''
    )


    # ========================================================
    # GRUPO INTERIOR
    #
    # Este grupo SOLO controla escala.
    # ========================================================

    svg.append(
        f'''
<g
    transform="
        scale(
            {first['scale']:.4f}
        )
    "
>
'''
    )


    # ========================================================
    # ICONO
    # ========================================================

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


    svg.append(
        '''
</g>
'''
    )


    # ========================================================
    # POSICIÓN X
    # ========================================================

    svg.append(
        f'''
<animate
    attributeName="x"
    values="{x_values}"
    keyTimes="{key_times}"
    dur="{ANIMATION_DURATION}s"
    repeatCount="indefinite"
    calcMode="linear"
/>
'''
    )


    # ========================================================
    # POSICIÓN Y
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
# GUARDAR
# ============================================================

svg.append(
    '''
</svg>
'''
)


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
    "Technologies & Tools generado correctamente"
)
print(
    f"Iconos: {len(icons)}"
)
print(
    f"Frames: {FRAME_COUNT}"
)
print(
    f"Duración: {ANIMATION_DURATION}s"
)
print(
    f"Archivo: {OUTPUT_FILE}"
)
print(
    "Movimiento: esfera 3D continua"
)
print(
    "=============================================="
)
