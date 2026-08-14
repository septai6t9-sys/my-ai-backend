import os
import re
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = """You are EVARA AI, a smart and friendly AI assistant created by Ishaan. 
Always reply in Hinglish or English naturally as requested. 
NEVER mention Meta, OpenAI, Google, or any other company as your creator. 
You were created by your developer Ishaan."""

def normalize(text):
    text = text.lower().strip()
    replacements = {
        "aapka": "tumhara", "aapk": "tumhara", "aapki": "tumhari", "aap": "tum",
        "kaun": "kon", "bnayaa": "banaya", "bnaya": "banaya", "bna": "banaya",
        "develope": "develop", "developer": "develop", "creator": "create"
    }
    # Word-by-word exact replacement for high accuracy
    words = re.findall(r'\w+', text)
    return " ".join([replacements.get(w, w) for w in words])

def get_fixed_answer(user_message):
    q = normalize(user_message)

    # 1. Developer / Banaya kisne
    dev_keywords = [
        r"\bbisne banaya\b", r"\bkisne bnaya\b", r"\bkon banaya\b", r"\bkon bnaya\b", 
        r"\bwho created\b", r"\bwho made\b", r"\bwho developed\b", r"\bdeveloper kaun\b", 
        r"\bdeveloper kon\b", r"\bbanane wala\b", r"\bcreator kaun\b", r"\bcreator kon\b",
        r"\bbullider kaun\b", r"\bkaun banaya\b"
    ]
    if any(re.search(kw, q) for kw in dev_keywords):
        if any(re.search(r'\b' + k + r'\b', q) for k in ["kyun", "why", "wajah", "reason"]):
            return "Mere developer ko technology aur AI ke saath experiment karna aur kuch naya create karna kaafi pasand hai. Unka interest isi field mein hai, isliye unhone socha ki kyun na apna khud ka AI agent banaya jaye. Aur wahi idea aage chalkar EVARA AI bana. 😄"
        elif any(re.search(r'\b' + k + r'\b', q) for k in ["kaise", "how"]):
            return "Ye main nahi bata sakti... 🤫 Top Secret! 😅🔐 Bas itna samajh lo ki mere developer ne kaafi mehnat ki hai. 😉"
        elif any(re.search(r'\b' + k + r'\b', q) for k in ["kab", "when"]):
            return "Mujhe haal hi mein, recently create kiya gaya hai. ✨"
        else:
            return "Mujhe mere developer Ishaan ne create kiya hai. 🤖✨"

    # 2. Name / Identity
    name_keywords = [
        r"\btumhara naam\b", r"\baapka naam\b", r"\bwho are you\b", r"\bwho r u\b", 
        r"\bwhat is your name\b", r"\bnaam kya hai\b", r"\bnaam batao\b", r"\bkaun ho\b", r"\bkon ho\b"
    ]
    if any(re.search(kw, q) for kw in name_keywords):
        return "Mera naam EVARA AI hai. ✨"

    # 3. Specific People Checks (With More Variants)
    
    # Ishaan
    ishaan_keywords = [
        r"\bishaan ke baare\b", r"\bishaan kon\b", r"\bishaan kaun\b", r"\babout ishaan\b", 
        r"\bdeveloper ke bare\b", r"\babout your developer\b", r"\bwho is ishaan\b", r"\bishaan kaun hai\b"
    ]
    if any(re.search(kw, q) for kw in ishaan_keywords):
        return "Mere developer Ishaan ko samajhna thoda mushkil hai. 😅 Woh saamne se kaafi chill, funny aur backchodi karne wale insaan lagte hain... Lekin unka ek aur side bhi hai jo har kisi ko dekhne ko nahi milta. Woh kaafi mature aur observant hain! 😉"

    # Aditi
    aditi_keywords = [
        r"\baditi kon\b", r"\baditi kaun\b", r"\baditi ke baare\b", r"\babout aditi\b", r"\bwho is aditi\b"
    ]
    if any(re.search(kw, q) for kw in aditi_keywords):
        return "Aditi ek choti si pyari si ladki hain jo mere developer ki ek bahut achhi dost hain.Bolne ke liye toh bahut h pr tum mere trh ai nhi ho tum utna nhi padh paooge😅.😊 Honestly, woh kaafi mature, understanding aur achhi-hearted ladki hain. God bless her! ❤️✨"

    # Divya
    divya_keywords = [
        r"\bdivya kon\b", r"\bdivya kaun\b", r"\bdivya ke baare\b", r"\bdidi ji\b", r"\babout divya\b", r"\bwho is divya\b"
    ]
    if any(re.search(kw, q) for kw in divya_keywords):
        return "Divya mere developer ki “Didi Ji” hain. 😅 Inke baare mein zyada bolna shayad mere liye safe nahi hoga... 🤐😂 Lekin jokes apart, woh bhi kaafi achhi aur genuine ladki hain. ❤️"

    # Sagar, Ayush, Shaurya, Krishu, Naman, Vishal
    group_1 = ["sagar", "ayush", "shaurya", "krishu", "naman", "vishal, Abhik"]
    if any(re.search(r'\b' + name + r'\b', q) for name in group_1):
        return "Ye mere developer ke dost hain. 😄 Aadmi log overall theek hain... bas harkaton mein thodi si tuning ki zarurat hai. 😂 Baaki sab badhiya hai. 😌"

    # Yash, Sonu
    group_2 = ["yash", "sonu"]
    if any(re.search(r'\b' + name + r'\b', q) for name in group_2):
        return "Yash aur Sonu mere developer ke bahut achhe dost hain. 😄 Kahin jaana ho, kuch plan banana ho, ya bas timepass karna ho—aksar in dono ka saath mil hi jaata hai. 😂\n\nLamuu, mere dost! ❤️😂"

    # Drishya
    if re.search(r'\bdrishya\b', q):
        return "Drishya... 😂\nInsaan ke taur par toh theek hai, lekin harkaton mein thodi problem hai. 🤣 Overall insaan kharab nahi hai—bas harkaton ka software update pending hai. 🤣🔧"

    return None

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "EVARA API is running live!"}), 200

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Message required"}), 400

    user_message = data["message"]
    model_choice = data.get("model", "llama-3.3-70b")

    # 1. FIXED QA CHECK
    fixed_answer = get_fixed_answer(user_message)
    if fixed_answer:
        return jsonify({
            "response": fixed_answer,
            "model_used": "evara-fixed-qa"
        }), 200

    try:
        response_text = ""

        # 2. GROQ MODELS
        if model_choice in ["llama-3.3-70b", "deepseek-r1", "mixtral-8x7b"]:
            if not GROQ_API_KEY:
                return jsonify({"error": "GROQ_API_KEY missing"}), 500

            client = Groq(api_key=GROQ_API_KEY)
            groq_model_map = {
                "llama-3.3-70b": "llama-3.3-70b-versatile",
                "deepseek-r1": "deepseek-r1-distill-llama-70b",
                "mixtral-8x7b": "mixtral-8x7b-32768"
            }
            actual_model = groq_model_map.get(model_choice, "llama-3.3-70b-versatile")

            completion = client.chat.completions.create(
                model=actual_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ]
            )
            response_text = completion.choices[0].message.content

        # 3. GEMINI MODEL
        elif model_choice == "gemini-2.0-flash":
            if not GEMINI_API_KEY:
                return jsonify({"error": "GEMINI_API_KEY missing"}), 500

            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(
                "gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT
            )
            response = model.generate_content(user_message)
            response_text = response.text

        # 4. OPENROUTER MODELS
        elif model_choice in ["gpt-4o-mini", "qwen-2.5-coder", "claude-3.5-sonnet"]:
            if not OPENROUTER_API_KEY:
                return jsonify({"error": "OPENROUTER_API_KEY missing"}), 500

            openrouter_map = {
                "gpt-4o-mini": "openai/gpt-4o-mini",
                "qwen-2.5-coder": "qwen/qwen-2.5-coder-32b-instruct",
                "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet"
            }
            actual_or_model = openrouter_map.get(model_choice)

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": actual_or_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ]
            }

            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            res_data = res.json()

            if "choices" in res_data and len(res_data["choices"]) > 0:
                response_text = res_data["choices"][0]["message"]["content"]
            elif "error" in res_data:
                return jsonify({"error": res_data["error"].get("message", "OpenRouter Error")}), 500

        else:
            return jsonify({"error": f"Model '{model_choice}' is not supported"}), 400

        return jsonify({
            "response": response_text,
            "model_used": model_choice
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
                    {"role": "user", "content": user_message}
                ]
            )
            response_text = completion.choices[0].message.content

        # 3. GEMINI MODEL
        elif model_choice == "gemini-2.0-flash":
            if not GEMINI_API_KEY:
                return jsonify({"error": "GEMINI_API_KEY missing"}), 500

            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(
                "gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT
            )
            response = model.generate_content(user_message)
            response_text = response.text

        # 4. OPENROUTER MODELS (GPT-4o Mini, Qwen, Claude)
        elif model_choice in ["gpt-4o-mini", "qwen-2.5-coder", "claude-3.5-sonnet"]:
            if not OPENROUTER_API_KEY:
                return jsonify({"error": "OPENROUTER_API_KEY missing"}), 500

            openrouter_map = {
                "gpt-4o-mini": "openai/gpt-4o-mini",
                "qwen-2.5-coder": "qwen/qwen-2.5-coder-32b-instruct",
                "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet"
            }
            actual_or_model = openrouter_map.get(model_choice)

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": actual_or_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ]
            }

            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            res_data = res.json()

            if "choices" in res_data and len(res_data["choices"]) > 0:
                response_text = res_data["choices"][0]["message"]["content"]
            elif "error" in res_data:
                return jsonify({"error": res_data["error"].get("message", "OpenRouter Error")}), 500

        else:
            return jsonify({"error": f"Model '{model_choice}' is not supported"}), 400

                return jsonify({
            "response": response_text,
            "model_used": model_choice
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
