from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import send_from_directory
from dotenv import load_dotenv 
from anthropic import Anthropic
import base64
import os
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

load_dotenv()

# Asignar la variable de entorno a una variable de Python
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Inicializar el cliente de Anthropic correctamente
client = Anthropic(
    api_key=ANTHROPIC_API_KEY
)

#PROMPT PRINCIPAL 
PROMPT_LECTURA_FACIL = """Eres un asistente especializado en hacer textos accesibles para todas las personas.

Tu tarea es convertir el siguiente texto en formato de "Lectura Fácil" siguiendo estas reglas:
1. Usa frases cortas y simples
2. Evita palabras técnicas o complejas
3. Si hay palabras difíciles, explícalas con ejemplos cotidianos
4. Usa un lenguaje claro y directo
5. Organiza la información de forma lógica
6. Si hay términos legales o técnicos, tradúcelos a lenguaje cotidiano
7. Manten el sentido y significado original del texto

El texto a simplificar es:

{texto}

Por favor, proporciona la versión en Lectura Fácil del texto."""

@app.route('/')
def index():
    # Enviar el archivo HTML al navegador
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/status') # Cambiamos la ruta del JSON a /status
def status():
    return jsonify({
        "endpoints": {
            "/simplificar-imagen": "POST...",
            "/simplificar-texto": "POST..."
        },
        "mensaje": "API de Asistente de Alfabetización Universal"
    })

@app.route('/simplificar-texto', methods=['POST'])
def simplificar_texto():
    """
    Endpoint para simplificar texto directo
    Espera JSON: {"texto": "tu texto aquí"}
    """
    try:
        data = request.get_json()
        
        if not data or 'texto' not in data:
            return jsonify({"error": "Debes enviar un campo 'texto' en el JSON"}), 400
        
        texto_original = data['texto']
        
        # Llamar a la API de Claude con el prompt
        mensaje = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {
                    "role": "user", 
                    "content": PROMPT_LECTURA_FACIL.format(texto=texto_original)
                }
            ]
        )
        
        texto_simplificado = mensaje.content[0].text
        
        return jsonify({
            "texto_original": texto_original,
            "texto_simplificado": texto_simplificado,
            "tokens_usados": mensaje.usage.input_tokens + mensaje.usage.output_tokens
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/simplificar-imagen', methods=['POST'])
def simplificar_imagen():
    """
    Endpoint para procesar una imagen con texto
    Espera una imagen en base64 en JSON: {"imagen": "data:image/jpeg;base64,..."}
    """
    try:
        data = request.get_json()
        
        if not data or 'imagen' not in data:
            return jsonify({"error": "Debes enviar un campo 'imagen' con la imagen en base64"}), 400
        
        imagen_base64 = data['imagen']
        
        # Remover el prefijo data:image/...;base64, si existe
        if ',' in imagen_base64:
            imagen_base64 = imagen_base64.split(',')[1]
        
        # Determinar el tipo de imagen
        tipo_imagen = "image/jpeg"
        if 'image/png' in data['imagen']:
            tipo_imagen = "image/png"
        elif 'image/webp' in data['imagen']:
            tipo_imagen = "image/webp"
        elif 'image/gif' in data['imagen']:
            tipo_imagen = "image/gif"
        
        # Prompt específico para extracción de texto de imagen
        prompt_imagen = """Analiza esta imagen y extrae todo el texto que encuentres.
        
Luego, convierte ese texto a formato de "Lectura Fácil" siguiendo estas reglas:
1. Usa frases cortas y simples
2. Evita palabras técnicas o complejas
3. Si hay palabras difíciles, explícalas con ejemplos cotidianos
4. Usa un lenguaje claro y directo
5. Si hay términos legales o técnicos, tradúcelos a lenguaje cotidiano
6. Manten el sentido y significado original

Responde en este formato:
TEXTO EXTRAÍDO:
[el texto que encontraste en la imagen]

VERSIÓN EN LECTURA FÁCIL:
[el texto simplificado]"""
        
        # Llamar a la API de Claude con la imagen
        mensaje = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": tipo_imagen,
                                "data": imagen_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt_imagen
                        }
                    ]
                }
            ]
        )
        
        respuesta = mensaje.content[0].text
        
        return jsonify({
            "respuesta_completa": respuesta,
            "tokens_usados": mensaje.usage.input_tokens + mensaje.usage.output_tokens
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/explicar-termino', methods=['POST'])
def explicar_termino():
    """
    Endpoint para explicar un término técnico o complejo
    Espera JSON: {"termino": "palabra o frase a explicar"}
    """
    try:
        data = request.get_json()
        
        if not data or 'termino' not in data:
            return jsonify({"error": "Debes enviar un campo 'termino' en el JSON"}), 400
        
        termino = data['termino']
        
        prompt_termino = f"""Explica el siguiente término de forma simple y clara, como si se lo explicaras a alguien que nunca ha escuchado esta palabra:

Término: {termino}

Proporciona:
1. Una definición simple y clara
2. Un ejemplo cotidiano que ayude a entenderlo
3. Si es posible, una comparación con algo familiar

Usa un lenguaje accesible para todos."""
        
        mensaje = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": prompt_termino
                }
            ]
        )
        
        explicacion = mensaje.content[0].text
        
        return jsonify({
            "termino": termino,
            "explicacion": explicacion
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Usamos la variable de entorno PORT que Render nos da
    port = int(os.environ.get('PORT', 5000))
    # '0.0.0.0' es fundamental para despliegues en la nube
    app.run(host='0.0.0.0', port=port)


