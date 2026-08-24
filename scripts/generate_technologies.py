from pathlib import Path
import io
import math
import random
import subprocess
import shutil

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

# ============================================================
# ANIMACIÓN
# ============================================================

FPS = 14
DURATION = 32
FRAME_COUNT = FPS * DURATION

# ============================================================
# LOGOS
# ============================================================

ICON_SIZE = 54

# ============================================================
# FONDO
# ============================================================

BACKGROUND = (13, 17, 23, 255)

# ============================================================
# ESFERA / NUBE
# ============================================================

# Radio de la zona donde se distribuyen inicialmente
# los logos.
SPREAD_X = 205
SPREAD_Y = 175

# ============================================================
# MOVIMIENTO
# ============================================================

# Velocidad general de movimiento
MOVEMENT_SPEED = 0.75

# ============================================================
# ALEATORIEDAD DETERMINISTA
# ============================================================

random.seed(12345)


# ============================================================
# COMPROBAR CAIROSVG
# ============================================================

try:
    import cairosvg
except ImportError:
    raise SystemExit(
        "CairoSVG no está instalado.\n"
        "Ejecuta: pip install pillow cairosvg"
    )


# ============================================================
# COMPROBAR GIFSICLE
# ============================================================

if shutil.which("gifsicle") is None:
    raise SystemExit(
        "Gifsicle no está instalado.\n"
        "En GitHub Actions utiliza:\n"
        "sudo apt-get update && sudo apt-get install -y gifsicle"
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


print(f"Encontrados {len(svg_files)} logos.")


# ============================================================
# CARGAR LOS LOGOS
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
# CREAR UNA NUBE 3D
# ============================================================

particles = []


for index, icon in enumerate(icons):

    # --------------------------------------------------------
    # Posición inicial aleatoria
    # --------------------------------------------------------

    theta = random.uniform(
        0,
        math.pi * 2
    )

    phi = random.uniform(
        -math.pi / 2,
        math.pi / 2
    )

    x = (
        math.cos(phi)
        * math.cos(theta)
    )

    y = (
        math.sin(phi)
    )

    z = (
        math.cos(phi)
        * math.sin(theta)
    )

    # --------------------------------------------------------
    # Movimiento individual
    # --------------------------------------------------------

    vx = random.uniform(
        -0.45,
        0.45
    )

    vy = random.uniform(
        -0.35,
        0.35
    )

    vz = random.uniform(
        -0.45,
        0.45
    )

    # --------------------------------------------------------
    # Movimiento orbital individual
    # --------------------------------------------------------

    orbit_speed = random.uniform(
        0.35,
        0.85
    )

    orbit_phase = random.uniform(
        0,
        math.pi * 2
    )

    orbit_radius = random.uniform(
        0.85,
        1.15
    )

    # --------------------------------------------------------
    # Oscilación
    # --------------------------------------------------------

    wobble_speed = random.uniform(
        0.5,
        1.2
    )

    wobble_phase = random.uniform(
        0,
        math.pi * 2
    )

    # --------------------------------------------------------
    # Cada logo parte de una posición diferente
    # --------------------------------------------------------

    particles.append(
        {
            "icon": icon["image"],
            "name": icon["name"],

            "x": x,
            "y": y,
            "z": z,

            "vx": vx,
            "vy": vy,
            "vz": vz,

            "orbit_speed": orbit_speed,
            "orbit_phase": orbit_phase,
            "orbit_radius": orbit_radius,

            "wobble_speed": wobble_speed,
            "wobble_phase": wobble_phase,

            "phase": random.uniform(
                0,
                math.pi * 2
            )
        }
    )


# ============================================================
# FUNCIÓN PARA LIMITAR LA POSICIÓN
# ============================================================

def wrap(value, minimum, maximum):

    if value < minimum:
        return maximum - (
            minimum - value
        )

    if value > maximum:
        return minimum + (
            value - maximum
        )

    return value


# ============================================================
# CALCULAR POSICIÓN DE CADA LOGO
# ============================================================

def calculate_particle(
    particle,
    time
):

    base_x = particle["x"]
    base_y = particle["y"]
    base_z = particle["z"]

    # --------------------------------------------------------
    # Movimiento orbital independiente
    # --------------------------------------------------------

    angle = (
        particle["orbit_phase"]
        +
        time
        *
        particle["orbit_speed"]
        *
        MOVEMENT_SPEED
    )

    radius = particle[
        "orbit_radius"
    ]

    orbit_x = (
        math.cos(angle)
        * radius
        * 0.16
    )

    orbit_y = (
        math.sin(
            angle * 0.73
        )
        * radius
        * 0.13
    )

    orbit_z = (
        math.sin(angle)
        * radius
        * 0.16
    )

    # --------------------------------------------------------
    # Movimiento propio
    # --------------------------------------------------------

    movement_x = (
        particle["vx"]
        *
        time
        *
        MOVEMENT_SPEED
        *
        0.10
    )

    movement_y = (
        particle["vy"]
        *
        time
        *
        MOVEMENT_SPEED
        *
        0.10
    )

    movement_z = (
        particle["vz"]
        *
        time
        *
        MOVEMENT_SPEED
        *
        0.10
    )

    # --------------------------------------------------------
    # Oscilación
    # --------------------------------------------------------

    wobble = (
        math.sin(
            particle["wobble_phase"]
            +
            time
            *
            particle["wobble_speed"]
        )
        * 0.06
    )

    x = (
        base_x
        + orbit_x
        + movement_x
        + wobble
    )

    y = (
        base_y
        + orbit_y
        + movement_y
    )

    z = (
        base_z
        + orbit_z
        + movement_z
    )

    # --------------------------------------------------------
    # Mantener los logos dentro de la zona
    # --------------------------------------------------------

    x = math.sin(x * 2.2) * 0.95

    y = math.sin(y * 2.0) * 0.90

    z = math.sin(z * 2.1) * 0.95

    # --------------------------------------------------------
    # PROYECCIÓN 3D
    # --------------------------------------------------------

    screen_x = (
        CENTER_X
        +
        x
        * SPREAD_X
    )

    screen_y = (
        CENTER_Y
        +
        y
        * SPREAD_Y
    )

    # --------------------------------------------------------
    # PROFUNDIDAD
    #
    # z = delante
    # z = detrás
    # --------------------------------------------------------

    depth = (
        z + 1
    ) / 2

    # --------------------------------------------------------
    # TAMAÑO
    # --------------------------------------------------------

    scale = (
        0.48
        +
        depth
        * 0.52
    )

    # --------------------------------------------------------
    # OPACIDAD
    # --------------------------------------------------------

    opacity = (
        0.30
        +
        depth
        * 0.70
    )

    return {
        "x": screen_x,
        "y": screen_y,
        "z": z,
        "scale": scale,
        "opacity": opacity,
        "icon": particle["icon"]
    }


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
        / FPS
    )

    objects = []

    for particle in particles:

        obj = calculate_particle(
            particle,
            time
        )

        objects.append(
            obj
        )

    # --------------------------------------------------------
    # Dibujar primero los objetos del fondo
    # --------------------------------------------------------

    objects.sort(
        key=lambda obj:
        obj["z"]
    )

    for obj in objects:

        icon = obj["icon"]

        scale = obj["scale"]

        opacity = obj["opacity"]

        size = max(
            16,
            int(
                ICON_SIZE
                * scale
            )
        )

        resized = icon.resize(
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
                * opacity
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

    return frame.convert("RGB")


# ============================================================
# GENERAR FRAMES
# ============================================================

frames = []

print()
print(
    "Generando nube 3D..."
)

for frame_number in range(
    FRAME_COUNT
):

    frame = create_frame(
        frame_number
    )

    # --------------------------------------------------------
    # 128 colores.
    #
    # Dejamos que Gifsicle haga posteriormente la optimización
    # principal de los frames.
    # --------------------------------------------------------

    frame = frame.quantize(
        colors=128,
        method=Image.Quantize.MEDIANCUT
    )

    frames.append(
        frame
    )

    if (
        frame_number % FPS
        == 0
    ):

        print(
            f"  {frame_number / FPS:.0f}/"
            f"{DURATION}s"
        )


# ============================================================
# GUARDAR GIF TEMPORAL
# ============================================================

TEMP_GIF.parent.mkdir(
    parents=True,
    exist_ok=True
)

print()
print(
    "Creando GIF temporal..."
)

frames[0].save(
    TEMP_GIF,
    save_all=True,
    append_images=frames[1:],
    duration=int(
        1000 / FPS
    ),
    loop=0,
    optimize=False,
    disposal=1
)


# ============================================================
# OPTIMIZACIÓN CON GIFSICLE
# ============================================================

print()
print(
    "Optimizando GIF con Gifsicle..."
)

command = [
    "gifsicle",

    "--optimize=3",

    "--colors",
    "128",

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

file_size = (
    OUTPUT_GIF.stat().st_size
    /
    1024
    /
    1024
)

print()
print(
    "=========================================="
)

print(
    "Technologies GIF generado correctamente"
)

print(
    f"Archivo: {OUTPUT_GIF}"
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
    f"Tamaño final: {file_size:.2f} MB"
)

print(
    "=========================================="
)
