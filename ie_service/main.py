from spyne import Application, rpc, ServiceBase, Unicode, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import spacy
import re
import logging

# -----------------------------------
# ⚙️ Initialisation du NLP
# -----------------------------------
logging.basicConfig(level=logging.INFO)
nlp = spacy.load("fr_core_news_sm")


# -----------------------------------
# 🧱 Modèles de données
# -----------------------------------
class ClientInfo(ComplexModel):
    name = Unicode
    address = Unicode
    monthly_income = Unicode


class LoanInfo(ComplexModel):
    amount = Unicode
    duration_years = Unicode


class ExtractionResult(ComplexModel):
    client = ClientInfo
    loan = LoanInfo


# -----------------------------------
# 🧠 Fonctions d’extraction
# -----------------------------------

def clean_text(text: str) -> str:
    """Nettoie et normalise le texte."""
    text = text.replace("\n", " ").strip()
    return " ".join(text.split())


def extract_client_info(text: str, doc):
    """Extraction du nom, adresse et revenu du client."""
    name, address, income = None, None, None

    for ent in doc.ents:
        if ent.label_ in ["PER", "PERSON"] and not name:
            name = ent.text
        elif ent.label_ in ["LOC", "GPE"] and not address:
            address = ent.text

    lower_text = text.lower()
    if "revenu" in lower_text or "salaire" in lower_text:
        for token in doc:
            if token.like_num:
                income = f"{token.text} euros"
                break

    return ClientInfo(
        name=name or "Inconnu",
        address=address or "Non détectée",
        monthly_income=income or "Non précisé"
    )


def extract_loan_info(text: str, doc):
    """Extraction du montant et de la durée du prêt."""
    amount, duration = None, None

    for ent in doc.ents:
        if ent.label_ == "MONEY" and not amount:
            amount = ent.text

    for token in doc:
        if token.like_num and token.i + 1 < len(doc) and "an" in doc[token.i + 1].text:
            duration = f"{token.text} ans"
            break

    return LoanInfo(
        amount=amount or "Non précisé",
        duration_years=duration or "Non précisée"
    )


# -----------------------------------
# 🧩 Service SOAP principal
# -----------------------------------
class IE_Service(ServiceBase):

    @rpc(Unicode, _returns=ExtractionResult)
    def extractInformation(ctx, text):
        """Analyse NLP du texte de la demande de prêt."""
        logging.info("📩 Requête reçue pour extraction d'information.")
        clean = clean_text(text)
        doc = nlp(clean)

        client_info = extract_client_info(clean, doc)
        loan_info = extract_loan_info(clean, doc)

        logging.info("✅ Extraction terminée avec succès.")
        return ExtractionResult(
            client=client_info,
            loan=loan_info
        )


# -----------------------------------
# 🌐 Application SOAP
# -----------------------------------
app = Application(
    [IE_Service],
    tns="urn:ie.service:v1",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

wsgi_app = WsgiApplication(app)


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    logging.info("🚀 IE_Service prêt sur http://0.0.0.0:8004/?wsdl")
    server = make_server("0.0.0.0", 8004, wsgi_app)
    server.serve_forever()
