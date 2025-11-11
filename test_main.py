from spyne import Application, rpc, ServiceBase, Unicode, ComplexModel, Float
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import requests
import logging

# Import des repositories internes
from data.client_directory_data import ClientData
from data.credit_data import CreditData
from data.finance_data import FinancialData

# -------------------------------------------------------
# 🔹 Configuration des logs
# -------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# -------------------------------------------------------
# 🧱 Modèle SOAP personnalisé (renommé pour éviter le conflit)
# -------------------------------------------------------
class SolvencyResponse(ComplexModel):
    """Réponse structurée du service de solvabilité"""
    __namespace__ = "urn:solvency.verification.service:v1"

    solvencyStatus = Unicode
    creditScore = Float
    creditScoreExplanation = Unicode


# -------------------------------------------------------
# 🧠 Service principal : Orchestrateur de solvabilité
# -------------------------------------------------------
class SolvencyVerificationService(ServiceBase):

    @rpc(Unicode, Unicode, _returns=SolvencyResponse)
    def VerifySolvency(ctx, clientId, demandeTexte):
        """
        Service d’orchestration de vérification de solvabilité.
        - Récupère les données internes du client
        - Appelle IE_Service pour extraire le texte de la demande
        - Calcule un score simplifié
        """

        logging.info(f"🧩 Vérification de solvabilité pour {clientId}")

        # Étape 1️⃣ — Récupérer les données locales
        client = ClientData.get_client_identity(clientId)
        financial = FinancialData.get_client_financials(clientId)
        credit = CreditData.get_credit_history(clientId)

        if not client or client["name"] == "Inconnu":
            logging.warning("⚠️ Client introuvable dans la base interne.")
            return SolvencyResponse(
                solvencyStatus="error",
                creditScore=0.0,
                creditScoreExplanation="Client introuvable dans les données internes."
            )

        # Étape 2️⃣ — Appeler le service IE (Extraction d'informations)
        try:
            soap_request = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                              xmlns:urn="urn:ie.service:v3">
               <soapenv:Body>
                  <urn:extractInformation>
                     <urn:text>{demandeTexte}</urn:text>
                  </urn:extractInformation>
               </soapenv:Body>
            </soapenv:Envelope>
            """

            response = requests.post(
                "http://ie_service:8001/",
                data=soap_request.encode("utf-8"),
                headers={"Content-Type": "text/xml;charset=UTF-8", "SOAPAction": "extractInformation"},
                timeout=10
            )

            if response.status_code != 200:
                raise RuntimeError(f"Réponse IE invalide: {response.status_code}")

            logging.info("✅ Réponse du service IE reçue avec succès.")

        except Exception as e:
            logging.error(f"Erreur d'appel au service IE : {e}")
            return SolvencyResponse(
                solvencyStatus="error",
                creditScore=0.0,
                creditScoreExplanation="Impossible d'extraire les informations de la demande."
            )

        #  Calcul simplifié de la solvabilité
        try:
            income = float(financial["MonthlyIncome"])
            expenses = float(financial["Expenses"])
            debt = float(credit["debt"])
            late = int(credit["late"])
            bankruptcy = credit["hasBankruptcy"]

            disposable_income = income - expenses
            score = max(0, disposable_income * 0.05 - debt * 0.001 - late * 2)
            if bankruptcy:
                score *= 0.5

            status = "solvent" if score >= 100 else "not_solvent"
            explanation = (
                f"Revenu disponible: {disposable_income} €. "
                f"Dette: {debt} €, Retards: {late}, Faillite: {bankruptcy}. "
                f"Score calculé: {score:.2f}."
            )

            logging.info(f"🧾 Résultat solvabilité: {status.upper()} (score={score:.2f})")

            return SolvencyResponse(
                solvencyStatus=status,
                creditScore=score,
                creditScoreExplanation=explanation
            )

        except Exception as e:
            logging.error(f"Erreur dans le calcul du score: {e}")
            return SolvencyResponse(
                solvencyStatus="error",
                creditScore=0.0,
                creditScoreExplanation="Erreur lors du calcul du score de solvabilité."
            )
        
        


# -------------------------------------------------------
# 🌐 Application SOAP
# -------------------------------------------------------
app = Application(
    [SolvencyVerificationService],
    tns="urn:solvency.verification.service:v1",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = WsgiApplication(app)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    logging.info("🚀 Service de Solvabilité prêt sur http://0.0.0.0:8000/?wsdl")
    server = make_server("0.0.0.0", 8000, wsgi_app)
    server.serve_forever()
