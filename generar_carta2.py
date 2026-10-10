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
    # ==========================================
    # CONFIGURACIÓN DE HOJA E IMPRESION
    # ==========================================

    card_size_list = {
        "tarot": {
            "w":"80mm",
            "h":"120mm"
            },
        "standard": {
            "w":"63mm",
            "h":"88mm"
        },
        "miniEuro": {
            "w":"44mm",
            "h":"67mm"
            }
    }
 
    # ==========================================
    # CONFIGURACIÓN DE CARTAS Y SELECCIÓN DESDE CLI
    # ==========================================
    card_list = {
        0: {
            "json": "tobarosBane.json",
            "template": "template_quest_card.html",
            "output": "carta_tobaros_bane.html"
        },
        1: {
            "json": "brokenAmulet1.json",
            "template": "template_quest_card.html",
            "output": "carta_warlord_lair.html"
        },
        2: {
            "json": "brokenAmulet2.json",
            "template": "template_quest_card.html",
            "output": "carta_magic_maze.html"
        },
        3: {
            "json": "plageTemple.json",
            "template": "template_quest_card.html",
            "output": "carta_plage_temple.html"
        },
        4: {
            "json": "ambarChamber.json",
            "template": "template_quest_card.html",
            "output": "carta_ambar_chamber.html"
        },
        5: {
            "json": "icePrison.json",
            "template": "template_quest_card.html",
            "output": "carta_ice_prison.html"
        },
        6: {
            "json": "enemiesTracker.json",
            "template": "template_enemies_tracker_card.html",
            "output": "carta_enemies_tracker.html"
        },
    }

    # Obtener el ID de la carta desde los argumentos de la consola (ej: python generar_carta.py 1)
    if len(sys.argv) < 2:
        print("Error: Debes proporcionar el ID de la carta.")
        print("Uso: python generar_carta.py <ID_CARTA>")
        return

    try:
        selected_card = int(sys.argv[1])
    except ValueError:
        print("Error: El ID de la carta debe ser un número entero.")
        return

    # Validar que la carta seleccionada exista en la lista
    if selected_card not in card_list:
        print(f"Error: La carta con ID {selected_card} no existe en la lista de configuración.")
        return

    card_path = card_list[selected_card]

    # Obtener los archivos correspondientes a la selección
    json_filename = os.path.join('data', card_path["json"])
    html_template_filename = os.path.join('templates', card_path["template"])
    html_output_filename = os.path.join('outputFiles', card_path["output"])

    # Verificar que los archivos existan
    if not os.path.exists(json_filename):
        print(f"Error: No se encuentra el archivo JSON: {json_filename}")
        return
    if not os.path.exists(html_template_filename):
        print(f"Error: No se encuentra el archivo de plantilla: {html_template_filename}")
        return

    # Cargar los datos del JSON seleccionado
    with open(json_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Cargar la plantilla HTML correspondiente
    with open(html_template_filename, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # ==========================================
    # LECTURA DE ATRIBUTOS NUEVOS DEL JSON
    # ==========================================
    card_size = data.get("meta")["cardSize"]
    selected_card_size = card_size_list[card_size]


    two_sided = data.get("twoSizedCard", False)  # Booleano: True/False
    matrix = data.get("multipleCardPrintMatrix", "1x1")  # Ejemplo: "2x4"
    paper_size = data.get("paperSize", "A4")  # Ejemplo: "A4", "letter"

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

    if 'frontCard' in data and 'objectiveParagraphs' in data['frontCard']:
        objectiveParagraphs = "".join([f'<p class="body">{p}</p>' for p in data['frontCard']['objectiveParagraphs']])
        data['frontCard']['objectiveParagraphs'] = objectiveParagraphs

    if 'frontCard' in data and 'rewardParagraphs' in data['frontCard']:
        rewardParagraphs = "".join([f'<p class="body">{p}</p>' for p in data['frontCard']['rewardParagraphs']])
        data['frontCard']['rewardParagraphs'] = rewardParagraphs

    if 'frontCard' in data and 'deploymentParagraphs' in data['frontCard']:
        deploymentParagraphs = "".join([f'<p class="body">{p}</p>' for p in data['frontCard']['deploymentParagraphs']])
        data['frontCard']['deploymentParagraphs'] = deploymentParagraphs

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
    # Generar estilos dinámicos basados en el JSON
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
        .print-matrix {{
            display: grid;
            grid-template-columns: repeat({cols}, 1fr);
            grid-template-rows: repeat({rows}, auto);
            gap: 4mm;
            justify-content: center;
            align-content: center;
            page-break-after: always;
        }}
        .card-wrapper {{
            box-sizing: border-box;
            /* Tamaños orientativos según el atributo cardSize */
            width: {selected_card_size["w"]};
            height: {selected_card_size["h"]};
            overflow: hidden;
            position: relative;
        }}
        .page-break {{
            page-break-after: always;
        }}
    </style>
    """

    # Insertar los estilos dinámicos antes de cerrar el </head> o al inicio del HTML
    if '</head>' in html_final:
        html_final = html_final.replace('</head>', f'{dynamic_styles}\n</head>')
    else:
        html_final = dynamic_styles + html_final

    # Manejo de la segunda hoja (twoSizedCard) si está habilitada
    if two_sided:
        # Nota: Aquí puedes estructurar cómo se añade la parte trasera si tu template lo requiere, 
        # por ejemplo, asegurando que se imprima una página adicional con los datos de backCard.
        print("-> Carta configurada como doble cara (twoSizedCard: true).")

    # Asegurar que el directorio de salida exista
    os.makedirs(os.path.dirname(html_output_filename), exist_ok=True)

    # Guardar el archivo HTML resultante
    with open(html_output_filename, 'w', encoding='utf-8') as f:
        f.write(html_final)

    print(f"¡Éxito! Se ha generado la carta ID {selected_card} usando '{json_filename}'.")
    print(f"Configuración aplicada -> Papel: {paper_size}, Tamaño carta: {card_size}, Matriz: {matrix}, Doble cara: {two_sided}")
    print(f"Archivo de salida creado: {html_output_filename}")

if __name__ == '__main__':
    main()