from pathlib import Path
import io
import math
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

# Fondo TRANSPARENTE
BACKGROUND = (0, 0, 0, 0)

# Renderizado de SVG a alta resolución
SVG_RENDER_SIZE = 256

# Tamaño máximo de los logos
ICON_SIZE = 64

# Tamaño de la esfera
SPHERE_RADIUS_X = 205
SPHERE_RADIUS_Y = 180


# ============================================================
# ANIMACIÓN
# ============================================================

DURATION = 16

# 15 FPS = equilibrio entre fluidez y tamaño
FPS = 15

FRAME_COUNT = DURATION * FPS

ROTATION_SPEED = (2 * math.pi) / DURATION


# ============================================================
# DEPENDENCIAS
# ============================================================

try:
    import cairosvg
except ImportError:
    raise SystemExit(
        "ERROR: CairoSVG no está instalado."
    )


if shutil.which("gifsicle") is None:
    raise SystemExit(
        "ERROR: gifsicle no está instalado."
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
# CARGAR SVG
# ============================================================

icons = []

for svg_file in svg_files:

    try:

        png_data = cairosvg.svg2png(
            url=str(svg_file),
            output_width=SVG_RENDER_SIZE,
            output_height=SVG_RENDER_SIZE
        )

        image = Image.open(
            io.BytesIO(png_data)
        ).convert("RGBA")

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

particles = []

count = len(icons)

golden_angle = math.pi * (
    3 - math.sqrt(5)
)

# Evitamos los polos exactos.
LATITUDE_LIMIT = 0.86


for index, icon in enumerate(icons):

    normalized = (
        (index + 0.5)
        /
        count
    )

    y = (
        1
        -
        2 * normalized
    )

    y *= LATITUDE_LIMIT

    radius = math.sqrt(
        max(
            0,
            1 - y * y
        )
    )

    angle = (
        index
        *
        golden_angle
    )

    particles.append(
        {
            "icon": icon["image"],
            "name": icon["name"],
            "y": y,
            "radius": radius,
            "angle": angle
        }
    )


# ============================================================
# CREAR FRAME
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

        angle = (
            particle["angle"]
            +
            time
            *
            ROTATION_SPEED
        )

        radius = particle["radius"]

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

        y = particle["y"]

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

        depth = (
            z + 1
        ) / 2

        scale = (
            0.58
            +
            depth
            *
            0.42
        )

        size = max(
            20,
            int(
                ICON_SIZE
                *
                scale
            )
        )

        opacity = (
            0.40
            +
            depth
            *
            0.60
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
    # PROFUNDIDAD
    # ========================================================

    objects.sort(
        key=lambda item: item["z"]
    )


    # ========================================================
    # DIBUJAR
    # ========================================================

    for obj in objects:

        size = obj["size"]

        resized = obj["icon"].resize(
            (
                size,
                size
            ),
            Image.Resampling.LANCZOS
        )

        alpha = resized.getchannel(
            "A"
        )

        alpha = alpha.point(
            lambda value:
            int(
                value
                *
                obj["opacity"]
            )
        )

        resized.putalpha(
            alpha
        )

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


    return frame


# ============================================================
# GENERAR FRAMES
# ============================================================

print()
print(
    "Generando animación..."
)

frames_rgba = []

for frame_number in range(
    FRAME_COUNT
):

    frame = create_frame(
        frame_number
    )

    frames_rgba.append(
        frame
    )

    if frame_number % FPS == 0:

        print(
            f"  {frame_number // FPS}"
            f"/{DURATION} segundos"
        )


# ============================================================
# CONVERTIR A GIF
# ============================================================
#
# GIF solamente permite una transparencia binaria.
# Reservamos el índice 0 de la paleta para transparencia.
#
# ============================================================

print()
print(
    "Preparando transparencia..."
)

frames = []

for frame in frames_rgba:

    # Crear máscara de transparencia
    alpha = frame.getchannel("A")

    # Convertir el frame a RGB sobre un fondo neutro
    rgb = Image.new(
        "RGB",
        frame.size,
        (255, 255, 255)
    )

    rgb.paste(
        frame,
        mask=alpha
    )

    # Convertir a paleta
    indexed = rgb.quantize(
        colors=255,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE
    )

    # Reservar índice 0 para transparencia
    indexed = indexed.convert("P")

    palette = indexed.getpalette()

    # Insertar color de transparencia en posición 0
    new_palette = [
        255, 255, 255
    ] + palette[:3 * 255]

    indexed.putpalette(
        new_palette
    )

    # Desplazar índices existentes +1
    pixels = indexed.load()

    alpha_pixels = alpha.load()

    for y in range(indexed.height):

        for x in range(indexed.width):

            if alpha_pixels[x, y] < 20:

                pixels[x, y] = 0

            else:

                pixels[x, y] = min(
                    pixels[x, y] + 1,
                    255
                )

    frames.append(
        indexed
    )


# ============================================================
# DURACIONES
# ============================================================

delay_pattern = [
    60,
    60,
    70,
    60,
    70,
    60,
    60,
    70,
    60,
    60
]

durations = [
    delay_pattern[
        i % len(delay_pattern)
    ]
    for i in range(
        FRAME_COUNT
    )
]


# ============================================================
# CREAR GIF TEMPORAL
# ============================================================

print()
print(
    "Creando GIF temporal..."
)

frames[0].save(
    TEMP_GIF,

    save_all=True,

    append_images=frames[1:],

    duration=durations,

    loop=0,

    optimize=False,

    disposal=2,

    transparency=0
)


# ============================================================
# OPTIMIZAR
# ============================================================

print()
print(
    "Optimizando GIF..."
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

    print(
        result.stdout
    )

    print(
        result.stderr
    )

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
# INFORMACIÓN FINAL
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
    "Fondo:        Transparente"
)

print(
    "=========================================="
)
