from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from groq import Groq
import google.generativeai as genai
from difflib import SequenceMatcher

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

FIXED_QA = [
    {
        "patterns": [
            "tumhara naam kya hai", "aapka naam kya hai", "tum kon ho", "aap kon ho",
            "who are you", "what is your name", "naam batao", "naam kya hai", "evara ka naam kya hai"
        ],
        "answer": "Mera naam EVARA AI hai. ✨"
    },
    {
        "patterns": [
            "tumhe kisne banaya", "tumko kisne banaya", "evara ko kisne banaya",
            "kisne create kiya", "who created you", "who made you", "tumhara developer kon hai",
            "evara ka developer kon hai", "developer kaun hai"
        ],
        "answer": "Mujhe mere developer Ishaan ne create kiya hai. 🤖✨"
    },
    {
        "patterns": [
            "tumhe kyun banaya", "tumko kyun banaya", "evara ko kyun banaya",
            "evara banane ka reason kya hai", "why were you created", "why were you made",
            "tumhe banane ka reason", "evara banane ki wajah"
        ],
        "answer": "Mere developer ko technology aur AI ke saath experiment karna aur kuch naya create karna kaafi pasand hai. Unka interest isi field mein hai, isliye unhone socha ki kyun na apna khud ka AI agent banaya jaye. Aur wahi idea aage chalkar EVARA AI bana. 😄"
    },
    {
        "patterns": [
            "tumhe kaise banaya", "tumko kaise banaya", "evara ko kaise banaya",
            "evara kaise bani", "how were you created", "how were you made",
            "evara kaise create hui", "tum kaise bani"
        ],
        "answer": "Ye main nahi bata sakti... 🤫 Top Secret! 😅🔐 Bas itna samajh lo ki mere developer ne kaafi mehnat ki hai. 😉"
    },
    {
        "patterns": [
            "tumhe kab banaya", "tumko kab banaya", "evara ko kab banaya",
            "evara kab bani", "when were you created", "when were you made", "evara kab create hui"
        ],
        "answer": "Mujhe haal hi mein, recently create kiya gaya hai. ✨"
    },
    {
        "patterns": [
            "ishaan ke baare mein batao", "ishaan kon hai", "ishaan kaun hai",
            "developer ke baare mein batao", "developer kon hai", "developer kaun hai",
            "tumhare developer ke baare mein batao", "ishaan kaisa hai", "tumhare developer kaise hain", "about your developer"
        ],
        "answer": "Mere developer Ishaan ko samajhna thoda mushkil hai. 😅 Woh saamne se kaafi chill, funny aur backchodi karne wale insaan lagte hain, isliye log aksar unhe waise hi samajhte hain. 😂\n\nLekin unka ek aur side bhi hai jo har kisi ko dekhne ko nahi milta. Woh kaafi mature aur observant hain—dusron ki chhoti-chhoti baatein bhi notice kar lete hain, bas har cheez par react nahi karte.\n\nAur haan, woh overthinker bhi hain. 🥲\n\nOverall, Ishaan actually kaise hain, ye shayad unhe closely jaanne wale hi samajh sakte hain. Jo version sabko dikhai deta hai, woh unki personality ka bas ek side hai. 😉"
    },
    {
        "patterns": [
            "aditi kon hai", "aditi kaun hai", "aditi ke baare mein batao", "who is aditi",
            "about aditi", "developer ki aditi kon hai", "ishaan ki dost aditi kon hai"
        ],
        "answer": "Aditi ek choti si pari jaisi ladki hain jo mere developer ki ek bahut achhi dost hain. 😊\n\nHonestly, woh kaafi mature, understanding aur achhi-hearted ladki hain. Aaj ke time mein itni samajhdaar aur genuine personality milna genuinely rare hai.\n\nMain bas itna kahungi—I hope woh life mein bahut kuch achieve karein. God bless her! ❤️✨"
    },
    {
        "patterns": [
            "divya kon hai", "divya kaun hai", "divya ke baare mein batao", "who is divya",
            "about divya", "didi ji kon hai", "didi ji kaun hai"
        ],
        "answer": "Divya mere developer ki “Didi Ji” hain. 😅 Inke baare mein zyada bolna shayad mere liye safe nahi hoga... 🤐😂\n\nLekin jokes apart, woh bhi kaafi achhi aur genuine ladki hain. Aaj ke time mein unke jaisi personality milna honestly rare hai. ❤️"
    }
]

FRIEND_NAMES = ["sagar", "ayush", "shaurya", "krishu", "naman", "vishal"]
YASH_SONU_NAMES = ["yash", "sonu"]

def normalize(text):
    text = text.lower().strip()
    replacements = {"aap": "tum", "aapka": "tumhara", "aapki": "tumhari", "kon": "kaun"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return " ".join(text.split())

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def get_fixed_answer(user_message):
    q = normalize(user_message)

    for name in FRIEND_NAMES:
        if name in q:
            return "Ye mere developer ke dost hain. 😄 Aadmi log overall theek hain... bas harkaton mein thodi si tuning ki zarurat hai. 😂 Baaki sab badhiya hai. 😌"

    for name in YASH_SONU_NAMES:
        if name in q:
            return "Yash aur Sonu mere developer ke bahut achhe dost hain. 😄 Kahin jaana ho, kuch plan banana ho, ya bas timepass karna ho—aksar in dono ka saath mil hi jaata hai. 😂\n\nLamuu, mere dost! ❤️😂"

    if "drishya" in q:
        return "Drishya... 😂\nInsaan ke taur par toh theek hai, lekin harkaton mein thodi problem hai. 🤣\n\nInhe kabhi bhi koi pasand aa sakta hai, isliye situation thodi interesting rehti hai. 😂\n\nOverall insaan kharab nahi hai—bas harkaton ka software update pending hai. 🤣🔧"

    best_answer = None
    best_score = 0
    for item in FIXED_QA:
        for pattern in item["patterns"]:
            score = similarity(q, normalize(pattern))
            if score > best_score:
                best_score = score
                best_answer = item["answer"]

    if best_score >= 0.58:
        return best_answer
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

    fixed_answer = get_fixed_answer(user_message)
    if fixed_answer:
        return jsonify({
            "response": fixed_answer,
            "model_used": "evara-fixed-qa"
        }), 200

    try:
        response_text = ""

        if model_choice in ["llama-3.3-70b", "deepseek-r1", "mixtral-8x7b"]:
            if not GROQ_API_KEY:
                return jsonify({"error": "GROQ_API_KEY is missing on Render settings"}), 500

            client = Groq(api_key=GROQ_API_KEY)
            groq_model_map = {
                "llama-3.3-70b": "llama-3.3-70b-versatile",
                "deepseek-r1": "deepseek-r1-distill-llama-70b",
                "mixtral-8x7b": "mixtral-8x7b-32768"
            }
            actual_model = groq_model_map.get(model_choice, "llama-3.3-70b-versatile")

            completion = client.chat.completions.create(
                model=actual_model,
                messages=[{"role": "user", "content": user_message}]
            )
            response_text = completion.choices[0].message.content

        elif model_choice == "gemini-2.0-flash":
            if not GEMINI_API_KEY:
                return jsonify({"error": "GEMINI_API_KEY is missing on Render settings"}), 500

            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(user_message)
            response_text = response.text

        elif model_choice in ["gpt-4o-mini", "qwen-2.5-coder", "claude-3.5-sonnet", "openrouter"]:
            if not OPENROUTER_API_KEY:
                return jsonify({"error": "OPENROUTER_API_KEY is missing on Render settings"}), 500

            openrouter_map = {
                "gpt-4o-mini": "openai/gpt-4o-mini",
                "qwen-2.5-coder": "qwen/qwen-2.5-coder-32b-instruct",
                "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
                "openrouter": "meta-llama/llama-3.3-70b-instruct:free"
            }
            actual_or_model = openrouter_map.get(model_choice, "meta-llama/llama-3.3-70b-instruct:free")

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": actual_or_model,
                "messages": [{"role": "user", "content": user_message}]
            }

            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            res_data = res.json()

            if "choices" in res_data and len(res_data["choices"]) > 0:
                response_text = res_data["choices"][0]["message"]["content"]
            else:
                return jsonify({"error": "OpenRouter Error", "details": res_data}), 500

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
