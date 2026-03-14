import os
import re
from urllib.parse import urlparse, parse_qs
from collections import Counter
from flask import Flask, request, jsonify, render_template_string
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)


HTML = """
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>استخراج النص العربي من يوتيوب</title>

<style>
*{box-sizing:border-box}

body{
  margin:0;
  padding:16px;
  background:#f3f4f6;
  font-family:Arial,sans-serif;
  color:#111827;
}

.container{
  max-width:1100px;
  margin:auto;
}

.box{
  background:#ffffff;
  border-radius:18px;
  padding:18px;
  margin-bottom:18px;
  box-shadow:0 2px 10px rgba(0,0,0,.08);
}

h1,h2,h3{
  margin-top:0;
}

h1{
  font-size:clamp(28px,5vw,44px);
  line-height:1.3;
  margin-bottom:10px;
}

.note{
  color:#6b7280;
  font-size:14px;
  margin-bottom:14px;
}

input[type=text]{
  width:100%;
  padding:14px;
  border:1px solid #d1d5db;
  border-radius:14px;
  font-size:17px;
  margin-bottom:12px;
  direction:ltr;
  text-align:left;
}

.row{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  margin-bottom:10px;
}

button{
  border:none;
  border-radius:14px;
  padding:12px 16px;
  font-size:17px;
  cursor:pointer;
  color:white;
}

.btn-blue{ background:#2563eb; }
.btn-green{ background:#047857; }
.btn-dark{ background:#111827; }
.btn-gray{ background:#374151; }
.btn-red{ background:#b91c1c; }

button:active{
  transform:scale(.98);
}

.status{
  background:#eef2ff;
  color:#312e81;
  border-radius:12px;
  padding:12px 14px;
  margin-top:10px;
  min-height:46px;
  line-height:1.7;
  font-size:16px;
  white-space:pre-wrap;
}

label{
  display:block;
  margin-bottom:8px;
  font-weight:bold;
  font-size:19px;
}

textarea{
  width:100%;
  min-height:260px;
  padding:16px;
  border:1px solid #d1d5db;
  border-radius:14px;
  font-size:18px;
  line-height:2;
  resize:vertical;
  background:#fafafa;
}

.small-actions{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-bottom:10px;
}

.copy-overlay{
  position:fixed;
  inset:0;
  background:rgba(0,0,0,.45);
  display:none;
  align-items:center;
  justify-content:center;
  z-index:9999;
  padding:14px;
}

.copy-panel{
  width:min(900px, 100%);
  background:#fff;
  border-radius:18px;
  padding:16px;
  box-shadow:0 8px 30px rgba(0,0,0,.2);
}

.copy-title{
  font-size:22px;
  font-weight:bold;
  margin-bottom:8px;
}

.copy-help{
  color:#4b5563;
  font-size:14px;
  line-height:1.8;
  margin-bottom:10px;
}

.copy-box{
  width:100%;
  min-height:300px;
  border:1px solid #d1d5db;
  border-radius:14px;
  padding:14px;
  font-size:18px;
  line-height:1.9;
  resize:vertical;
  background:#fafafa;
}

.copy-actions{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-top:12px;
}

@media (max-width:700px){
  body{
    padding:12px;
  }

  .box{
    padding:14px;
    border-radius:16px;
  }

  button{
    font-size:16px;
    padding:12px 14px;
  }

  textarea{
    font-size:17px;
    min-height:220px;
  }

  .copy-box{
    min-height:240px;
    font-size:17px;
  }
}
</style>
</head>
<body>

<div class="container">

  <div class="box">
    <h1>استخراج النص العربي من يوتيوب</h1>
    <div class="note">ضع رابط الفيديو، ثم استخرج النص. الملخص وأهم النقاط يظهران في مربعات مستقلة.</div>

    <input id="url" type="text" placeholder="ضع رابط يوتيوب هنا">

    <div class="row">
      <button class="btn-blue" onclick="extractText()">استخراج النص</button>
      <button class="btn-gray" onclick="formatMainText()">ترتيب النص</button>
      <button class="btn-green" onclick="makeSummary()">تلخيص</button>
      <button class="btn-dark" onclick="makePoints()">أهم النقاط</button>
      <button class="btn-red" onclick="clearAllData()">مسح</button>
    </div>

    <div id="status" class="status">جاهز</div>
  </div>

  <div class="box">
    <label for="mainText">النص الكامل</label>
    <div class="small-actions">
      <button class="btn-gray" onclick="openCopyPanel('النص الكامل','mainText')">نسخ النص</button>
      <button class="btn-gray" onclick="downloadBox('mainText','youtube_text.txt')">حفظ TXT</button>
    </div>
    <textarea id="mainText" placeholder="سيظهر النص الكامل هنا"></textarea>
  </div>

  <div class="box">
    <label for="summaryBox">الملخص</label>
    <div class="small-actions">
      <button class="btn-gray" onclick="openCopyPanel('الملخص','summaryBox')">نسخ الملخص</button>
      <button class="btn-gray" onclick="downloadBox('summaryBox','youtube_summary.txt')">حفظ الملخص</button>
    </div>
    <textarea id="summaryBox" placeholder="سيظهر الملخص هنا"></textarea>
  </div>

  <div class="box">
    <label for="pointsBox">أهم النقاط</label>
    <div class="small-actions">
      <button class="btn-gray" onclick="openCopyPanel('أهم النقاط','pointsBox')">نسخ النقاط</button>
      <button class="btn-gray" onclick="downloadBox('pointsBox','youtube_points.txt')">حفظ النقاط</button>
    </div>
    <textarea id="pointsBox" placeholder="ستظهر أهم النقاط هنا"></textarea>
  </div>

</div>

<div id="copyOverlay" class="copy-overlay">
  <div class="copy-panel">
    <div id="copyTitle" class="copy-title">نسخ النص</div>
    <div class="copy-help">
      على الآيفون قد لا يعمل النسخ التلقائي دائمًا. اضغط داخل المربع ضغطًا مطولًا ثم اختر تحديد الكل ثم نسخ.
    </div>
    <textarea id="copyBox" class="copy-box"></textarea>
    <div class="copy-actions">
      <button class="btn-blue" onclick="selectCopyText()">تحديد النص</button>
      <button class="btn-green" onclick="tryCopyPanelText()">محاولة النسخ</button>
      <button class="btn-red" onclick="closeCopyPanel()">إغلاق</button>
    </div>
  </div>
</div>

<script>
function setStatus(msg){
  document.getElementById("status").textContent = msg;
}

function selectTextareaText(el){
  el.focus();
  el.select();
  el.setSelectionRange(0, el.value.length);
}

function openCopyPanel(title, sourceId){
  const source = document.getElementById(sourceId);
  const text = source.value || "";

  if(!text.trim()){
    setStatus("لا يوجد نص للنسخ");
    return;
  }

  document.getElementById("copyTitle").textContent = title;
  const box = document.getElementById("copyBox");
  box.value = text;
  document.getElementById("copyOverlay").style.display = "flex";

  setTimeout(() => {
    selectTextareaText(box);
  }, 80);

  setStatus("تم فتح نافذة النسخ");
}

function closeCopyPanel(){
  document.getElementById("copyOverlay").style.display = "none";
}

function selectCopyText(){
  const box = document.getElementById("copyBox");
  selectTextareaText(box);
  setStatus("تم تحديد النص");
}

async function tryCopyPanelText(){
  const box = document.getElementById("copyBox");
  const text = box.value || "";

  if(!text.trim()){
    setStatus("لا يوجد نص للنسخ");
    return;
  }

  try{
    if(navigator.clipboard && window.isSecureContext){
      await navigator.clipboard.writeText(text);
      setStatus("تم النسخ بنجاح");
      return;
    }
  }catch(e){}

  try{
    selectTextareaText(box);
    const ok = document.execCommand("copy");
    if(ok){
      setStatus("تم النسخ بنجاح");
    }else{
      setStatus("اضغط مطولًا داخل المربع ثم اختر نسخ");
    }
  }catch(e){
    setStatus("اضغط مطولًا داخل المربع ثم اختر نسخ");
  }
}

function downloadBox(id, filename){
  const text = document.getElementById(id).value || "";
  if(!text.trim()){
    setStatus("لا يوجد نص للحفظ");
    return;
  }

  const blob = new Blob([text], {type: "text/plain;charset=utf-8"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
  setStatus("تم حفظ الملف");
}

async function extractText(){
  const url = document.getElementById("url").value.trim();

  if(!url){
    setStatus("ضع رابط يوتيوب أولًا");
    return;
  }

  setStatus("جاري استخراج النص...");

  try{
    const res = await fetch("/extract", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({url})
    });

    const data = await res.json();

    if(!data.ok){
      setStatus(data.error || "حدث خطأ");
      return;
    }

    document.getElementById("mainText").value = data.text || "";
    document.getElementById("summaryBox").value = "";
    document.getElementById("pointsBox").value = "";
    setStatus("تم استخراج النص بنجاح");
  }catch(e){
    setStatus("تعذر الاتصال بالخادم");
  }
}

async function formatMainText(){
  const text = document.getElementById("mainText").value.trim();

  if(!text){
    setStatus("لا يوجد نص لترتيبه");
    return;
  }

  setStatus("جاري ترتيب النص...");

  try{
    const res = await fetch("/format", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({text})
    });

    const data = await res.json();

    if(!data.ok){
      setStatus(data.error || "حدث خطأ");
      return;
    }

    document.getElementById("mainText").value = data.text || "";
    setStatus("تم ترتيب النص");
  }catch(e){
    setStatus("تعذر تنفيذ العملية");
  }
}

async function makeSummary(){
  const text = document.getElementById("mainText").value.trim();

  if(!text){
    setStatus("لا يوجد نص لتلخيصه");
    return;
  }

  setStatus("جاري إنشاء الملخص...");

  try{
    const res = await fetch("/summarize", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({text})
    });

    const data = await res.json();

    if(!data.ok){
      setStatus(data.error || "حدث خطأ");
      return;
    }

    document.getElementById("summaryBox").value = data.summary || "";
    setStatus("تم إنشاء الملخص");
  }catch(e){
    setStatus("تعذر تنفيذ العملية");
  }
}

async function makePoints(){
  const text = document.getElementById("mainText").value.trim();

  if(!text){
    setStatus("لا يوجد نص لاستخراج النقاط");
    return;
  }

  setStatus("جاري استخراج أهم النقاط...");

  try{
    const res = await fetch("/points", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({text})
    });

    const data = await res.json();

    if(!data.ok){
      setStatus(data.error || "حدث خطأ");
      return;
    }

    document.getElementById("pointsBox").value = data.points || "";
    setStatus("تم استخراج أهم النقاط");
  }catch(e){
    setStatus("تعذر تنفيذ العملية");
  }
}

function clearAllData(){
  document.getElementById("url").value = "";
  document.getElementById("mainText").value = "";
  document.getElementById("summaryBox").value = "";
  document.getElementById("pointsBox").value = "";
  closeCopyPanel();
  setStatus("تم المسح");
}
</script>

</body>
</html>
"""

def extract_video_id(url: str):
    url = url.strip()

    try:
        parsed = urlparse(url)

        if "youtu.be" in parsed.netloc:
            video_id = parsed.path.strip("/").split("/")[0]
            if len(video_id) == 11:
                return video_id

        if "youtube.com" in parsed.netloc or "www.youtube.com" in parsed.netloc or "m.youtube.com" in parsed.netloc:
            qs = parse_qs(parsed.query)

            if "v" in qs:
                video_id = qs["v"][0]
                if len(video_id) == 11:
                    return video_id

            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) >= 2 and parts[0] in ("shorts", "live", "embed"):
                video_id = parts[1]
                if len(video_id) == 11:
                    return video_id

    except Exception:
        pass

    patterns = [
        r"(?:v=)([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"youtube\.com/shorts/([A-Za-z0-9_-]{11})",
        r"youtube\.com/live/([A-Za-z0-9_-]{11})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{11})",
    ]

    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)

    return None

def normalize_spaces(text: str) -> str:
    text = text.replace("\\u200f", " ").replace("\\u200e", " ")
    text = re.sub(r"\\s+", " ", text)
    return text.strip()

def split_into_word_chunks(text: str, words_per_chunk: int = 45):
    words = text.split()
    chunks = []

    for i in range(0, len(words), words_per_chunk):
        chunk = " ".join(words[i:i + words_per_chunk]).strip()
        if chunk:
            chunks.append(chunk)

    return chunks

def format_text_readable(text: str, words_per_paragraph: int = 45) -> str:
    text = normalize_spaces(text)
    chunks = split_into_word_chunks(text, words_per_paragraph)
    return "\\n\\n".join(chunks)

def get_word_frequencies(text: str):
    stop_words = {
        "في", "من", "على", "الى", "إلى", "عن", "أن", "إن", "او", "أو", "ثم", "قد",
        "هذا", "هذه", "ذلك", "تلك", "هناك", "هنا", "كان", "كانت", "يكون", "تكون",
        "هو", "هي", "هم", "هن", "كما", "لكن", "لأن", "ما", "لا", "لم", "لن", "مع",
        "كل", "بعد", "قبل", "بين", "حتى", "اذا", "إذا", "اي", "أي", "تم", "أكثر",
        "اقل", "أقل", "جدا", "جداً", "التي", "الذي", "الذين", "يعني", "ايضا", "أيضا",
        "مثل", "فقط", "عند", "بأن", "بها", "فيه", "فيها", "عليه", "عليها", "لها",
        "له", "منه", "منها", "انه", "إنه", "أنها", "انها"
    }

    words = re.findall(r"[\\u0600-\\u06FFA-Za-z0-9_]+", text)
    cleaned = []

    for w in words:
        if len(w) < 3:
            continue
        if w in stop_words:
            continue
        cleaned.append(w)

    return Counter(cleaned)

def summarize_by_chunks(text: str, max_chunks: int = 8, chunk_size: int = 55) -> str:
    text = normalize_spaces(text)
    chunks = split_into_word_chunks(text, chunk_size)

    if not chunks:
        return ""

    if len(chunks) <= max_chunks:
        return "\\n\\n".join(chunks)

    freqs = get_word_frequencies(text)

    if not freqs:
        return "\\n\\n".join(chunks[:max_chunks])

    scored = []

    for idx, chunk in enumerate(chunks):
        score = 0
        words = re.findall(r"[\\u0600-\\u06FFA-Za-z0-9_]+", chunk)
        for w in words:
            score += freqs.get(w, 0)

        bonus = 0
        if idx < 2:
            bonus += 20
        if abs(idx - len(chunks) // 2) <= 1:
            bonus += 10
        if idx >= len(chunks) - 2:
            bonus += 15

        scored.append((score + bonus, idx, chunk))

    scored.sort(reverse=True)
    selected = scored[:max_chunks]
    selected.sort(key=lambda x: x[1])

    return "\\n\\n".join(item[2] for item in selected)

def extract_key_points(text: str, points_count: int = 8, chunk_size: int = 28) -> str:
    text = normalize_spaces(text)
    chunks = split_into_word_chunks(text, chunk_size)

    if not chunks:
        return ""

    freqs = get_word_frequencies(text)
    scored = []

    for idx, chunk in enumerate(chunks):
        score = 0
        words = re.findall(r"[\\u0600-\\u06FFA-Za-z0-9_]+", chunk)
        for w in words:
            score += freqs.get(w, 0)
        scored.append((score, idx, chunk))

    scored.sort(reverse=True)
    selected = scored[:points_count]
    selected.sort(key=lambda x: x[1])

    lines = []
    for i, item in enumerate(selected, 1):
        lines.append(f"{i}- {item[2]}")

    return "\\n\\n".join(lines)

def clean_text_from_transcript(transcript_items) -> str:
    parts = []

    for item in transcript_items:
        if isinstance(item, dict):
            t = str(item.get("text", "")).strip()
        else:
            try:
                t = item.text.strip()
            except Exception:
                t = str(item).strip()

        if not t:
            continue
        if t in ("[Music]", "[موسيقى]"):
            continue

        parts.append(t)

    text = " ".join(parts)
    return normalize_spaces(text)

def get_transcript_compat(video_id: str):
    # يدعم الإصدارات القديمة والجديدة من المكتبة
    if hasattr(YouTubeTranscriptApi, "get_transcript"):
        return YouTubeTranscriptApi.get_transcript(video_id, languages=["ar"])

    api = YouTubeTranscriptApi()
    if hasattr(api, "fetch"):
        return api.fetch(video_id, languages=["ar"])

    raise Exception("إصدار مكتبة youtube-transcript-api غير مدعوم في هذه البيئة")

@app.get("/")
def index():
    return render_template_string(HTML)

@app.post("/extract")
def extract():
    try:
        data = request.get_json(force=True)
        url = (data.get("url") or "").strip()

        if not url:
            return jsonify({"ok": False, "error": "ضع رابط يوتيوب أولًا"})

        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({"ok": False, "error": "الرابط غير صحيح أو غير مدعوم"})

        transcript = get_transcript_compat(video_id)
        text = clean_text_from_transcript(transcript)

        if not text:
            return jsonify({"ok": False, "error": "تم العثور على النص لكن المحتوى فارغ"})

        pretty = format_text_readable(text, words_per_paragraph=45)
        return jsonify({"ok": True, "text": pretty})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.post("/format")
def format_route():
    try:
        data = request.get_json(force=True)
        text = (data.get("text") or "").strip()

        if not text:
            return jsonify({"ok": False, "error": "لا يوجد نص لترتيبه"})

        result = format_text_readable(text, words_per_paragraph=45)
        return jsonify({"ok": True, "text": result})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.post("/summarize")
def summarize_route():
    try:
        data = request.get_json(force=True)
        text = (data.get("text") or "").strip()

        if not text:
            return jsonify({"ok": False, "error": "لا يوجد نص لتلخيصه"})

        summary = summarize_by_chunks(text, max_chunks=8, chunk_size=55)
        summary = "ملخص النص:\\n\\n" + format_text_readable(summary, words_per_paragraph=35)

        return jsonify({"ok": True, "summary": summary})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.post("/points")
def points_route():
    try:
        data = request.get_json(force=True)
        text = (data.get("text") or "").strip()

        if not text:
            return jsonify({"ok": False, "error": "لا يوجد نص لاستخراج النقاط"})

        points = extract_key_points(text, points_count=8, chunk_size=28)
        points = "أهم النقاط:\\n\\n" + points

        return jsonify({"ok": True, "points": points})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.get("/health")
def health():
    return {"ok": True, "status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
