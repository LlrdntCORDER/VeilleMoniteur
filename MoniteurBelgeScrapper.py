from datetime import datetime
from PyPDF2 import PdfReader
import os, requests, csv, re
import pandas as pd

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

def generate_md_from_csv(csv_file, output_md):
    df = pd.read_csv(csv_file, delimiter=";")
    table_md = df.to_markdown(index=False)
    md_template = f'''---
layout: default
title: "Résultats de l'extraction"
---

# 📄 Résultats de l'extraction

{table_md}
'''
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(md_template)
    print(f"Page Markdown générée : {output_md}")

dailyIDPath = generate_date("path")
url = f"https://www.ejustice.just.fgov.be/mopdf{dailyIDPath}_1.pdf"
date = generate_date()
PDFPath = download_pdf(url)
if PDFPath:
    SearchTermList = ["pesticide", "autorisation", "travail", "produit phytosanitaire", "zone tampon", "produits phytopharmaceutiques", "herbicide", "local phyto", "plantes exotiques envahissante", "herbicides"]
    extract_terms_from_pdf(PDFPath, SearchTermList, date, "result/Data.csv")
    generate_md_from_csv("result/Data.csv", "index.md")