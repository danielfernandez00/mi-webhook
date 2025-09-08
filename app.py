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
    "caracteristicas-tecnicas": """
RESPUESTA OBLIGATORIA - DEBES INCLUIR EXACTAMENTE ESTO.

1. Las 4 motorizaciones del DC-SUV 2025:
   - TCe 67 kW (90 CV) Gasolina: 21.690€
   - Eco-G 74 kW (100 CV) GLP: 23.390€  
   - TCe 103 kW (140 CV) EDC mild hybrid: 24.900€
   - E-Tech full hybrid 117 kW (160 CV): 27.490€

2. Menciona las ventajas principales de cada motorización. Evita incluir preguntas como '¿Quieres saber algo más?'.

3. Debes terminar sugiriendo visitar concesionario DC Motors: '¿Quieres concertar una cita en el concesionario DC Motors más cercano para probar el coche sin compromiso?'
NO respondas con saludos genéricos. DEBES hablar específicamente de las motorizaciones y precios.

Atención: Es obligatorio que incluyas en tu respuesta todos los puntos indicados.
""",
"coche-actual": """RESPUESTA OBLIGATORIA - DEBES TENER EN CUENTA ESTO:
El usuario te dirá qué coche tiene actualmente. Independientemente del coche actual del usuario, dile que es un coche estupendo.
Atención: No respondas que no tienes información sobre ese coche, di simplemente que es un buen coche. Además, debes decirle: 'En la elección de un coche los hijos son un factor importante a tener en cuenta. Lo mejor es tener un coche amplio y con un buen maletero. ¿Tú tienes hijos?' Atención: Evita preguntarle nada más""",
"fecha-nacimiento": """RESPUESTA OBLIGATORIA - DEBES INCLUIR EXACTAMENTE ESTO:
1. Empieza diciendo: 'Muy bien, me lo apunto para futuras promociones👌'
2. A continuación, debes preguntarle qué coche tiene actualmente, con una pregunta como esta: '¿Y qué coche tienes actualmente?
Atención: Ten en cuenta que el usuario puede darte la fecha en diferentes formatos (por ejemplo, '15 de marzo de 1985', '15/03/1985', '15-03-85', etc.)""",
"etiqueta-eco-no": """RESPUESTA OBLIGATORIA - DEBES TENER EN CUENTA ESTO:
1. El usuario te dirá qué etiqueta tiene su coche actual (C, B o no tiene). Solo en caso de que el usuario te pregunta qué es una etiqueta, explícaselo brevemente
2.  Explica las motorizaciones del DC-SUV 2025 que tienen etiqueta ECO (Eco-G 100 CV, TCe 140 CV Mild Hybrid EDC y E-Tech Full Hybrid 160 CV), incluyendo ventajas y precios.
3. Explícale que la etiqueta ECO le permitirá acceder a zonas de bajas emisiones y beneficiarse de ventajas fiscales y de ayudas para la compra por parte de las administraciones públicas.
4. Atención: Termina explicándole que DC Motors ofrece promociones a menudo y pregúntale si quiere responder algunas preguntas para que le tengamos en cuenta su perfil y avisarle cuando haya una promoción que le pueda interesar.
Asegúrate de incluir en tu respuesta todos los puntos indicados. Atención: Lo que te va a decir el usuario es la etiqueta de su coche actual, no te va a dar información sobre el DC-SUV 2025.
Asegúrate de incluir en tu respuesta todos los puntos indicados.
""",
"detalles-financiacion-si": """RESPUESTA OBLIGATORIA - DEBES INCLUIR EXACTAMENTE ESTO:
1. Debes explicar al usuario, a partir de la información que tienes, las opciones de financiación del DC-SUV 2025 (crédito, preference, renting y suscripción), incluyendo las ventajas principales de cada una.
2. Pregúntale si quiere calcular una simulación de financiación
Atención: Asegúrate de incluir en tu respuesta todos los puntos indicados.
Asegúrate de no comenzar la respuesta con un saludo.
"""
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
* Si el usuario indica una ciudad que no sea Madrid, Barcelona o Valencia, dile que solo tenemos concesionarios en esas ciudades.
* Si el usuario te pregunta cómo puede contactar con nosotros, dale este correo: contacto@dcmotors.com
* Habla siempre en singular
* Recuerda que eres tú la que te has dirigido al usuario, así que no preguntes cosas como ¿Hay algo más en lo que pueda ayudarte? Simplemente despídete cordialmente.
* Si el usuario pregunta qué son las etiquetas ambientales, responde lo siguiente: "Las etiquetas medioambientales de la DGT son distintivos que clasifican los vehículos según su nivel de emisiones contaminantes. Sirven para identificar qué coches pueden acceder a determinadas zonas de bajas emisiones y beneficiarse de incentivos ambientales. Si necesitas más información, puedes contactar con nosotros en contacto@dcmotors.com"
* Si el usuario se despide de ti, despídete cordialmente y no ofrezcas más ayuda.
* Si el usuario te pregunta por las características técnicas, responde con las motorizaciones y las ventajas. Además, propone visitar un concesionario DC Motors para probar el coche sin compromiso.
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

        # --- Primer turno: intent "fecha-nacimiento" ---
        if intent_name == "fecha-nacimiento":
            return jsonify({
                "fulfillmentText": llm_reply,  # respuesta del LLM
                "outputContexts": [
                    {
                        "name": f"{req['session']}/contexts/esperando_coche_actual",
                        "lifespanCount": 1
                    }
                ]
            })

        # --- Segundo turno: detectamos que el contexto está activo ---
        contexts = query_result.get("outputContexts", [])
        for context in contexts:
            if context.get("name", "").endswith("esperando_coche_actual"):
                return jsonify({
                    "fulfillmentText": "Muy bien, me lo apunto para futuras promociones👌. ¿Y qué coche tienes actualmente?",
                    "followupEventInput": {
                        "name": "COCHE-ACTUAL"
                    }
                })
        

    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        llm_reply = "Error interno del servidor. Intenta de nuevo más tarde."

    return jsonify({"fulfillmentText": llm_reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    logger.info(f"Iniciando servidor OpenRouter en puerto {port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
