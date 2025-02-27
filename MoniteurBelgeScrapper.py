from datetime import datetime
from PyPDF2 import PdfReader
import os, requests, re
import pandas as pd
import matplotlib.pyplot as plt
import openpyxl


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
    NewsFlag = True
    term_regex = re.compile(r"(?:\b|\s|,|\.|:|;|/|!|\?)({})(?:\b|\s|,|\.|:|;|/|!|\?)".format("|".join(map(re.escape, terms))), re.IGNORECASE)
    
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text:
            continue
        matches = term_regex.findall(text)
        if len(matches) == 0:
            pass
        else:
            for match in matches:
                results.append([date, match.lower().replace("\n", ""), page_num])
    
    if len (results)== 0:
        NewsFlag = False
        results.append([date, "Rien ne nous concerne aujourd'hui !", "NA"])
    df = pd.DataFrame(results, columns=["Date", "Terme", "Numéro de page"])
    df["Occurences"] = df.groupby(["Terme", "Numéro de page"])['Terme'].transform('count')
    df.drop_duplicates(inplace=True)
    
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    # Vérifier si le fichier CSV existe pour ajouter les nouvelles données
    if os.path.exists(output_csv):
        df_existing = pd.read_csv(output_csv, sep=";")
        df = pd.concat([df_existing, df], ignore_index=True)
    
    df.to_csv(output_csv, sep=";", index=False)
    df.to_excel("result/Data.xlsx", index=False, engine="openpyxl")
    
    return NewsFlag


def generate_markdown_report(csv_file="result/Data.csv", output_file="README.md"):
    df = pd.read_csv(csv_file, delimiter=';')
    df["Date"] = pd.to_datetime(df["Date"])  
    last_date = df["Date"].max().strftime("%Y-%m-%d")
    last_day_data = df[df["Date"] == df["Date"].max()]
    last_day_terms = last_day_data.groupby("Terme")["Occurences"].sum()

    plt.figure(figsize=(6, 6))
    last_day_terms.plot(kind="pie", autopct='%1.1f%%')
    plt.title("Termes les plus cités - Dernière journée")
    plt.ylabel("")
    plt.savefig("img/last_day_pie.png")
    plt.close()

    last_day_table = last_day_data[["Terme", "Numéro de page", "Occurences"]]
    total_terms = df.groupby("Terme")["Occurences"].sum()

    plt.figure(figsize=(6, 6))
    total_terms.plot(kind="pie", autopct='%1.1f%%')
    plt.title("Termes les plus cités - Global")
    plt.ylabel("")
    plt.savefig("img/global_pie.png")
    plt.close()

    daily_counts = df.groupby("Date")["Occurences"].sum()

    plt.figure(figsize=(8, 4))
    daily_counts.plot(kind="line", marker="o")
    plt.title("Évolution du nombre de termes cités par jour")
    plt.xlabel("Date")
    plt.ylabel("Nombre d'occurrences")
    plt.xticks(rotation=45)
    plt.grid()
    plt.savefig("img/evolution_line.png")
    plt.close()

    # Génération du README avec le lien vers la dernière release
    release_url = "https://github.com/LlrdntCORDER/VeilleMoniteur/releases/latest/download/Data.xlsx"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# Rapport quotidien\n\n")
        f.write(f"**Dernière mise à jour : {last_date}**\n\n")
        f.write(f"[📥 Télécharger la liste des obeservation en XLSX]({release_url})\n\n")
        f.write("## Termes les plus cités (dernière journée)\n\n")
        f.write("![Graphique](img/last_day_pie.png)\n\n")
        f.write("### Données de la dernière journée\n\n")
        f.write(last_day_table.to_markdown(index=False))
        f.write("\n\n")
        f.write("## Évolution globale\n\n")
        f.write("![Graphique](img/global_pie.png)\n\n")
        f.write("![Graphique](img/evolution_line.png)\n\n")

    print(f"Rapport généré : {output_file}")

def generate_markdown_empty_report(csv_file="result/Data.csv",output_file="README.md"):
    # Charger les données
    df = pd.read_csv(csv_file, delimiter=';')
    df["Date"] = pd.to_datetime(df["Date"])  # Convertir en datetime
    
    # Dernière date mentionnée
    last_date = df["Date"].max().strftime("%Y-%m-%d")
    
    # Agréger les occurrences par terme (toutes dates confondues)
    total_terms = df.groupby("Terme")["Occurences"].sum()
    
    # Graphique des termes les plus cités (toutes dates confondues)
    plt.figure(figsize=(6, 6))
    total_terms.plot(kind="pie", autopct='%1.1f%%')
    plt.title("Termes les plus cités - Global")
    plt.ylabel("")
    plt.savefig("img/lobal_pie.png")
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
    plt.savefig("img/evolution_line.png")
    plt.close()

    # Génération du README avec le lien vers la dernière release
    release_url = "https://github.com/LlrdntCORDER/VeilleMoniteur/releases/latest/download/Data.xlsx"
    
    # Génération du Markdown
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# Rapport quotidien\n\n")
        f.write(f"**Dernière mise à jour : {last_date}**\n\n")
        f.write(f"[📥 Télécharger la liste des obeservation en XLSX]({release_url})\n\n")

        f.write("## Pas d'actualités aujourd'hui 🥱\n\n")
        f.write("\n\n")
        
        f.write("## Évolution globale 🚀\n\n")
        f.write("![Graphique](img/global_pie.png)\n\n")
        f.write("![Graphique](img/evolution_line.png)\n\n")
    
    print(f"Rapport généré : {output_file}")

    
dailyIDPath = generate_date("path")
url = f"https://www.ejustice.just.fgov.be/mopdf{dailyIDPath}_1.pdf"
date = generate_date()
PDFPath = download_pdf(url)


SearchTermList = [
  "substances actives",
  "substance active",
  "SUBSTANCES ACTIVES",
  "SUBSTANCE ACTIVE",
  "Substances actives",
  "Substance active",
  "phytoprotecteurs",
  "PHYTOPROTECTEURS",
  "Phytoprotecteurs",
  "phytoprotecteur",
  "PHYTOPROTECTEUR",
  "Phytoprotecteur",
  "lutte intégrée",
  "LUTTE INTÉGRÉE",
  "Lutte intégrée",
  "agriculture biologique",
  "AGRICULTURE BIOLOGIQUE",
  "Agriculture biologique",
  "conversion biologique",
  "CONVERSION BIOLOGIQUE",
  "Conversion biologique",
  "phytolicence",
  "PHYTOLICENCE",
  "Phytolicence",
  "pulvérisation aérienne",
  "PULVÉRISATION AÉRIENNE",
  "Pulvérisation aérienne",
  "matériel d'application des produits",
  "MATÉRIEL D'APPLICATION DES PRODUITS",
  "Matériel d'application des produits",
  "eaux de surface",
  "EAUX DE SURFACE",
  "Eaux de surface",
  "eaux souterraines",
  "EAUX SOUTERRAINES",
  "Eaux souterraines",
  "traitement post-récolte",
  "TRAITEMENT POST-RÉCOLTE",
  "Traitement post-récolte",
  "traitement d'une serre",
  "TRAITEMENT D'UNE SERRE",
  "Traitement d'une serre",
  "zone tampon",
  "ZONE TAMPON",
  "Zone tampon",
  "réduction de la dérive",
  "RÉDUCTION DE LA DÉRIVE",
  "Réduction de la dérive",
  "assistant usage professionnel",
  "ASSISTANT USAGE PROFESSIONNEL",
  "Assistant usage professionnel",
  "distribution/conseil de produits à usage non professionnel",
  "DISTRIBUTION/CONSEIL DE PRODUITS À USAGE NON PROFESSIONNEL",
  "Distribution/conseil de produits à usage non professionnel",
  "usage professionnel spécifique",
  "USAGE PROFESSIONNEL SPÉCIFIQUE",
  "Usage professionnel spécifique",
  "distribution/conseil",
  "DISTRIBUTION/CONSEIL",
  "Distribution/conseil",
  "le local ou l'armoire",
  "LE LOCAL OU L'ARMOIRE",
  "Le local ou l'armoire",
  "acte d'agréation",
  "ACTE D'AGRÉATION",
  "Acte d'agréation",
  "herbicides",
  "HERBICIDES",
  "Herbicides",
  "herbicide",
  "HERBICIDE",
  "Herbicide",
  "insecticide",
  "INSECTICIDE",
  "Insecticide",
  "fongicide",
  "FONGICIDE",
  "Fongicide",
  "ennemis des végétaux",
  "ENNEMIS DES VÉGÉTAUX",
  "Ennemis des végétaux",
  "terrains revêtus non cultivables",
  "TERRAINS REVÊTUS NON CULTIVABLES",
  "Terrains revêtus non cultivables",
  "terrains meubles non cultivés en permanence",
  "TERRAINS MEUBLES NON CULTIVÉS EN PERMANENCE",
  "Terrains meubles non cultivés en permanence",
  "développement durable",
  "DÉVELOPPEMENT DURABLE",
  "Développement durable",
  "carduus",
  "CARDUUS",
  "Carduus",
  "cirsium",
  "CIRSIUM",
  "Cirsium",
  "rumex",
  "RUMEX",
  "Rumex",
  "espèces exotiques envahissantes",
  "ESPÈCES EXOTIQUES ENVAHISSANTES",
  "Espèces exotiques envahissantes",
  "ruissellement",
  "RUISSLEMENT",
  "Ruissellement",
  "bonnes pratiques",
  "BONNES PRATIQUES",
  "Bonnes pratiques",
  "bouillie phytopharmaceutique",
  "BOUILLIE PHYTOPHARMACEUTIQUE",
  "Bouillie phytopharmaceutique",
  "fond de cuve",
  "FOND DE CUVE",
  "Fond de cuve",
  "effluents phytopharmaceutiques",
  "EFFLUENTS PHYTOPHARMACEUTIQUES",
  "Effluents phytopharmaceutiques",
  "code de l'environnement",
  "code de l'Environnement",
  "CODE DE L'ENVIRONNEMENT",
  "Code de l'environnement",
  "Code de l'Environnement",
  "code de l'eau",
  "code de l'Eau",
  "CODE DE L'EAU",
  "Code de l'eau",
  "Code de l'Eau",
  "organismes de quarantaine",
  "ORGANISMES DE QUARANTAINE",
  "Organismes de quarantaine",
  "organismes nuisibles aux végétaux",
  "ORGANISMES NUISIBLES AUX VÉGÉTAUX",
  "Organismes nuisibles aux végétaux",
  "buse",
  "BUSE",
  "Buse",
  "feu bactérien",
  "FEU BACTÉRIEN",
  "Feu bactérien",
  "mildiou",
  "MILDIOU",
  "Mildiou",
  "éco-régime",
  "ÉCO-RÉGIME",
  "Éco-régime",
  "conditionnalité",
  "CONDITIONNALITÉ",
  "Conditionnalité",
  "glyphosate",
  "GLYPHOSATE",
  "Glyphosate"
]

ModificationRate = extract_terms_from_pdf(PDFPath, SearchTermList, date, "result/Data.csv")
if ModificationRate :
    generate_markdown_report()
else :
    generate_markdown_empty_report()
