from datetime import datetime
from PyPDF2 import PdfReader
import os, requests, csv, re
from bs4 import BeautifulSoup
import pandas as pd

def generate_date():
    return datetime.now().strftime("%Y-%m-%d")

def generate_date_path():
    return datetime.now().strftime("%Y\\%m\\%d")

def VeilleMoniteur(url, search_terms, output_csv="decrees_results.csv"):
    """
    Extrait les décrets d'une page web et enregistre les informations pertinentes dans un fichier CSV.

    Args:
        url (str): URL de la page web à analyser.
        search_terms (list): Liste des termes à rechercher dans les titres et descriptions.
        output_csv (str): Nom du fichier CSV de sortie.
    """
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Erreur lors de la requête HTTP : {response.status_code}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    # Trouver tous les éléments de décret sur la page
    decrees = soup.find_all('div', class_='list-item')

    results = []
    base_url = "https://www.ejustice.just.fgov.be/cgi/"

    for decree in decrees:
        # Extraction du titre
        title_tag = decree.find('div', class_='list-item--content')
        title_subtag = title_tag.find('p', class_='list-item--subtitle') if title_tag else None
        title = title_subtag.get_text(strip=True) if title_subtag else "Titre non trouvé"

        # Extraction de la description
        description_tag = decree.find('a', class_='list-item--title')
        description = description_tag.get_text(strip=True) if description_tag else "Description non trouvée"

        # Extraction du numéro de page (dernier élément de la description)
        page_number_match = re.findall(r'\d+', description)
        page_number = page_number_match[-1] if page_number_match else "Numéro de page non trouvé"

        # Extraction du lien vers le décret
        link_tag = decree.find('a', class_='list-item--title')
        link = base_url + link_tag['href'] if link_tag and link_tag.get('href') else "Lien non trouvé"

        # Vérification de la présence des termes de recherche
        for term in search_terms:
            if term.lower() in title.lower() or term.lower() in description.lower():
                results.append([term, title, description, page_number, link])

    # Écriture des résultats dans le fichier CSV
    with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(["Terme repéré", "Titre du décret", "Description du décret", "Numéro de page", "Hyperlien"])
        writer.writerows(results)
    df = pd.read_csv(output_csv, delimiter=';', encoding='utf-8')
    df.to_excel(f"Rapports\\{dailyPath} - VeilleMoniteur.xlsx", index=False, engine='openpyxl')
    print(f"Extraction terminée. Les résultats ont été enregistrés dans '{output_csv}'.")

# Liste de termes à surveiller
SearchTermList = ["pesticide","autorisation", "produit phytosanitaire","zone tampon", "produits phytopharmaceutiques", "herbicide", "local phyto", "plantes exotiques envahissante", "herbicides"]

dailyID = generate_date()
dailyPath = generate_date_path()

url = f"https://www.ejustice.just.fgov.be/cgi/summary.pl?language=fr&sumnext={dailyID}"

VeilleMoniteur(url, SearchTermList,f"Rapports\\{dailyPath} - VeilleMoniteur.csv")

