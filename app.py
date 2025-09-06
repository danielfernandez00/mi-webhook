from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Variables de entorno
HF_API_KEY = os.environ.get("HF_API_KEY")
MODEL_NAME = os.environ.get("MODEL_NAME", "microsoft/DialoGPT-small")
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        req = request.get_json(silent=True, force=True)
        user_text = req["queryResult"]["queryText"]

        payload = {
            "inputs": f"Eres un asistente amable y útil.\nUsuario: {user_text}\nAsistente:",
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
            timeout=60  # Aumenta el timeout si el modelo es grande
        )

        # Manejo de errores según el status code
        if response.status_code == 401:
            llm_reply = "Error: API Key de Hugging Face no válida o no autorizada."
        elif response.status_code == 403:
            llm_reply = "Error: No tienes permisos para usar este modelo."
        elif response.status_code == 404:
            llm_reply = "Error: Modelo no encontrado en Hugging Face."
        elif response.status_code != 200:
            llm_reply = f"Error: La API devolvió código {response.status_code}."
        else:
            data = response.json()
            llm_reply = data[0]["generated_text"].split("Asistente:")[-1].strip()

    except requests.exceptions.Timeout:
        llm_reply = "Error: La petición al modelo tardó demasiado y se agotó el tiempo."
    except Exception as e:
        print("Error interno:", e)
        llm_reply = f"Error interno: {str(e)}"

    return jsonify({"fulfillmentText": llm_reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
