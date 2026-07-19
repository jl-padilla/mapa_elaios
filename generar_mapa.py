import json
import re
from pathlib import Path

import pandas as pd


# =========================
# CONFIGURACIÓN
# =========================

BASE_DIR = Path(__file__).parent

EXCEL_PATH = BASE_DIR / "datos" / "excursiones.xlsx"
ASSETS_DIR = BASE_DIR / "assets"
LOGOS_DIR = ASSETS_DIR / "logos"
FOTOS_DIR = ASSETS_DIR / "excursiones"

OUTPUT_HTML = BASE_DIR / "index.html"

EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


# =========================
# FUNCIONES AUXILIARES
# =========================

def limpiar_texto(valor):
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def normalizar_logo(nombre):
    nombre = limpiar_texto(nombre).lower()
    nombre = nombre.replace(" ", "_")
    nombre = nombre.replace("-", "_")
    nombre = re.sub(r"[^a-z0-9_]", "", nombre)
    return nombre


def valor_columna(row, posibles_nombres):
    for col in posibles_nombres:
        if col in row:
            return row[col]
    return ""


def obtener_logos(valor_logos):
    if pd.isna(valor_logos):
        return []

    logos = []

    for parte in str(valor_logos).split(";"):
        nombre = normalizar_logo(parte)

        if not nombre:
            continue

        for extension in [".png", ".jpg", ".jpeg", ".webp"]:
            ruta_logo = LOGOS_DIR / f"{nombre}{extension}"

            if ruta_logo.exists():
                logos.append(f"assets/logos/{nombre}{extension}")
                break
        else:
            print(f"⚠️ Logo no encontrado: {nombre}")

    return logos


def obtener_fotos(id_excursion):
    carpeta = FOTOS_DIR / id_excursion

    if not carpeta.exists():
        print(f"⚠️ Carpeta de fotos no encontrada: {carpeta}")
        return []

    fotos = []

    for archivo in sorted(carpeta.iterdir()):
        if archivo.is_file() and archivo.suffix.lower() in EXTENSIONES_IMAGEN:
            fotos.append(f"assets/excursiones/{id_excursion}/{archivo.name}")

    return fotos


def construir_id(fecha):
    fecha_txt = limpiar_texto(fecha).replace("-", "_").replace("/", "_")
    return fecha_txt[:10] if fecha_txt else "sin_fecha"


# =========================
# LECTURA DEL EXCEL
# =========================

df = pd.read_excel(EXCEL_PATH)

excursiones = []

for _, row in df.iterrows():
    fecha = limpiar_texto(valor_columna(row, ["FECHA", "Fecha", "fecha"]))
    nombre = limpiar_texto(valor_columna(row, ["EXCURSION", "Excursion", "Excursión", "NOMBRE", "Nombre"]))
    poblacion = limpiar_texto(valor_columna(row, ["POBLACION", "Poblacion", "Población"]))
    provincia = limpiar_texto(valor_columna(row, ["PROVINCIA", "Provincia"]))
    tipo = limpiar_texto(valor_columna(row, ["TIPO", "Tipo", "TIPO_ACTIVIDAD"]))
    dificultad = limpiar_texto(valor_columna(row, ["DIFICULTAD", "Dificultad"]))


    track_confirmado = limpiar_texto(valor_columna(row, ["Track_confirmado", "TRACK_CONFIRMADO", "track_confirmado"]))
    track_sugerido = limpiar_texto(valor_columna(row, ["Track_Wikiloc_sugerido", "TRACK_SUGERIDO", "Track_sugerido"]))
    track = track_confirmado if track_confirmado else track_sugerido

    logos_excel = valor_columna(row, ["LOGOS", "Logos", "logos"])

    lat = valor_columna(row, ["LATITUD", "Latitud", "latitud"])
    lon = valor_columna(row, ["LONGITUD", "Longitud", "longitud"])

    id_excel = limpiar_texto(valor_columna(row, ["ID_EXCURSION", "ID", "id"]))
    id_excursion = id_excel if id_excel else construir_id(fecha)

    try:
        lat = float(str(lat).replace(",", "."))
        lon = float(str(lon).replace(",", "."))
    except Exception:
        print(f"⚠️ Coordenadas no válidas en: {nombre}")
        continue

    anio = fecha[:4] if fecha else ""

    excursiones.append({
        "id": id_excursion,
        "fecha": fecha,
        "anio": anio,
        "nombre": nombre,
        "poblacion": poblacion,
        "provincia": provincia,
        "tipo": tipo,
        "dificultad": dificultad,
        "track": track,
        "lat": lat,
        "lon": lon,
        "logos": obtener_logos(logos_excel),
        "fotos": obtener_fotos(id_excursion),
    })


# =========================
# HTML DEL MAPA
# =========================

datos_json = json.dumps(excursiones, ensure_ascii=False)

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Mapa de excursiones ELAIOS</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<style>
body {{
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f4f6f5;
    color: #263238;
}}

.marker-elaios {{
    width: 46px;
    height: 46px;
    border-radius: 50%;
    background: white;
    border: 3px solid #7b2cbf;
    display: flex;
    justify-content: center;
    align-items: center;
    box-shadow: 0 4px 12px rgba(0,0,0,.35);
}}

.marker-elaios img {{
    width: 32px;
    height: 32px;
    object-fit: contain;
}}

.entidad-header {{
    display: grid;
    grid-template-columns: 260px 1fr 320px;
    align-items: center;
    gap: 24px;
    padding: 22px 28px;
    background: white;
    border-bottom: 1px solid #e5e5e5;
}}

.entidad-header-imagen {{
    background:
        linear-gradient(90deg, rgba(255,255,255,0.97) 0%, rgba(255,255,255,0.92) 48%, rgba(255,255,255,0.30) 100%),
        url("assets/cabecera/elaios_montana.jpg");
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
    border-left: 2px solid #7b2cbf;
    padding-left: 22px;
    font-size: 15px;
    line-height: 1.7;
    background: rgba(255,255,255,0.75);
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

.stats {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    padding: 16px;
}}

.stat {{
    background: white;
    border-radius: 12px;
    padding: 14px;
    box-shadow: 0 1px 5px rgba(0,0,0,.12);
}}

.stat strong {{
    display: block;
    font-size: 25px;
    color: #1f6f43;
}}

.layout {{
    display: grid;
    grid-template-columns: 330px 1fr;
    height: 720px;
}}

aside {{
    background: white;
    padding: 16px;
    overflow: auto;
    border-right: 1px solid #ddd;
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

input, select {{
    width: 100%;
    box-sizing: border-box;
    padding: 9px;
    margin-top: 5px;
    border: 1px solid #ccc;
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
    border-bottom: 1px solid #eee;
    cursor: pointer;
}}

.list-item:hover {{
    background: #eef8f1;
}}

.list-item strong {{
    color: #1f6f43;
}}

.popup h3 {{
    margin: 0 0 8px;
    color: #1f6f43;
}}

.meta {{
    margin: 4px 0;
}}

.logos img {{
    height: 38px;
    margin: 6px 8px 6px 0;
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
    border: 1px solid #ddd;
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

    .entidad-contacto {{
        font-size: 14px;
        border-left: 0;
        border-top: 2px solid #7b2cbf;
        padding-left: 0;
    }}

    .stats {{
        grid-template-columns: repeat(2, 1fr);
        padding: 10px;
        gap: 8px;
    }}

    .stat {{
        padding: 10px;
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
        border-bottom: 1px solid #ddd;
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

<header class="entidad-header entidad-header-imagen">

    <div class="entidad-logo">
        <img src="assets/logos/elaios.png" alt="Logo Elaios Asociación Deportiva LGTBI+">
    </div>

    <div class="entidad-titulo">
        <h1>Mapa de excursiones</h1>
        <p>Memoria interactiva de actividades realizadas por la asociación</p>
    </div>

    <div class="entidad-contacto">
        <div>🌐 <a href="https://www.elaios.org/" target="_blank">www.elaios.org</a></div>
        <div>✉️ montana@elaios.org</div>
        <div>📍 Zaragoza, Aragón</div>
        <div>🏳️‍🌈 Asociación Deportiva LGTBI+</div>
    </div>

</header>

<section class="stats">
    <div class="stat"><strong id="stat-exc">0</strong>Excursiones</div>
    <div class="stat"><strong id="stat-anios">0</strong>Años</div>
    <div class="stat"><strong id="stat-prov">0</strong>Provincias</div>
</section>

<div class="layout">
    <aside>
        <label>Buscar excursión</label>
        <input id="buscar" placeholder="Ej. Moncayo, Gratal, Broto...">

        <label>Año</label>
        <select id="filtro-anio"><option value="">Todos</option></select>

        <label>Provincia</label>
        <select id="filtro-provincia"><option value="">Todas</option></select>

        <label>Tipo</label>
        <select id="filtro-tipo"><option value="">Todos</option></select>

        <label>Dificultad</label>
        <select id="filtro-dificultad"><option value="">Todas</option></select>

        <label>Asociación</label>
        <select id="filtro-logo"><option value="">Todas</option></select>

        <button id="limpiar">Limpiar filtros</button>

        <h3 id="contador"></h3>
        <div id="lista"></div>
    </aside>

    <main id="map"></main>
</div>

<script>
const excursiones = {datos_json};

const map = L.map("map");

L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap"
}}).addTo(map);

const markersLayer = L.layerGroup().addTo(map);
let markerById = {{}};

const iconoElaios = L.divIcon({{
    html: `
        <div class="marker-elaios">
            <img src="assets/logos/elaios.png" alt="ELAIOS">
        </div>
    `,
    className: "",
    iconSize: [46, 46],
    iconAnchor: [23, 46],
    popupAnchor: [0, -40]
}});

function unique(arr) {{
    return [...new Set(arr.filter(Boolean))].sort();
}}

function basename(path) {{
    if (!path) return "";
    return path.split("/").pop().split("?")[0].replace(/\\.(png|jpg|jpeg|webp|gif)$/i, "");
}}

function nombreBonitoLogo(path) {{
    return basename(path).replaceAll("_", " ").toUpperCase();
}}

function fillSelect(id, values) {{
    const sel = document.getElementById(id);
    values.forEach(v => {{
        const opt = document.createElement("option");
        opt.value = v;
        opt.textContent = v;
        sel.appendChild(opt);
    }});
}}

function popupHtml(e) {{
    const logos = (e.logos || [])
        .map(src => `<img src="${{src}}" title="${{nombreBonitoLogo(src)}}" onerror="this.style.display='none'">`)
        .join("");

    const fotos = (e.fotos || [])
        .map(src => `<a href="${{src}}" target="_blank"><img src="${{src}}" onerror="this.style.display='none'"></a>`)
        .join("");

    const bloqueLogos = logos ? `<div class="logos">${{logos}}</div>` : "";
    const bloqueFotos = fotos ? `<div class="gallery">${{fotos}}</div>` : "<p><em>Sin fotos cargadas</em></p>";
    const track = e.track ? `<a class="track" href="${{e.track}}" target="_blank">Ver track</a>` : "";

    return `
    <div class="popup">
        <h3>${{e.nombre}}</h3>
        <div class="meta"><b>Fecha:</b> ${{e.fecha || "-"}}</div>
        <div class="meta"><b>Población:</b> ${{e.poblacion || "-"}}</div>
        <div class="meta"><b>Provincia:</b> ${{e.provincia || "-"}}</div>
        <div class="meta"><b>Tipo:</b> ${{e.tipo || "-"}}</div>
        <div class="meta"><b>Dificultad:</b> ${{e.dificultad || "-"}}</div>
        ${{bloqueLogos}}
        ${{bloqueFotos}}
        ${{track}}
    </div>`;
}}

function aplicarFiltros() {{
    const q = document.getElementById("buscar").value.toLowerCase().trim();
    const anio = document.getElementById("filtro-anio").value;
    const provincia = document.getElementById("filtro-provincia").value;
    const tipo = document.getElementById("filtro-tipo").value;
    const dificultad = document.getElementById("filtro-dificultad").value;
    const logo = document.getElementById("filtro-logo").value;

    return excursiones.filter(e => {{
        const texto = `${{e.nombre}} ${{e.poblacion}} ${{e.provincia}} ${{e.tipo}} ${{e.dificultad}}`.toLowerCase();
        const logos = (e.logos || []).map(basename);

        return (!q || texto.includes(q)) &&
               (!anio || e.anio == anio) &&
               (!provincia || e.provincia == provincia) &&
               (!tipo || e.tipo == tipo) &&
               (!dificultad || e.dificultad == dificultad) &&
               (!logo || logos.includes(logo));
    }});
}}

function pintar() {{
    const datos = aplicarFiltros();
    markersLayer.clearLayers();
    markerById = {{}};

    const bounds = [];

    datos.forEach(e => {{
        const marker = L.marker([e.lat, e.lon], {{icon: iconoElaios}})
            .bindPopup(popupHtml(e), {{maxWidth: 420}})
            .bindTooltip(e.nombre);

        marker.addTo(markersLayer);
        markerById[e.id] = marker;
        bounds.push([e.lat, e.lon]);
    }});

    if (bounds.length) {{
        map.fitBounds(bounds, {{padding: [30, 30]}});
    }} else {{
        map.setView([41.65, -0.9], 7);
    }}

    document.getElementById("contador").textContent = `${{datos.length}} excursiones visibles`;

    document.getElementById("lista").innerHTML = datos.map(e => `
        <div class="list-item" data-id="${{e.id}}">
            <strong>${{e.nombre}}</strong><br>
            <small>${{e.fecha || ""}} · ${{e.poblacion || ""}} </small>
        </div>
    `).join("");

    document.querySelectorAll(".list-item").forEach(item => {{
        item.addEventListener("click", () => {{
            const m = markerById[item.dataset.id];
            if (m) {{
                map.setView(m.getLatLng(), 13);
                m.openPopup();
            }}
        }});
    }});
}}

function inicializar() {{
    fillSelect("filtro-anio", unique(excursiones.map(e => e.anio)));
    fillSelect("filtro-provincia", unique(excursiones.map(e => e.provincia)));
    fillSelect("filtro-tipo", unique(excursiones.map(e => e.tipo)));
    fillSelect("filtro-dificultad", unique(excursiones.map(e => e.dificultad)));
    fillSelect("filtro-logo", unique(excursiones.flatMap(e => (e.logos || []).map(basename))));

    document.getElementById("stat-exc").textContent = excursiones.length;
    document.getElementById("stat-anios").textContent = unique(excursiones.map(e => e.anio)).length;
    document.getElementById("stat-prov").textContent = unique(excursiones.map(e => e.provincia)).length;

    ["buscar", "filtro-anio", "filtro-provincia", "filtro-tipo", "filtro-dificultad", "filtro-logo"]
        .forEach(id => document.getElementById(id).addEventListener("input", pintar));

    document.getElementById("limpiar").addEventListener("click", () => {{
        document.getElementById("buscar").value = "";
        ["filtro-anio", "filtro-provincia", "filtro-tipo", "filtro-dificultad", "filtro-logo"]
            .forEach(id => document.getElementById(id).value = "");
        pintar();
    }});

    pintar();
}}

inicializar();
</script>

</body>
</html>
"""

OUTPUT_HTML.write_text(html, encoding="utf-8")

print("✅ Mapa generado correctamente")
print(f"📍 Archivo creado: {OUTPUT_HTML}")
print(f"📊 Excursiones incluidas: {len(excursiones)}")