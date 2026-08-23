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
CENTER_Y = 220

# Radio visual de la esfera
SPHERE_RADIUS_X = 155
SPHERE_RADIUS_Y = 145

# Tamaño de los iconos
ICON_SIZE = 58

# Número de posiciones de animación.
# Más frames = movimiento más fluido, pero SVG más grande.
FRAME_COUNT = 96

# Duración de una vuelta completa
ANIMATION_DURATION = 18


# ============================================================
# LEER SVG
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

    result = []

    for child in list(root):

        result.append(
            ET.tostring(
                child,
                encoding="unicode"
            )
        )

    return "\n".join(result)


# ============================================================
# CARGAR TECNOLOGÍAS
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
            f"WARNING: error procesando "
            f"{svg_file.name}: {error}"
        )


if not icons:

    raise SystemExit(
        "No se pudo cargar ningún icono."
    )


print()
print("Tecnologías encontradas:")

for icon in icons:

    print(
        f"  - {icon['name']}.svg"
    )


# ============================================================
# DISTRIBUCIÓN FIBONACCI SOBRE UNA ESFERA
# ============================================================

def fibonacci_sphere(count):

    points = []

    if count == 1:

        return [
            (0.0, 0.0, 1.0)
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
# GENERAR LOS FRAMES
# ============================================================

frames = []


for frame_index in range(FRAME_COUNT):

    progress = (
        frame_index /
        FRAME_COUNT
    )

    angle_y = (
        progress *
        math.pi *
        2
    )

    # Pequeña inclinación de la esfera.
    angle_x = (
        math.radians(12) *
        math.sin(
            progress *
            math.pi *
            2
        )
    )

    angle_z = (
        math.radians(5) *
        math.sin(
            progress *
            math.pi *
            4
        )
    )


    frame_icons = []


    for index, icon in enumerate(icons):

        # ----------------------------------------------------
        # Cada logo tiene una pequeña fase propia.
        # Esto evita que todos parezcan estar en un único
        # plano.
        # ----------------------------------------------------

        phase = (
            index *
            0.17
        )

        point = base_points[index].copy()


        # Rotación global de la esfera.
        point = rotate_y(
            point,
            angle_y
        )


        # Inclinación.
        point = rotate_x(
            point,
            angle_x
        )


        # Pequeño movimiento adicional.
        point = rotate_z(
            point,
            angle_z
        )


        x3d, y3d, z3d = point


        # ----------------------------------------------------
        # PROYECCIÓN
        # ----------------------------------------------------

        x = (
            CENTER_X +
            x3d *
            SPHERE_RADIUS_X
        )

        y = (
            CENTER_Y +
            y3d *
            SPHERE_RADIUS_Y
        )


        # ----------------------------------------------------
        # PROFUNDIDAD
        #
        # z > 0 = delante
        # z < 0 = detrás
        # ----------------------------------------------------

        depth = (
            z3d + 1.0
        ) / 2.0


        # ----------------------------------------------------
        # PERSPECTIVA
        # ----------------------------------------------------

        scale = (
            0.58 +
            depth *
            0.42
        )


        # ----------------------------------------------------
        # OPACIDAD
        # ----------------------------------------------------

        opacity = (
            0.25 +
            depth *
            0.75
        )


        # Los elementos más alejados se hacen ligeramente
        # más transparentes.
        if z3d < -0.65:

            opacity *= 0.65


        # ----------------------------------------------------
        # TAMAÑO DEL ICONO
        # ----------------------------------------------------

        vb_x, vb_y, vb_width, vb_height = (
            icon["viewbox"]
        )


        if vb_width <= 0:
            vb_width = 100

        if vb_height <= 0:
            vb_height = 100


        rendered_width = (
            ICON_SIZE *
            scale
        )

        rendered_height = (
            ICON_SIZE *
            scale
        )


        # ----------------------------------------------------
        # GUARDAR FRAME
        # ----------------------------------------------------

        frame_icons.append(
            {
                "icon": icon,
                "x": x,
                "y": y,
                "z": z3d,
                "scale": scale,
                "opacity": opacity,
                "width": rendered_width,
                "height": rendered_height
            }
        )


    # --------------------------------------------------------
    # IMPORTANTE:
    #
    # Los logos de detrás se dibujan primero.
    # Los delanteros se dibujan después.
    # --------------------------------------------------------

    frame_icons.sort(
        key=lambda item: item["z"]
    )


    frames.append(
        frame_icons
    )


# ============================================================
# SVG
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
# TÍTULO
# ============================================================

svg.append(
    f'''
<text
    x="{CENTER_X}"
    y="38"
    fill="#ffffff"
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
# CONTENEDOR
# ============================================================

svg.append(
    '''
<g id="technology-sphere">
'''
)


# ============================================================
# CREAR LOS FRAMES
# ============================================================

for frame_index, frame_icons in enumerate(frames):

    # --------------------------------------------------------
    # Cada frame ocupa un pequeño intervalo de tiempo.
    # Solo uno permanece visible.
    # --------------------------------------------------------

    start = (
        frame_index /
        FRAME_COUNT
    )

    end = (
        (frame_index + 1) /
        FRAME_COUNT
    )


    # Animación discreta de opacidad.
    #
    # El frame aparece al comenzar su intervalo
    # y desaparece al terminar.
    #

    values = []

    key_times = []


    for i in range(FRAME_COUNT):

        time = (
            i /
            FRAME_COUNT
        )

        key_times.append(
            f"{time:.6f}"
        )


        if i == frame_index:

            values.append("1")

        else:

            values.append("0")


    # --------------------------------------------------------
    # Para evitar un instante vacío entre frames,
    # el frame anterior permanece visible hasta el siguiente.
    # --------------------------------------------------------

    if frame_index > 0:

        values[frame_index - 1] = "1"


    group = []

    group.append(
        f'''
<g
    opacity="{1 if frame_index == 0 else 0}"
    pointer-events="none"
>
'''
    )


    # --------------------------------------------------------
    # ICONOS DEL FRAME
    # --------------------------------------------------------

    for item in frame_icons:

        icon = item["icon"]

        x = item["x"]
        y = item["y"]

        scale = item["scale"]
        opacity = item["opacity"]

        width = item["width"]
        height = item["height"]

        vb_x, vb_y, vb_width, vb_height = (
            icon["viewbox"]
        )


        # ----------------------------------------------------
        # Posición del icono
        # ----------------------------------------------------

        left = (
            x -
            width / 2
        )

        top = (
            y -
            height / 2
        )


        group.append(
            f'''
<g
    transform="
        translate(
            {left:.2f}
            {top:.2f}
        )
        scale({scale:.4f})
    "
    opacity="{opacity:.3f}"
    filter="url(#shadow)"
>
'''
        )


        # ----------------------------------------------------
        # FONDO INDIVIDUAL
        # ----------------------------------------------------

        group.append(
            f'''
<circle
    cx="{width / (2 * scale):.2f}"
    cy="{height / (2 * scale):.2f}"
    r="{ICON_SIZE * 0.48:.2f}"
    fill="#161b22"
    opacity="0.92"
/>
'''
        )


        # ----------------------------------------------------
        # SVG ORIGINAL
        # ----------------------------------------------------

        group.append(
            f'''
<svg
    x="{(width / 2 - ICON_SIZE / 2) / scale:.2f}"
    y="{(height / 2 - ICON_SIZE / 2) / scale:.2f}"
    width="{ICON_SIZE / scale:.2f}"
    height="{ICON_SIZE / scale:.2f}"
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


        group.append(
            icon["content"]
        )


        group.append(
            '''
</svg>
</g>
'''
        )


    group.append(
        '''
<animate
    attributeName="opacity"
    values="'''
        +
        ";".join(values)
        +
        '''"
    keyTimes="'''
        +
        ";".join(key_times)
        +
        '''"
    dur="'''
        +
        str(ANIMATION_DURATION)
        +
        '''s"
    repeatCount="indefinite"
    calcMode="discrete"
/>
'''
    )


    group.append(
        '''
</g>
'''
    )


    svg.extend(group)


# ============================================================
# CERRAR ESFERA
# ============================================================

svg.append(
    '''
</g>
'''
)


# ============================================================
# TEXTO
# ============================================================

svg.append(
    f'''
<text
    x="{CENTER_X}"
    y="{HEIGHT - 20}"
    fill="#ffffff"
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
    "Technologies & Tools generado correctamente"
)

print(
    f"Iconos: {len(icons)}"
)

print(
    f"Frames: {FRAME_COUNT}"
)

print(
    f"Duración: {ANIMATION_DURATION} segundos"
)

print(
    f"Salida: {OUTPUT_FILE}"
)

print(
    "=============================================="
)
