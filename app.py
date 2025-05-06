from flask import Flask, render_template, request, send_file, redirect, url_for
from pypdf import PdfWriter, PdfReader
from PIL import Image
from io import BytesIO
import os
import zipfile

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

@app.route("/split", methods=["GET", "POST"])
def split_pdf():
    if request.method == "POST":
        file = request.files.get("pdf")
        split_type = request.form.get("split_type", "all_pages")
        page_range = request.form.get("page_range", "")
        every_n = request.form.get("every_n", "")

        if not file or not file.filename.lower().endswith('.pdf'):
            return "Please upload a valid PDF file.", 400

        reader = PdfReader(file)
        output_files = []

        if split_type == "all_pages":
            # Split every page into a separate PDF
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                output_io = BytesIO()
                writer.write(output_io)
                output_io.seek(0)
                output_files.append((f'page_{i+1}.pdf', output_io.read()))
        elif split_type == "range":
            # Split by a page range, e.g., 3-7
            try:
                start, end = map(int, page_range.strip().split('-'))
                if start < 1 or end > len(reader.pages) or start > end:
                    raise ValueError
            except Exception:
                return "Invalid page range.", 400
            writer = PdfWriter()
            for i in range(start-1, end):
                writer.add_page(reader.pages[i])
            output_io = BytesIO()
            writer.write(output_io)
            output_io.seek(0)
            output_files.append((f'pages_{start}_to_{end}.pdf', output_io.read()))
        elif split_type == "every_n":
            # Split every N pages
            try:
                n = int(every_n)
                if n < 1:
                    raise ValueError
            except Exception:
                return "Invalid value for N.", 400
            total = len(reader.pages)
            for i in range(0, total, n):
                writer = PdfWriter()
                for j in range(i, min(i+n, total)):
                    writer.add_page(reader.pages[j])
                output_io = BytesIO()
                writer.write(output_io)
                output_io.seek(0)
                output_files.append((f'pages_{i+1}_to_{min(i+n, total)}.pdf', output_io.read()))
        else:
            return "Unknown split type.", 400

        # Package as ZIP for download
        zip_io = BytesIO()
        with zipfile.ZipFile(zip_io, 'w') as zf:
            for filename, data in output_files:
                zf.writestr(filename, data)
        zip_io.seek(0)
        return send_file(zip_io, mimetype='application/zip', as_attachment=True, download_name='split_pdfs.zip')

    return render_template("split.html")

if __name__ == "__main__":
    app.run(debug=True)