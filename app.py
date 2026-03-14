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

        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ar"])
        text = clean_text_from_transcript(transcript)

        if not text:
            return jsonify({"ok": False, "error": "تم العثور على النص لكن المحتوى فارغ"})

        pretty = format_text_readable(text, words_per_paragraph=45)
        return jsonify({"ok": True, "text": pretty})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})
