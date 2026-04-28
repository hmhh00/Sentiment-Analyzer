from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
import json, os

app = Flask(__name__)
CORS(app)

# نموذج متقدم للمشاعر (يدعم 6 مشاعر)
classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=None
)

DATA_FILE = "data/training_data.json"
if not os.path.exists("data"):
    os.makedirs("data")

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.json.get("text", "")
    results = classifier(text)[0]
    
    # ترتيب حسب الثقة
    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    top_emotion = sorted_results[0]
    
    # تحديد إيجابي/سلبي/محايد
    positive_emotions = ["joy", "surprise"]
    negative_emotions = ["anger", "disgust", "fear", "sadness"]
    
    if top_emotion["label"] in positive_emotions:
        sentiment = "positive"
    elif top_emotion["label"] in negative_emotions:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return jsonify({
        "text": text,
        "sentiment": sentiment,
        "emotion": top_emotion["label"],
        "confidence": round(top_emotion["score"] * 100, 1),
        "all_emotions": sorted_results[:3]
    })

@app.route("/feedback", methods=["POST"])
def feedback():
    """المستخدم يصحح النتيجة - هذا يساعد في التعلم"""
    data = request.json
    training_data = load_data()
    training_data.append({
        "text": data["text"],
        "correct_emotion": data["correct_emotion"],
        "predicted_emotion": data["predicted_emotion"]
    })
    with open(DATA_FILE, "w") as f:
        json.dump(training_data, f)
    return jsonify({"status": "saved"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)