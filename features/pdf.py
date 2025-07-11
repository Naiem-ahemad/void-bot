# Re-run the final code after state reset
import os
import subprocess
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

def encrypt_pdf(file_path: str, password: str, output_path: str):
    reader = PdfReader(file_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.encrypt(password)

    with open(output_path, "wb") as f:
        writer.write(f)


def decrypt_pdf(file_path: str, password: str, output_path: str):
    reader = PdfReader(file_path)

    if reader.is_encrypted:
        result = reader.decrypt(password)
        if result == 0:
            return False

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return True



def pdf_to_images(file_path: str) -> list:
    images = convert_from_path(file_path)
    image_paths = []

    for i, img in enumerate(images):
        img_filename = f"page_{i + 1}.png"
        img.save(img_filename, "PNG")
        image_paths.append(img_filename)

    return image_paths

def ocr_pdf(file_path: str) -> str:
    images = convert_from_path(file_path)
    full_text = ""

    for img in images:
        text = pytesseract.image_to_string(img)
        full_text += text + "\n"

    return full_text.strip()


def merge_pdfs(file_paths: list, output_name: str = "merged_output") -> str:
    writer = PdfWriter()
    for path in file_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)
    output = f"{output_name}.pdf"
    with open(output, "wb") as f:
        writer.write(f)
    return output


def split_pdf(file_path: str, ranges: list) -> list:
    reader = PdfReader(file_path)
    split_files = []
    for i, (start, end) in enumerate(ranges):
        writer = PdfWriter()
        for page_num in range(start - 1, end):
            writer.add_page(reader.pages[page_num])
        output = f"split_part_{i+1}.pdf"
        with open(output, "wb") as f:
            writer.write(f)
        split_files.append(output)
    return split_files


def extract_pages(file_path: str, pages: list) -> str:
    reader = PdfReader(file_path)
    writer = PdfWriter()
    for num in pages:
        writer.add_page(reader.pages[num - 1])
    output = "extracted_pages.pdf"
    with open(output, "wb") as f:
        writer.write(f)
    return output


def compress_pdf(input_path, user_id):
    output_folder = f"downloads/{user_id}"
    os.makedirs(output_folder, exist_ok=True)  # ✅ Ensure folder exists

    output_path = f"{output_folder}/compressed.pdf"

    command = [
        "gswin32c",  # or 'gswin64c' depending on your installation
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/screen",
        "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path
    ]

    subprocess.run(command, check=True)
    return output_path

def images_to_pdf(image_paths: list, output_name: str = "images_output") -> str:
    images = [Image.open(p).convert("RGB") for p in image_paths]
    output = f"{output_name}.pdf"
    images[0].save(output, save_all=True, append_images=images[1:])
    return output