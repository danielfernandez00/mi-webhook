from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Configuración de OpenRouter
openai.api_key = os.environ.get("OPENROUTER_API_KEY")  # Tu API Key de OpenRouter
openai.api_base = "https://openrouter.ai/api/v1"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # Obtener texto del usuario desde Dialogflow
        req = request.get_json(force=True)
        user_text = req["queryResult"]["queryText"]

        # Llamada a GPT-3.5 via OpenRouter
        response = openai.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_text}]
        )

        # Extraer respuesta generada
        llm_reply = response.choices[0].message.content.strip()

    except Exception as e:
        # Manejo robusto de errores
        print("Error interno:", e)
        llm_reply = f"Error interno: {str(e)}"

    # Devolver respuesta a Dialogflow
    return jsonify({"fulfillmentText": llm_reply})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
