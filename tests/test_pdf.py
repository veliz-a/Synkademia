import pdfplumber

from pathlib import Path

# Get the directory of the current script
script_dir = Path(__file__).parent

# Reference the target file
PDF_PATH = script_dir / "rubrica ejemplo.pdf"

texto = ""


with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        page_text = page.extract_text()
        print("---- PAGE ----")
        print(page_text[:500])  # ver primeras líneas
        print("--------------")

        if page_text:
            texto += page_text + "\n"

print("\n===== RESULTADO FINAL =====")
print(texto[:2000])
print("LONGITUD:", len(texto))