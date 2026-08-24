from pathlib import Path
import io
import math
import random
import shutil
import subprocess

from PIL import Image


# ============================================================
# CONFIGURACIÓN
# ============================================================

INPUT_DIR = Path("assets/technologies")

TEMP_GIF = Path("assets/technologies_raw.gif")
OUTPUT_GIF = Path("assets/technologies.gif")

WIDTH = 535
HEIGHT = 460

CENTER_X = WIDTH / 2
CENTER_Y = HEIGHT / 2

FPS = 14
DURATION = 32
FRAME_COUNT = FPS * DURATION

BACKGROUND = (13, 17, 23, 255)

ICON_SIZE = 56

SPHERE_RADIUS_X = 205
SPHERE_RADIUS_Y = 180

# Una vuelta completa cada 32 segundos
ROTATION_SPEED = (2 * math.pi) / DURATION

# Opacidad mínima de los logos que están detrás
MIN_OPACITY = 0.30

random.seed(12345)


# ============================================================
# DEPENDENCIAS
# ============================================================

try:
    import cairosvg
except ImportError:
    raise SystemExit(
        "CairoSVG no está instalado."
    )


if shutil.which("gifsicle") is None:
    raise SystemExit(
        "Gifsicle no está instalado."
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

print(
    f"Encontrados {len(svg_files)} logos."
)


icons = []

for svg_file in svg_files:

    try:

        png_data = cairosvg.svg2png(
            url=str(svg_file),
            output_width=ICON_SIZE * 3,
            output_height=ICON_SIZE * 3
        )

        image = Image.open(
            io.BytesIO(png_data)
        ).convert("RGBA")

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
# DISTRIBUCIÓN DE FIBONACCI
# ============================================================
#
# Distribución uniforme sobre la SUPERFICIE de una esfera.
#
# No hay logos en el interior.
#
# La fórmula utiliza el "golden angle" para evitar
# agrupaciones y repartir los puntos uniformemente.
#
# ============================================================

particles = []

count = len(icons)

golden_angle = math.pi * (
    3 - math.sqrt(5)
)


for index, icon in enumerate(icons):

    # --------------------------------------------------------
    # Coordenada Y sobre la esfera
    # --------------------------------------------------------

    if count == 1:

        y = 0

    else:

        y = 1 - (
            2 * index / (count - 1)
        )

    # --------------------------------------------------------
    # Radio horizontal correspondiente a la latitud
    # --------------------------------------------------------

    radius = math.sqrt(
        max(
            0,
            1 - y * y
        )
    )

    # --------------------------------------------------------
    # Ángulo Fibonacci
    # --------------------------------------------------------

    angle = (
        index
        *
        golden_angle
    )

    particles.append(
        {
            "icon": icon["image"],
            "name": icon["name"],

            # Altura FIJA
            "y": y,

            # Radio FIJO
            "radius": radius,

            # Longitud inicial
            "angle": angle
        }
    )


# ============================================================
# FRAME
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

    time = (
        frame_number
        /
        FPS
    )

    objects = []

    for particle in particles:

        # ----------------------------------------------------
        # GIRO SOBRE EL EJE Y
        # ----------------------------------------------------

        angle = (
            particle["angle"]
            +
            time
            *
            ROTATION_SPEED
        )

        radius = particle["radius"]

        # ----------------------------------------------------
        # POSICIÓN SOBRE LA SUPERFICIE
        # ----------------------------------------------------

        x = (
            radius
            *
            math.cos(angle)
        )

        z = (
            radius
            *
            math.sin(angle)
        )

        # Y permanece completamente fija
        y = particle["y"]

        # ----------------------------------------------------
        # PROYECCIÓN 3D
        # ----------------------------------------------------

        screen_x = (
            CENTER_X
            +
            x
            *
            SPHERE_RADIUS_X
        )

        screen_y = (
            CENTER_Y
            +
            y
            *
            SPHERE_RADIUS_Y
        )

        # ----------------------------------------------------
        # PROFUNDIDAD
        # ----------------------------------------------------

        depth = (
            z + 1
        ) / 2

        # ----------------------------------------------------
        # TAMAÑO
        # ----------------------------------------------------

        scale = (
            0.52
            +
            depth
            *
            0.48
        )

        size = max(
            18,
            int(
                ICON_SIZE
                *
                scale
            )
        )

        # ----------------------------------------------------
        # OPACIDAD
        # ----------------------------------------------------

        opacity = (
            MIN_OPACITY
            +
            depth
            *
            (
                1
                -
                MIN_OPACITY
            )
        )

        objects.append(
            {
                "x": screen_x,
                "y": screen_y,
                "z": z,
                "size": size,
                "opacity": opacity,
                "icon": particle["icon"]
            }
        )


    # ========================================================
    # ORDEN DE PROFUNDIDAD
    # ========================================================

    objects.sort(
        key=lambda item: item["z"]
    )


    # ========================================================
    # DIBUJAR
    # ========================================================

    for obj in objects:

        size = obj["size"]

        icon = obj["icon"]

        resized = icon.resize(
            (
                size,
                size
            ),
            Image.Resampling.LANCZOS
        )

        # Solo modificamos transparencia.
        # Los colores originales del SVG permanecen intactos.

        alpha = resized.getchannel("A")

        alpha = alpha.point(
            lambda value:
            int(
                value
                *
                obj["opacity"]
            )
        )

        resized.putalpha(alpha)

        x = int(
            obj["x"]
            -
            size / 2
        )

        y = int(
            obj["y"]
            -
            size / 2
        )

        frame.alpha_composite(
            resized,
            (
                x,
                y
            )
        )


    return frame.convert("RGB")


# ============================================================
# GENERAR FRAMES
# ============================================================

print()
print(
    "Generando esfera Fibonacci..."
)

frames_rgb = []

for frame_number in range(
    FRAME_COUNT
):

    frame = create_frame(
        frame_number
    )

    frames_rgb.append(frame)

    if frame_number % FPS == 0:

        print(
            f"  {frame_number // FPS}/"
            f"{DURATION} segundos"
        )


# ============================================================
# PALETA GLOBAL
# ============================================================

print()
print(
    "Creando paleta global..."
)

sample_count = min(
    32,
    len(frames_rgb)
)

samples = []

for i in range(
    sample_count
):

    index = int(
        i
        *
        (
            len(frames_rgb) - 1
        )
        /
        max(
            1,
            sample_count - 1
        )
    )

    image = frames_rgb[index]

    image = image.resize(
        (
            268,
            230
        ),
        Image.Resampling.BILINEAR
    )

    samples.append(image)


palette_canvas = Image.new(
    "RGB",
    (
        268,
        230 * len(samples)
    )
)


for index, image in enumerate(samples):

    palette_canvas.paste(
        image,
        (
            0,
            index * 230
        )
    )


palette = palette_canvas.quantize(
    colors=256,
    method=Image.Quantize.MEDIANCUT
)


# ============================================================
# APLICAR PALETA
# ============================================================

print()
print(
    "Aplicando paleta común..."
)

frames = []

for index, frame in enumerate(
    frames_rgb
):

    indexed = frame.quantize(
        palette=palette,
        dither=Image.Dither.NONE
    )

    frames.append(indexed)


# ============================================================
# DELAYS
# ============================================================
#
# Inspirado en los tiempos observados en el GIF de Kiran.
#
# No todos los frames tienen exactamente el mismo delay.
#
# ============================================================

delay_pattern = [
    70,
    70,
    70,
    80,
    70,
    70,
    70,
    90,
    70,
    70,
    70,
    80,
    70,
    70,
    70,
    90
]

durations = [
    delay_pattern[
        i % len(delay_pattern)
    ]
    for i in range(FRAME_COUNT)
]


# ============================================================
# GUARDAR GIF TEMPORAL
# ============================================================

print()
print(
    "Creando GIF..."
)

frames[0].save(
    TEMP_GIF,

    save_all=True,

    append_images=frames[1:],

    duration=durations,

    loop=0,

    optimize=False,

    disposal=1
)


# ============================================================
# GIFSICLE
# ============================================================

print()
print(
    "Optimizando con Gifsicle..."
)

command = [
    "gifsicle",

    "--optimize=3",

    "--colors",
    "256",

    "--careful",

    "--output",
    str(OUTPUT_GIF),

    str(TEMP_GIF)
]


result = subprocess.run(
    command,
    capture_output=True,
    text=True
)


if result.returncode != 0:

    print(result.stdout)
    print(result.stderr)

    raise SystemExit(
        "Gifsicle ha fallado."
    )


# ============================================================
# ELIMINAR TEMPORAL
# ============================================================

try:

    TEMP_GIF.unlink()

except FileNotFoundError:

    pass


# ============================================================
# INFORMACIÓN
# ============================================================

size_mb = (
    OUTPUT_GIF.stat().st_size
    /
    1024
    /
    1024
)

average_delay = (
    sum(durations)
    /
    len(durations)
)

average_fps = (
    1000
    /
    average_delay
)


print()
print(
    "=========================================="
)

print(
    "Technologies GIF generado correctamente"
)

print(
    f"Resolución:   {WIDTH}x{HEIGHT}"
)

print(
    f"Logos:        {count}"
)

print(
    f"Frames:       {FRAME_COUNT}"
)

print(
    f"Duración:     {DURATION}s"
)

print(
    f"Delay medio:  {average_delay:.1f} ms"
)

print(
    f"FPS medio:    {average_fps:.2f}"
)

print(
    f"Tamaño:       {size_mb:.2f} MB"
)

print(
    "=========================================="
)
