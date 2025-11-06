import re
import logging


# -------------------------------------------------------------------
# 🧠 Fonctions d’extraction
# -------------------------------------------------------------------
def clean_text(text: str) -> str:
    """Nettoie et normalise le texte."""
    text = text.replace("\n", " ").strip()
    return " ".join(text.split())


def extract_amount(text: str):
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(€|euros?)", text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1).replace(",", "."))
        except ValueError:
            logging.error("⚠️ Erreur lors de la conversion du montant.")
    return None


def extract_duration(text: str):
    match = re.search(r"(\d+)\s*(ans?|années?)", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def extract_property_type(text: str):
    types = ["maison", "appartement", "villa", "studio", "immeuble", "terrain"]
    for t in types:
        if re.search(rf"\b{t}\b", text.lower()):
            return t.capitalize()
    return None


def extract_property_description(text: str):
    keywords = ["maison", "appartement", "villa", "studio", "immeuble", "terrain"]
    for kw in keywords:
        if kw in text.lower():
            start = text.lower().find(kw)
            return text[start:start+120].split(".")[0]
    return None


def extract_location(text: str):
    match = re.search(r"à\s+([A-Z][a-zéèêëàâäïîôöûüç\-]+)", text)
    return match.group(1) if match else None