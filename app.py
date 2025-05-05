from flask import Flask, render_template, request, send_file
from pypdf import PdfWriter
from PIL import Image
from io import BytesIO
import os

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("files")
        order = request.form.get("order", "")
        order_list = order.split(",") if order else []

        # Map filenames to file objects
        file_dict = {file.filename: file for file in files}
        # Reorder files as per user selection
        ordered_files = [file_dict[name] for name in order_list if name in file_dict]

        writer = PdfWriter()

        for file in ordered_files:
            ext = file.filename.rsplit('.', 1)[-1].lower()
            if ext == 'pdf':
                writer.append(file.stream)
            elif ext in {'jpg', 'jpeg', 'png'}:
                image = Image.open(file.stream).convert("RGB")
                img_pdf_io = BytesIO()
                image.save(img_pdf_io, format="PDF")
                img_pdf_io.seek(0)
                writer.append(img_pdf_io)

        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "merged.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)
        writer.close()
        return send_file(output_path, as_attachment=True, download_name="merged.pdf")
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

if __name__ == "__main__":
    app.run()