import json
import math
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

    front_cards = result.get("frontCard", [])
    if isinstance(front_cards, dict):
        front_cards = [front_cards]

    back_cards = result.get("backCard", [])
    if isinstance(back_cards, dict):
        back_cards = [back_cards]

    transformed_fronts = []
    for front in front_cards:
        sections = front.get("sections", {})
        for key in PARAGRAPH_SECTIONS:
            if key in sections:
                sections[key] = unir_parrafos(sections[key])

        if "monstersTableHeaders" in sections:
            sections["monstersTableHeaders"] = generar_encabezados(
                sections["monstersTableHeaders"]
            )

        if "monstersTableRows" in sections:
            sections["monstersTableRows"] = generar_filas_monstruos(
                sections["monstersTableRows"]
            )

        if "unitSlots" in sections:
            sections["unitSlotsRows"] = generar_ranuras_unidades(
                sections["unitSlots"], sections["statSlots"]
            )

        if "equipment" in sections:
            sections["equipment"] = generar_equipo(sections["equipment"])

        if isinstance(sections.get("meleeCombat"), dict):
            sections["meleeCombatHtml"] = generar_combate_cuerpo_a_cuerpo(
                sections["meleeCombat"]
            )
        transformed_fronts.append(front)

    transformed_backs = []
    for back in back_cards:
        sections = back.get("sections", {})
        for key in ("loreParagraphs",):
            if key in sections:
                sections[key] = unir_parrafos(sections[key])
        transformed_backs.append(back)

    result["frontCard"] = transformed_fronts
    result["backCard"] = transformed_backs
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
        
    front_cards = data.get("frontCard", [])
    stat_slots = 1
    if front_cards and isinstance(front_cards, list):
        stat_slots = front_cards[0].get("sections", {}).get("statSlots", 1)

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
            break-after: page;
            position: relative;
            background: #fff;
        }}

        .print-matrix {{
            display: grid;
            grid-template-columns: repeat({cols}, 1fr);
            grid-template-rows: repeat({rows}, auto);
            background-color: transparent;
            gap: 4mm;
            justify-content: center;
            align-content: center;
        }}

        .print-matrix.back-matrix {{
            direction: rtl;
        }}

        .print-matrix.back-matrix .card {{
            direction: ltr;
        }}

        .card {{
            width: {card_w};
            height: {card_h};
            background-image: url('{bg_by_orientation}');
            box-sizing: border-box;
            position: relative;
            overflow: hidden;
            outline: 0.2mm dashed #888; /* Línea segmentada */
            outline-offset: 2mm;        /* Ubicada a 2mm exactos (en el medio del gap de 4mm) */
        }}
        
        .track-table {{
            grid-template-columns: 7mm repeat({stat_slots}, 8mm) !important;
        }}
    </style>
    """


# ============================================================
# GENERACIÓN DEL HTML
# ============================================================

def reemplazar_variables(html, data):
    """Resuelve los marcadores {{ ruta.anidada }} del HTML."""
    def reemplazar(match):
        path = match.group(1).strip()
        value = obtener_valor_anidado(data, path)
        return str(value)

    return VARIABLE_PATTERN.sub(reemplazar, html)


def insertar_caras(html, quest_template, data, meta):
    """Inserta las cartas (frentes y reversos) organizadas en páginas según la matriz."""
    if "{{ TWO_SIDED }}" in quest_template:
        front_template, back_template = quest_template.split("{{ TWO_SIDED }}", 1)
    else:
        front_template, back_template = quest_template, ""

    cols, rows = obtener_matriz(meta.get("multipleCardPrintMatrix", "1x1"))
    cards_per_page = cols * rows

    front_cards = data.get("frontCard", [])
    if isinstance(front_cards, dict):
        front_cards = [front_cards]

    back_cards = data.get("backCard", [])
    if isinstance(back_cards, dict):
        back_cards = [back_cards]

    two_sided = meta.get("twoSizedCard", False)

    rendered_fronts = []
    for card in front_cards:
        single_data = deepcopy(data)
        single_data["frontCard"] = card
        rendered_fronts.append(reemplazar_variables(front_template, single_data))

    rendered_backs = []
    if two_sided and back_template.strip():
        for card in back_cards:
            single_data = deepcopy(data)
            single_data["backCard"] = card
            rendered_backs.append(reemplazar_variables(back_template, single_data))
        while len(rendered_backs) < len(rendered_fronts):
            rendered_backs.append("")

    front_sheets = []
    back_sheets = []

    total_cards = len(rendered_fronts)
    total_pages = math.ceil(total_cards / cards_per_page) if total_cards > 0 else 1

    for page_idx in range(total_pages):
        start = page_idx * cards_per_page
        end = start + cards_per_page

        page_fronts = rendered_fronts[start:end]
        front_grid_html = "\n".join(page_fronts)
        front_sheets.append(f"""
        <section class="sheet">
            <div class="print-matrix">
                {front_grid_html}
            </div>
        </section>
        """)

        if two_sided and rendered_backs:
            page_backs = rendered_backs[start:end]
            back_grid_html = "\n".join(page_backs)
            back_sheets.append(f"""
            <section class="sheet">
                <div class="print-matrix back-matrix">
                    {back_grid_html}
                </div>
            </section>
            """)

    html = html.replace("{{ FRONTCARD }}", "".join(front_sheets))
    html = html.replace("{{ BACKCARD }}", "".join(back_sheets))
    return html


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