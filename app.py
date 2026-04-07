from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)

def extract_video_id(url):
    import re
    match = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

def fetch_text(video_id, lang):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang, "en", "ar"])
        return "\n".join([i["text"] for i in transcript])
    except:
        return None

def summarize(text):
    parts = text.split("\n")
    return " ".join(parts[:5])

def key_points(text):
    parts = text.split("\n")
    return parts[:7]

@app.route("/api/process", methods=["POST"])
def process():
    data = request.json
    url = data.get("url")
    lang = data.get("language", "ar")

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"ok": False, "error": "رابط غير صحيح"}), 400

    text = fetch_text(video_id, lang)
    if not text:
        return jsonify({"ok": False, "error": "لا يمكن استخراج النص"}), 400

    return jsonify({
        "ok": True,
        "full_text": text,
        "summary": summarize(text),
        "key_points": key_points(text),
        "transcript_status": "تم بنجاح"
    })

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
