from pathlib import Path
import math
import io

from PIL import Image, ImageDraw


# ============================================================
# CONFIGURACIÓN
# ============================================================

INPUT_DIR = Path("assets/technologies")
OUTPUT_FILE = Path("assets/technologies.gif")

WIDTH = 900
HEIGHT = 460

CENTER_X = WIDTH / 2
CENTER_Y = HEIGHT / 2

# Tamaño aproximado de la esfera
SPHERE_RADIUS_X = 165
SPHERE_RADIUS_Y = 145

# Tamaño de cada logo
ICON_SIZE = 58

# Animación
FPS = 20
DURATION = 18

FRAME_COUNT = FPS * DURATION

# Fondo
BACKGROUND = (13, 17, 23, 255)

# Color del pequeño fondo circular de cada logo
ICON_BACKGROUND = (22, 27, 34, 235)

# Borde de los logos
ICON_BORDER = (48, 54, 61, 255)


# ============================================================
# DEPENDENCIA SVG -> PNG
# ============================================================

try:

    import cairosvg

except ImportError:

    raise SystemExit(
        "\nERROR: falta cairosvg.\n"
        "Instálalo con:\n\n"
        "pip install cairosvg pillow\n"
    )


# ============================================================
# CARGAR SVG
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

        # ----------------------------------------------------
        # Convertimos el SVG a PNG de alta resolución.
        # Lo hacemos una sola vez antes de crear los frames.
        # ----------------------------------------------------

        png_data = cairosvg.svg2png(
            url=str(svg_file),
            output_width=ICON_SIZE * 4,
            output_height=ICON_SIZE * 4
        )

        icon = Image.open(
            io.BytesIO(png_data)
        ).convert("RGBA")

        # ----------------------------------------------------
        # Reducimos al tamaño final.
        # ----------------------------------------------------

        icon = icon.resize(
            (
                ICON_SIZE,
                ICON_SIZE
            ),
            Image.Resampling.LANCZOS
        )

        icons.append(
            {
                "name": svg_file.stem,
                "image": icon
            }
        )

        print(
            f"OK: {svg_file.name}"
        )

    except Exception as error:

        print(
            f"ERROR procesando "
            f"{svg_file.name}: {error}"
        )


if not icons:

    raise SystemExit(
        "No se pudo cargar ningún logo."
    )


print()
print(
    f"Logos cargados: {len(icons)}"
)


# ============================================================
# ESFERA 3D
# ============================================================

def fibonacci_sphere(count):

    points = []

    # Ángulo dorado
    golden_angle = (
        math.pi *
        (3.0 - math.sqrt(5.0))
    )

    for i in range(count):

        # Evitamos exactamente los polos.
        y = (
            1.0 -
            2.0 *
            (i + 0.5) /
            count
        )

        radius = math.sqrt(
            max(
                0.0,
                1.0 -
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
# ROTACIONES 3D
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
# CALCULAR POSICIONES
# ============================================================

def calculate_frame(frame):

    progress = (
        frame /
        FRAME_COUNT
    )

    # --------------------------------------------------------
    # Rotación principal.
    # --------------------------------------------------------

    rotation_y = (
        progress *
        math.pi *
        2
    )

    # --------------------------------------------------------
    # Inclinación de la esfera.
    #
    # No permanece fija para que todos los logos tengan
    # movimiento y no haya logos clavados arriba/abajo.
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
        math.radians(8)
    )

    rotation_z = (
        math.sin(
            progress *
            math.pi *
            2
        )
        *
        math.radians(5)
    )

    result = []


    for index, point in enumerate(points):

        x, y, z = point

        # ----------------------------------------------------
        # Pequeña diferencia de fase por logo.
        # ----------------------------------------------------

        phase = (
            index *
            0.19
        )

        x, y, z = rotate_y(
            x,
            y,
            z,
            rotation_y + phase
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
        # Proyección 3D -> 2D
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
        # Profundidad
        #
        # z = 1  -> totalmente delante
        # z = -1 -> totalmente detrás
        # ----------------------------------------------------

        depth = (
            z + 1.0
        ) / 2.0


        # ----------------------------------------------------
        # Perspectiva
        # ----------------------------------------------------

        scale = (
            0.58 +
            depth *
            0.42
        )


        # ----------------------------------------------------
        # Opacidad
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
    # MUY IMPORTANTE:
    #
    # Los logos que están detrás se dibujan primero.
    # Los que están delante se dibujan después.
    # --------------------------------------------------------

    result.sort(
        key=lambda item: item["z"]
    )


    return result


# ============================================================
# CREAR UN FRAME
# ============================================================

def create_frame(frame_number):

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

        index = position["index"]

        x = position["x"]
        y = position["y"]

        scale = position["scale"]

        opacity = position["opacity"]


        # ----------------------------------------------------
        # Logo original
        # ----------------------------------------------------

        icon = icons[index]["image"]


        # ----------------------------------------------------
        # Tamaño según profundidad.
        # ----------------------------------------------------

        size = max(
            20,
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
        # Opacidad.
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
        # Fondo circular.
        #
        # No representa la esfera:
        # es solamente el fondo individual del logo.
        # ----------------------------------------------------

        circle_radius = (
            size *
            0.52
        )


        overlay = Image.new(
            "RGBA",
            (
                size * 2,
                size * 2
            ),
            (
                0,
                0,
                0,
                0
            )
        )


        draw = ImageDraw.Draw(
            overlay
        )


        center = size


        draw.ellipse(
            (
                center - circle_radius,
                center - circle_radius,
                center + circle_radius,
                center + circle_radius
            ),
            fill=(
                ICON_BACKGROUND[0],
                ICON_BACKGROUND[1],
                ICON_BACKGROUND[2],
                int(
                    235 *
                    opacity
                )
            ),
            outline=(
                ICON_BORDER[0],
                ICON_BORDER[1],
                ICON_BORDER[2],
                int(
                    255 *
                    opacity
                )
            ),
            width=1
        )


        # ----------------------------------------------------
        # Colocar logo sobre el círculo.
        # ----------------------------------------------------

        overlay.alpha_composite(
            icon_scaled,
            (
                size // 2,
                size // 2
            )
        )


        # ----------------------------------------------------
        # Posición final.
        # ----------------------------------------------------

        paste_x = int(
            x -
            overlay.width / 2
        )

        paste_y = int(
            y -
            overlay.height / 2
        )


        frame.alpha_composite(
            overlay,
            (
                paste_x,
                paste_y
            )
        )


    # ========================================================
    # CONVERTIR A RGB
    #
    # GIF no necesita canal alpha.
    # ========================================================

    return frame.convert(
        "RGB"
    )


# ============================================================
# GENERAR FRAMES
# ============================================================

frames = []


print()
print(
    "Generando frames..."
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
        frame_number % FPS
        == 0
    ):

        seconds = (
            frame_number /
            FPS
        )

        print(
            f"  {seconds:.0f}/{DURATION}s"
        )


# ============================================================
# GUARDAR GIF
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


frame_duration = int(
    1000 /
    FPS
)


print()
print(
    "Guardando GIF..."
)


frames[0].save(
    OUTPUT_FILE,
    save_all=True,
    append_images=frames[1:],
    duration=frame_duration,
    loop=0,
    optimize=False
)


# ============================================================
# RESULTADO
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
    "Technologies & Tools generado correctamente"
)

print(
    f"Archivo: {OUTPUT_FILE}"
)

print(
    f"Logos: {len(icons)}"
)

print(
    f"Frames: {FRAME_COUNT}"
)

print(
    f"FPS: {FPS}"
)

print(
    f"Duración: {DURATION} segundos"
)

print(
    f"Tamaño: {file_size:.2f} MB"
)

print(
    "Loop: infinito"
)

print(
    "=============================================="
)
