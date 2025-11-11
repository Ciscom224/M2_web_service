from spyne import Application, rpc, ServiceBase, Unicode, Float, Integer, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import logging

#importation des fonctions d'extraction
from utils import clean_text,extract_amount,extract_duration,extract_location,extract_property_description,extract_property_type

# -------------------------------------------------------------------
# 🔹 Configuration du journal de logs
# -------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# -------------------------------------------------------------------
# 🧱 Modèle de données de sortie
# -------------------------------------------------------------------
class ExtractionResult(ComplexModel):
    amount = Float
    duration_years = Integer
    property_type = Unicode
    property_description = Unicode
    location = Unicode
    warning_message = Unicode  # Nouveau : champ pour signaler les erreurs ou avertissements





# -------------------------------------------------------------------
# 🚀 Service principal IE
# -------------------------------------------------------------------
class IE_Service(ServiceBase):

    @rpc(Unicode, _returns=ExtractionResult)
    def extractInformation(ctx, text):
        """Analyse du texte et extraction des informations clés avec gestion des erreurs."""
        logging.info("🧠 Début du traitement du texte de la demande...")
        clean = clean_text(text)

        # Extraction des éléments
        amount = extract_amount(clean)
        duration = extract_duration(clean)
        property_type = extract_property_type(clean)
        property_description = extract_property_description(clean)
        location = extract_location(clean)

        # Gestion des erreurs et avertissements
        warnings = []
        if amount is None:
            warnings.append("Montant du prêt non détecté.")
        if duration is None:
            warnings.append("Durée du prêt non détectée.")
        if property_type is None:
            warnings.append("Type de propriété non identifié.")
        if location is None:
            warnings.append("Localisation non détectée.")

        warning_message = " | ".join(warnings) if warnings else "Aucun problème détecté."

        # Logs détaillés
        logging.info(f"Montant détecté : {amount}")
        logging.info(f"Durée détectée : {duration}")
        logging.info(f"Type : {property_type}")
        logging.info(f"Localisation : {location}")
        if warnings:
            logging.warning(f"Avertissements : {warning_message}")

        return ExtractionResult(
            amount=amount or 0.0,
            duration_years=duration or 0,
            property_type=property_type or "Inconnu",
            property_description=property_description or "non détectée",
            location=location or "inconnue",
            warning_message=warning_message
        )


# -------------------------------------------------------------------
# 🌐 Application SOAP
# -------------------------------------------------------------------
app = Application(
    [IE_Service],
    tns="urn:ie.service:v7",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = WsgiApplication(app)


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    logging.info("🚀 Service IE (v7) prêt sur http://0.0.0.0:8001/?wsdl")
    server = make_server("0.0.0.0", 8001, wsgi_app)
    server.serve_forever()