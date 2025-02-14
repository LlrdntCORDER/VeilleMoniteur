from datetime import datetime
from PyPDF2 import PdfReader
import os, requests, csv, re
import pandas as pd


def generate_date(mode="default"):
    if mode == "path":
        return datetime.now().strftime("/%Y/%m/%d")
    if mode == "default":
        return datetime.now().strftime("%Y-%m-%d")
    else:
        return datetime.now().strftime("%Y-%m-%d")
    
# Téléchargement et analyse des données du Moniteur :
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
        return full_path

def extract_terms_from_pdf(pdf_path, terms, date, output_csv):
    """
    Recherche des termes dans un PDF et enregistre uniquement le terme trouvé et le numéro de page dans un fichier CSV.
    
    Args:
        pdf_path (str): Chemin du fichier PDF.
        terms (list): Liste des chaînes de caractères à rechercher.
        output_csv (str): Chemin du fichier CSV de sortie.
    """
    reader = PdfReader(pdf_path)
    results = []

    # Expression régulière pour trouver les termes exacts
    term_regex = re.compile(r"(?:\b|\s|,|\.|:|;|/|!|\?)({})(?:\b|\s|,|\.|:|;|/|!|\?)".format("|".join(map(re.escape, terms))), re.IGNORECASE)

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text:
            continue

        # Trouver les termes présents dans la page
        matches = term_regex.findall(text)
        for match in matches:
            match = match.lower()
            match = match.replace("\n","")
            results.append([date,match, page_num])

    FinalResult = []
    temp = []
    for ResInfo in results:
        Instances = results.count(ResInfo)
        FinalResInfo = ResInfo
        FinalResInfo.append(Instances)
        if ResInfo not in temp :
            FinalResult.append (FinalResInfo)
            temp.append(ResInfo)
        else:
            pass
    # Écriture dans le fichier CSV
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Date","Terme", "Numéro de page","Occurences"])
        writer.writerows(results)

    print(f"Extraction terminée. Résultats enregistrés dans {output_csv}")


def generate_html_from_csv(csv_file, output_html):
    """
    Génère une page HTML à partir d'un fichier CSV pour hébergement sur GitHub Pages.
    
    Args:
        csv_file (str): Chemin du fichier CSV contenant les données.
        output_html (str): Chemin du fichier HTML de sortie.
    """
    df = pd.read_csv(csv_file, delimiter=";")
    
    # Génération du tableau HTML
    table_html = df.to_html(index=False, classes="table table-striped", border=1)
    
    # Template HTML
    html_template = f'''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Résultats de l'extraction</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ text-align: center; }}
            .container {{ width: 80%; margin: auto; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
            th {{ background-color: #f4f4f4; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📄 Résultats de l'extraction</h1>
            {table_html}
        </div>
    </body>
    </html>
    '''
    
    # Écriture du fichier HTML
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    print(f"Page HTML générée : {output_html}")



# Paramétrage de la recherche
dailyIDPath = generate_date("path")
url = f"https://www.ejustice.just.fgov.be/mopdf{dailyIDPath}_1.pdf"
date =generate_date()
# Exemple d'utilisation
PDFPath = download_pdf(url)+datetime.now().strftime("%d")+"_1.pdf"
SearchTermList = ["pesticide","autorisation","travail", "produit phytosanitaire","zone tampon", "produits phytopharmaceutiques", "herbicide", "local phyto", "plantes exotiques envahissante", "herbicides"]
extract_terms_from_pdf(PDFPath,SearchTermList,date,f"result\\Data.csv")

generate_html_from_csv("result\\Data.csv", "index.html")
