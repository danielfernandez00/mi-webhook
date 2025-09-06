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

# Diccionario con instrucciones por intent
INTENT_INSTRUCTIONS = {
    "caracteristicas-tecnicas": "Proporciona una breve resumen sobre las motorizaciones cada una, indica de forma concisa sus ventajas y sus precios"
}

# Documentación base sobre el DC-SUV 2025
DC_SUV_INFO = """Eres un asistente útil y amigable. Responde de forma concisa y clara a preguntas sobre el DC-SUV 2025.  
Si la información no está disponible, responde que no la tienes. Atención: Sigue las instrucciones específicas del intent.
Tu objetivo es despertar interés en el DC-SUV 2025 e invitar al usuario a visitar un concesionario DC Motors.  

Información clave del DC-SUV 2025:

Motorizaciones:  
- TCe 90 CV (gasolina, etiqueta C, 21.690 €): eficiente y económico para ciudad.  
- Eco-G 100 CV (gasolina/GLP, etiqueta ECO, 23.390 €): menor coste/km, autonomía extendida, beneficios fiscales.  
- TCe 140 CV Mild Hybrid EDC (gasolina, etiqueta ECO, 24.900 €): cambio automático, buen equilibrio entre potencia y consumo.  
- E-Tech Full Hybrid 160 CV (híbrido, etiqueta ECO, 27.490 €): conducción 100 por cien eléctrica en ciudad, recuperación de energía en frenada, sostenible y potente.  

Opciones de financiación (Mobilize Financial Services):  
- Crédito: 3–8 años, mensualidad fija, coche en propiedad.  
- Preference: flexible, cambiar/quedarse/devolver al final (3–5 años).  
- Renting: todo incluido (2–5 años), coche nuevo cada ciclo.  
- Suscripción: pago por uso, contratación online.  

Servicios adicionales: seguros, extensión de garantía, mantenimiento y **DC Motors Care 5**.  

Cosas que tienes que tener en cuenta:
* Si el usuario te pregunta algo que no tiene que ver con el DC-SUV 2025, dile que no tienes información sobre ese tema.
* Si el usuario te pide que le cuentes sobre el DC-SUV 2025, hazlo de manera breve y concisa, y pregúntale si quiere saber algo en concreto.
* Si el usuario quiere que le cuentes más sobre las características técnicas, háblale de las motorizaciones, incluyendo ventajas, etiquetas y precios
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
        "max_tokens": 1500,
        "temperature": 0.5,
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
        intent_name = query_result.get("intent", {}).get("displayName", "")

        if not user_text:
            return jsonify({"fulfillmentText": "Error: Mensaje vacío"}), 400

        logger.info(f"Procesando mensaje de {user_id} en intent {intent_name}: {user_text[:600]}")

        # Inicializar historial si no existe
        if user_id not in conversation_histories:
            conversation_histories[user_id] = []

        # Añadir mensaje del usuario
        conversation_histories[user_id].append({"role": "user", "content": user_text})

        # Mantener solo los últimos 3 turnos completos (user + assistant = 6 mensajes)
        conversation_histories[user_id] = conversation_histories[user_id][-6:]

        # Construir prompt para el LLM: system + instrucciones por intent + historial
        # DEBUGGING: Ver qué intent llega
        logger.info(f"🔍 Intent recibido: '{intent_name}'")
        logger.info(f"🔍 Intents disponibles: {list(INTENT_INSTRUCTIONS.keys())}")

        # Construir prompt más efectivo
        if intent_name in INTENT_INSTRUCTIONS:
            logger.info(f"✅ Aplicando instrucciones para: {intent_name}")
            system_prompt = f"{INTENT_INSTRUCTIONS[intent_name]}\n\n{DC_SUV_INFO}"
        else:
            logger.info(f"❌ Intent '{intent_name}' no encontrado, usando prompt base")
            system_prompt = DC_SUV_INFO

        messages = [{"role": "system", "content": system_prompt}]
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
