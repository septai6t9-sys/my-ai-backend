from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from groq import Groq
import google.generativeai as genai

app = Flask(__name__)
CORS(app)  # Mobile website/Frontend se request accept karne ke liye

# Render Environment Variables se Keys load me aayengi
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "API is running live!"}), 200

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    if not data or "message" not in data:
        return jsonify({"error": "Message required"}), 400

    user_message = data.get("message")
    model_choice = data.get("model", "groq")  # Default model Groq rahega

    try:
        # Option 1: Groq API Call
        if model_choice == "groq":
            if not GROQ_API_KEY:
                return jsonify({"error": "GROQ_API_KEY missing in Render settings"}), 500
            client = Groq(api_key=GROQ_API_KEY)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": user_message}],
            )
            response_text = completion.choices[0].message.content

        # Option 2: Gemini API Call
        elif model_choice == "gemini":
            if not GEMINI_API_KEY:
                return jsonify({"error": "GEMINI_API_KEY missing in Render settings"}), 500
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(user_message)
            response_text = response.text

        # Option 3: OpenRouter API Call (Free Models)
        elif model_choice == "openrouter":
            if not OPENROUTER_API_KEY:
                return jsonify({"error": "OPENROUTER_API_KEY missing in Render settings"}), 500
            
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "meta-llama/llama-3.3-70b-instruct:free", # Aap deepseek/deepseek-r1:free bhi use kar sakte hain
                "messages": [{"role": "user", "content": user_message}]
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            res_data = res.json()
            
            if "choices" in res_data and len(res_data["choices"]) > 0:
                response_text = res_data["choices"][0]["message"]["content"]
            else:
                return jsonify({"error": "OpenRouter API Error", "details": res_data}), 500

        else:
            return jsonify({"error": "Invalid model choice"}), 400

        return jsonify({"response": response_text, "model_used": model_choice}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
