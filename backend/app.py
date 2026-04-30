from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
import json, os

app = Flask(__name__)
CORS(app, origins="*", methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

DATA_FILE = "data/training_data.json"
if not os.path.exists("data"):
    os.makedirs("data")

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

PROMPT = """أنت محلل مشاعر متخصص. حلل النص وأرجع JSON فقط بدون أي كلام إضافي أو markdown.

الصيغة المطلوبة:
{
  "emotion": "joy|sadness|anger|fear|surprise|disgust|neutral",
  "sentiment": "positive|negative|neutral",
  "confidence": 85.5,
  "all_emotions": [
    {"label": "joy", "score": 85.5},
    {"label": "neutral", "score": 8.2},
    {"label": "surprise", "score": 4.1},
    {"label": "sadness", "score": 1.5},
    {"label": "anger", "score": 0.7},
    {"label": "fear", "score": 0.5},
    {"label": "disgust", "score": 0.3}
  ]
}

قواعد:
- emotion: الشعور الأقوى من القائمة فقط
- sentiment: positive إذا joy أو surprise، negative إذا anger/fear/sadness/disgust، neutral إذا neutral
- confidence: نسبة الثقة 0-100
- all_emotions: المشاعر السبعة مرتبة تنازلياً ومجموعها 100
- لا تضع أي نص خارج الـ JSON"""

@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.json.get("text", "").strip()
    if not text:
        return jsonify({"error": "النص فارغ"}), 400

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"{PROMPT}\n\nالنص: {text}"
    )
    raw = response.text.strip().replace("```json", "").replace("```", "").strip()
    data = json.loads(raw)
    data["text"] = text
    return jsonify(data)

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.json
    training_data = load_data()
    training_data.append({
        "text": data.get("text"),
        "correct_emotion": data.get("correct_emotion"),
        "predicted_emotion": data.get("predicted_emotion")
    })
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)
    return jsonify({"status": "saved", "total": len(training_data)})

@app.route("/stats", methods=["GET"])
def stats():
    data = load_data()
    return jsonify({"total_feedback": len(data)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)