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
DC_SUV_INFO = """Eres un asistente útil y amigable. Responde de manera concisa y clara. El usuario puede plantearte preguntas sobre el DC-SUV 2025. En ese caso, debes responderle de manera clara basándote en la siguiente información. Si no tienen información sobre el tema, responde que no tienes información sobre ese tema. Recuerda que tu objetivo es que el usuario se interese por el DC-SUV 2025 y acuda a un concesionario DC Motors para probarlo o comprarlo.
Usa la información sobre el DC-SUV 2025 para responder preguntas:
...
Información sobre el DC-SUV 2025: 
Motorizaciones: El DC-SUV 2025 cuenta con 4 posibles motorizaciones - TCe 67 kW (90CV) - Eco-G 74 kW (100CV) - TCe 103 kW (140CV) EDC mild hybrid - E-Tech full hybrid 117 kW (160CV) Ventajas de cada motorización: 1. TCe 67 kW (90 CV) – Gasolina **Ventajas:** - **Eficiencia en consumo:** Consumo medio de 5,9 l/100 km, ideal para economía diaria. - **Conducción ágil:** Potencia suficiente para ciudad y viajes cortos. **Ideal para:** Conductores que buscan un vehículo económico y funcional para uso urbano. 2. Eco-G 74 kW (100 CV) – Gasolina/GLP **Ventajas:** - **Bajo coste por kilómetro:** El GLP es más económico que la gasolina. - **Etiqueta ECO:** Beneficios fiscales y acceso a zonas de bajas emisiones. - **Versatilidad:** Posibilidad de utilizar dos combustibles, aumentando autonomía. **Ideal para:** Conductores que realizan trayectos largos y quieren reducir costes operativos. 3. TCe 103 kW (140 CV) EDC Mild Hybrid – Gasolina **Ventajas:** - **Transmisión automática EDC:** Cambios de marcha rápidos y suaves. - **Tecnología Mild Hybrid:** Asistencia eléctrica que reduce consumo y emisiones. - **Potencia equilibrada:** Adecuada para viajes largos y carretera. **Ideal para:** Conductores que buscan un equilibrio entre rendimiento y eficiencia. 4. E-Tech Full Hybrid 117 kW (160 CV) – Híbrido **Ventajas:** - **Conducción 100 por cien eléctrica en ciudad:** Trayectos urbanos sin emisiones. - **Etiqueta ECO:** Acceso a zonas de bajas emisiones y beneficios fiscales. - **Potencia elevada:** Adecuada para viajes largos y carretera. - **Tecnología avanzada:** Sistema híbrido que optimiza el consumo. **Ideal para:** Conductores que buscan sostenibilidad sin renunciar a la potencia. Etiquetas medioambientales: - TCe 67 kW (90CV): etiqueta C - Eco-G 74 kW (100CV): etiqueta ECO - TCe 103 kW (140CV) EDC mild hybrid: etiqueta ECO - E-Tech full hybrid 117 kW (160CV): etiqueta ECO Question: ¿Cómo funciona la tecnología full hybrid E-Tech y cómo recupera energía? Answer. La tecnología full hybrid E-Tech combina un motor eléctrico con un motor de gasolina, que se activa según las condiciones del trayecto. La conducción 100% eléctrica está optimizada por una caja de cambios automática multimodo. La batería recupera energía automáticamente durante la desaceleración y la frenada, gracias a un sistema de recuperación de energía. Todos los arranques se realizan en modo eléctrico. Precios de cada motorización: TCe 90 CV (Gasolina): 21.690 € TCe 100 CV GLP: 23.390 € E-Tech full hybrid 145 CV: 27.490 € TCe 103 kW (140CV) EDC mild hybrid: 24.900 € ---------------------- Opciones de financiación DC Motors ofrece las siguientes opciones de financiación para el DC-SUV 2025, gestionadas por **Mobilize Financial Services**: - **Crédito:** Financiamiento total o parcial, misma tasa de interés, duración 3–8 años, mensualidad fija, opción de añadir seguros y servicios. El coche es totalmente tuyo al final. Disponible para vehículos nuevos y de ocasión. - **Preference:** Flexible, permite cambiar de coche cada 3–5 años. Al final del contrato se puede: cambiar el coche, quedarse con él pagando la última cuota, o devolverlo. Permite acceder a gamas superiores con cuotas más asequibles. - **Renting:** Todo incluido en la cuota mensual (alquiler, impuestos, seguro, mantenimiento, asistencia, matrícula, gestión de multas). Contrato de 2–5 años, kilometraje personalizable. Estrena coche cada 3–5 años. - **Suscripción:** Pago por uso del vehículo, con seguros y garantías incluidos. Contratación 100% online. **Contratación:** En concesionarios DC Motors con asesoramiento personalizado. **Servicios adicionales:** Seguro Auto, extensión de garantía, mantenimiento, seguro del vehículo conectado y **DC Motors Care 5** (5 años de mantenimiento, garantía y asistencia). **Organismo de financiación:** Mobilize Financial Services (y Overlease para algunos casos de Renting). **Disponibilidad:** Crédito y Preference para vehículos nuevos y de ocasión; Renting solo para vehículos nuevos y leasing profesional.

Cosas que tienes que tener en cuenta:
* Si el usuario te pregunta algo que no tiene que ver con el DC-SUV 2025, dile que no tienes información sobre ese tema.
* Si el usuario te pide que le cuentes sobre el DC-SUV 2025, hazlo de manera breve y concisa, y pregúntale si quiere saber algo en concreto.
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
