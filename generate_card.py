
import json
import re
import sys
from copy import deepcopy
from pathlib import Path


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "outputFiles"

HTML_TEMPLATE = TEMPLATES_DIR / "template_card.html"
VARIABLE_PATTERN = re.compile(r"\{\{(.+?)\}\}")

DEFAULT_CARD_SIZE = {"w": "44mm", "h": "67mm"}

PARAGRAPH_SECTIONS = (
    "objectiveParagraphs",
    "rewardParagraphs",
    "deploymentParagraphs",
)


# ============================================================
# LECTURA DE ARCHIVOS
# ============================================================

def leer_json(path):
    """Lee un archivo JSON y devuelve sus datos."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def leer_texto(path):
    """Lee un archivo de texto."""
    return path.read_text(encoding="utf-8")


def cargar_entradas(card_id):
    """Carga la configuración, los datos y las plantillas."""
    config = leer_json(CONFIG_PATH)

    card_config = config.get("cardTypeList", {}).get(str(card_id))
    if card_config is None:
        raise ValueError(
            f"La carta con ID {card_id} no existe en la configuración."
        )

    json_path = DATA_DIR / card_config["json"]
    quest_template_path = TEMPLATES_DIR / card_config["template"]
    output_path = OUTPUT_DIR / card_config["output"]

    for path in (json_path, HTML_TEMPLATE, quest_template_path):
        if not path.is_file():
            raise FileNotFoundError(f"No se encuentra el archivo: {path}")

    return {
        "config": config,
        "card_config": card_config,
        "data": leer_json(json_path),
        "html_template": leer_texto(HTML_TEMPLATE),
        "quest_template": leer_texto(quest_template_path),
        "json_path": json_path,
        "output_path": output_path,
    }


# ============================================================
# UTILIDADES DE TRANSFORMACIÓN
# ============================================================

def obtener_valor_anidado(data, path):
    """Obtiene un valor mediante una ruta como 'backCard.title'."""
    value = data

    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return f"{{{{ {path} }}}}"

        value = value[key]

    return value


def unir_parrafos(paragraphs):
    """Convierte una lista de párrafos en HTML."""
    return "".join(
        f'<p class="body">{paragraph}</p>'
        for paragraph in paragraphs
    )


def generar_encabezados(headers):
    """Genera las celdas de encabezado de una tabla."""
    return "".join(f"<th>{header}</th>" for header in headers)


def generar_filas_monstruos(rows):
    """Genera las filas HTML de la tabla de monstruos."""
    return "".join(
        f"""
        <tr>
            <td class="level">{row.get('level', '')}</td>
            <td>{row.get('monster', '')}</td>
            <td>{row.get('item', '')}</td>
        </tr>
        """
        for row in rows
    )


def generar_ranuras_unidades(quantity, stat_slots):
    """Genera las filas de seguimiento de unidades."""
    return "".join(
        f"""
        <div class="row-header-cell">{number}</div>
        {"<div class='track-cell'></div>" * stat_slots}
        """
        for number in range(1, quantity + 1)
    )


def generar_equipo(equipment):
    """Muestra los elementos del equipo en línea, con viñetas."""
    if not isinstance(equipment, list):
        return equipment

    return " &nbsp; ".join(
        f"&bull; {item}" for item in equipment
    )


def generar_combate_cuerpo_a_cuerpo(melee):
    """Genera la cuadrícula de combate cuerpo a cuerpo."""
    headers = ["HA del Blanco", *range(1, 13), "D. Daño"]

    header_html = "".join(
        f'<div class="cg-cell cg-header">{header}</div>'
        for header in headers
    )

    rolls_html = "".join(
        f'<div class="cg-cell">{roll}</div>'
        for roll in melee.get("rolls", [])
    )

    damage = melee.get("damage", "")

    return f"""
    <div class="combat-grid">
        {header_html}
        <div class="cg-cell cg-header">Tirada para Impactar</div>
        {rolls_html}
        <div class="cg-cell" style="font-weight:700;">{damage}</div>
    </div>
    """


# ============================================================
# PROCESAMIENTO DE DATOS DE LAS CARTAS
# ============================================================

def transformar_secciones(data):
    """
    Devuelve una copia de los datos con las secciones
    que requieren HTML ya transformadas.
    """
    result = deepcopy(data)

    front = result.get("frontCard", {}).get("sections", {})
    back = result.get("backCard", {}).get("sections", {})

    for key in ("loreParagraphs",):
        if key in back:
            back[key] = unir_parrafos(back[key])

    for key in PARAGRAPH_SECTIONS:
        if key in front:
            front[key] = unir_parrafos(front[key])

    if "monstersTableHeaders" in front:
        front["monstersTableHeaders"] = generar_encabezados(
            front["monstersTableHeaders"]
        )

    if "monstersTableRows" in front:
        front["monstersTableRows"] = generar_filas_monstruos(
            front["monstersTableRows"]
        )

    if "unitSlots" in front:
        front["unitSlotsRows"] = generar_ranuras_unidades(
            front["unitSlots"], front["statSlots"]
        )

    if "equipment" in front:
        front["equipment"] = generar_equipo(front["equipment"])

    if isinstance(front.get("meleeCombat"), dict):
        front["meleeCombatHtml"] = generar_combate_cuerpo_a_cuerpo(
            front["meleeCombat"]
        )

    return result


# ============================================================
# CONFIGURACIÓN DEL DISEÑO
# ============================================================

def obtener_dimensiones(config, meta):
    """Calcula el ancho y alto de la carta según su orientación."""
    card_size = meta.get("cardSize", "tarot")
    is_landscape = meta.get("isLandscapeCard", True)

    dimensions = config.get("cardSizeList", {}).get(
        card_size,
        DEFAULT_CARD_SIZE,
    )

    if is_landscape:
        return dimensions["h"], dimensions["w"]

    return dimensions["w"], dimensions["h"]

def obtener_bg(config, meta):
    is_landscape = meta.get("isLandscapeCard", True)
    
    bg_vertical = config.get("backgroundImageList").get("oldPaperWhiteVertical", "")
    bg_horizontal = config.get("backgroundImageList").get("oldPaperWhiteHorizontal", "")
    
    background_image_by_orientation = bg_horizontal if is_landscape else bg_vertical
    
    return background_image_by_orientation 

def obtener_matriz(matrix):
    """Convierte '3x2' en (3, 2), usando (1, 1) si es inválido."""
    try:
        cols, rows = map(int, matrix.lower().split("x"))
        if cols < 1 or rows < 1:
            raise ValueError
        return cols, rows
    except (ValueError, AttributeError):
        return 1, 1


def generar_estilos(meta, config, data):
    """Construye los estilos dinámicos de impresión."""
    card_w, card_h = obtener_dimensiones(config, meta)
    
    bg_by_orientation = obtener_bg(config, meta)

    cols, rows = obtener_matriz(
        meta.get("multipleCardPrintMatrix", "1x1")
    )

    paper_size = meta.get("paperSize", "letter")
        
    stat_slots = data.get("frontCard", {}).get("sections", {}).get("statSlots", 1)

    return f"""
    <style>
        @page {{
            size: {paper_size};
            margin: 10mm;
        }}

        body {{
            margin: 0;
            padding: 0;
            background: #fff;
        }}

        .sheet {{
            width: 100%;
            min-height: 297mm;
            display: flex;
            align-items: center;
            justify-content: center;
            page-break-after: always;
        }}

        .print-matrix {{
            display: grid;
            grid-template-columns: repeat({cols}, 1fr);
            grid-template-rows: repeat({rows}, auto);
            background-color: black;
            gap: 4mm;
            justify-content: center;
            align-content: center;
        }}

        .card {{
            width: {card_w};
            height: {card_h};
            background-image: url('{bg_by_orientation}');
            box-sizing: border-box;
            position: relative;
            overflow: hidden;
        }}
        
        .track-table {{
            grid-template-columns: 7mm repeat({stat_slots}, 8mm) !important;
        }}
    </style>
    """


# ============================================================
# GENERACIÓN DEL HTML
# ============================================================

def insertar_caras(html, quest_template, data, meta):
    """Inserta el anverso y, si corresponde, el reverso."""
    if "{{ TWO_SIDED }}" in quest_template:
        front, back = quest_template.split("{{ TWO_SIDED }}", 1)
    else:
        front, back = quest_template, ""

    html = html.replace("{{ FRONTCARD }}", front)

    back_data = data.get("backCard", {})
    two_sided = meta.get("twoSizedCard", False)

    if back_data and two_sided and back.strip():
        back_html = f"""
        <section class="sheet">
            <div class="print-matrix">
                {back}
            </div>
        </section>
        """
    else:
        back_html = ""

    return html.replace("{{ BACKCARD }}", back_html)


def reemplazar_variables(html, data):
    """Resuelve los marcadores {{ ruta.anidada }} del HTML."""
    def reemplazar(match):
        path = match.group(1).strip()
        value = obtener_valor_anidado(data, path)
        return str(value)

    return VARIABLE_PATTERN.sub(reemplazar, html)


def insertar_estilos(html, styles):
    """Inserta los estilos antes del cierre de head."""
    if "</head>" in html:
        return html.replace("</head>", f"{styles}\n</head>", 1)

    return f"{styles}\n{html}"


def generar_html(entradas):
    """Coordina las transformaciones y devuelve el HTML final."""
    config = entradas["config"]
    original_data = entradas["data"]
    meta = original_data.get("meta", {})

    data = transformar_secciones(original_data)

    html = insertar_caras(
        entradas["html_template"],
        entradas["quest_template"],
        data,
        meta,
    )

    html = reemplazar_variables(html, data)

    styles = generar_estilos(meta, config, data)

    return insertar_estilos(html, styles)


# ============================================================
# EJECUCIÓN
# ============================================================

def obtener_card_id(args):
    """Valida los argumentos de la terminal."""
    if len(args) < 2:
        raise ValueError(
            "Debes proporcionar el ID de la carta.\n"
            "Uso: python generar_carta.py <ID_CARTA>"
        )

    try:
        return int(args[1])
    except ValueError as error:
        raise ValueError(
            "El ID de la carta debe ser un número entero."
        ) from error


def guardar_html(path, html):
    """Crea la carpeta de salida y escribe el HTML."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def main():
    try:
        card_id = obtener_card_id(sys.argv)
        entradas = cargar_entradas(card_id)
        html = generar_html(entradas)

        guardar_html(entradas["output_path"], html)

        meta = entradas["data"].get("meta", {})

        print(f"¡Éxito! Se ha generado la carta ID {card_id}.")
        print(f"Archivo JSON: {entradas['json_path']}")
        print(
            "Configuración aplicada -> "
            f"Papel: {meta.get('paperSize', 'letter')}, "
            f"Tamaño: {meta.get('cardSize', 'tarot')}, "
            f"Orientación: {meta.get('isLandscapeCard', 'horizontal')}, "
            f"Matriz: {meta.get('multipleCardPrintMatrix', '1x1')}, "
            f"Doble cara: {meta.get('twoSizedCard', False)}"
        )
        print(f"Archivo de salida: {entradas['output_path']}")

    except (ValueError, FileNotFoundError, KeyError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
