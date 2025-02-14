from datetime import datetime
from PyPDF2 import PdfReader
import os, requests, csv, re
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64


def generate_date(mode="default"):
    if mode == "path":
        return datetime.now().strftime("/%Y/%m/%d")
    return datetime.now().strftime("%Y-%m-%d")

def download_pdf(url, save_dir="downloads"):
    os.makedirs(save_dir, exist_ok=True)
    date_path = datetime.now().strftime("%Y/%m/")
    full_path = os.path.join(save_dir, date_path)
    os.makedirs(full_path, exist_ok=True)
    filename = os.path.join(full_path, url.split("/")[-1])
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"PDF téléchargé avec succès : {filename}")
        return filename
    else:
        print(f"Échec du téléchargement : {response.status_code}")
        return None

def extract_terms_from_pdf(pdf_path, terms, date, output_csv):
    reader = PdfReader(pdf_path)
    results = []
    term_regex = re.compile(r"(?:\\b|\\s|,|\\.|:|;|/|!|\\?)({})(?:\\b|\\s|,|\\.|:|;|/|!|\\?)".format("|".join(map(re.escape, terms))), re.IGNORECASE)
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text:
            continue
        matches = term_regex.findall(text)
        for match in matches:
            results.append([date, match.lower().replace("\n", ""), page_num])
    df = pd.DataFrame(results, columns=["Date", "Terme", "Numéro de page"])
    df["Occurences"] = df.groupby(["Terme", "Numéro de page"])['Terme'].transform('count')
    df.drop_duplicates(inplace=True)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, sep=";", index=False)
    print(f"Extraction terminée. Résultats enregistrés dans {output_csv}")

def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def generate_markdown_report(csv_file, output_file="report.md"):
    # Charger les données
    df = pd.read_csv(csv_file, delimiter=';')
    df["Date"] = pd.to_datetime(df["Date"])  # Convertir en datetime
    
    # Dernière date mentionnée
    last_date = df["Date"].max().strftime("%Y-%m-%d")
    
    # Filtrer les données pour la dernière journée
    last_day_data = df[df["Date"] == df["Date"].max()]
    
    # Agréger les occurrences par terme pour la dernière journée
    last_day_terms = last_day_data.groupby("Terme")["Occurences"].sum()
    
    # Graphique des termes les plus cités (dernière journée)
    plt.figure(figsize=(6, 6))
    last_day_terms.plot(kind="pie", autopct='%1.1f%%')
    plt.title("Termes les plus cités - Dernière journée")
    plt.ylabel("")
    plt.savefig("img\\last_day_pie.png")
    plt.close()
    
    # Tableau des données pour la dernière journée
    last_day_table = last_day_data[["Terme", "Numéro de page", "Occurences"]]
    
    # Agréger les occurrences par terme (toutes dates confondues)
    total_terms = df.groupby("Terme")["Occurences"].sum()
    
    # Graphique des termes les plus cités (toutes dates confondues)
    plt.figure(figsize=(6, 6))
    total_terms.plot(kind="pie", autopct='%1.1f%%')
    plt.title("Termes les plus cités - Global")
    plt.ylabel("")
    plt.savefig("img\\global_pie.png")
    plt.close()
    
    # Nombre de termes cités par jour
    daily_counts = df.groupby("Date")["Occurences"].sum()
    
    # Graphique de l'évolution des termes cités
    plt.figure(figsize=(8, 4))
    daily_counts.plot(kind="line", marker="o")
    plt.title("Évolution du nombre de termes cités par jour")
    plt.xlabel("Date")
    plt.ylabel("Nombre d'occurrences")
    plt.xticks(rotation=45)
    plt.grid()
    plt.savefig("img\\evolution_line.png")
    plt.close()
    
    # Génération du Markdown
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# Rapport quotidien\n\n")
        f.write(f"**Dernière mise à jour : {last_date}**\n\n")
        
        f.write("## Termes les plus cités (dernière journée)\n\n")
        f.write("![Graphique](img/last_day_pie.png)\n\n")
        
        f.write("### Données de la dernière journée\n\n")
        f.write(last_day_table.to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## Évolution globale\n\n")
        f.write("![Graphique](img/global_pie.png)\n\n")
        f.write("![Graphique](img/evolution_line.png)\n\n")
    
    print(f"Rapport généré : {output_file}")



    
dailyIDPath = generate_date("path")
url = f"https://www.ejustice.just.fgov.be/mopdf{dailyIDPath}_1.pdf"
date = generate_date()
PDFPath = download_pdf(url)


SearchTermList = ["pesticide", "autorisation", "travail", "produit phytosanitaire", "zone tampon", "produits phytopharmaceutiques", "herbicide", "local phyto", "plantes exotiques envahissante", "herbicides"]
extract_terms_from_pdf(PDFPath, SearchTermList, date, "result/Data.csv")
generate_markdown_report("result\\Data.csv", output_file="README.md")

