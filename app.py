import os
import re
import json
import math
import time
import sqlite3
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs, quote
from urllib.request import urlopen, Request
from collections import Counter
from flask import Flask, request, jsonify, render_template_string
from youtube_transcript_api import YouTubeTranscriptApi

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)
CORS(app)

# ===== أضف الكود بعد هذا السطر مباشرة =====

def extract_video_id(url):
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]

    if "youtube.com" in url:
        parsed = urlparse(url)
        return parse_qs(parsed.query).get("v", [""])[0]

    return url


def build_points_and_summary(text):
    sentences = [s.strip() for s in text.split(".") if s.strip()]

    summary = ". ".join(sentences[:3])
    if summary:
        summary += "."

    points = sentences[:5]

    return points, summary


@app.route("/youtube")
def youtube():

    url = request.args.get("url")

    if not url:
        return jsonify({"error": "missing url"}), 400

    video_id = extract_video_id(url)

    try:
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=["ar","en"]
        )

        text = " ".join([x["text"] for x in transcript])

        points, summary = build_points_and_summary(text)

        return jsonify({
            "text": text,
            "summary": summary,
            "points": points
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

DB_PATH = "site_analytics.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        visitor_key TEXT,
        ip TEXT,
        country TEXT,
        city TEXT,
        path TEXT,
        user_agent TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ip_cache (
        ip TEXT PRIMARY KEY,
        country TEXT,
        city TEXT,
        updated_at INTEGER
    )
    """)

    conn.commit()
    conn.close()


init_db()


HTML = """
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ali M Tools - YouTube Arabic Extractor</title>

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

.top-brand{
  text-align:center;
  margin-bottom:25px;
}

.top-brand h2{
  margin:0;
  font-size:32px;
  color:#111827;
  font-weight:bold;
}

.top-brand .sub{
  font-size:16px;
  color:#6b7280;
  margin-top:6px;
}

.top-brand .copy{
  font-size:14px;
  color:#6b7280;
  margin-top:10px;
  line-height:1.8;
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
  white-space:pre-wrap;
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
  white-space:pre-wrap;
}

.copy-actions{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-top:12px;
}

.meta-grid{
  display:grid;
  grid-template-columns: 280px 1fr;
  gap:16px;
  align-items:start;
}

.thumb-box{
  background:#fafafa;
  border:1px solid #d1d5db;
  border-radius:14px;
  padding:10px;
}

.thumb-box img{
  width:100%;
  height:auto;
  border-radius:10px;
  display:block;
}

.meta-title{
  font-size:22px;
  font-weight:bold;
  margin-bottom:10px;
  line-height:1.6;
}

.meta-sub{
  color:#6b7280;
  font-size:14px;
  margin-bottom:10px;
}

.stats-grid{
  display:grid;
  grid-template-columns: repeat(2, minmax(140px, 1fr));
  gap:10px;
}

.stat-card{
  background:#fafafa;
  border:1px solid #d1d5db;
  border-radius:12px;
  padding:12px;
}

.stat-label{
  color:#6b7280;
  font-size:13px;
  margin-bottom:6px;
}

.stat-value{
  color:#111827;
  font-size:18px;
  font-weight:bold;
  word-break:break-word;
}

.site-stats-grid{
  display:grid;
  grid-template-columns: repeat(3, minmax(140px, 1fr));
  gap:10px;
  margin-bottom:14px;
}

.country-list{
  background:#fafafa;
  border:1px solid #d1d5db;
  border-radius:12px;
  padding:12px;
}

.country-item{
  display:flex;
  justify-content:space-between;
  gap:10px;
  padding:8px 0;
  border-bottom:1px solid #ececec;
}

.country-item:last-child{
  border-bottom:none;
}

.footer-copy{
  text-align:center;
  margin-top:40px;
  padding:20px;
  color:#6b7280;
  font-size:14px;
  border-top:1px solid #e5e7eb;
  line-height:1.8;
}

@media (max-width:850px){
  .meta-grid{
    grid-template-columns:1fr;
  }
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

  .stats-grid{
    grid-template-columns:1fr 1fr;
  }

  .site-stats-grid{
    grid-template-columns:1fr;
  }
}
</style>
</head>
<body>

<div class="container">

  <div class="top-brand">
    <h2>Ali M Tools</h2>
    <div class="sub">YouTube Arabic Extractor</div>
    <div class="copy">
      © Ali M 2026
      <br>
      alix24028@gmail.com
    </div>
  </div>

  <div class="box">
    <h3>إحصائيات استخدام الرابط</h3>
    <div class="site-stats-grid">
      <div class="stat-card">
        <div class="stat-label">إجمالي الزيارات</div>
        <div id="siteTotalVisits" class="stat-value">0</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">الزوار الفريدون</div>
        <div id="siteUniqueVisitors" class="stat-value">0</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">زيارات اليوم</div>
        <div id="siteTodayVisits" class="stat-value">0</div>
      </div>
    </div>

    <div class="country-list">
      <div style="font-weight:bold; margin-bottom:8px;">أكثر الدول زيارة</div>
      <div id="topCountriesBox">لا توجد بيانات بعد</div>
    </div>
  </div>

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
    <h3>بيانات الفيديو وإحصائيات النص</h3>
    <div class="meta-grid">
      <div class="thumb-box">
        <img id="videoThumb" src="" alt="صورة الفيديو" style="display:none;">
      </div>

      <div>
        <div id="videoTitle" class="meta-title">لم يتم استخراج بيانات الفيديو بعد</div>
        <div id="videoSub" class="meta-sub"></div>

        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">معرف الفيديو</div>
            <div id="statVideoId" class="stat-value">—</div>
          </div>

          <div class="stat-card">
            <div class="stat-label">عدد الكلمات</div>
            <div id="statWords" class="stat-value">0</div>
          </div>

          <div class="stat-card">
            <div class="stat-label">عدد الأحرف</div>
            <div id="statChars" class="stat-value">0</div>
          </div>

          <div class="stat-card">
            <div class="stat-label">عدد الفقرات</div>
            <div id="statParagraphs" class="stat-value">0</div>
          </div>

          <div class="stat-card">
            <div class="stat-label">وقت قراءة تقريبي</div>
            <div id="statReadTime" class="stat-value">0 دقيقة</div>
          </div>

          <div class="stat-card">
            <div class="stat-label">لغة النص</div>
            <div id="statLang" class="stat-value">العربية</div>
          </div>
        </div>
      </div>
    </div>
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

  <div class="footer-copy">
    © Ali M 2026
    <br>
    alix24028@gmail.com
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

function updateVideoMeta(meta){
  document.getElementById("videoTitle").textContent = meta.title || "عنوان غير متوفر";
  document.getElementById("videoSub").textContent = meta.author ? ("القناة: " + meta.author) : "";

  document.getElementById("statVideoId").textContent = meta.video_id || "—";
  document.getElementById("statWords").textContent = meta.word_count || 0;
  document.getElementById("statChars").textContent = meta.char_count || 0;
  document.getElementById("statParagraphs").textContent = meta.paragraph_count || 0;
  document.getElementById("statReadTime").textContent = (meta.read_time_minutes || 0) + " دقيقة";
  document.getElementById("statLang").textContent = meta.language || "العربية";

  const img = document.getElementById("videoThumb");
  if(meta.thumbnail_url){
    img.src = meta.thumbnail_url;
    img.style.display = "block";
  }else{
    img.style.display = "none";
  }
}

function updateSiteStats(stats){
  document.getElementById("siteTotalVisits").textContent = stats.total_visits || 0;
  document.getElementById("siteUniqueVisitors").textContent = stats.unique_visitors || 0;
  document.getElementById("siteTodayVisits").textContent = stats.today_visits || 0;

  const box = document.getElementById("topCountriesBox");
  const countries = stats.top_countries || [];

  if(!countries.length){
    box.innerHTML = "لا توجد بيانات بعد";
    return;
  }

  box.innerHTML = countries.map(item => `
    <div class="country-item">
      <div>${item.country}</div>
      <div>${item.count}</div>
    </div>
  `).join("");
}

async function loadSiteStats(){
  try{
    const res = await fetch("/stats");
    const data = await res.json();
    if(data.ok){
      updateSiteStats(data);
    }
  }catch(e){}
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
    updateVideoMeta(data.meta || {});
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
  document.getElementById("videoTitle").textContent = "لم يتم استخراج بيانات الفيديو بعد";
  document.getElementById("videoSub").textContent = "";
  document.getElementById("statVideoId").textContent = "—";
  document.getElementById("statWords").textContent = "0";
  document.getElementById("statChars").textContent = "0";
  document.getElementById("statParagraphs").textContent = "0";
  document.getElementById("statReadTime").textContent = "0 دقيقة";
  document.getElementById("statLang").textContent = "العربية";
  document.getElementById("videoThumb").style.display = "none";
  closeCopyPanel();
  setStatus("تم المسح");
}

window.addEventListener("load", loadSiteStats);
</script>

</body>
</html>
"""


def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return request.remote_addr or "0.0.0.0"


def get_visitor_key(ip: str, user_agent: str) -> str:
    raw = f"{ip}|{user_agent}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_country_from_ip(ip: str):
    if not ip or ip.startswith("127.") or ip == "0.0.0.0":
        return ("محلي", "محلي")

    now_ts = int(time.time())
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT country, city, updated_at FROM ip_cache WHERE ip = ?", (ip,))
    row = cur.fetchone()

    if row:
        country, city, updated_at = row
        if now_ts - int(updated_at or 0) < 60 * 60 * 24 * 7:
            conn.close()
            return (country or "غير معروف", city or "")

    conn.close()

    try:
        req = Request(
            f"https://ipwho.is/{ip}",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
            country = data.get("country") or "غير معروف"
            city = data.get("city") or ""
    except Exception:
        country = "غير معروف"
        city = ""

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ip_cache (ip, country, city, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(ip) DO UPDATE SET
          country=excluded.country,
          city=excluded.city,
          updated_at=excluded.updated_at
    """, (ip, country, city, now_ts))
    conn.commit()
    conn.close()

    return (country, city)


def record_visit(path="/"):
    ip = get_client_ip()
    user_agent = request.headers.get("User-Agent", "")
    visitor_key = get_visitor_key(ip, user_agent)
    country, city = get_country_from_ip(ip)
    now_iso = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO visits (visitor_key, ip, country, city, path, user_agent, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (visitor_key, ip, country, city, path, user_agent, now_iso))
    conn.commit()
    conn.close()


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
    text = text.replace("\u200f", " ").replace("\u200e", " ")
    text = re.sub(r"\s+", " ", text)
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
    return "\n\n".join(chunks)


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

    words = re.findall(r"[\u0600-\u06FFA-Za-z0-9_]+", text)
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
        return "\n\n".join(chunks)

    freqs = get_word_frequencies(text)

    if not freqs:
        return "\n\n".join(chunks[:max_chunks])

    scored = []

    for idx, chunk in enumerate(chunks):
        score = 0
        words = re.findall(r"[\u0600-\u06FFA-Za-z0-9_]+", chunk)
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

    return "\n\n".join(item[2] for item in selected)


def extract_key_points(text: str, points_count: int = 8, chunk_size: int = 28) -> str:
    text = normalize_spaces(text)
    chunks = split_into_word_chunks(text, chunk_size)

    if not chunks:
        return ""

    freqs = get_word_frequencies(text)
    scored = []

    for idx, chunk in enumerate(chunks):
        score = 0
        words = re.findall(r"[\u0600-\u06FFA-Za-z0-9_]+", chunk)
        for w in words:
            score += freqs.get(w, 0)
        scored.append((score, idx, chunk))

    scored.sort(reverse=True)
    selected = scored[:points_count]
    selected.sort(key=lambda x: x[1])

    lines = []
    for i, item in enumerate(selected, 1):
        lines.append(f"{i}- {item[2]}")

    return "\n\n".join(lines)


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
    if hasattr(YouTubeTranscriptApi, "get_transcript"):
        return YouTubeTranscriptApi.get_transcript(video_id, languages=["ar"])

    api = YouTubeTranscriptApi()
    if hasattr(api, "fetch"):
        return api.fetch(video_id, languages=["ar"])

    raise Exception("إصدار مكتبة youtube-transcript-api غير مدعوم في هذه البيئة")


def get_video_metadata(url: str, video_id: str):
    title = "عنوان غير متوفر"
    author = ""

    try:
        oembed_url = "https://www.youtube.com/oembed?url=" + quote(url, safe="") + "&format=json"
        req = Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            title = data.get("title") or title
            author = data.get("author_name") or ""
    except Exception:
        pass

    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

    return {
        "title": title,
        "author": author,
        "thumbnail_url": thumbnail_url,
        "video_id": video_id
    }


def build_stats(text: str, meta: dict):
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    paragraph_count = len(paragraphs)
    read_time_minutes = max(1, math.ceil(word_count / 200)) if word_count else 0

    meta.update({
        "word_count": word_count,
        "char_count": char_count,
        "paragraph_count": paragraph_count,
        "read_time_minutes": read_time_minutes,
        "language": "العربية"
    })
    return meta


def get_site_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM visits")
    total_visits = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT visitor_key) FROM visits")
    unique_visitors = cur.fetchone()[0]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cur.execute("SELECT COUNT(*) FROM visits WHERE substr(created_at, 1, 10) = ?", (today,))
    today_visits = cur.fetchone()[0]

    cur.execute("""
        SELECT country, COUNT(*) as c
        FROM visits
        GROUP BY country
        ORDER BY c DESC
        LIMIT 10
    """)
    top_countries = [{"country": row[0] or "غير معروف", "count": row[1]} for row in cur.fetchall()]

    conn.close()

    return {
        "ok": True,
        "total_visits": total_visits,
        "unique_visitors": unique_visitors,
        "today_visits": today_visits,
        "top_countries": top_countries
    }


@app.get("/")
def index():
    record_visit("/")
    return render_template_string(HTML)


@app.get("/stats")
def stats_route():
    return jsonify(get_site_stats())


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
        meta = get_video_metadata(url, video_id)
        meta = build_stats(pretty, meta)

        return jsonify({"ok": True, "text": pretty, "meta": meta})

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
        summary = "ملخص النص:\n\n" + format_text_readable(summary, words_per_paragraph=35)

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
        points = "أهم النقاط:\n\n" + points

        return jsonify({"ok": True, "points": points})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.get("/health")
def health():
    return {"ok": True, "status": "healthy"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
