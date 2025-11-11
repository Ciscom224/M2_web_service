from spyne import Application, rpc, ServiceBase, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import requests
import logging
import xml.etree.ElementTree as ET

# Imports internes
from data.client_directory_data import ClientData
from data.credit_data import CreditData
from data.finance_data import FinancialData
from data.models import SolvencyResponse, ClientIdentity, Financials, CreditHistory, Explanations

# -------------------------------------------------------
# 🔹 Configuration des logs
# -------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# -------------------------
# Middleware CORS (pour accès via navigateur)
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
# 🧠 Service principal d’orchestration
# -------------------------------------------------------
class SolvencyService(ServiceBase):

    @rpc(Unicode, Unicode, _returns=SolvencyResponse)
    def VerifySolvency(ctx, clientId, demandeTexte):
        logging.info(f"🧩 Vérification de solvabilité pour {clientId}")

        # 1️⃣ Récupération des données internes
        client = ClientData.get_client_identity(clientId)
        financial = FinancialData.get_client_financials(clientId)
        credit = CreditData.get_credit_history(clientId)

        if not client or client["name"] == "Inconnu":
            return SolvencyResponse(
                solvencyStatus="error",
                creditScore=0,
                explanations=Explanations(
                    creditScoreExplanation="Client introuvable dans la base interne.",
                    incomeVsExpensesExplanation="",
                    creditHistoryExplanation=""
                )
            )

        # 2️⃣ Appel du service IE (extraction du montant + durée)
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
                headers={"Content-Type": "text/xml;charset=UTF-8"},
                timeout=10
            )
            resp.raise_for_status()
            ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
                  "tns": "urn:ie.service:v7"}
            root = ET.fromstring(resp.content)
            result = root.find(".//tns:extractInformationResult", ns)
            amount = float(result.find("tns:amount", ns).text or 0.0)
            duration = int(result.find("tns:duration_years", ns).text or 0)
            logging.info(f"📊 Montant extrait: {amount}, Durée: {duration} ans")
        except Exception as e:
            logging.error(f"Erreur IE_Service: {e}")

        # 3️⃣ Appel du service CreditScore
        credit_score = 0
        try:
            soap_request = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                              xmlns:urn="urn:creditscore.service:v1">
               <soapenv:Body>
                  <urn:ComputeCreditScore>
                     <urn:debt>{credit['debt']}</urn:debt>
                     <urn:latePayments>{credit['late']}</urn:latePayments>
                     <urn:hasBankruptcy>{str(credit['hasBankruptcy']).lower()}</urn:hasBankruptcy>
                  </urn:ComputeCreditScore>
               </soapenv:Body>
            </soapenv:Envelope>
            """
            resp = requests.post(
                "http://credit_scoring_service:8002/",
                data=soap_request.encode("utf-8"),
                headers={"Content-Type": "text/xml;charset=UTF-8"},
                timeout=10
            )
            root = ET.fromstring(resp.content)
            ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/", "tns": "urn:creditscore.service:v1"}
            credit_score = int(float(root.find(".//tns:score", ns).text or 0))
        except Exception as e:
            logging.error(f"Erreur CreditScoreService: {e}")

        # 4️⃣ Appel du service DecisionService
        solvency_status = "unknown"
        try:
            soap_request = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                              xmlns:urn="urn:solvency.decision:v1">
               <soapenv:Body>
                  <urn:MakeDecision>
                     <urn:creditScore>{credit_score}</urn:creditScore>
                     <urn:monthlyIncome>{financial['MonthlyIncome']}</urn:monthlyIncome>
                     <urn:monthlyDebtPayments>{financial['Expenses']}</urn:monthlyDebtPayments>
                  </urn:MakeDecision>
               </soapenv:Body>
            </soapenv:Envelope>
            """
            resp = requests.post(
                "http://decision_solvability_service:8003/",
                data=soap_request.encode("utf-8"),
                headers={"Content-Type": "text/xml;charset=UTF-8"},
                timeout=10
            )
            root = ET.fromstring(resp.content)
            ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/", "tns": "urn:solvency.decision:v1"}
            solvency_status = root.find(".//tns:solvencyStatus", ns).text or "unknown"
        except Exception as e:
            logging.error(f"Erreur DecisionService: {e}")

        # 5️⃣ Appel du service ExplanationService
        explanations = Explanations()
        try:
            soap_request = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                              xmlns:urn="urn:explain.service:v1">
               <soapenv:Body>
                  <urn:Explain>
                     <urn:score>{credit_score}</urn:score>
                     <urn:monthlyIncome>{financial['MonthlyIncome']}</urn:monthlyIncome>
                     <urn:monthlyExpenses>{financial['Expenses']}</urn:monthlyExpenses>
                     <urn:debt>{credit['debt']}</urn:debt>
                     <urn:latePayments>{credit['late']}</urn:latePayments>
                     <urn:hasBankruptcy>{str(credit['hasBankruptcy']).lower()}</urn:hasBankruptcy>
                  </urn:Explain>
               </soapenv:Body>
            </soapenv:Envelope>
            """
            resp = requests.post(
                "http://explain_service:8005/",
                data=soap_request.encode("utf-8"),
                headers={"Content-Type": "text/xml;charset=UTF-8"},
                timeout=10
            )
            root = ET.fromstring(resp.content)
            ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/", "tns": "urn:explain.service:v1"}
            explanations.creditScoreExplanation = root.find(".//tns:creditScoreExplanation", ns).text or ""
            explanations.incomeVsExpensesExplanation = root.find(".//tns:incomeVsExpensesExplanation", ns).text or ""
            explanations.creditHistoryExplanation = root.find(".//tns:creditHistoryExplanation", ns).text or ""
        except Exception as e:
            logging.error(f"Erreur ExplanationService: {e}")

        # 6️⃣ Construction du retour structuré
        return SolvencyResponse(
            clientIdentity=ClientIdentity(name=client["name"], address=client["address"]),
            financials=Financials(MonthlyIncome=financial["MonthlyIncome"], Expenses=financial["Expenses"]),
            creditHistory=CreditHistory(
                debt=credit["debt"], late=credit["late"], hasBankruptcy=credit["hasBankruptcy"]
            ),
            creditScore=credit_score,
            solvencyStatus=solvency_status,
            explanations=explanations
        )


# -------------------------------------------------------
# 🌐 Application SOAP + CORS
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
    logging.info("🚀 Solvency Orchestrator prêt sur http://0.0.0.0:8000/?wsdl")
    server = make_server("0.0.0.0", 8000, wsgi_app)
    server.serve_forever()
