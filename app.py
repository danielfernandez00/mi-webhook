from flask import Flask, request, jsonify
import requests
import os
import logging

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de OpenRouter
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY es requerida")

# Configuración del modelo
DEFAULT_MODEL = "openai/gpt-3.5-turbo"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_openrouter_api(user_text, model=DEFAULT_MODEL):
    """Llama a la API de OpenRouter"""
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system", 
                "content": "Eres un asistente útil y amigable. Responde de manera concisa y clara."
            },
            {
                "role": "user", 
                "content": user_text
            }
        ],
        "max_tokens": 150,
        "temperature": 0.7,
        "top_p": 0.9
    }
    
    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        return response
        
    except requests.exceptions.Timeout:
        raise Exception("Timeout en la petición a OpenRouter")
    except requests.exceptions.ConnectionError:
        raise Exception("Error de conexión con OpenRouter")

def process_openrouter_response(response):
    """Procesa la respuesta de OpenRouter"""
    
    if response.status_code == 200:
        try:
            data = response.json()
            
            # Verificar estructura de respuesta
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                content = message.get("content", "").strip()
                
                if content:
                    return content
                else:
                    return "Lo siento, no pude generar una respuesta."
            else:
                logger.error(f"Estructura de respuesta inesperada: {data}")
                return "Error: Estructura de respuesta inesperada."
                
        except ValueError as e:
            logger.error(f"Error parseando JSON: {e}")
            return "Error: Respuesta no válida de la API."
            
    elif response.status_code == 401:
        return "Error: API Key de OpenRouter no válida."
    elif response.status_code == 403:
        return "Error: Sin permisos para usar OpenRouter."
    elif response.status_code == 429:
        return "Error: Has excedido el límite de requests. Intenta más tarde."
    elif response.status_code == 400:
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", "Request inválido")
            return f"Error: {error_msg}"
        except:
            return "Error: Request inválido."
    else:
        logger.error(f"Error OpenRouter: {response.status_code} - {response.text}")
        return f"Error: La API devolvió código {response.status_code}."

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # Validar petición
        req = request.get_json(force=True)
        if not req:
            return jsonify({"fulfillmentText": "Error: Petición vacía"}), 400
        
        # Extraer texto del usuario
        query_result = req.get("queryResult", {})
        user_text = query_result.get("queryText", "").strip()
        
        if not user_text:
            return jsonify({"fulfillmentText": "Error: Mensaje vacío"}), 400
        
        # Limitar longitud de entrada
        if len(user_text) > 500:
            user_text = user_text[:500]
        
        logger.info(f"Procesando mensaje: {user_text[:100]}...")
        
        # Llamar a OpenRouter
        response = call_openrouter_api(user_text)
        
        # Procesar respuesta
        llm_reply = process_openrouter_response(response)
        
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        llm_reply = f"Error de validación: {str(e)}"
    except Exception as e:
        logger.error(f"Error interno: {e}")
        llm_reply = "Error interno del servidor. Intenta de nuevo más tarde."

    return jsonify({"fulfillmentText": llm_reply})

@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint de salud"""
    return jsonify({
        "status": "healthy",
        "service": "OpenRouter Webhook",
        "model": DEFAULT_MODEL
    })

@app.route("/test", methods=["GET"])
def test_openrouter():
    """Endpoint para probar la conexión con OpenRouter"""
    test_text = request.args.get('text', 'Hola, ¿cómo estás?')
    
    try:
        response = call_openrouter_api(test_text)
        result = process_openrouter_response(response)
        
        return jsonify({
            "success": True,
            "input": test_text,
            "output": result,
            "status_code": response.status_code
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    
    logger.info(f"Iniciando servidor OpenRouter en puerto {port}")
    logger.info(f"Modelo: {DEFAULT_MODEL}")
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)