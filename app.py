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

DEFAULT_MODEL = "openai/gpt-3.5-turbo"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Diccionario para almacenar el historial de conversación por usuario
conversation_histories = {}

# Documentación base sobre el DC-SUV 2025
DC_SUV_INFO = """Eres un asistente útil y amigable. Responde en español de manera clara y concisa.
Usa la información sobre el DC-SUV 2025 para responder preguntas:
...
# Aquí va toda tu info de motorizaciones, precios, financiación, accesorios, etc.
"""

def call_openrouter_api(messages, model=DEFAULT_MODEL):
    """Llama a la API de OpenRouter con el historial de mensajes"""
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 150,
        "temperature": 0.7,
        "top_p": 0.9
    }
    
    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=30
    )
    return response

def process_openrouter_response(response):
    """Procesa la respuesta de OpenRouter"""
    if response.status_code == 200:
        data = response.json()
        if "choices" in data and len(data["choices"]) > 0:
            message = data["choices"][0].get("message", {})
            content = message.get("content", "").strip()
            return content if content else "Lo siento, no pude generar una respuesta."
        else:
            return "Error: Estructura de respuesta inesperada."
    else:
        return f"Error: Código {response.status_code} de OpenRouter."

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        req = request.get_json(force=True)
        if not req:
            return jsonify({"fulfillmentText": "Error: Petición vacía"}), 400
        
        query_result = req.get("queryResult", {})
        user_text = query_result.get("queryText", "").strip()
        user_id = req.get("originalDetectIntentRequest", {}).get("payload", {}).get("userId", "default_user")
        
        if not user_text:
            return jsonify({"fulfillmentText": "Error: Mensaje vacío"}), 400

        logger.info(f"Procesando mensaje de {user_id}: {user_text[:100]}")

        # Inicializar historial si no existe
        if user_id not in conversation_histories:
            conversation_histories[user_id] = []

        # Añadir mensaje del usuario
        conversation_histories[user_id].append({"role": "user", "content": user_text})

        # Mantener solo los últimos 3 turnos completos (user + assistant = 6 mensajes)
        conversation_histories[user_id] = conversation_histories[user_id][-6:]

        # Construir mensajes para el LLM: primero system, luego historial
        messages = [{"role": "system", "content": DC_SUV_INFO}]
        messages.extend(conversation_histories[user_id])

        # Llamar al LLM
        response = call_openrouter_api(messages)
        llm_reply = process_openrouter_response(response)

        # Guardar la respuesta del asistente en el historial
        conversation_histories[user_id].append({"role": "assistant", "content": llm_reply})

    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        llm_reply = "Error interno del servidor. Intenta de nuevo más tarde."

    return jsonify({"fulfillmentText": llm_reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    logger.info(f"Iniciando servidor OpenRouter en puerto {port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
