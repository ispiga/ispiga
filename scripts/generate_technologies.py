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

FPS_TARGET = 14
DURATION_SECONDS = 32
FRAME_COUNT = FPS_TARGET * DURATION_SECONDS

BACKGROUND = (13, 17, 23, 255)

# Tamaño máximo de los logos
ICON_SIZE = 58

# Tamaño de la esfera
SPHERE_RADIUS_X = 205
SPHERE_RADIUS_Y = 175

# Velocidad de giro
ROTATION_SPEED = 2 * math.pi / 32

# Profundidad mínima de los logos que están detrás
MIN_BACK_OPACITY = 0.28

# Semilla fija para que cada generación mantenga
# las mismas posiciones iniciales.
random.seed(12345)


# ============================================================
# COMPROBAR DEPENDENCIAS
# ============================================================

try:
    import cairosvg
except ImportError:
    raise SystemExit(
        "CairoSVG no está instalado. "
        "Ejecuta: pip install pillow cairosvg"
    )


if shutil.which("gifsicle") is None:
    raise SystemExit(
        "Gifsicle no está instalado."
    )


# ============================================================
# BUSCAR SVG
# ============================================================

svg_files = sorted(INPUT_DIR.glob("*.svg"))

if not svg_files:
    raise SystemExit(
        f"No se encontraron SVG en {INPUT_DIR}"
    )

print(f"Encontrados {len(svg_files)} logos.")


# ============================================================
# CARGAR SVG
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
            io.BytesIO(png_data)
        ).convert("RGBA")

        image = image.resize(
            (ICON_SIZE, ICON_SIZE),
            Image.Resampling.LANCZOS
        )

        icons.append(
            {
                "name": svg_file.stem,
                "image": image
            }
        )

        print(f"  OK: {svg_file.name}")

    except Exception as error:

        print(
            f"  ERROR: {svg_file.name}: {error}"
        )


if not icons:
    raise SystemExit(
        "No se pudo cargar ningún logo."
    )


# ============================================================
# CREAR POSICIONES SOBRE LA SUPERFICIE DE LA ESFERA
# ============================================================
#
# Cada logo tiene:
#
#   Y       -> FIJO
#   radio   -> FIJO
#   ángulo  -> cambia con el tiempo
#
# Por tanto cada logo gira alrededor del eje vertical,
# pero nunca sube ni baja.
#
# ============================================================

particles = []

count = len(icons)

# Distribuir las alturas para ocupar bien la esfera.
#
# No utilizamos posiciones completamente aleatorias porque
# queremos evitar que varios logos queden exactamente juntos.

for index, icon in enumerate(icons):

    if count == 1:
        normalized_y = 0
    else:
        normalized_y = (
            -0.72
            +
            (
                index
                /
                (count - 1)
            )
            * 1.44
        )

    # Pequeña variación determinista
    normalized_y += random.uniform(
        -0.08,
        0.08
    )

    normalized_y = max(
        -0.82,
        min(
            0.82,
            normalized_y
        )
    )

    # Radio correspondiente a esa altura de la esfera.
    #
    # En una esfera:
    #
    # radius = sqrt(1 - y²)
    #
    orbit_radius = math.sqrt(
        max(
            0.05,
            1 - normalized_y ** 2
        )
    )

    # Ángulo inicial independiente.
    angle = random.uniform(
        0,
        math.pi * 2
    )

    particles.append(
        {
            "icon": icon["image"],
            "name": icon["name"],

            "y": normalized_y,

            "radius": orbit_radius,

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

    # Tiempo real de la animación
    time_seconds = (
        frame_number
        /
        FPS_TARGET
    )

    objects = []

    for particle in particles:

        # ----------------------------------------------------
        # GIRO
        # ----------------------------------------------------
        #
        # El ángulo cambia.
        #
        # Y NO cambia.
        #
        # Por eso cada logo describe una circunferencia
        # horizontal alrededor de la esfera.
        #

        angle = (
            particle["angle"]
            +
            time_seconds
            *
            ROTATION_SPEED
        )

        radius = particle["radius"]

        # ----------------------------------------------------
        # POSICIÓN 3D
        # ----------------------------------------------------

        x3d = (
            radius
            *
            math.cos(angle)
        )

        z3d = (
            radius
            *
            math.sin(angle)
        )

        y3d = particle["y"]

        # ----------------------------------------------------
        # PROYECCIÓN
        # ----------------------------------------------------

        screen_x = (
            CENTER_X
            +
            x3d
            *
            SPHERE_RADIUS_X
        )

        screen_y = (
            CENTER_Y
            +
            y3d
            *
            SPHERE_RADIUS_Y
        )

        # ----------------------------------------------------
        # PROFUNDIDAD
        # ----------------------------------------------------
        #
        # z3d:
        #
        # +1 = completamente delante
        # -1 = completamente detrás
        #

        depth = (
            z3d + 1
        ) / 2

        # ----------------------------------------------------
        # TAMAÑO
        # ----------------------------------------------------

        scale = (
            0.55
            +
            depth
            *
            0.45
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
            MIN_BACK_OPACITY
            +
            depth
            *
            (
                1
                -
                MIN_BACK_OPACITY
            )
        )

        objects.append(
            {
                "x": screen_x,
                "y": screen_y,
                "z": z3d,
                "size": size,
                "opacity": opacity,
                "icon": particle["icon"]
            }
        )

    # ========================================================
    # ORDENAR POR PROFUNDIDAD
    # ========================================================

    objects.sort(
        key=lambda item:
        item["z"]
    )

    # ========================================================
    # DIBUJAR LOGOS
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

        # ----------------------------------------------------
        # Aplicar únicamente opacidad.
        #
        # NO modificamos los colores.
        # ----------------------------------------------------

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
# GENERAR FRAMES RGB
# ============================================================

print()
print(
    "Generando frames de la esfera..."
)

frames_rgb = []

for frame_number in range(
    FRAME_COUNT
):

    frame = create_frame(
        frame_number
    )

    frames_rgb.append(frame)

    if frame_number % FPS_TARGET == 0:

        print(
            f"  {frame_number // FPS_TARGET}/"
            f"{DURATION_SECONDS} segundos"
        )


# ============================================================
# CREAR PALETA GLOBAL
# ============================================================
#
# IMPORTANTE:
#
# Antes cada frame tenía su propia paleta.
#
# Ahora generamos UNA SOLA paleta para toda la animación.
#
# Esto evita cambios de color entre frames.
#
# ============================================================

print()
print("Creando paleta global...")


# Tomamos varios frames repartidos por toda la animación.
sample_indices = []

sample_count = min(
    32,
    len(frames_rgb)
)

for i in range(sample_count):

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

    sample_indices.append(index)


# Reducimos los samples para crear una imagen
# representativa de la animación.

sample_width = 535
sample_height = 460

sample_images = []

for index in sample_indices:

    image = frames_rgb[index]

    # Reducimos ligeramente para no consumir
    # memoria innecesaria.

    image = image.resize(
        (
            268,
            230
        ),
        Image.Resampling.BILINEAR
    )

    sample_images.append(image)


# Crear una imagen de muestras vertical.
palette_canvas = Image.new(
    "RGB",
    (
        268,
        230 * len(sample_images)
    )
)

for index, image in enumerate(
    sample_images
):

    palette_canvas.paste(
        image,
        (
            0,
            index * 230
        )
    )


# Obtener la paleta global.
palette_image = palette_canvas.quantize(
    colors=256,
    method=Image.Quantize.MEDIANCUT
)


# ============================================================
# CONVERTIR TODOS LOS FRAMES A LA MISMA PALETA
# ============================================================

print(
    "Aplicando paleta global a los frames..."
)

frames = []

for index, frame in enumerate(
    frames_rgb
):

    indexed = frame.quantize(
        palette=palette_image,
        dither=Image.Dither.NONE
    )

    frames.append(indexed)

    if index % FPS_TARGET == 0:

        print(
            f"  Paleta: "
            f"{index // FPS_TARGET}/"
            f"{DURATION_SECONDS}"
        )


# Liberar memoria RGB
del frames_rgb
del sample_images
del palette_canvas


# ============================================================
# DELAYS VARIABLES
# ============================================================
#
# Kiran no utiliza exactamente el mismo delay en todos
# los frames.
#
# Utilizamos una secuencia suave alrededor de 70 ms.
#
# El promedio queda aproximadamente en la zona de 14 FPS.
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
    90,
]


durations = []

for index in range(
    FRAME_COUNT
):

    durations.append(
        delay_pattern[
            index
            %
            len(delay_pattern)
        ]
    )


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

    disposal=1
)


# ============================================================
# OPTIMIZAR CON GIFSICLE
# ============================================================

print()
print(
    "Optimizando GIF con Gifsicle..."
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
# INFORMACIÓN FINAL
# ============================================================

file_size = (
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
    f"Archivo:       {OUTPUT_GIF}"
)

print(
    f"Resolución:    {WIDTH}x{HEIGHT}"
)

print(
    f"Frames:        {FRAME_COUNT}"
)

print(
    f"Duración:      {DURATION_SECONDS}s"
)

print(
    f"Delay medio:   {average_delay:.1f} ms"
)

print(
    f"FPS medio:     {average_fps:.2f}"
)

print(
    f"Tamaño final:  {file_size:.2f} MB"
)

print(
    "=========================================="
)
