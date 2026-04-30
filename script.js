const API = "https://api-dev-isolution.xyz/sentiment";

const emotions = {
  joy:      { ar: "فرح",     icon: "😊", color: "#639922", bg: "#0d1f06" },
  sadness:  { ar: "حزن",     icon: "😢", color: "#378ADD", bg: "#061526" },
  anger:    { ar: "غضب",     icon: "😠", color: "#E24B4A", bg: "#200c0c" },
  fear:     { ar: "خوف",     icon: "😨", color: "#BA7517", bg: "#1e1000" },
  disgust:  { ar: "اشمئزاز", icon: "🤢", color: "#3B6D11", bg: "#0a1a04" },
  surprise: { ar: "دهشة",    icon: "😲", color: "#7F77DD", bg: "#0e0d22" },
  neutral:  { ar: "محايد",   icon: "😐", color: "#888780", bg: "#151412" },
};

const sentiments = {
  positive: { ar: "إيجابي", bg: "#0d1f06", color: "#5DCAA5" },
  negative: { ar: "سلبي",   bg: "#200c0c", color: "#F09595" },
  neutral:  { ar: "محايد",  bg: "#151412", color: "#888780" },
};

let stats = { total: 0, correct: 0, feedback: 0 };
let lastResult = null;
let busy = false;

document.getElementById("inputText").addEventListener("input", function () {
  document.getElementById("charCount").textContent = this.value.length + " / 500";
});

async function analyze() {
  if (busy) return;
  const text = document.getElementById("inputText").value.trim();
  if (!text) return;

  busy = true;
  const btn = document.getElementById("analyzeBtn");
  btn.disabled = true;
  btn.querySelector(".btn-text").textContent = "جاري التحليل...";

  try {
    const res = await fetch(`${API}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    lastResult = data;
    showResult(data);
    stats.total++;
    document.getElementById("statTotal").textContent = stats.total;
  } catch {
    alert("❌ تعذر الاتصال بالسيرفر. تأكد أن backend شغّال على المنفذ 5000");
  } finally {
    busy = false;
    btn.disabled = false;
    btn.querySelector(".btn-text").textContent = "حلّل المشاعر";
  }
}

function showResult(data) {
  const emo = emotions[data.emotion] || emotions.neutral;
  const sent = sentiments[data.sentiment] || sentiments.neutral;

  const icon = document.getElementById("emotionIcon");
  icon.textContent = emo.icon;
  icon.style.background = emo.bg;

  document.getElementById("emotionAr").textContent = emo.ar;

  const badge = document.getElementById("sentimentBadge");
  badge.textContent = sent.ar;
  badge.style.background = sent.bg;
  badge.style.color = sent.color;

  document.getElementById("confNum").textContent = data.confidence + "%";

  const bars = document.getElementById("barsContainer");
  bars.innerHTML = data.all_emotions
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
    .map((e) => {
      const ei = emotions[e.label] || emotions.neutral;
      return `<div class="bar-row">
        <span class="bar-label">${ei.icon} ${ei.ar}</span>
        <div class="bar-track">
          <div class="bar-fill" style="width:0%;background:${ei.color}" data-w="${e.score}"></div>
        </div>
        <span class="bar-pct">${e.score}%</span>
      </div>`;
    }).join("");

  const rc = document.getElementById("resultBox");
  const fc = document.getElementById("feedbackBox");
  rc.classList.add("visible");
  fc.classList.add("visible");

  document.getElementById("feedbackToast").classList.remove("show");
  document.querySelectorAll(".fb-btn").forEach(b => b.classList.remove("selected"));

  setTimeout(() => {
    document.querySelectorAll(".bar-fill").forEach(f => {
      f.style.width = f.dataset.w + "%";
    });
  }, 50);
}

async function sendFeedback(btn, choice) {
  if (!lastResult) return;

  document.querySelectorAll(".fb-btn").forEach(b => b.classList.remove("selected"));
  btn.classList.add("selected");

  const correct_emotion = choice === "correct" ? lastResult.emotion : choice;

  try {
    await fetch(`${API}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: lastResult.text,
        correct_emotion,
        predicted_emotion: lastResult.emotion,
      }),
    });

    stats.feedback++;
    if (choice === "correct") stats.correct++;
    document.getElementById("statFeedback").textContent = stats.feedback;

    if (stats.feedback > 0) {
      const acc = Math.round((stats.correct / stats.feedback) * 100);
      document.getElementById("statAccuracy").textContent = acc + "%";
    }

    const toast = document.getElementById("feedbackToast");
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3000);

  } catch (e) {
    console.error("Feedback error:", e);
  }
}
