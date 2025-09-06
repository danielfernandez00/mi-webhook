from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Tu API Key de DeepSeek (desde variables de entorno en Railway)
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        req = request.get_json(silent=True, force=True)
        user_text = req["queryResult"]["queryText"]

        # Petición a DeepSeek
        url = "https://api.openrouter.ai/v1/deepseek-r1"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-reasoner",
            "messages": [{"role": "user", "content": user_text}]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            llm_reply = f"Error: DeepSeek API devolvió código {response.status_code}"
        else:
            data = response.json()
            llm_reply = data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("Error interno:", e)
        llm_reply = f"Error interno: {str(e)}"

    return jsonify({"fulfillmentText": llm_reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
