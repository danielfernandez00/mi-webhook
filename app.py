from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# API Key y modelo desde variables de entorno
HF_API_KEY = os.environ.get("HF_API_KEY")
MODEL_NAME = os.environ.get("MODEL_NAME", "TheBloke/WizardLM-7B-uncensored-GPTQ")

HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        req = request.get_json(silent=True, force=True)
        user_text = req["queryResult"]["queryText"]

        # Prompt para el modelo
        payload = {
            "inputs": f"Eres un asistente amable y útil. Debes devolver el saludo al usuario\nUsuario: {user_text}\nAsistente:",
            "parameters": {
                "max_new_tokens": 150,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }

        response = requests.post(
            f"https://api-inference.huggingface.co/models/{MODEL_NAME}",
            headers=HEADERS,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            llm_reply = "Lo siento, hubo un problema procesando tu solicitud."
        else:
            data = response.json()
            llm_reply = data[0]["generated_text"].split("Asistente:")[-1].strip()

    except Exception as e:
        print("Error:", e)
        llm_reply = "Ocurrió un error inesperado. Intenta de nuevo."

    return jsonify({"fulfillmentText": llm_reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
