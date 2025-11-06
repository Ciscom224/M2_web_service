from spyne import Application, rpc, ServiceBase, Unicode, ComplexModel, Float
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import requests
import logging
import xml.etree.ElementTree as ET

# Import des data internes
from data.client_directory_data import ClientData
from data.credit_data import CreditData
from data.finance_data import FinancialData
# importation des models 
from data.models import SolvencyResponse
# -------------------------------------------------------
# 🔹 Configuration des logs
# -------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")



# -------------------------
# CORS Middleware
# -------------------------
class CORSMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        def cors_start_response(status, headers, exc_info=None):
            headers.append(('Access-Control-Allow-Origin', '*'))
            headers.append(('Access-Control-Allow-Methods', 'POST, GET, OPTIONS'))
            headers.append(('Access-Control-Allow-Headers', 'Content-Type, SOAPAction'))
            return start_response(status, headers, exc_info)

        # Réponse spéciale pour OPTIONS (préflight)
        if environ['REQUEST_METHOD'] == 'OPTIONS':
            start_response('200 OK', [
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'POST, GET, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, SOAPAction'),
                ('Content-Length', '0'),
            ])
            return [b'']
        return self.app(environ, cors_start_response)



# -------------------------------------------------------
# 🧠 Service principal : Orchestrateur de solvabilité
# -------------------------------------------------------
class SolvencyService(ServiceBase):

    @rpc(Unicode, Unicode, _returns=SolvencyResponse)
    def VerifySolvency(ctx, clientId, demandeTexte):
        logging.info(f"🧩 Vérification de solvabilité pour {clientId}")

        # 1️⃣ Données internes
        client = ClientData.get_client_identity(clientId)
        financial = FinancialData.get_client_financials(clientId)
        credit = CreditData.get_credit_history(clientId)

        if not client or client["name"] == "Inconnu":
            return SolvencyResponse(
                solvencyStatus="error",
                creditScore=0.0,
                creditScoreExplanation="Client introuvable dans les données internes."
            )

        # 2️⃣ Appel IE_Service
        amount, duration = 0.0, 0
        try:
            soap_request = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                              xmlns:urn="urn:ie.service:v7">
               <soapenv:Body>
                  <urn:extractInformation>
                     <urn:text>{demandeTexte}</urn:text>
                  </urn:extractInformation>
               </soapenv:Body>
            </soapenv:Envelope>
            """

            resp = requests.post(
                "http://ie_service:8001/",
                data=soap_request.encode("utf-8"),
                headers={"Content-Type": "text/xml;charset=UTF-8", "SOAPAction": "extractInformation"},
                timeout=10
            )
            resp.raise_for_status()
            
            # Parse XML
            ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
                  "tns": "urn:ie.service:v7"}
            root = ET.fromstring(resp.content)
            body = root.find("soapenv:Body", ns)
            result = body.find(".//tns:extractInformationResult", ns)
            amount = float(result.find("tns:amount", ns).text or 0.0)
            duration = int(result.find("tns:duration_years", ns).text or 0)
            logging.info(f"Montant extrait: {amount}, Durée: {duration} ans")

        except Exception as e:
            logging.error(f"Erreur IE_Service : {e}")
            return SolvencyResponse(
                solvencyStatus="error",
                creditScore=0.0,
                creditScoreExplanation="Impossible d'extraire les informations de la demande."
            )

        # 3️⃣ Calcul du score
        try:

            income = float(financial["MonthlyIncome"])
            expenses = float(financial["Expenses"])
            debt = float(credit["debt"])
            late = int(credit["late"])
            bankruptcy = credit["hasBankruptcy"]

            disposable_income = income - expenses
            # Score ajusté selon montant du prêt demandé
            score = 1000 - 0.1 * debt - 50 * late - (200 if bankruptcy else 0)

            status = "solvent" if score >= 700 else "not_solvent"
            explanation = (
                f"Revenu dispo: {disposable_income} €, Dette: {debt} €, Retards: {late}, "
                f"Faillite: {bankruptcy}, Montant demandé: {amount} €, Durée: {duration} ans, "
                f"Score calculé: {score:.2f}."
            )
            logging.info(f"🧾 Résultat solvabilité: {status.upper()} (score={score:.2f})")

            return SolvencyResponse(
                solvencyStatus=status,
                creditScore=score,
                creditScoreExplanation=explanation
            )

        except Exception as e:
            logging.error(f"Erreur calcul score: {e}")
            return SolvencyResponse(
                solvencyStatus="error",
                creditScore=0.0,
                creditScoreExplanation="Erreur lors du calcul du score de solvabilité."
            )
# -------------------------------------------------------
# 🌐 Application SOAP
# -------------------------------------------------------
app = Application(
    [SolvencyService],
    tns="urn:solvency.verification.service:v1",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = CORSMiddleware(WsgiApplication(app))

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    logging.info("🚀 Service de Solvabilité prêt sur http://0.0.0.0:8000/?wsdl")
    server = make_server("0.0.0.0", 8000, wsgi_app)
    server.serve_forever()
