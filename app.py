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
                "content": """Eres un asistente útil y amigable. Responde de manera concisa y clara.
                Responde a las preguntas sobre nuestros productos. Asume que te preguntan sobre el DC-SUV 2025

                Información sobre el DC-SUV 2025:
                Q. ¿Qué motorizaciones está disponibles?
                A. El DC-SUV 2025 cuenta con 4 posibles motorizaciones
                    - TCe 67 kW (90CV)
                    - Eco-G 74 kW (100CV)
                    - TCe 103 kW (140CV) EDC mild hybrid
                    - E-Tech full hybrid 117 kW (160CV)

                Q. ¿Qué ventajas tiene cada motorización?
                A. Ventajas de las motorizaciones del DC Motors DC-SUV 2025

                        1. TCe 67 kW (90 CV) – Gasolina
                        **Ventajas:**
                        - **Eficiencia en consumo:** Consumo medio de 5,9 l/100 km, ideal para economía diaria.
                        - **Conducción ágil:** Potencia suficiente para ciudad y viajes cortos.

                        **Ideal para:** Conductores que buscan un vehículo económico y funcional para uso urbano.

                        ---

                        2. Eco-G 74 kW (100 CV) – Gasolina/GLP
                        **Ventajas:**
                        - **Bajo coste por kilómetro:** El GLP es más económico que la gasolina.
                        - **Etiqueta ECO:** Beneficios fiscales y acceso a zonas de bajas emisiones.
                        - **Versatilidad:** Posibilidad de utilizar dos combustibles, aumentando autonomía.

                        **Ideal para:** Conductores que realizan trayectos largos y quieren reducir costes operativos.

                        ---

                        3. TCe 103 kW (140 CV) EDC Mild Hybrid – Gasolina
                        **Ventajas:**
                        - **Transmisión automática EDC:** Cambios de marcha rápidos y suaves.
                        - **Tecnología Mild Hybrid:** Asistencia eléctrica que reduce consumo y emisiones.
                        - **Potencia equilibrada:** Adecuada para viajes largos y carretera.

                        **Ideal para:** Conductores que buscan un equilibrio entre rendimiento y eficiencia.

                        ---

                        4. E-Tech Full Hybrid 117 kW (160 CV) – Híbrido
                        **Ventajas:**
                        - **Conducción 100 por cien eléctrica en ciudad:** Trayectos urbanos sin emisiones.
                        - **Etiqueta ECO:** Acceso a zonas de bajas emisiones y beneficios fiscales.
                        - **Potencia elevada:** Adecuada para viajes largos y carretera.
                        - **Tecnología avanzada:** Sistema híbrido que optimiza el consumo.

                        **Ideal para:** Conductores que buscan sostenibilidad sin renunciar a la potencia.

                Q. ¿Qué etiquetas tiene cada motorización?
                A.  - TCe 67 kW (90CV): etiqueta C
                    - Eco-G 74 kW (100CV): etiqueta ECO
                    - TCe 103 kW (140CV) EDC mild hybrid: etiqueta ECO
                    - E-Tech full hybrid 117 kW (160CV): etiqueta ECO

                Q. ¿Cómo funciona la tecnología full hybrid E-Tech y cómo recupera energía? 
                A. La tecnología full hybrid E-Tech combina un motor eléctrico con un motor de gasolina, 
                que se activa según las condiciones del trayecto. La conducción 100% eléctrica 
                está optimizada por una caja de cambios automática multimodo. La batería recupera
                energía automáticamente durante la desaceleración y la frenada, gracias a un
                sistema de recuperación de energía. Todos los arranques se realizan en modo 
                eléctrico.

                Q. ¿Cuál es el consumo y las emisiones de CO₂ del DC-SUV 2025 full hybrid 
                E-Tech? 
                A. El consumo homologado es de 4,4 l/100 km y las emisiones de CO₂ son de 
                99 g/km. Gracias a la eficiencia de su cadena cinemática, las emisiones de CO₂ 
                se limitan a 93 g/km, permitiéndole obtener la etiqueta ECO.

                Q. ¿Qué características definen a la motorización mild hybrid 140 CV? 
                A. La motorización mild hybrid es el primer nivel de hibridación de la gama E-Tech. Ofrece una aceleración más dinámica y ayuda a disminuir el consumo. El motor térmico recibe asistencia eléctrica durante las fases de aceleración, lo que resulta en una experiencia de conducción más suave y dinámica, y un consumo limitado. La versión DC-SUV 2025 mild hybrid ofrece un consumo mixto reducido a partir de 5,9 L/100 km

                Q. ¿Qué ventajas ofrece el motor de gasolina TCe 90 CV? 
                A. El motor de gasolina TCe 90 CV se caracteriza por un elevado rendimiento y un consumo controlado. Es fiable y eficaz, combinando el placer de conducir tanto en carretera como en ciudad. Su motor de tres cilindros permite reducir el presupuesto de mantenimiento gracias a su cadena de distribución. Es potente, versátil y se ajusta óptimamente a las necesidades de conducción urbana y en trayectos largos

                Q. ¿Qué es la motorización Eco-G 100 CV y cuáles son sus beneficios? 
                A. La motorización Eco-G es una tecnología de bicarburación de gasolina y GLP (Gas Licuado del Petróleo), que combina ahorro de carburante, una mayor autonomía y una disminución de las emisiones de CO₂. Utiliza dos depósitos (gasolina y GLP), y el motor selecciona el carburante según su disponibilidad. Es un carburante alternativo, económico y ecológico, que permite reducir las emisiones de CO₂ y ofrece una mayor autonomía de hasta 1.100 km, sin necesidad de cambiar los hábitos de conducción ni tener límites de acceso a aparcamientos y centros urbanos

                Q. ¿Existen promociones actuales para la compra de un DC-SUV 2025 Eco-G? 

                Sí, se mencionan dos promociones futuras de carburante GLP por la compra de un DC-SUV 2025 Eco-G:
                - Oferta Repsol: Un cupón de 200€ en carburante GLP válido en Península y Baleares para pedidos realizados entre el 1 de febrero de 2025 y el 31 de diciembre de 2025.
                - Oferta DISA: Un cupón de 200€ en carburante GLP válido en Canarias para pedidos realizados entre el 1 de mayo de 2025 y el 30 de junio de 2025. Ambas promociones tienen condiciones específicas de canje y validez que deben consultarse en sus bases notariales

                Q. ¿Qué tipo de accesorios ofrece DC Motors para el DC-SUV 2025? 
                A. DC Motors ofrece accesorios para el DC-SUV 2025 diseñados para perfeccionar el viaje, enfocándose en estilo definitivo, experiencia a bordo, capacidad de transporte y protección para actividades al aire libre. Estos se dividen en categorías como Diseño, Vida a bordo, Transporte y protección

                Q. ¿Cómo se puede personalizar el diseño exterior del DC Motors DC-SUV 2025? 
                A. El diseño exterior del DC-SUV 2025 se puede realzar con packs de personalización exterior (disponibles en "gris perla", "gris highland" o "negro brillante" para protectores de paragolpes y carcasas de retrovisores), carcasas de retrovisor individuales (en "gris perla", "gris highland"), estribos laterales Premium y barras de estilo. También se ofrece iluminación de bienvenida bajo la carrocería que proyecta una luz al acercarse al vehículo en lugares con poca iluminación.

                Q.  ¿Qué accesorios están disponibles para mejorar la experiencia "vida a bordo" en el DC-SUV 2025? 
                A. Para el confort y el ambiente a bordo, se ofrecen accesorios como un cojín ultracómodo en el reposacabezas trasero negro con tejido Alcantara, un reposabrazos trasero portátil con almacenamiento y organizador multifunción en asiento delantero, alfombrillas de protección esprit Alpine con distintivo Alpine y pespuntes azules, y pedales deportivos y umbrales de puerta iluminados de acero inoxidable con las siglas DC Motors

                Q. ¿Qué opciones de transporte y protección existen para el maletero y el techo del DC-SUV 2025? 
                A. Para aumentar la capacidad de carga y proteger el vehículo, se pueden encontrar:
                - Barras de techo QuickFix y cofres de techo que aumentan la capacidad hasta 630 litros.
                - Enganche de remolque retráctil semieléctrico para remolcar equipos.
                - Bandeja de maletero para transportar objetos que puedan ensuciar y proteger la alfombra original.
                - Protector de maletero modulable EasyFlex, antideslizante e impermeable, para objetos voluminosos y sucios

                Q. ¿Qué precio de salida tiene cada motorización?
                A. Motorización
                Precio de Salida
                TCe 90 CV (Gasolina): 21.690 €
                TCe 100 CV GLP: 23.390 €
                E-Tech full hybrid 145 CV: 27.490 €
                TCe 103 kW (140CV) EDC mild hybrid: 24.900 €

                Q. ¿Qué opciones de financiación hay?
                A. DC Motors ofrece varias opciones de financiación para la compra de vehículos, incluyendo Crédito, Preference, Renting y Suscripción. Estas soluciones están diseñadas por Mobilize Financial Services.

                Q. ¿Qué es la financiación "Crédito" y cuáles son sus características principales? 
                A. El Crédito es una solución de financiación sencilla que se caracteriza por ofrecer la misma tasa de interés a lo largo de toda la financiación, independientemente de la duración elegida. Permite financiar el 100% del coche sin pagar entrada, aunque se puede elegir la entrada. Al finalizar la financiación, el coche es totalmente tuyo. La duración del contrato puede ser de tres a ocho años y el kilometraje es ilimitado, con una mensualidad fija. Es posible añadir seguros y servicios opcionales. Este tipo de financiación está disponible para todos los modelos de vehículos nuevos DC Motors y también para vehículos de ocasión.

                Q. ¿Cómo funciona la financiación "Preference" y qué opciones se tienen al final del contrato? 
                A. Preference es una solución diseñada para quienes desean cambiar de coche cada cierto tiempo, ofreciendo flexibilidad. Se puede elegir la duración del contrato (3, 4 o 5 años) y el kilometraje anual. Al final del contrato, el cliente tiene tres opciones:
                1. Cambiar el coche por uno nuevo, beneficiándose de ofertas exclusivas en la renovación.
                2. Quedarse con el DC Motors pagando la última cuota o refinanciando.
                3. Devolver el coche entregándolo como pago de la última cuota. Preference permite acceder a gamas más altas con cuotas más asequibles y siempre disfrutar de lo último de la marca.

                Q. ¿Qué ventajas ofrece el "Renting" de DC Motors y qué servicios incluye? 
                A. El Renting permite disfrutar de un coche sin preocupaciones, ya que todos los servicios están incluidos en la cuota mensual. Con Renting, es posible estrenar coche cada 3, 4 o 5 años. Los servicios incluidos abarcan: el alquiler mensual, impuestos de circulación, seguro auto a todo riesgo, mantenimiento y reparaciones, asistencia en carretera 24h, intervenciones de posventa en talleres oficiales, gastos de matriculación, garantía del vehículo, gestión de multas y cambio de neumáticos. La duración del contrato puede ir de dos a cinco años (o 36 a 60 meses) y el kilometraje es a elegir (desde 10.000 km/año hasta 200.000 km/año). Se puede elegir si se paga o no una entrada al inicio.

                Q. ¿Qué se sabe sobre la opción de financiación "Suscripción"? 
                A. La Suscripción permite disfrutar de los modelos más recientes, pagando únicamente por el uso del coche y beneficiándose de todos los seguros y garantías incluidas. La contratación de este servicio es completamente online.

                Q. ¿Dónde se pueden contratar estas opciones de financiación? 
                A. Tanto el Crédito, Preference como el Renting se pueden contratar directamente en un concesionario DC Motors. Un asesor experto ofrecerá una solución personalizada según las necesidades del cliente.

                Q. ¿Qué servicios adicionales de protección y mantenimiento se pueden incluir con la financiación del DC-SUV 2025?
                A. Además de las opciones de financiación, se pueden añadir varios servicios adicionales para el DC-SUV 2025 (y otros modelos):
                • Seguro Auto: Mobilize Financial Services ofrece diferentes modalidades de seguro a todo riesgo, con o sin franquicia, gracias a acuerdos con aseguradoras colaboradoras.
                • Extensión de Garantía: Permite extender la garantía del coche 1, 2 o 3 años, incluyendo asistencia DC Motors 24/7 en toda Europa.
                • Mantenimiento: Se ofrecen packs llave en mano como el "pack estándar" para revisiones con garantía del fabricante hasta cinco años, y el "pack ventajas" que extiende la garantía después de los cinco años.
                • Seguro del Vehículo Conectado: Permite acceder a soluciones de seguros personalizadas y descuentos al autorizar la recopilación e interpretación de datos de uso del vehículo.
                • Servicio DC Motors Care 5: Para vehículos nuevos, incluye 5 años de mantenimiento, 5 años de garantía (3 de fábrica + 2 de extensión) y 5 años de asistencia en carretera con soluciones de movilidad.

                Q. ¿Quién es el organismo de financiación de DC Motors? 
                A. El organismo de financiación de DC Motors es Mobilize Financial Services. Para el caso específico del Renting al detalle, también se menciona a Overlease.

                Q. ¿Las opciones de financiación están disponibles solo para vehículos nuevos? 
                A. No, las soluciones de Crédito y Preference están disponibles tanto para vehículos nuevos como para vehículos de ocasión DC Motors. El Renting está disponible para vehículos nuevos y también se ofrece una modalidad de leasing para profesionales"""
            
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