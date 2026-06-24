# al inicio de test_pipeline.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pdfplumber

from src.core.heuristicas import extraer_contexto_integral

PDF_PATH = os.path.join("tests", "rubrica ejemplo.pdf")


def extract_text_from_pdf(path: str) -> str:
    texto = ""

    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()

            if page_text:
                texto += page_text + "\n"

    return texto.strip()


def main():
    print("\n=== TEST PIPELINE PDF ===\n")

    # 1. Verificar archivo
    if not os.path.exists(PDF_PATH):
        print("PDF no encontrado:", PDF_PATH)
        return

    # 2. Extraer texto
    texto = extract_text_from_pdf(PDF_PATH)

    print("\n--- TEXTO EXTRAIDO (preview) ---\n")
    print(texto[:1000])
    print("\n[LONGITUD]:", len(texto))

    if not texto:
        print("No se extrajo texto del PDF")
        return
    
    print("\n=== TIPO DE CONTENIDO ===")

    if "peso" in texto.lower():
        print("Contiene criterios de evaluación")

    if "avance" in texto.lower():
        print("Contiene fases/entregas")

    if "palabras" in texto.lower():
        print("Contiene restricciones de redacción")

    # 3. Ejecutar pipeline completo
    resultado = extraer_contexto_integral(texto, requiere_fases=True)

    print("\n--- RESULTADO NORMALIZADO ---\n")
    for k, v in resultado.items():
        if k != "raw":
            print(f"{k}: {v}")

    # 4. Debug opcional (muy importante)
    if "raw" in resultado:
        print("\n--- RAW DEL MODELO ---\n")
        print(resultado["raw"])


if __name__ == "__main__":
    main()