import json
import re
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).parent

EXCEL_PATH = BASE_DIR / "datos" / "excursiones.xlsx"
ASSETS_DIR = BASE_DIR / "assets"
LOGOS_DIR = ASSETS_DIR / "logos"
FOTOS_DIR = ASSETS_DIR / "excursiones"

# GitHub Pages busca index.html automáticamente
OUTPUT_HTML = BASE_DIR / "index.html"

EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def limpiar_texto(valor):
    """Convierte un valor de Excel en texto limpio."""
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def normalizar_logo(nombre):
    """Normaliza el nombre del logo para buscarlo en assets/logos."""
    nombre = limpiar_texto(nombre).lower()
    nombre = nombre.replace(" ", "_")
    nombre = nombre.replace("-", "_")
    nombre = re.sub(r"[^a-z0-9_]", "", nombre)
    return nombre


def valor_columna(row, posibles_nombres):
    """Busca una columna admitiendo distintas variantes del nombre."""
    for col in posibles_nombres:
        if col in row:
            return row[col]
    return ""


def obtener_logos(valor_logos):
    """
    Convierte el contenido de LOGOS del Excel en rutas a imágenes.

    Ejemplo Excel:
        elaios;adi

    Busca:
        assets/logos/elaios.png
        assets/logos/adi.png
    """
    if pd.isna(valor_logos):
        return []

    logos = []

    for parte in str(valor_logos).split(";"):
        nombre = normalizar_logo(parte)

        if not nombre:
            continue

        encontrado = False

        for extension in [".png", ".jpg", ".jpeg", ".webp"]:
            ruta_logo = LOGOS_DIR / f"{nombre}{extension}"

            if ruta_logo.exists():
                logos.append(f"assets/logos/{nombre}{extension}")
                encontrado = True
                break

        if not encontrado:
            print(f"⚠️ Logo no encontrado: {nombre}")

    return logos


def obtener_fotos(id_excursion):
    """
    Busca automáticamente las fotografías de cada excursión.

    Ejemplo:
        assets/excursiones/2025_02_15/foto1.jpg
        assets/excursiones/2025_02_15/foto2.jpg
    """
    carpeta = FOTOS_DIR / id_excursion

    # No mostramos error: es normal que haya excursiones sin fotografías.
    if not carpeta.exists():
        return []

    fotos = []

    for archivo in sorted(carpeta.iterdir()):
        if (
            archivo.is_file()
            and archivo.suffix.lower() in EXTENSIONES_IMAGEN
        ):
            fotos.append(
                f"assets/excursiones/{id_excursion}/{archivo.name}"
            )

    return fotos


def construir_id(fecha):
    """Construye un ID a partir de la fecha cuando el Excel no lo incluye."""
    fecha_txt = limpiar_texto(fecha)
    fecha_txt = fecha_txt.replace("-", "_").replace("/", "_")

    return fecha_txt[:10] if fecha_txt else "sin_fecha"


def limpiar_anio(valor):
    """Evita que Excel convierta 2006 en '2006.0'."""
    anio = limpiar_texto(valor)

    if anio.endswith(".0"):
        anio = anio[:-2]

    return anio


def limpiar_track(track):
    """Elimina valores que indican que todavía no existe un track."""
    track = limpiar_texto(track)

    valores_sin_track = {
        "",
        "PENDIENTE",
        "SIN TRACK",
        "NO",
        "-",
        "N/A",
        "NA",
        "NINGUNO",
    }

    if track.upper() in valores_sin_track:
        return ""

    return track


# ============================================================
# COMPROBACIONES INICIALES
# ============================================================

if not EXCEL_PATH.exists():
    raise FileNotFoundError(
        f"No se encuentra el Excel:\n{EXCEL_PATH}"
    )

if not LOGOS_DIR.exists():
    print(f"⚠️ No existe la carpeta de logos: {LOGOS_DIR}")

if not FOTOS_DIR.exists():
    print(f"⚠️ No existe la carpeta de fotografías: {FOTOS_DIR}")


# ============================================================
# LECTURA DEL EXCEL
# ============================================================

df = pd.read_excel(EXCEL_PATH)

excursiones = []

for indice, row in df.iterrows():

    fecha = limpiar_texto(
        valor_columna(row, ["FECHA", "Fecha", "fecha"])
    )

    nombre = limpiar_texto(
        valor_columna(
            row,
            [
                "EXCURSION",
                "Excursion",
                "Excursión",
                "NOMBRE",
                "Nombre",
            ],
        )
    )

    poblacion = limpiar_texto(
        valor_columna(
            row,
            ["POBLACION", "Poblacion", "Población"],
        )
    )

    provincia = limpiar_texto(
        valor_columna(
            row,
            ["PROVINCIA", "Provincia"],
        )
    )

    tipo = limpiar_texto(
        valor_columna(
            row,
            ["TIPO", "Tipo", "TIPO_ACTIVIDAD"],
        )
    )

    dificultad = limpiar_texto(
        valor_columna(
            row,
            ["DIFICULTAD", "Dificultad"],
        )
    )

    # --------------------------------------------------------
    # AÑO
    # --------------------------------------------------------

    anio = limpiar_anio(
        valor_columna(
            row,
            ["Año", "AÑO", "ANIO", "anio"],
        )
    )

    # Si no hay columna Año, intentamos obtenerlo de la fecha.
    if not anio and fecha:
        anio = fecha[:4]

    # --------------------------------------------------------
    # ESTADO
    # --------------------------------------------------------

    estado = limpiar_texto(
        valor_columna(
            row,
            ["ESTADO", "Estado", "estado"],
        )
    ).upper()

    sin_registros = estado == "SIN_REGISTROS"

    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    id_excel = limpiar_texto(
        valor_columna(
            row,
            ["ID_EXCURSION", "ID", "id"],
        )
    )

    # ID usado para localizar la carpeta de fotos (mantiene compatibilidad)
    id_fotos = (
        id_excel
        if id_excel
        else construir_id(fecha)
    )

    # ID único para el mapa. Si dos excursiones comparten fecha,
    # evitamos que una sustituya a la otra en markerById.
    id_excursion = (
        id_excel
        if id_excel
        else f"{construir_id(fecha)}_{indice + 2}"
    )

    # --------------------------------------------------------
    # TRACK
    # --------------------------------------------------------

    track_confirmado = limpiar_texto(
        valor_columna(
            row,
            [
                "Track_confirmado",
                "TRACK_CONFIRMADO",
                "track_confirmado",
            ],
        )
    )

    track_sugerido = limpiar_texto(
        valor_columna(
            row,
            [
                "Track_Wikiloc_sugerido",
                "TRACK_SUGERIDO",
                "Track_sugerido",
            ],
        )
    )

    track = (
        track_confirmado
        if track_confirmado
        else track_sugerido
    )

    track = limpiar_track(track)

    # --------------------------------------------------------
    # LOGOS
    # --------------------------------------------------------

    logos_excel = valor_columna(
        row,
        ["LOGOS", "Logos", "logos"],
    )

    # --------------------------------------------------------
    # AÑOS SIN REGISTROS
    # --------------------------------------------------------
    #
    # IMPORTANTE:
    # Se procesan ANTES de validar las coordenadas.
    #
    # Así 2006/2007 pueden estar en el Excel sin coordenadas
    # ficticias.
    # --------------------------------------------------------

    if sin_registros:

        excursiones.append({
            "id": id_excursion,
            "fecha": fecha,
            "anio": anio,
            "sin_registros": True,
            "nombre": nombre or "Sin excursiones registradas",
            "poblacion": "",
            "provincia": "",
            "tipo": "",
            "dificultad": "",
            "track": "",
            "lat": None,
            "lon": None,
            "logos": [],
            "fotos": [],
        })

        continue

    # --------------------------------------------------------
    # COORDENADAS DE EXCURSIONES REALES
    # --------------------------------------------------------

    lat = valor_columna(
        row,
        ["LATITUD", "Latitud", "latitud"],
    )

    lon = valor_columna(
        row,
        ["LONGITUD", "Longitud", "longitud"],
    )

    try:
        lat = float(str(lat).replace(",", "."))
        lon = float(str(lon).replace(",", "."))

    except Exception:
        print(
            f"⚠️ Coordenadas no válidas "
            f"(fila Excel {indice + 2}): {nombre}"
        )
        continue

    # Comprobación adicional de coordenadas
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        print(
            f"⚠️ Coordenadas fuera de rango "
            f"(fila Excel {indice + 2}): {nombre}"
        )
        continue

    # --------------------------------------------------------
    # EXCURSIÓN REAL
    # --------------------------------------------------------

    excursiones.append({
        "id": id_excursion,
        "fecha": fecha,
        "anio": anio,
        "sin_registros": False,
        "nombre": nombre,
        "poblacion": poblacion,
        "provincia": provincia,
        "tipo": tipo,
        "dificultad": dificultad,
        "track": track,
        "lat": lat,
        "lon": lon,
        "logos": obtener_logos(logos_excel),
        "fotos": obtener_fotos(id_fotos),
    })


# ============================================================
# CONVERTIR LOS DATOS A JSON
# ============================================================

datos_json = json.dumps(
    excursiones,
    ensure_ascii=False
)


# ============================================================
# HTML DEL MAPA
# ============================================================

html = f"""<!DOCTYPE html>
<html lang="es">

<head>

<meta charset="utf-8">

<title>Mapa de excursiones ELAIOS</title>

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
>

<script
    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
</script>


<style>

body {{
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f4f6f5;
    color: #263238;
}}


/* ========================================================
   MARCADOR ELAIOS
   ======================================================== */

.marker-elaios {{
    width: 46px;
    height: 46px;

    border-radius: 50%;

    background: white;

    border: 3px solid #7b2cbf;

    display: flex;

    justify-content: center;
    align-items: center;

    box-shadow:
        0 4px 12px rgba(0,0,0,.35);
}}

.marker-elaios img {{
    width: 32px;
    height: 32px;
    object-fit: contain;
}}


/* ========================================================
   CABECERA
   ======================================================== */

.entidad-header {{
    display: grid;

    grid-template-columns:
        260px 1fr 320px;

    align-items: center;

    gap: 24px;

    padding: 22px 28px;

    background: white;

    border-bottom:
        1px solid #e5e5e5;
}}


.entidad-header-imagen {{
    background:

        linear-gradient(
            90deg,
            rgba(255,255,255,0.97) 0%,
            rgba(255,255,255,0.92) 48%,
            rgba(255,255,255,0.30) 100%
        ),

        url(
            "assets/cabecera/elaios_montana.jpg"
        );

    background-size: cover;
    background-position: center;
}}


.entidad-logo img {{
    max-width: 230px;
    height: auto;
}}


.entidad-titulo h1 {{
    margin: 0;

    font-size: 34px;

    color: #0f3d2e;
}}


.entidad-titulo p {{
    margin: 6px 0 0;

    font-size: 18px;

    color: #667085;
}}


.entidad-contacto {{
    border-left:
        2px solid #7b2cbf;

    padding-left: 22px;

    font-size: 15px;

    line-height: 1.7;

    background:
        rgba(255,255,255,0.75);

    border-radius: 10px;

    padding-top: 10px;
    padding-bottom: 10px;
}}


.entidad-contacto a {{
    color: #0f3d2e;

    font-weight: bold;

    text-decoration: none;
}}


.entidad-contacto a:hover {{
    text-decoration: underline;
}}


/* ========================================================
   ESTADÍSTICAS
   ======================================================== */

.stats {{
    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 12px;

    padding: 16px;
}}


.stat {{
    background: white;

    border-radius: 12px;

    padding: 14px;

    box-shadow:
        0 1px 5px rgba(0,0,0,.12);

    text-align: center;
}}


.stat strong {{
    display: block;

    font-size: 25px;

    color: #1f6f43;
}}


/* ========================================================
   MAPA + PANEL
   ======================================================== */

.layout {{
    display: grid;

    grid-template-columns:
        330px 1fr;

    height: 720px;
}}


aside {{
    background: white;

    padding: 16px;

    overflow: auto;

    border-right:
        1px solid #ddd;
}}


#map {{
    height: 720px;
}}


label {{
    display: block;

    margin-top: 10px;

    font-size: 13px;

    font-weight: bold;
}}


input,
select {{
    width: 100%;

    box-sizing: border-box;

    padding: 9px;

    margin-top: 5px;

    border:
        1px solid #ccc;

    border-radius: 8px;
}}


button {{
    width: 100%;

    margin-top: 12px;

    padding: 10px;

    background: #1f6f43;

    color: white;

    border: 0;

    border-radius: 8px;

    font-weight: bold;

    cursor: pointer;
}}


.list-item {{
    padding: 10px;

    border-bottom:
        1px solid #eee;

    cursor: pointer;
}}


.list-item:hover {{
    background: #eef8f1;
}}


.list-item strong {{
    color: #1f6f43;
}}


/* ========================================================
   POPUP
   ======================================================== */

.popup h3 {{
    margin: 0 0 8px;

    color: #1f6f43;
}}


.meta {{
    margin: 4px 0;
}}


.logos img {{
    height: 38px;

    margin:
        6px 8px 6px 0;

    vertical-align: middle;
}}


.gallery {{
    display: flex;

    gap: 7px;

    overflow-x: auto;

    max-width: 360px;

    margin-top: 8px;
}}


.gallery img {{
    width: 105px;

    height: 78px;

    object-fit: cover;

    border-radius: 8px;

    border:
        1px solid #ddd;
}}


.track {{
    display: inline-block;

    margin-top: 10px;

    padding: 8px 10px;

    background: #1f6f43;

    color: white !important;

    text-decoration: none;

    border-radius: 8px;
}}


/* ========================================================
   MENSAJE SIN REGISTROS
   ======================================================== */

.sin-registros {{
    margin-top: 15px;

    padding: 14px;

    background: #f6f2fa;

    border-left:
        4px solid #7b2cbf;

    border-radius: 8px;

    color: #4a3557;

    line-height: 1.4;
}}


/* ========================================================
   MÓVIL
   ======================================================== */

@media (max-width: 700px) {{

    body {{
        font-size: 15px;
    }}


    .entidad-header {{
        grid-template-columns: 1fr;

        padding: 16px;

        gap: 12px;

        text-align: center;
    }}


    .entidad-logo img {{
        max-width: 180px;
    }}


    .entidad-titulo h1 {{
        font-size: 24px;
    }}


    .entidad-titulo p {{
        font-size: 15px;
    }}


    .entidad-contacto {{
        font-size: 14px;

        border-left: 0;

        border-top:
            2px solid #7b2cbf;

        padding-left: 0;

        padding-top: 12px;
    }}


    .stats {{
        grid-template-columns:
            repeat(3, 1fr);

        padding: 10px;

        gap: 8px;
    }}


    .stat {{
        padding: 10px 5px;

        font-size: 12px;
    }}


    .stat strong {{
        font-size: 21px;
    }}


    .layout {{
        display: flex;

        flex-direction: column;

        height: auto;
    }}


    aside {{
        max-height: 360px;

        overflow: auto;

        border-right: 0;

        border-bottom:
            1px solid #ddd;
    }}


    #map {{
        height: 70vh;

        min-height: 420px;

        width: 100%;
    }}


    .gallery {{
        max-width: 280px;
    }}


    .gallery img {{
        width: 88px;

        height: 66px;
    }}


    .leaflet-popup-content {{
        max-width: 280px;
    }}

}}

</style>

</head>


<body>


<header
    class="entidad-header entidad-header-imagen"
>

    <div class="entidad-logo">

        <img
            src="assets/logos/elaios.png"
            alt="Logo Elaios Asociación Deportiva LGTBI+"
        >

    </div>


    <div class="entidad-titulo">

        <h1>
            Mapa de excursiones
        </h1>

        <p>
            Memoria interactiva de actividades
            realizadas por la asociación
        </p>

    </div>


    <div class="entidad-contacto">

        <div>
            🌐
            <a
                href="https://www.elaios.org/"
                target="_blank"
                rel="noopener noreferrer"
            >
                www.elaios.org
            </a>
        </div>

        <div>
            ✉️ montana@elaios.org
        </div>

        <div>
            📍 Aragón
        </div>

        <div>
            🏳️‍🌈 Asociación Deportiva LGTBI+
        </div>

    </div>

</header>


<section class="stats">

    <div class="stat">

        <strong id="stat-exc">
            0
        </strong>

        Excursiones

    </div>


    <div class="stat">

        <strong id="stat-anios">
            0
        </strong>

        Años

    </div>


    <div class="stat">

        <strong id="stat-prov">
            0
        </strong>

        Provincias

    </div>

</section>


<div class="layout">

    <aside>

        <label>
            Buscar excursión
        </label>

        <input
            id="buscar"
            placeholder="Ej. Moncayo, Gratal, Broto..."
        >


        <label>
            Año
        </label>

        <select id="filtro-anio">

            <option value="">
                Todos
            </option>

        </select>


        <label>
            Provincia
        </label>

        <select id="filtro-provincia">

            <option value="">
                Todas
            </option>

        </select>


        <label>
            Tipo
        </label>

        <select id="filtro-tipo">

            <option value="">
                Todos
            </option>

        </select>


        <label>
            Dificultad
        </label>

        <select id="filtro-dificultad">

            <option value="">
                Todas
            </option>

        </select>


        <label>
            Asociación
        </label>

        <select id="filtro-logo">

            <option value="">
                Todas
            </option>

        </select>


        <button id="limpiar">

            Limpiar filtros

        </button>


        <h3 id="contador"></h3>

        <div id="mensaje-sin-registros"></div>

        <div id="lista"></div>

    </aside>


    <main id="map"></main>

</div>


<script>


// ========================================================
// DATOS
// ========================================================

const excursiones = {datos_json};


// ========================================================
// MAPA
// ========================================================

const map = L.map("map");


L.tileLayer(
    "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
    {{
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap"
    }}
).addTo(map);


const markersLayer =
    L.layerGroup().addTo(map);


let markerById = {{}};


// ========================================================
// ICONO ELAIOS
// ========================================================

const iconoElaios = L.divIcon({{

    html: `
        <div class="marker-elaios">
            <img
                src="assets/logos/elaios.png"
                alt="ELAIOS"
            >
        </div>
    `,

    className: "",

    iconSize: [46, 46],

    iconAnchor: [23, 46],

    popupAnchor: [0, -40]

}});


// ========================================================
// FUNCIONES AUXILIARES JAVASCRIPT
// ========================================================

function unique(arr) {{

    return [
        ...new Set(
            arr.filter(Boolean)
        )
    ].sort();

}}


function basename(path) {{

    if (!path) return "";

    return path
        .split("/")
        .pop()
        .split("?")[0]
        .replace(
            /\\.(png|jpg|jpeg|webp|gif)$/i,
            ""
        );

}}


function nombreBonitoLogo(path) {{

    return basename(path)
        .replaceAll("_", " ")
        .toUpperCase();

}}


function formatearFecha(fecha) {{

    if (!fecha) return "-";

    const partes = fecha.split("_");

    if (partes.length === 3) {{
        return `${{partes[2]}}-${{partes[1]}}-${{partes[0]}}`;
    }}

    return fecha;

}}


function fillSelect(id, values) {{

    const sel =
        document.getElementById(id);

    values.forEach(v => {{

        const opt =
            document.createElement("option");

        opt.value = v;

        opt.textContent = v;

        sel.appendChild(opt);

    }});

}}


// ========================================================
// POPUP
// ========================================================

function popupHtml(e) {{

    const logos =
        (e.logos || [])
        .map(
            src =>
            `<img
                src="${{src}}"
                title="${{nombreBonitoLogo(src)}}"
                onerror="this.style.display='none'"
            >`
        )
        .join("");


    const fotos =
        (e.fotos || [])
        .map(
            src =>
            `<a
                href="${{src}}"
                target="_blank"
                rel="noopener noreferrer"
            >
                <img
                    src="${{src}}"
                    onerror="this.style.display='none'"
                >
            </a>`
        )
        .join("");


    const bloqueLogos =
        logos
        ? `<div class="logos">${{logos}}</div>`
        : "";


    const bloqueFotos =
        fotos
        ? `<div class="gallery">${{fotos}}</div>`
        : "<p><em>Sin fotos cargadas</em></p>";


    const track =
        e.track
        ? `<a
              class="track"
              href="${{e.track}}"
              target="_blank"
              rel="noopener noreferrer"
           >
              Ver track
           </a>`
        : "";


    return `

        <div class="popup">

            <h3>
                ${{e.nombre}}
            </h3>

            <div class="meta">
                <b>Fecha:</b>
                ${{formatearFecha(e.fecha)}}
            </div>

            <div class="meta">
                <b>Población:</b>
                ${{e.poblacion || "-"}}
            </div>

            <div class="meta">
                <b>Provincia:</b>
                ${{e.provincia || "-"}}
            </div>

            <div class="meta">
                <b>Tipo:</b>
                ${{e.tipo || "-"}}
            </div>

            <div class="meta">
                <b>Dificultad:</b>
                ${{e.dificultad || "-"}}
            </div>

            ${{bloqueLogos}}

            ${{bloqueFotos}}

            ${{track}}

        </div>

    `;

}}


// ========================================================
// FILTROS
// ========================================================

function aplicarFiltros() {{

    const q =
        document
        .getElementById("buscar")
        .value
        .toLowerCase()
        .trim();


    const anio =
        document
        .getElementById("filtro-anio")
        .value;


    const provincia =
        document
        .getElementById("filtro-provincia")
        .value;


    const tipo =
        document
        .getElementById("filtro-tipo")
        .value;


    const dificultad =
        document
        .getElementById("filtro-dificultad")
        .value;


    const logo =
        document
        .getElementById("filtro-logo")
        .value;


    return excursiones.filter(e => {{

        const texto = `
            ${{e.nombre}}
            ${{e.poblacion}}
            ${{e.provincia}}
            ${{e.tipo}}
            ${{e.dificultad}}
        `.toLowerCase();


        const logos =
            (e.logos || [])
            .map(basename);


        return (

            (!q ||
                texto.includes(q)
            )

            &&

            (!anio ||
                e.anio == anio
            )

            &&

            (!provincia ||
                e.provincia == provincia
            )

            &&

            (!tipo ||
                e.tipo == tipo
            )

            &&

            (!dificultad ||
                e.dificultad == dificultad
            )

            &&

            (!logo ||
                logos.includes(logo)
            )

        );

    }});

}}


// ========================================================
// PINTAR MAPA
// ========================================================

function pintar() {{

    const datos =
        aplicarFiltros();


    markersLayer.clearLayers();


    markerById = {{}};


    const bounds = [];


    const excursionesReales =
        datos.filter(
            e => !e.sin_registros
        );


    // ----------------------------------------------------
    // COORDENADAS REPETIDAS
    // ----------------------------------------------------
    // Si varias excursiones tienen exactamente el mismo punto,
    // las separamos SOLO visualmente unos metros alrededor del
    // punto real. Así todos los marcadores quedan accesibles.

    const gruposCoordenadas = {{}};

    excursionesReales.forEach(e => {{
        if (e.lat === null || e.lon === null) return;

        const clave = `${{e.lat.toFixed(6)}},${{e.lon.toFixed(6)}}`;

        if (!gruposCoordenadas[clave]) {{
            gruposCoordenadas[clave] = [];
        }}

        gruposCoordenadas[clave].push(e.id);
    }});


    // ----------------------------------------------------
    // CREAR MARCADORES
    // ----------------------------------------------------

    excursionesReales.forEach(e => {{

        // Seguridad adicional:
        // nunca intentamos dibujar coordenadas vacías.
        if (
            e.lat === null ||
            e.lon === null
        ) {{
            return;
        }}

        let latVisual = e.lat;
        let lonVisual = e.lon;

        const clave = `${{e.lat.toFixed(6)}},${{e.lon.toFixed(6)}}`;
        const grupo = gruposCoordenadas[clave] || [];

        if (grupo.length > 1) {{
            const posicion = grupo.indexOf(e.id);
            const angulo = (2 * Math.PI * posicion) / grupo.length;
            const radio = 0.00018;

            latVisual = e.lat + Math.sin(angulo) * radio;
            lonVisual = e.lon + Math.cos(angulo) * radio;
        }}


        const marker =
            L.marker(
                [latVisual, lonVisual],
                {{
                    icon: iconoElaios
                }}
            )

            .bindPopup(
                popupHtml(e),
                {{
                    maxWidth: 420
                }}
            )

            .bindTooltip(
                e.nombre
            );


        marker.addTo(
            markersLayer
        );


        markerById[e.id] =
            marker;


        bounds.push(
            [latVisual, lonVisual]
        );

    }});


    // ----------------------------------------------------
    // AJUSTAR MAPA
    // ----------------------------------------------------

    if (bounds.length) {{

        map.fitBounds(
            bounds,
            {{
                padding: [30, 30]
            }}
        );

    }} else {{

        map.setView(
            [41.65, -0.9],
            7
        );

    }}


    // ----------------------------------------------------
    // CONTADOR Y MENSAJES
    // ----------------------------------------------------

    const contador =
        document.getElementById(
            "contador"
        );


    const mensaje =
        document.getElementById(
            "mensaje-sin-registros"
        );


    mensaje.innerHTML = "";


        if (excursionesReales.length === 0
        ) {{

        contador.textContent =
            "0 excursiones visibles";


        const anioSeleccionado =
            document
            .getElementById(
                "filtro-anio"
            )
            .value;


        const anioSinRegistros =
            anioSeleccionado &&
            excursiones.some(
                e =>
                    e.anio == anioSeleccionado &&
                    e.sin_registros
            );

        if (anioSinRegistros) {{

            mensaje.innerHTML = `

                <div class="sin-registros">

                    <strong>
                        ${{anioSeleccionado}}
                    </strong>

                    <br>

                    No hay excursiones
                    registradas para este año.

                </div>

            `;

        }} else {{

            mensaje.innerHTML = `

                <div class="sin-registros">

                    No hay excursiones
                    que coincidan con
                    los filtros seleccionados.

                </div>

            `;

        }}

    }} else {{

        contador.textContent =
            `${{excursionesReales.length}} excursiones visibles`;

    }}


    // ----------------------------------------------------
    // LISTA LATERAL
    // ----------------------------------------------------

    document
        .getElementById("lista")
        .innerHTML =

        excursionesReales
        .map(e => `

            <div
                class="list-item"
                data-id="${{e.id}}"
            >

                <strong>
                    ${{e.nombre}}
                </strong>

                <br>

                <small>
                    ${{formatearFecha(e.fecha)}}
                    ·
                    ${{e.poblacion || ""}}
                </small>

            </div>

        `)
        .join("");


    // ----------------------------------------------------
    // CLIC EN LA LISTA
    // ----------------------------------------------------

    document
        .querySelectorAll(
            ".list-item"
        )
        .forEach(item => {{

            item.addEventListener(
                "click",
                () => {{

                    const m =
                        markerById[
                            item.dataset.id
                        ];


                    if (m) {{

                        map.setView(
                            m.getLatLng(),
                            13
                        );

                        m.openPopup();

                    }}

                }}
            );

        }});

}}


// ========================================================
// INICIALIZACIÓN
// ========================================================

function inicializar() {{

    // ----------------------------------------------------
    // FILTRO AÑOS
    // Incluye también años SIN_REGISTROS
    // ----------------------------------------------------

    fillSelect(
        "filtro-anio",
        unique(
            excursiones.map(
                e => e.anio
            )
        )
    );


    // ----------------------------------------------------
    // RESTO DE FILTROS
    // Solo utilizamos excursiones reales.
    // ----------------------------------------------------

    const excursionesRealesTotal =
        excursiones.filter(
            e => !e.sin_registros
        );


    fillSelect(
        "filtro-provincia",
        unique(
            excursionesRealesTotal.map(
                e => e.provincia
            )
        )
    );


    fillSelect(
        "filtro-tipo",
        unique(
            excursionesRealesTotal.map(
                e => e.tipo
            )
        )
    );


    fillSelect(
        "filtro-dificultad",
        unique(
            excursionesRealesTotal.map(
                e => e.dificultad
            )
        )
    );


    fillSelect(
        "filtro-logo",
        unique(
            excursionesRealesTotal.flatMap(
                e =>
                (e.logos || [])
                .map(basename)
            )
        )
    );


    // ----------------------------------------------------
    // ESTADÍSTICAS
    // ----------------------------------------------------

    document
        .getElementById(
            "stat-exc"
        )
        .textContent =
        excursionesRealesTotal.length;


    // Aquí SÍ contamos 2006/2007 porque forman parte
    // del histórico aunque no tengan excursiones.
    document
        .getElementById(
            "stat-anios"
        )
        .textContent =
        unique(
            excursiones.map(
                e => e.anio
            )
        ).length;


    // Provincias únicamente de excursiones reales.
    document
        .getElementById(
            "stat-prov"
        )
        .textContent =
        unique(
            excursionesRealesTotal.map(
                e => e.provincia
            )
        ).length;


    // ----------------------------------------------------
    // EVENTOS DE FILTROS
    // ----------------------------------------------------

    [
        "buscar",
        "filtro-anio",
        "filtro-provincia",
        "filtro-tipo",
        "filtro-dificultad",
        "filtro-logo"
    ]

    .forEach(id =>

        document
        .getElementById(id)
        .addEventListener(
            "input",
            pintar
        )

    );


    // ----------------------------------------------------
    // LIMPIAR FILTROS
    // ----------------------------------------------------

    document
        .getElementById(
            "limpiar"
        )
        .addEventListener(
            "click",
            () => {{

                document
                    .getElementById(
                        "buscar"
                    )
                    .value = "";


                [
                    "filtro-anio",
                    "filtro-provincia",
                    "filtro-tipo",
                    "filtro-dificultad",
                    "filtro-logo"
                ]

                .forEach(id =>

                    document
                        .getElementById(id)
                        .value = ""

                );


                pintar();

            }}
        );


    // ----------------------------------------------------
    // PRIMER DIBUJADO
    // ----------------------------------------------------

    pintar();

}}


inicializar();


</script>


</body>

</html>
"""


# ============================================================
# GUARDAR HTML
# ============================================================

OUTPUT_HTML.write_text(
    html,
    encoding="utf-8"
)


# ============================================================
# RESUMEN EN CONSOLA
# ============================================================

excursiones_reales = [
    e
    for e in excursiones
    if not e["sin_registros"]
]

anios_sin_registros = [
    e["anio"]
    for e in excursiones
    if e["sin_registros"]
]


print()
print("==============================================")
print("  MAPA ELAIOS GENERADO CORRECTAMENTE")
print("==============================================")
print()

print(f"📍 Archivo creado: {OUTPUT_HTML}")

print(
    f"🥾 Excursiones reales: "
    f"{len(excursiones_reales)}"
)

print(
    f"📅 Años incluidos: "
    f"{len(set(e['anio'] for e in excursiones if e['anio']))}"
)

if anios_sin_registros:
    print(
        "ℹ️ Años sin registros: "
        + ", ".join(
            sorted(set(anios_sin_registros))
        )
    )

print()