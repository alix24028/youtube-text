# -*- coding: utf-8 -*-
import re
import math
from html import unescape
from urllib.parse import urlparse, parse_qs

from flask import Flask, jsonify, render_template_string, request
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    CouldNotRetrieveTranscript,
)

app = Flask(__name__)

HTML = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>تحويل فيديو يوتيوب إلى نص</title>
  <style>
    :root{
      --bg:#f6f8fb; --card:#ffffff; --text:#111827; --muted:#6b7280;
      --primary:#0f766e; --primary-dark:#115e59; --border:#e5e7eb;
      --shadow:0 12px 35px rgba(15,23,42,.08); --danger:#b91c1c; --ok:#0f766e;
    }
    *{box-sizing:border-box}
    body{
      margin:0; font-family:Tahoma,Arial,"Segoe UI",system-ui,sans-serif;
      background:linear-gradient(180deg,#f8fafc 0%,#eef2f7 100%); color:var(--text); line-height:1.9;
    }
    .wrap{max-width:1100px;margin:22px auto;padding:0 12px}
    .hero{
      background:linear-gradient(135deg,#0f172a,#134e4a); color:#fff; border-radius:22px;
      padding:24px 20px; box-shadow:var(--shadow); margin-bottom:16px;
    }
    .hero h1{margin:0 0 8px;font-size:clamp(1.5rem,4vw,2.5rem);font-weight:800}
    .hero p{margin:0;color:rgba(255,255,255,.92);font-size:1rem}
    .card{
      background:var(--card); border:1px solid var(--border); border-radius:20px;
      box-shadow:var(--shadow); padding:18px; margin-bottom:16px;
    }
    .grid{
      display:grid; grid-template-columns:1.6fr 220px 180px; gap:14px; align-items:end;
    }
    .field{display:flex; flex-direction:column; gap:8px}
    label{font-weight:800; font-size:1rem}
    input,select,button{font-family:inherit}
    input,select{
      width:100%; min-height:54px; border:1px solid #d1d5db; border-radius:14px; background:#fff;
      padding:0 16px; font-size:1rem; outline:none;
    }
    input:focus,select:focus{border-color:#14b8a6; box-shadow:0 0 0 4px rgba(20,184,166,.12)}
    button{
      min-height:54px; border:none; border-radius:14px; background:var(--primary); color:#fff;
      font-size:1rem; font-weight:800; padding:0 18px; cursor:pointer;
    }
    button:hover{background:var(--primary-dark)}
    button:disabled{opacity:.75; cursor:wait}
    .toolbar{display:flex; gap:10px; flex-wrap:wrap; margin-top:14px}
    .mini{min-height:44px; background:#0f172a; font-size:.95rem}
    .mini:hover{background:#1f2937}
    .status{
      margin-top:14px; padding:14px 16px; border-radius:14px; display:none; white-space:pre-wrap;
      font-weight:700;
    }
    .status.ok{display:block; background:#ecfeff; border:1px solid #99f6e4; color:var(--ok)}
    .status.err{display:block; background:#fef2f2; border:1px solid #fecaca; color:var(--danger)}
    .box{
      border:1px solid var(--border); background:#fcfcfd; border-radius:16px; padding:18px;
      min-height:220px; white-space:pre-wrap; word-break:break-word; font-size:1.06rem; line-height:2.1;
    }
    .box.big{min-height:340px}
    .head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
    .head h2{margin:0;font-size:1.18rem}
    .point{padding:10px 12px;border:1px solid #e2e8f0;background:#f8fafc;border-radius:12px;margin-bottom:10px}
    @media (max-width:900px){
      .grid{grid-template-columns:1fr}
      .wrap{padding:0 10px}
      .box{font-size:1rem}
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>تحويل فيديو يوتيوب إلى نص كامل + ملخص + أهم النقاط</h1>
      <p>نسخة بايثون مستقرة بواجهة عربية واضحة ومريحة للنظر.</p>
    </section>

    <section class="card">
      <div class="grid">
        <div class="field">
          <label for="youtubeUrl">رابط فيديو يوتيوب</label>
          <input id="youtubeUrl" type="text" placeholder="ضع رابط الفيديو هنا" />
        </div>
        <div class="field">
          <label for="language">لغة النص</label>
          <select id="language">
            <option value="ar">عربي</option>
            <option value="en">English</option>
          </select>
        </div>
        <div class="field">
          <label>&nbsp;</label>
          <button id="processBtn" type="button">استخراج النص</button>
        </div>
      </div>

      <div class="toolbar">
        <button class="mini" id="copyFullBtn" type="button">نسخ النص الكامل</button>
        <button class="mini" id="copySummaryBtn" type="button">نسخ الملخص</button>
        <button class="mini" id="copyPointsBtn" type="button">نسخ أهم النقاط</button>
        <button class="mini" id="clearBtn" type="button">مسح الكل</button>
      </div>

      <div id="statusBox" class="status"></div>
    </section>

    <section class="card">
      <div class="head"><h2>النص الكامل</h2></div>
      <div id="fullText" class="box big"></div>
    </section>

    <section class="card">
      <div class="head"><h2>الملخص</h2></div>
      <div id="summaryText" class="box"></div>
    </section>

    <section class="card">
      <div class="head"><h2>أهم النقاط</h2></div>
      <div id="keyPointsText" class="box"></div>
    </section>
  </div>

  <script>
    const youtubeUrl = document.getElementById("youtubeUrl");
    const language = document.getElementById("language");
    const processBtn = document.getElementById("processBtn");
    const statusBox = document.getElementById("statusBox");
    const fullText = document.getElementById("fullText");
    const summaryText = document.getElementById("summaryText");
    const keyPointsText = document.getElementById("keyPointsText");
    const copyFullBtn = document.getElementById("copyFullBtn");
    const copySummaryBtn = document.getElementById("copySummaryBtn");
    const copyPointsBtn = document.getElementById("copyPointsBtn");
    const clearBtn = document.getElementById("clearBtn");

    function setStatus(message, type) {
      statusBox.className = "status " + (type === "error" ? "err" : "ok");
      statusBox.textContent = message;
    }

    function clearStatus() {
      statusBox.className = "status";
      statusBox.textContent = "";
    }

    function clearOutputs() {
      fullText.textContent = "";
      summaryText.textContent = "";
      keyPointsText.innerHTML = "";
    }

    function setLoading(loading) {
      processBtn.disabled = loading;
      processBtn.textContent = loading ? "جارٍ المعالجة..." : "استخراج النص";
    }

    function renderPoints(points) {
      keyPointsText.innerHTML = "";
      if (!Array.isArray(points) || !points.length) {
        keyPointsText.textContent = "لا توجد نقاط متاحة.";
        return;
      }
      points.forEach((point, index) => {
        const div = document.createElement("div");
        div.className = "point";
        div.textContent = (index + 1) + ") " + point;
        keyPointsText.appendChild(div);
      });
    }

    async function copyText(text, okMessage) {
      if (!text || !text.trim()) {
        setStatus("لا يوجد محتوى لنسخه.", "error");
        return;
      }
      try {
        await navigator.clipboard.writeText(text);
        setStatus(okMessage, "ok");
      } catch (_) {
        setStatus("تعذر النسخ من هذا المتصفح.", "error");
      }
    }

    async function processVideo() {
      const url = youtubeUrl.value.trim();
      const lang = language.value;

      if (!url) {
        setStatus("الرجاء إدخال رابط يوتيوب أولًا.", "error");
        youtubeUrl.focus();
        return;
      }

      clearOutputs();
      setLoading(true);
      setStatus("جارٍ استخراج النص وتحليل المحتوى...", "ok");

      try {
        const response = await fetch("/api/process", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url, language: lang })
        });

        const result = await response.json();
        if (!response.ok || result.ok === false) {
          throw new Error(result.error || "فشل في المعالجة.");
        }

        fullText.textContent = result.full_text || "";
        summaryText.textContent = result.summary || "";
        renderPoints(result.key_points || []);
        setStatus(result.transcript_status || "تمت المعالجة بنجاح.", "ok");
      } catch (error) {
        setStatus(error.message || "حدث خطأ غير متوقع.", "error");
      } finally {
        setLoading(false);
      }
    }

    copyFullBtn.addEventListener("click", () => copyText(fullText.innerText, "تم نسخ النص الكامل."));
    copySummaryBtn.addEventListener("click", () => copyText(summaryText.innerText, "تم نسخ الملخص."));
    copyPointsBtn.addEventListener("click", () => copyText(keyPointsText.innerText, "تم نسخ أهم النقاط."));
    clearBtn.addEventListener("click", () => {
      youtubeUrl.value = "";
      clearOutputs();
      clearStatus();
      youtubeUrl.focus();
    });
    processBtn.addEventListener("click", processVideo);
    youtubeUrl.addEventListener("keydown", (e) => {
      if (e.key === "Enter") processVideo();
    });
  </script>
</body>
</html>
"""

ARABIC_STOPWORDS = {
    "في", "من", "على", "إلى", "الى", "عن", "هذا", "هذه", "ذلك", "تلك", "ثم", "لقد",
    "كما", "لكن", "لأن", "لان", "إن", "ان", "أن", "او", "أو", "ما", "كيف", "هل",
    "هنا", "هناك", "مع", "بعد", "قبل", "كل", "بعض", "قد", "تم", "بين", "حتى", "أي",
    "هو", "هي", "هم", "كان", "كانت", "يكون", "يمكن", "ولا", "لا", "لم", "لن", "به",
    "بها", "له", "لها", "عليه", "عليها", "الذي", "التي", "الذين", "حيث", "عند"
}
ENGLISH_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "for", "to", "of", "in",
    "on", "at", "by", "with", "from", "as", "is", "are", "was", "were", "be", "been",
    "it", "this", "that", "these", "those", "he", "she", "they", "we", "you", "i",
    "not", "do", "does", "did", "can", "could", "will", "would", "should", "may",
    "have", "has", "had", "about", "there", "here", "what", "when", "where", "why", "how"
}

def normalize_arabic(text: str) -> str:
    text = unescape(text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي").replace("ة", "ه")
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def normalize_english(text: str) -> str:
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_video_id(url: str) -> str:
    url = (url or "").strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url

    parsed = urlparse(url)
    if parsed.netloc in {"www.youtube.com", "youtube.com", "m.youtube.com"}:
        qs = parse_qs(parsed.query)
        if qs.get("v"):
            return qs["v"][0]
        for pattern in [r"/shorts/([A-Za-z0-9_-]{11})", r"/embed/([A-Za-z0-9_-]{11})"]:
            m = re.search(pattern, parsed.path)
            if m:
                return m.group(1)

    if parsed.netloc in {"youtu.be", "www.youtu.be"}:
        m = re.match(r"/([A-Za-z0-9_-]{11})", parsed.path)
        if m:
            return m.group(1)

    m = re.search(r"([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)

    raise ValueError("تعذر استخراج معرف الفيديو من الرابط.")

def split_sentences(text: str, lang: str) -> list[str]:
    text = (text or "").replace("\r", "\n").replace("\n", " ").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[\.\!\؟\?])\s+|[؛\n]+", text)
    out = []
    for p in parts:
        s = re.sub(r"\s+", " ", p).strip()
        if len(s) >= 20:
            out.append(s)
    if not out:
        rough = re.split(r"[\.!\?؟\n]+", text)
        out = [re.sub(r"\s+", " ", x).strip() for x in rough if len(re.sub(r'\s+', ' ', x).strip()) >= 20]
    return out

def tokenize(text: str, lang: str) -> list[str]:
    if lang == "ar":
        text = normalize_arabic(text)
        words = re.findall(r"[\u0600-\u06FF]+", text)
        return [w for w in words if len(w) > 1 and w not in ARABIC_STOPWORDS]
    text = normalize_english(text).lower()
    words = re.findall(r"[A-Za-z']+", text)
    return [w for w in words if len(w) > 1 and w not in ENGLISH_STOPWORDS]

def build_frequency(text: str, lang: str) -> dict[str, int]:
    freq = {}
    for w in tokenize(text, lang):
        freq[w] = freq.get(w, 0) + 1
    return freq

def sentence_score(sentence: str, freq: dict[str, int], lang: str) -> float:
    words = tokenize(sentence, lang)
    if not words:
        return 0.0
    score = sum(freq.get(w, 0) for w in words)
    return score / (1 + math.log(len(words) + 1, 2))

def summarize_text(text: str, lang: str) -> str:
    sentences = split_sentences(text, lang)
    if not sentences:
        return "تعذر إنشاء الملخص."
    freq = build_frequency(text, lang)
    ranked = [(i, s, sentence_score(s, freq, lang)) for i, s in enumerate(sentences)]
    ranked.sort(key=lambda x: x[2], reverse=True)
    take = max(4, min(8, int(len(sentences) * 0.22) or 4))
    selected = sorted(ranked[:take], key=lambda x: x[0])
    return " ".join(s for _, s, _ in selected).strip() or "تعذر إنشاء الملخص."

def extract_key_points(text: str, lang: str) -> list[str]:
    sentences = split_sentences(text, lang)
    if not sentences:
        return ["تعذر استخراج أهم النقاط."]
    freq = build_frequency(text, lang)
    ranked = [(i, s, sentence_score(s, freq, lang)) for i, s in enumerate(sentences)]
    ranked.sort(key=lambda x: x[2], reverse=True)
    points = []
    seen = set()
    for _, s, _ in ranked:
        key = s.strip().lower()
        if key and key not in seen and len(s.strip()) >= 25:
            points.append(s.strip())
            seen.add(key)
        if len(points) >= 7:
            break
    return points or ["تعذر استخراج أهم النقاط."]

def format_transcript_items(items, lang: str) -> str:
    parts = []
    for item in items:
        txt = (item.text if hasattr(item, "text") else item.get("text", "")).strip()
        if txt:
            parts.append(unescape(txt))
    text = "\n".join(parts).strip()
    if lang == "ar":
        return normalize_arabic(text)
    return normalize_english(text)

def fetch_transcript_text(video_id: str, target_lang: str) -> tuple[str, str]:
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)

    # exact manual / generated
    for finder, label in [
        (lambda: transcript_list.find_manually_created_transcript([target_lang]), "تم جلب النص اليدوي"),
        (lambda: transcript_list.find_generated_transcript([target_lang]), "تم جلب النص التلقائي"),
        (lambda: transcript_list.find_transcript([target_lang]), "تم جلب النص"),
    ]:
        try:
            tr = finder()
            return format_transcript_items(tr.fetch(), target_lang), f"{label} باللغة: {target_lang}"
        except Exception:
            pass

    # translate from any translatable transcript
    for tr in transcript_list:
        try:
            if getattr(tr, "is_translatable", False):
                translated = tr.translate(target_lang)
                return format_transcript_items(translated.fetch(), target_lang), f"تمت ترجمة النص إلى: {target_lang}"
        except Exception:
            continue

    # fallback to first available transcript
    for tr in transcript_list:
        try:
            base_lang = getattr(tr, "language_code", "") or target_lang
            text_lang = "ar" if base_lang.startswith("ar") else "en"
            return format_transcript_items(tr.fetch(), text_lang), f"تم جلب نص متاح بلغة الفيديو الأصلية: {base_lang}"
        except Exception:
            continue

    raise NoTranscriptFound(video_id, [], None)

@app.get("/")
def index():
    return render_template_string(HTML)

@app.post("/api/process")
def api_process():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    lang = "ar" if (data.get("language") or "ar") == "ar" else "en"

    if not url:
        return jsonify({"ok": False, "error": "الرجاء إدخال رابط يوتيوب صحيح."}), 400

    try:
        video_id = extract_video_id(url)
        full_text, status = fetch_transcript_text(video_id, lang)
        if not full_text or len(full_text.strip()) < 10:
            return jsonify({"ok": False, "error": "تم العثور على الفيديو لكن النص فارغ أو غير كافٍ."}), 400

        summary = summarize_text(full_text, lang)
        points = extract_key_points(full_text, lang)

        return jsonify({
            "ok": True,
            "video_id": video_id,
            "transcript_status": status,
            "full_text": full_text,
            "summary": summary,
            "key_points": points,
        })
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except TranscriptsDisabled:
        return jsonify({"ok": False, "error": "هذا الفيديو لا يوفّر نصًا أو ترجمات على يوتيوب."}), 400
    except VideoUnavailable:
        return jsonify({"ok": False, "error": "الفيديو غير متاح أو الرابط غير صحيح."}), 400
    except NoTranscriptFound:
        return jsonify({"ok": False, "error": "لم يتم العثور على نص مناسب لهذا الفيديو."}), 400
    except CouldNotRetrieveTranscript:
        return jsonify({"ok": False, "error": "تعذر جلب النص من يوتيوب حاليًا. جرّب لاحقًا أو جرّب فيديو آخر."}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": "حدث خطأ غير متوقع: " + str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
