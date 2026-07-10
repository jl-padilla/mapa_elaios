# Proyecto demo: Mapa de excursiones

Este paquete permite generar un mapa interactivo desde un Excel usando Python. Los socios o la gerencia solo abrirán el archivo HTML generado; no tienen que ejecutar Python.

## 1. Estructura de carpetas

```text
proyecto_mapa_excursiones/
├── datos/
│   └── excursiones.xlsx
├── assets/
│   ├── logos/
│   │   ├── elaios.png
│   │   ├── dracs.png
│   │   └── panteres.png
│   └── excursiones/
│       ├── 2025_01_01/
│       │   ├── foto1.jpg
│       │   └── foto2.jpg
│       └── 2025_02_01/
│           └── foto1.jpg
├── salida/
│   └── mapa_excursiones.html
├── generar_mapa.py
└── requirements.txt
```

## 2. Instalar dependencias

Desde la carpeta del proyecto:

```bash
pip install -r requirements.txt
```

## 3. Generar el mapa

```bash
python generar_mapa.py
```

El mapa se crea en:

```text
salida/mapa_excursiones.html
```

Puedes abrirlo con doble clic en Chrome, Edge o Firefox.

## 4. Excel recomendado

Para que el mantenimiento sea sencillo, usa estas columnas:

| Columna | Obligatoria | Ejemplo | Observación |
|---|---:|---|---|
| FECHA | Sí | 2025_01_01 | Sirve también como carpeta de fotos |
| AÑO | Sí | 2025 | Para filtro por año |
| EXCURSION | Sí | Torrollones de la Gabarda | Nombre visible en mapa |
| POBLACION | Recomendable | Grañén | Sale en la ficha |
| LATITUD | Sí | 41.9422982 | Coordenada decimal |
| LONGITUD | Sí | -0.3729445 | Coordenada decimal |
| PARTICIPANTES | Recomendable | 25 | Para estadísticas |
| TRACK | Recomendable | https://... | Enlace a Wikiloc, GPX o similar |
| LOGOS | Recomendable | elaios;dracs | Una sola columna, separada por punto y coma |
| FOTOS | Opcional | foto1.jpg;foto2.jpg | Galería de fotos |
| TIPO | Opcional | Senderismo | Filtro futuro |
| DIFICULTAD | Opcional | baja | Filtro actual |
| PROVINCIA | Opcional | Huesca | Filtro actual |

## 5. Cómo gestionar logos

Guarda los logos en:

```text
assets/logos/
```

Ejemplo:

```text
assets/logos/elaios.png
assets/logos/dracs.png
assets/logos/panteres.png
```

En el Excel, en la columna `LOGOS`, escribe solo los códigos:

```text
elaios;dracs
```

No escribas rutas completas tipo `C:\Users\...`.

## 6. Cómo gestionar fotos en galería

Crea una carpeta por excursión usando el código de la fecha:

```text
assets/excursiones/2025_01_01/
```

Dentro guarda las fotos:

```text
foto1.jpg
foto2.jpg
foto3.jpg
```

En el Excel, en la columna `FOTOS`, puedes escribir:

```text
foto1.jpg;foto2.jpg;foto3.jpg
```

Si dejas la columna `FOTOS` vacía, el script intentará cargar automáticamente todas las imágenes que haya dentro de la carpeta de esa excursión.

## 7. Para enseñar la demo a gerencia

La forma más sencilla es enviar o abrir:

```text
salida/mapa_excursiones.html
```

Para que se vean fotos y logos, conserva la estructura de carpetas junto al HTML o abre el proyecto completo desde la carpeta original.

## 8. Para subirlo a WordPress más adelante

Cuando esté aprobado, sube esta estructura a:

```text
/wp-content/uploads/mapa_excursiones/
```

Y en una página de WordPress inserta:

```html
<iframe src="/wp-content/uploads/mapa_excursiones/salida/mapa_excursiones.html" width="100%" height="760" style="border:0;" loading="lazy"></iframe>
```

En `generar_mapa.py`, cambia:

```python
BASE_URL_PUBLICA = ""
```

por:

```python
BASE_URL_PUBLICA = "/wp-content/uploads/mapa_excursiones/"
```

Así las imágenes y logos apuntarán correctamente a la web.
