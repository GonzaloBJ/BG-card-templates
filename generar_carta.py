import json
import os
import re
import sys

def obtener_valor_anidado(diccionario, ruta):
    """Navega por un diccionario usando notación de puntos (ej: 'backCard.title')."""
    partes = ruta.split('.')
    actual = diccionario
    for parte in partes:
        if isinstance(actual, dict) and parte in actual:
            actual = actual[parte]
        else:
            return f"{{{{ {ruta} }}}}"  # Si no lo encuentra, deja la etiqueta intacta
    return actual

def main():
    # CONFIG
    with open('config.json', 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
    
    # ==========================================
 
    if len(sys.argv) < 2:
        print("Error: Debes proporcionar el ID de la carta.")
        print("Uso: python generar_carta.py <ID_CARTA>")
        return

    try:
        selected_card = int(sys.argv[1])
    except ValueError:
        print("Error: El ID de la carta debe ser un número entero.")
        return

    if str(selected_card) not in CONFIG.get('cardTypeList'):
        print(f"Error: La carta con ID {selected_card} no existe en la lista de configuración.")
        return

    card_path = CONFIG.get('cardTypeList')[str(selected_card)]

    json_filename = os.path.join('data', card_path["json"])
    html_template_filename = os.path.join('templates', 'template_card.html')
    html_template_quest = os.path.join('templates', card_path["template"])
    html_output_filename = os.path.join('outputFiles', card_path["output"])

    if not os.path.exists(json_filename):
        print(f"Error: No se encuentra el archivo JSON: {json_filename}")
        return
    if not os.path.exists(html_template_filename):
        print(f"Error: No se encuentra el archivo de plantilla: {html_template_filename}")
        return
    if not os.path.exists(html_template_quest):
        print(f"Error: No se encuentra el archivo de plantilla quest: {html_template_quest}")
        return

    with open(json_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open(html_template_filename, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    with open(html_template_quest, 'r', encoding='utf-8') as f:
        quest_content = f.read()
        
    # ==========================================
    # LECTURA DE ATRIBUTOS DESDE EL BLOQUE 'meta'
    # ==========================================
    meta = data.get("meta", {})
    card_size = meta.get("cardSize", "tarot")
    is_lanscape_card = meta.get("isLanscapeCard", "horizontal")
    two_sided = meta.get("twoSizedCard", False)
    matrix = meta.get("multipleCardPrintMatrix", "1x1")
    paper_size = meta.get("paperSize", "letter")
    
    front_content, back_content = quest_content.split('{{ TWO_SIDED }}')
    html_content = html_content.replace('{{ FRONTCARD }}', front_content)
    
    back_card_content = data.get("backCard", {})
    if back_card_content != {} and two_sided:
        back_card_section = f"""
            <section class="sheet">
                <div class="print-matrix">
                    {back_content}
                </div>
            </section>'
        """
        html_content = html_content.replace('{{ BACKCARD }}', back_card_section)
        
    # Resolver dimensiones base según el tamaño de carta
    base_dimensions = CONFIG.get('cardSizeList').get(card_size, {"w": "44mm", "h": "67mm"})
    
    # Ajustar ancho y alto según la orientación (horizontal invierte las dimensiones vertical por defecto)
    if is_lanscape_card:
        card_w = base_dimensions["h"]
        card_h = base_dimensions["w"]
    else:
        card_w = base_dimensions["w"]
        card_h = base_dimensions["h"]

    # Procesar dimensiones de la matriz (columnas x filas)
    try:
        cols, rows = map(int, matrix.lower().split('x'))
    except ValueError:
        cols, rows = 1, 1

    # ==========================================
    # PROCESAMIENTO DE ESTRUCTURAS COMPLEJAS
    # ==========================================
    if 'backCard' in data and 'loreParagraphs' in data['backCard']:
        parrafos_historia = "".join([f'<p class="body">{p}</p>' for p in data['backCard']['loreParagraphs']])
        data['backCard']['loreParagraphs'] = parrafos_historia

    for key in ['objectiveParagraphs', 'rewardParagraphs', 'deploymentParagraphs']:
        if 'frontCard' in data and key in data['frontCard']:
            data['frontCard'][key] = "".join([f'<p class="body">{p}</p>' for p in data['frontCard'][key]])

    if 'frontCard' in data and 'monstersTableHeaders' in data['frontCard']:
        headers_html = "".join([f'<th>{h}</th>' for h in data['frontCard']['monstersTableHeaders']])
        data['frontCard']['monstersTableHeaders'] = headers_html

    if 'frontCard' in data and 'monstersTableRows' in data['frontCard']:
        filas_html = ""
        for row in data['frontCard']['monstersTableRows']:
            filas_html += f"""
                <tr>
                  <td class="level">{row.get('level', '')}</td>
                  <td>{row.get('monster', '')}</td>
                  <td>{row.get('item', '')}</td>
                </tr>
            """
        data['frontCard']['monstersTableRows'] = filas_html
    
    if 'frontCard' in data and 'unitSlots' in data['frontCard']:
        ranuras_html = ""
        for i in range(data['frontCard']['unitSlots']):
            ranuras_html += f"""
                <div class="row-header-cell">{i+1}</div>
                <div class="track-cell"></div>
                <div class="track-cell"></div>
                <div class="track-cell"></div>
                <div class="track-cell"></div>
                <div class="track-cell"></div>
                <div class="track-cell"></div>
            """
        data['frontCard']['unitSlotsRows'] = ranuras_html

    # ==========================================
    # REEMPLAZO DE VARIABLES EN EL HTML
    # ==========================================
    def reemplazar_variable(match):
        ruta = match.group(1).strip()
        return str(obtener_valor_anidado(data, ruta))

    html_final = re.sub(r'\{\{(.+?)\}\}', reemplazar_variable, html_content)

    # ==========================================
    # INYECCIÓN DE ESTILOS DE IMPRESIÓN Y DISEÑO
    # ==========================================
    dynamic_styles = f"""
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
            box-sizing: border-box;
            position: relative;
            overflow: hidden;
        }}
    </style>
    """

    if '</head>' in html_final:
        html_final = html_final.replace('</head>', f'{dynamic_styles}\n</head>')
    else:
        html_final = dynamic_styles + html_final

    if two_sided:
        print("-> Carta configurada como doble cara (twoSizedCard: true).")

    os.makedirs(os.path.dirname(html_output_filename), exist_ok=True)

    with open(html_output_filename, 'w', encoding='utf-8') as f:
        f.write(html_final)

    print(f"¡Éxito! Se ha generado la carta ID {selected_card} usando '{json_filename}'.")
    print(f"Configuración aplicada -> Papel: {paper_size}, Tamaño: {card_size}, Orientación: {is_lanscape_card}, Matriz: {matrix}, Doble cara: {two_sided}")
    print(f"Archivo de salida creado: {html_output_filename}")

if __name__ == '__main__':
    main()