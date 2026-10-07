import json
import os
import re

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
    # CONFIGURACIÓN DE CARTAS Y SELECCIÓN
    # ==========================================
    # Puedes agregar más cartas aquí cambiando el número de índice
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
            "json": "magicMaze.json",
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
    
    # Selecciona el número de la carta que deseas generar
    selected_card = 1
    card_path =  card_list[selected_card]
    
    # Validar que la carta seleccionada exista en la lista
    if selected_card not in card_list:
        print(f"Error: La carta con ID {selected_card} no existe en la lista de configuración.")
        return

    # Obtener los archivos correspondientes a la selección
    json_filename = 'data/'+card_path["json"]
    html_template_filename = 'templates/'+card_path["template"]
    html_output_filename = 'outputFiles/'+card_path["output"]

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
    # PROCESAMIENTO DE ESTRUCTURAS COMPLEJAS
    # ==========================================
    # Párrafos de la historia
    if 'backCard' in data and 'loreParagraphs' in data['backCard']:
        parrafos_historia = "".join([f'<p class="body">{p}</p>' for p in data['backCard']['loreParagraphs']])
        data['backCard']['loreParagraphs'] = parrafos_historia
        
    # parrafos de objetivos
    if 'frontCard' in data and 'objectiveParagraphs' in data['frontCard']:
        objectiveParagraphs = "".join([f'<p class="body">{p}</p>' for p in data['frontCard']['objectiveParagraphs']])
        data['frontCard']['objectiveParagraphs'] = objectiveParagraphs

    # parrafos de recompensas
    if 'frontCard' in data and 'rewardParagraphs' in data['frontCard']:
        rewardParagraphs = "".join([f'<p class="body">{p}</p>' for p in data['frontCard']['rewardParagraphs']])
        data['frontCard']['rewardParagraphs'] = rewardParagraphs

    # Párrafos de despliegue
    if 'frontCard' in data and 'deploymentParagraphs' in data['frontCard']:
        deploymentParagraphs = "".join([f'<p class="body">{p}</p>' for p in data['frontCard']['deploymentParagraphs']])
        data['frontCard']['deploymentParagraphs'] = deploymentParagraphs

    # Cabeceras de la tabla
    if 'frontCard' in data and 'monstersTableHeaders' in data['frontCard']:
        headers_html = "".join([f'<th>{h}</th>' for h in data['frontCard']['monstersTableHeaders']])
        data['frontCard']['monstersTableHeaders'] = headers_html

    # Filas de la tabla de monstruos especiales
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

    # Guardar el archivo HTML resultante especificado para esta carta
    with open(html_output_filename, 'w', encoding='utf-8') as f:
        f.write(html_final)

    print(f"¡Éxito! Se ha generado la carta ID {selected_card} usando '{json_filename}' y '{html_template_filename}'.")
    print(f"Archivo de salida creado: {html_output_filename}")

if __name__ == '__main__':
    main()