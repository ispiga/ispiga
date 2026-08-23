from pathlib import Path
import io
import math

from PIL import Image, ImageDraw


# ============================================================
# CONFIGURACIÓN
# ============================================================

INPUT_DIR = Path("assets/technologies")
OUTPUT_FILE = Path("assets/technologies.gif")

# ------------------------------------------------------------
# Resolución REAL del GIF.
#
# Lo hacemos deliberadamente pequeño.
# GitHub lo ampliará visualmente en el README.
# ------------------------------------------------------------

WIDTH = 640
HEIGHT = 330

CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2

# Tamaño de la esfera
SPHERE_RADIUS_X = 145
SPHERE_RADIUS_Y = 125

# Tamaño máximo de los logos
ICON_SIZE = 46


# ============================================================
# ANIMACIÓN
# ============================================================

# 15 FPS es suficiente para una rotación suave y reduce
# considerablemente el tamaño del GIF.
FPS = 15

# Una vuelta completa cada 18 segundos.
DURATION = 18

FRAME_COUNT = FPS * DURATION


# ============================================================
# CALIDAD / COMPRESIÓN
# ============================================================

# Paleta GIF.
#
# 64 colores en lugar de 256 reduce muchísimo el tamaño.
# Los logos siguen teniendo buena apariencia porque son
# pequeños y normalmente tienen pocos colores.
COLORS = 64


# ============================================================
# FONDO
# ============================================================

BACKGROUND = (
    13,
    17,
    23,
    255
)


# ============================================================
# CARGAR CAIROSVG
# ============================================================

try:

    import cairosvg

except ImportError:

    raise SystemExit(
        "\n"
        "ERROR: CairoSVG no está instalado.\n\n"
        "Ejecuta:\n"
        "pip install pillow cairosvg\n"
    )


# ============================================================
# BUSCAR SVG
# ============================================================

svg_files = sorted(
    INPUT_DIR.glob("*.svg")
)


if not svg_files:

    raise SystemExit(
        f"No se encontraron SVG en {INPUT_DIR}"
    )


print(
    f"Encontrados {len(svg_files)} logos."
)


# ============================================================
# CONVERTIR SVG -> PNG
#
# Se hace solamente UNA VEZ por logo.
# No se vuelve a convertir en cada frame.
# ============================================================

icons = []


for svg_file in svg_files:

    try:

        png_data = cairosvg.svg2png(
            url=str(svg_file),
            output_width=ICON_SIZE * 3,
            output_height=ICON_SIZE * 3
        )


        image = Image.open(
            io.BytesIO(
                png_data
            )
        ).convert(
            "RGBA"
        )


        image = image.resize(
            (
                ICON_SIZE,
                ICON_SIZE
            ),
            Image.Resampling.LANCZOS
        )


        icons.append(
            {
                "name": svg_file.stem,
                "image": image
            }
        )


        print(
            f"  OK: {svg_file.name}"
        )


    except Exception as error:

        print(
            f"  ERROR: {svg_file.name}: {error}"
        )


if not icons:

    raise SystemExit(
        "No se pudo cargar ningún logo."
    )


# ============================================================
# DISTRIBUCIÓN SOBRE UNA ESFERA
# ============================================================

def fibonacci_sphere(
    count
):

    points = []

    golden_angle = (
        math.pi *
        (
            3 -
            math.sqrt(5)
        )
    )


    for i in range(
        count
    ):

        y = (
            1 -
            2 *
            (
                i + 0.5
            ) /
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
            i
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
            (
                x,
                y,
                z
            )
        )


    return points


points = fibonacci_sphere(
    len(icons)
)


# ============================================================
# ROTACIONES
# ============================================================

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
# CALCULAR POSICIONES DE UN FRAME
# ============================================================

def calculate_frame(
    frame_number
):

    progress = (
        frame_number /
        FRAME_COUNT
    )


    # --------------------------------------------------------
    # ROTACIÓN PRINCIPAL
    # --------------------------------------------------------

    rotation_y = (
        progress *
        math.pi *
        2
    )


    # --------------------------------------------------------
    # INCLINACIÓN
    #
    # Cambia ligeramente durante la vuelta para que ningún
    # logo quede permanentemente clavado en el eje vertical.
    # --------------------------------------------------------

    rotation_x = (
        math.radians(18)
        +
        math.sin(
            progress *
            math.pi *
            2
        )
        *
        math.radians(7)
    )


    rotation_z = (
        math.sin(
            progress *
            math.pi *
            2
        )
        *
        math.radians(4)
    )


    result = []


    for index, point in enumerate(
        points
    ):

        x, y, z = point


        # Pequeña diferencia de fase.
        phase = (
            index *
            0.17
        )


        x, y, z = rotate_y(
            x,
            y,
            z,
            rotation_y +
            phase
        )


        x, y, z = rotate_x(
            x,
            y,
            z,
            rotation_x
        )


        x, y, z = rotate_z(
            x,
            y,
            z,
            rotation_z
        )


        # ----------------------------------------------------
        # PROYECCIÓN
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
        # ESCALA
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
            0.35 +
            depth *
            0.65
        )


        result.append(
            {
                "index": index,
                "x": screen_x,
                "y": screen_y,
                "z": z,
                "scale": scale,
                "opacity": opacity
            }
        )


    # --------------------------------------------------------
    # PROFUNDIDAD:
    # atrás -> delante
    # --------------------------------------------------------

    result.sort(
        key=lambda item:
        item["z"]
    )


    return result


# ============================================================
# CREAR FRAME
# ============================================================

def create_frame(
    frame_number
):

    frame = Image.new(
        "RGBA",
        (
            WIDTH,
            HEIGHT
        ),
        BACKGROUND
    )


    positions = calculate_frame(
        frame_number
    )


    for position in positions:

        index = position[
            "index"
        ]

        x = position[
            "x"
        ]

        y = position[
            "y"
        ]

        scale = position[
            "scale"
        ]

        opacity = position[
            "opacity"
        ]


        icon = icons[
            index
        ][
            "image"
        ]


        # ----------------------------------------------------
        # Tamaño según profundidad
        # ----------------------------------------------------

        size = max(
            18,
            int(
                ICON_SIZE *
                scale
            )
        )


        icon_scaled = icon.resize(
            (
                size,
                size
            ),
            Image.Resampling.LANCZOS
        )


        # ----------------------------------------------------
        # Opacidad
        # ----------------------------------------------------

        alpha = icon_scaled.getchannel(
            "A"
        )


        alpha = alpha.point(
            lambda value:
            int(
                value *
                opacity
            )
        )


        icon_scaled.putalpha(
            alpha
        )


        # ----------------------------------------------------
        # Composición
        #
        # NO dibujamos ningún círculo.
        # ----------------------------------------------------

        paste_x = int(
            x -
            size / 2
        )


        paste_y = int(
            y -
            size / 2
        )


        frame.alpha_composite(
            icon_scaled,
            (
                paste_x,
                paste_y
            )
        )


    # ========================================================
    # CONVERSIÓN A PALETA
    #
    # Esta parte es una de las claves para reducir el GIF.
    # ========================================================

    frame = frame.convert(
        "RGB"
    )


    frame = frame.quantize(
        colors=COLORS,
        method=Image.Quantize.MEDIANCUT
    )


    return frame


# ============================================================
# GENERAR FRAMES
# ============================================================

frames = []


print()
print(
    "Generando animación..."
)


for frame_number in range(
    FRAME_COUNT
):

    frame = create_frame(
        frame_number
    )


    frames.append(
        frame
    )


    if (
        frame_number %
        FPS
        == 0
    ):

        seconds = (
            frame_number /
            FPS
        )

        print(
            f"  {seconds:.0f}/"
            f"{DURATION}s"
        )


# ============================================================
# GUARDAR GIF
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


print()
print(
    "Guardando GIF optimizado..."
)


frames[0].save(
    OUTPUT_FILE,
    save_all=True,
    append_images=frames[1:],
    duration=int(
        1000 /
        FPS
    ),
    loop=0,
    optimize=True,
    disposal=2
)


# ============================================================
# INFORMACIÓN FINAL
# ============================================================

file_size = (
    OUTPUT_FILE.stat().st_size
    /
    1024
    /
    1024
)


print()
print(
    "=============================================="
)

print(
    "Technologies GIF generado"
)

print(
    f"Archivo: {OUTPUT_FILE}"
)

print(
    f"Logos: {len(icons)}"
)

print(
    f"Resolución: {WIDTH}x{HEIGHT}"
)

print(
    f"FPS: {FPS}"
)

print(
    f"Duración: {DURATION}s"
)

print(
    f"Frames: {FRAME_COUNT}"
)

print(
    f"Paleta: {COLORS} colores"
)

print(
    f"Tamaño: {file_size:.2f} MB"
)

print(
    "=============================================="
)
