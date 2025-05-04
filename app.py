from flask import Flask, render_template, request, send_file
from pypdf import PdfWriter
from io import BytesIO
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("pdfs")
        if not files or any(f.filename == "" for f in files):
            return "No files selected", 400

        writer = PdfWriter()
        for file in files:
            writer.append(file.stream)

        # Ensure output directory exists
        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "merged.pdf")

        # Write merged PDF to disk
        with open(output_path, "wb") as f:
            writer.write(f)
        writer.close()

        # Also serve file for download
        return send_file(output_path, as_attachment=True, download_name="merged.pdf")

    return render_template("index.html")

if __name__ == "__main__":
    app.run()