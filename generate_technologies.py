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

OUTPUT_GIF_DARK = Path(
    "assets/technologies-dark.gif"
)

OUTPUT_GIF_LIGHT = Path(
    "assets/technologies-light.gif"
)


# ============================================================
# DIMENSIONES
# ============================================================

WIDTH = 535
HEIGHT = 460

CENTER_X = WIDTH / 2
CENTER_Y = HEIGHT / 2


# ============================================================
# FONDOS
# ============================================================

DARK_BACKGROUND = (
    13,
    17,
    23,
    255
)

LIGHT_BACKGROUND = (
    255,
    255,
    255,
    255
)


# ============================================================
# RENDERIZADO DE LOS SVG
# ============================================================

# Los SVG se renderizan a mayor resolución
# y posteriormente se reducen.
#
# Esto ayuda a mantener una mejor calidad
# de los logos.

SVG_RENDER_SIZE = 256


# ============================================================
# TAMAÑO DE LOS LOGOS
# ============================================================

ICON_SIZE = 64


# ============================================================
# TAMAÑO VISUAL DE LA ESFERA
# ============================================================

SPHERE_RADIUS_X = 205
SPHERE_RADIUS_Y = 180


# ============================================================
# ANIMACIÓN
# ============================================================

# Duración de un ciclo completo.

DURATION = 16


# Número de frames por segundo.

FPS = 15


FRAME_COUNT = (
    DURATION *
    FPS
)


# Una vuelta completa durante todo el GIF.

ROTATION_SPEED = (
    2 *
    math.pi
) / DURATION


# ============================================================
# COMPROBAR DEPENDENCIAS
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


print()
print(
    f"Encontrados {len(svg_files)} logos."
)


# ============================================================
# CARGAR SVG A ALTA RESOLUCIÓN
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
            f"  ERROR: "
            f"{svg_file.name}: "
            f"{error}"
        )


if not icons:

    raise SystemExit(
        "No se pudo cargar ningún logo."
    )


# ============================================================
# DISTRIBUCIÓN DE FIBONACCI
# ============================================================
#
# Los logos se colocan sobre la SUPERFICIE
# de una esfera.
#
# No colocamos ningún logo exactamente
# en los polos.
#
# Esto permite que incluso los logos de
# la zona superior e inferior tengan
# movimiento orbital visible.
#
# ============================================================

particles = []


count = len(icons)


golden_angle = (
    math.pi *
    (
        3 -
        math.sqrt(5)
    )
)


# Evitamos los polos exactos.

LATITUDE_LIMIT = 0.86


for index, icon in enumerate(icons):

    # --------------------------------------------------------
    # Distribución vertical
    # --------------------------------------------------------

    normalized = (
        (index + 0.5)
        /
        count
    )

    y = (
        1 -
        2 * normalized
    )

    y *= LATITUDE_LIMIT


    # --------------------------------------------------------
    # Radio horizontal de la esfera
    # --------------------------------------------------------

    radius = math.sqrt(
        max(
            0,
            1 -
            y * y
        )
    )


    # --------------------------------------------------------
    # Longitud inicial
    # --------------------------------------------------------

    angle = (
        index *
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

def create_frame(
    frame_number,
    background
):

    frame = Image.new(
        "RGBA",
        (
            WIDTH,
            HEIGHT
        ),
        background
    )


    # --------------------------------------------------------
    # Tiempo
    # --------------------------------------------------------

    time = (
        frame_number
        /
        FPS
    )


    # --------------------------------------------------------
    # Objetos
    # --------------------------------------------------------

    objects = []


    for particle in particles:

        # ----------------------------------------------------
        # ROTACIÓN
        # ----------------------------------------------------

        angle = (
            particle["angle"]
            +
            time *
            ROTATION_SPEED
        )


        radius = (
            particle["radius"]
        )


        # ----------------------------------------------------
        # POSICIÓN SOBRE LA SUPERFICIE
        # ----------------------------------------------------

        x = (
            radius *
            math.cos(angle)
        )


        z = (
            radius *
            math.sin(angle)
        )


        y = (
            particle["y"]
        )


        # ----------------------------------------------------
        # PROYECCIÓN
        # ----------------------------------------------------

        screen_x = (
            CENTER_X
            +
            x *
            SPHERE_RADIUS_X
        )


        screen_y = (
            CENTER_Y
            +
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
        # ESCALA SEGÚN PROFUNDIDAD
        # ----------------------------------------------------

        scale = (
            0.58
            +
            depth *
            0.42
        )


        size = max(
            20,
            int(
                ICON_SIZE *
                scale
            )
        )


        # ----------------------------------------------------
        # OPACIDAD SEGÚN PROFUNDIDAD
        # ----------------------------------------------------

        opacity = (
            0.40
            +
            depth *
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


        # ----------------------------------------------------
        # REDUCIR EL SVG RENDERIZADO
        # ----------------------------------------------------

        resized = obj["icon"].resize(
            (
                size,
                size
            ),
            Image.Resampling.LANCZOS
        )


        # ----------------------------------------------------
        # APLICAR OPACIDAD
        # ----------------------------------------------------

        alpha = (
            resized.getchannel("A")
        )


        alpha = alpha.point(
            lambda value:
            int(
                value *
                obj["opacity"]
            )
        )


        resized.putalpha(
            alpha
        )


        # ----------------------------------------------------
        # POSICIÓN
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # DIBUJAR
        # ----------------------------------------------------

        frame.alpha_composite(
            resized,
            (
                x,
                y
            )
        )


    return frame.convert(
        "RGB"
    )


# ============================================================
# GENERAR UN GIF
# ============================================================

def generate_gif(
    background,
    output_gif
):

    print()
    print(
        "=========================================="
    )

    print(
        f"Generando: {output_gif}"
    )

    print(
        "=========================================="
    )


    # ========================================================
    # CREAR FRAMES
    # ========================================================

    frames_rgb = []


    for frame_number in range(
        FRAME_COUNT
    ):

        frame = create_frame(
            frame_number,
            background
        )


        frames_rgb.append(
            frame
        )


        if (
            frame_number %
            FPS
            == 0
        ):

            print(
                f"  "
                f"{frame_number // FPS}"
                f"/"
                f"{DURATION}"
                f" segundos"
            )


    # ========================================================
    # PALETA GLOBAL
    # ========================================================
    #
    # Una única paleta para TODO el GIF.
    #
    # Esto evita que los colores de los
    # logos cambien entre frames.
    #
    # ========================================================

    print()
    print(
        "Generando paleta global..."
    )


    sample_count = min(
        32,
        len(frames_rgb)
    )


    sample_width = (
        WIDTH // 2
    )


    sample_height = (
        HEIGHT // 2
    )


    palette_canvas = Image.new(
        "RGB",
        (
            sample_width,
            sample_height *
            sample_count
        )
    )


    for i in range(
        sample_count
    ):

        index = int(
            i *
            (
                len(frames_rgb)
                -
                1
            )
            /
            max(
                1,
                sample_count -
                1
            )
        )


        sample = (
            frames_rgb[index]
            .resize(
                (
                    sample_width,
                    sample_height
                ),
                Image.Resampling.LANCZOS
            )
        )


        palette_canvas.paste(
            sample,
            (
                0,
                i *
                sample_height
            )
        )


    palette = (
        palette_canvas.quantize(
            colors=256,
            method=Image.Quantize.MEDIANCUT
        )
    )


    # ========================================================
    # CONVERTIR FRAMES A GIF
    # ========================================================

    print()
    print(
        "Aplicando paleta global..."
    )


    frames = []


    for frame in frames_rgb:

        indexed = (
            frame.quantize(
                palette=palette,
                dither=Image.Dither.NONE
            )
        )


        frames.append(
            indexed
        )


    # ========================================================
    # DURACIONES
    # ========================================================
    #
    # Pequeña variación del delay para que
    # la cadencia no sea completamente uniforme.
    #
    # ========================================================

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
            i %
            len(delay_pattern)
        ]
        for i in range(
            FRAME_COUNT
        )
    ]


    # ========================================================
    # GIF TEMPORAL
    # ========================================================

    temp_gif = output_gif.with_name(
        output_gif.stem +
        "_raw.gif"
    )


    print()
    print(
        "Creando GIF temporal..."
    )


    frames[0].save(
        temp_gif,

        save_all=True,

        append_images=(
            frames[1:]
        ),

        duration=durations,

        loop=0,

        optimize=False,

        disposal=1
    )


    # ========================================================
    # OPTIMIZAR CON GIFSICLE
    # ========================================================

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
        str(output_gif),

        str(temp_gif)
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


    # ========================================================
    # ELIMINAR TEMPORAL
    # ========================================================

    try:

        temp_gif.unlink()

    except FileNotFoundError:

        pass


    # ========================================================
    # INFORMACIÓN FINAL
    # ========================================================

    size_mb = (
        output_gif.stat().st_size
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
        f"Archivo:      {output_gif}"
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
        f"Delay medio:  "
        f"{average_delay:.1f} ms"
    )


    print(
        f"FPS medio:    "
        f"{average_fps:.2f}"
    )


    print(
        f"Tamaño:       "
        f"{size_mb:.2f} MB"
    )


    print(
        "=========================================="
    )


# ============================================================
# GENERAR VERSIÓN OSCURA
# ============================================================

generate_gif(
    DARK_BACKGROUND,
    OUTPUT_GIF_DARK
)


# ============================================================
# GENERAR VERSIÓN CLARA
# ============================================================

generate_gif(
    LIGHT_BACKGROUND,
    OUTPUT_GIF_LIGHT
)
