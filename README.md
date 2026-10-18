# Generador de Cartas HTML

Este script de Python permite transformar datos estructurados en formato JSON y plantillas HTML/CSS en archivos HTML listos para imprimir o visualizar. Está diseñado para procesar cartas individuales o juegos de cartas con soporte para configuraciones dinámicas de impresión (tamaño de papel, orientación, matrices de impresión y caras).

---

## 🚀 Características
- **Sustitución de variables:** Reemplaza dinámicamente marcadores del tipo `{{ ruta.anidada }}` en las plantillas.
- **Soporte para doble cara:** Permite generar cartas de una cara o de dos caras ( `frontCard` y `backCard` ).
- **Ajustes dinámicos de impresión:** Configura estilos de CSS `@page` y retículas ( `grid` ) según el tamaño de papel, tamaño de carta, orientación (horizontal/vertical) y matriz de impresión (ej. `3x2` ).
- **Generación de componentes HTML:** Transformación automática de listas y estructuras complejas (párrafos, tablas de monstruos, ranuras de seguimiento de unidades, listas de equipo y grillas de combate).

---

## 📁 Estructura del Proyecto

```text
  .
  ├── generar_carta.py        # Script principal de generación
  ├── config.json             # Configuración general de tipos de carta y dimensiones
  ├── data/                   # Archivos JSON con los datos específicos de cada carta
  │   └── -TODO- (ej. carta_01.json)
  ├── templates/              # Plantillas HTML
  │   ├── template_card.html  # Estructura base de la página HTML
  │   └── -TODO- (ej. plantilla_mision.html)
  └── outputFiles/            # Carpeta donde se guardan los archivos HTML generados
```

---

## ⚙️ Requisitos Previos

- **Python 3.7** o superior.
- No se requieren librerías de terceros (utiliza módulos estándar de Python: ` json `, ` re `, ` sys `, ` copy `, ` pathlib `).

---

## 🛠️ Configuración

### 1. Archivo ` config.json `
El archivo ` config.json ` debe ubicarse en la raíz y contener las secciones ` cardTypeList ` y ` cardSizeList `.

**Ejemplo de estructura de ` config.json `:**
```json
{
  "cardTypeList": {
    "1": {
      "json": "carta_mision_01.json",
      "template": "template_quest.html",
      "output": "carta_mision_01.html"
    }
  },
  "cardSizeList": {
    "tarot": {
      "w": "70mm",
      "h": "120mm"
    },
    "standard": {
      "w": "63mm",
      "h": "88mm"
    },
    "-TODO-": {
      "w": "-TODO-",
      "h": "-TODO-"
    }
  }
}
```
                    
---

## 📄 Estructura de los Datos de Entrada (JSON)
Cada archivo en ` data/ ` debe contener un bloque ` meta ` y los datos de las caras de la carta:

```json
{
  "meta": {
    "paperSize": "letter",
    "cardSize": "tarot",
    "isLandscapeCard": "horizontal",
    "multipleCardPrintMatrix": "3x2",
    "twoSizedCard": true
  },
  "frontCard": {
    "title": "-TODO-",
    "sections": {
      "objectiveParagraphs": [
        "Párrafo 1",
        "Párrafo 2"
      ],
      "rewardParagraphs": [
        "Recompensa..."
      ],
      "deploymentParagraphs": [
        "Despliegue..."
      ],
      "monstersTableHeaders": [
        "Nivel",
        "Monstruo",
        "Objeto"
      ],
      "monstersTableRows": [
        {
          "level": "1",
          "monster": "Trasgo",
          "item": "Espada corta"
        }
      ],
      "unitSlots": 3,
      "equipment": [
        "Casco",
        "Escudo"
      ],
      "meleeCombat": {
        "rolls": [
          2,
          3,
          4,
          5,
          6,
          7,
          8,
          9,
          10,
          11,
          12,
          12
        ],
        "damage": "1D6"
      }
    }
  },
  "backCard": {
    "title": "-TODO-",
    "sections": {
      "loreParagraphs": [
        "Historia de fondo..."
      ]
    }
  }
}
```

---

## 🖥️ Uso del Script

Para generar una carta, ejecuta el script pasando como argumento el **ID numérico** de la carta definido en ` config.json `:

` ` `bash
python generar_carta.py <ID_CARTA>
` ` `

### Ejemplo:
` ` `bash
python generar_carta.py 1
` ` `

### Salida esperada:
` ` `text
¡Éxito! Se ha generado la carta ID 1.
Archivo JSON: .../data/carta_mision_01.json
Configuración aplicada -> Papel: letter, Tamaño: tarot, Orientación: horizontal, Matriz: 3x2, Doble cara: True
Archivo de salida: .../outputFiles/carta_mision_01.html
` ` `

---

## 📌 Marcadores Especiales en Plantillas

En las plantillas HTML dentro de ` templates/ `, puedes usar:

- **` {{ FRONTCARD }} `**: Punto donde se insertará el contenido del anverso.
- **` {{ TWO_SIDED }} `**: Delimitador dentro de la plantilla específica para separar la sección frontal de la trasera.
- **` {{ BACKCARD }} `**: Punto donde se insertará el reverso de la carta (si ` twoSizedCard ` es ` true `).
- **` {{ ruta.anidada }} `**: Sustitución dinámica de propiedades de la carta (ej. ` {{ frontCard.title }}`).

---

## 📝 Notas Adicionales y Mejoras Pendientes

- -TODO- *(Añade aquí cualquier nota sobre fuentes de tipografía usadas, librerías CSS externas o instrucciones específicas para imprimir el HTML)*
- -TODO- *(Añade aquí detalles adicionales sobre el proyecto general o juego de mesa asociado)*
