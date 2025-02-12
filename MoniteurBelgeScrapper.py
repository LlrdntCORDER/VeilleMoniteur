from datetime import datetime
from PyPDF2 import PdfReader
import os, requests, csv, re

def generate_date_path():
    return datetime.now().strftime("/%Y/%m/%d")

def download_pdf(url, save_dir="downloads"):
    # Créer le répertoire s'il n'existe pas
    os.makedirs(save_dir, exist_ok=True)
    
    # Générer le chemin de sauvegarde avec la structure /YEAR/MONTH/DAY
    date_path = datetime.now().strftime("%Y/%m/")
    full_path = os.path.join(save_dir, date_path)
    os.makedirs(full_path, exist_ok=True)
    
    # Nom du fichier
    filename = os.path.join(full_path, url.split("/")[-1])
    
    # Télécharger le fichier
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"PDF téléchargé avec succès : {filename}")
        return full_path
    else:
        print(f"Échec du téléchargement : {response.status_code}")


def extract_terms_from_pdf(pdf_path, terms, output_csv):
    """
    Recherche des termes dans un PDF et enregistre les occurrences dans un fichier CSV.
    
    Args:
        pdf_path (str): Chemin du fichier PDF.
        terms (list): Liste des chaînes de caractères à rechercher.
        output_csv (str): Chemin du fichier CSV de sortie.
    """
    reader = PdfReader(pdf_path)
    results = []

    # Expression régulière pour extraire des phrases
    sentence_regex = re.compile(r"[^.]*\b({})\b[^.]*\.".format("|".join(map(re.escape, terms))), re.IGNORECASE)

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text:
            continue

        # Trouver les phrases contenant un des termes
        for match in sentence_regex.finditer(text):
            matched_sentence = match.group(0).strip()
            matched_sentence = matched_sentence.replace("\n","")
            found_term = match.group(1)  # Terme exact trouvé
            results.append([found_term, page_num, matched_sentence])

    # Écriture dans le fichier CSV
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Terme", "Numéro de page", "Phrase"])
        writer.writerows(results)

    print(f"Extraction terminée. Résultats enregistrés dans {output_csv}")



dailyID = generate_date_path()
url = f"https://www.ejustice.just.fgov.be/mopdf{dailyID}_1.pdf"
# Exemple d'utilisation
PDFPath = download_pdf(url).replace("/","\\")+datetime.now().strftime("%d")+"_1.pdf"
print (PDFPath)
SearchTermList = ["pesticide","autorisation", "produit phytosanitaire","zone tampon", "produits phytopharmaceutiques", "herbicide", "local phyto", "plantes exotiques envahissante", "herbicides"]
extract_terms_from_pdf(PDFPath,SearchTermList,f"Rapports\\{dailyID} - results.csv")
