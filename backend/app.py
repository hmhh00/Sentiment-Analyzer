from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import json, os

app = Flask(__name__)
CORS(app)

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise RuntimeError("Environment variable ANTHROPIC_API_KEY is required")

client = anthropic.Anthropic(api_key=api_key)

DATA_FILE = "data/training_data.json"
if not os.path.exists("data"):
    os.makedirs("data")

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

SYSTEM_PROMPT = """أنت محلل مشاعر متخصص. مهمتك تحليل النص وإرجاع JSON فقط بدون أي كلام إضافي.

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
    {"label": "anger", "score": 0.7}
  ]
}

قواعد:
- emotion: الشعور الأقوى من القائمة المحددة فقط
- sentiment: positive إذا كان joy أو surprise، negative إذا كان anger/fear/sadness/disgust، neutral إذا كان neutral
- confidence: نسبة الثقة من 0 إلى 100
- all_emotions: جميع المشاعر السبعة مرتبة تنازلياً، مجموعها 100
- لا تضع أي نص خارج الـ JSON"""

@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.json.get("text", "").strip()
    if not text:
        return jsonify({"error": "النص فارغ"}), 400

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"حلل هذا النص: {text}"}]
    )

    raw = message.content[0].text.strip()
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
    app.run(debug=True, port=5000)