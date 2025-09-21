import os
import io
import base64
import tempfile
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from Pdf_Utils import extract_text_from_pdf
from Github_Utils import summarize_text, ask_question_about_text

try:
    from flask_cors import CORS
    CORS_ENABLED = True
except ImportError:
    CORS_ENABLED = False

ALLOWED_EXTENSIONS = {"pdf"}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024 

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

if CORS_ENABLED:
    CORS(app)

def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# Extract raw text
@app.route("/extract", methods=["POST"])
def extract():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No filename provided."}), 400
    if not _allowed_file(file.filename):
        return jsonify({"error": "Only .pdf files are allowed."}), 400

    filename = secure_filename(file.filename)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        text = extract_text_from_pdf(tmp_path) or ""
    except Exception as e:
        os.remove(tmp_path)
        return jsonify({"error": f"PDF extraction failed: {e}"}), 500
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    if not text.strip():
        return jsonify({"error": "No text found in PDF."}), 422

    return jsonify({"filename": filename, "chars": len(text), "text": text}), 200

# Summarize directly from an uploaded file
@app.route("/summarize", methods=["POST"])
def summarize():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No filename provided."}), 400
    if not _allowed_file(file.filename):
        return jsonify({"error": "Only .pdf files are allowed."}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        text = extract_text_from_pdf(tmp_path) or ""
        if not text.strip():
            return jsonify({"error": "No text found in PDF."}), 422
        summary = summarize_text(text)
        return jsonify({"summary": summary}), 200
    except Exception as e:
        return jsonify({"error": f"Summarization failed: {e}"}), 500
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

# Ask: supports multipart OR JSON(base64), for qns being asked, answers accordingly
@app.route("/ask", methods=["POST"])
def ask():
    content_type = (request.content_type or "").lower()

    tmp_path = None
    try:
        if content_type.startswith("multipart/form-data"):
            if "file" not in request.files:
                return jsonify({"error": "No file uploaded."}), 400

            file = request.files["file"]
            question = (request.form.get("question") or "").strip()

            if not file or file.filename == "":
                return jsonify({"error": "No filename provided."}), 400
            if not _allowed_file(file.filename):
                return jsonify({"error": "Only .pdf files are allowed."}), 400
            if not question:
                return jsonify({"error": "Missing question."}), 400

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name

        elif content_type.startswith("application/json"):
            data = request.get_json(silent=True) or {}
            filename = (data.get("filename") or "").strip()
            file_b64 = data.get("file_base64")
            question = (data.get("question") or "").strip()

            if not filename or not file_b64 or not question:
                return jsonify({"error": "filename, file_base64, and question are required."}), 400
            if not _allowed_file(filename):
                return jsonify({"error": "Only .pdf files are allowed."}), 400

            try:
                pdf_bytes = base64.b64decode(file_b64, validate=True)
            except Exception:
                return jsonify({"error": "file_base64 is not valid base64."}), 400

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_bytes)
                tmp.flush()
                tmp_path = tmp.name

        else:
            return jsonify({"error": "Unsupported Content-Type. Use multipart/form-data or application/json."}), 415

        text = extract_text_from_pdf(tmp_path) or ""
        if not text.strip():
            return jsonify({"error": "No text found in PDF."}), 422

        answer = ask_question_about_text(text, question)
        return jsonify({"answer": answer}), 200

    except Exception as e:
        return jsonify({"error": f"Q&A failed: {e}"}), 500
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

# Entry Point
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5002")), debug=True)
