from datetime import datetime
from PyPDF2 import PdfReader
import os, requests, csv, re
import pandas as pd
import matplotlib.pyplot as plt



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


def generate_daily_report(csv_path, output_dir="./"):
    # Charger les données
    df = pd.read_csv(csv_path, sep=";")
    
    # Vérifier si le fichier contient des données
    if df.empty:
        return "Aucune donnée disponible."
    
    # Récupérer la dernière date mentionnée
    derniere_date = df["Date"].max()
    df_last_day = df[df["Date"] == derniere_date]
    
    # Agréger les occurrences des termes pour la dernière journée
    terms_last_day = df_last_day.groupby("Terme")["Occurences"].sum()
    
    # Générer une pie chart pour la dernière journée
    pie_chart_last_day_path = os.path.join(output_dir, "img\\pie_chart_last_day.png")
    plt.figure(figsize=(8, 6))
    terms_last_day.plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title(f"Répartition des termes les plus cités ({derniere_date})")
    plt.ylabel("")
    plt.savefig(pie_chart_last_day_path)
    plt.close()
    
    # Préparer le tableau des données pour la dernière journée
    df_last_day_sorted = df_last_day.sort_values(by="Occurences", ascending=False)
    table_last_day = df_last_day_sorted[["Terme", "Numéro de page", "Occurences"]]
    
    # Agréger les occurrences des termes pour toutes les dates
    terms_all_days = df.groupby("Terme")["Occurences"].sum()
    
    # Générer une pie chart pour toutes les dates
    pie_chart_all_days_path = os.path.join(output_dir, "img\\pie_chart_all_days.png")
    plt.figure(figsize=(8, 6))
    terms_all_days.plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("Répartition des termes les plus cités (toutes dates confondues)")
    plt.ylabel("")
    plt.savefig(pie_chart_all_days_path)
    plt.close()
    
    # Compter le nombre total d'occurrences de termes par jour
    terms_per_day = df.groupby("Date")["Occurences"].sum()
    
    # Générer une line chart pour l'évolution globale
    line_chart_terms_per_day_path = os.path.join(output_dir, "img\\line_chart_terms_per_day.png")
    plt.figure(figsize=(10, 5))
    plt.plot(terms_per_day.index, terms_per_day.values, marker="o", linestyle="-")
    plt.xlabel("Date")
    plt.ylabel("Nombre total d'occurrences")
    plt.title("Évolution du nombre de termes cités par jour")
    plt.xticks(rotation=45)
    plt.savefig(line_chart_terms_per_day_path)
    plt.close()
    
    # Générer le contenu Markdown
    markdown_content = f"""
# Rapport quotidien

**Dernière mise à jour : {derniere_date}**

## Répartition des termes les plus cités ({derniere_date})
![Pie Chart](pie_chart_last_day.png)

### Détails des occurrences pour la dernière journée
| Terme | Page | Occurrence |
|-------|------|------------|
"""
    
    for _, row in table_last_day.iterrows():
        markdown_content += f"| {row['Terme']} | {row['Numéro de page']} | {row['Occurences']} |\n"
    
    markdown_content += f"""

# Évolution globale

## Répartition des termes les plus cités (toutes dates confondues)
![Pie Chart](pie_chart_all_days.png)

## Évolution du nombre de termes cités par jour
![Line Chart](line_chart_terms_per_day.png)
"""
    
    return markdown_content

def ReadMeUpdater():
    with open ("README.md","w",encoding="utf-8") as ReadMeFile:
        ReadMeFile.write(generate_daily_report("result\\Data.csv"))
    
dailyIDPath = generate_date("path")
url = f"https://www.ejustice.just.fgov.be/mopdf{dailyIDPath}_1.pdf"
date = generate_date()
PDFPath = download_pdf(url)


SearchTermList = ["pesticide", "autorisation", "travail", "produit phytosanitaire", "zone tampon", "produits phytopharmaceutiques", "herbicide", "local phyto", "plantes exotiques envahissante", "herbicides"]
extract_terms_from_pdf(PDFPath, SearchTermList, date, "result/Data.csv")
ReadMeUpdater()


