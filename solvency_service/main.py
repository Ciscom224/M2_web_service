# solvency_orchestrator.py
# solvency_orchestrator.py
from spyne import Application, rpc, ServiceBase, Unicode, Float, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import requests
import logging
import xml.etree.ElementTree as ET

# --- Données simulées pour l'exemple
from data.client_directory_data import ClientData
from data.credit_data import CreditData
from data.finance_data import FinancialData

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Modèle Spyne pour le retour
class SolvencyResponse(ComplexModel):
    solvencyStatus = Unicode
    creditScore = Float
    creditScoreExplanation = Unicode

# --- Middleware pour CORS
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

# --- Service d'orchestration
class SolvencyOrchestrator(ServiceBase):

    @rpc(Unicode, Unicode, _returns=SolvencyResponse)
    def GetFinalSolvency(ctx, clientId, demandeTexte):
        logging.info(f"🧩 Orchestration complète pour clientId={clientId}")

        # 1️⃣ Données internes
        client = ClientData.get_client_identity(clientId)
        financial = FinancialData.get_client_financials(clientId)
        credit = CreditData.get_credit_history(clientId)

        if not client or client["name"] == "Inconnu":
            return SolvencyResponse(
                solvencyStatus="error",
                creditScore=0.0,
                creditScoreExplanation="Client introuvable."
            )

        # --- 2️⃣ Appel du service CreditScore
        credit_score = 0.0
        try:
            soap_request = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:creditscore.service:v1">
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
                "http://credit_scoring_service:8002/",  # Nom du conteneur Docker
                data=soap_request.encode("utf-8"),
                headers={"Content-Type": "text/xml;charset=UTF-8"},
                timeout=10
            )
            root = ET.fromstring(resp.content)
            ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/", "tns": "urn:creditscore.service:v1"}
            credit_score = float(root.find(".//tns:score", ns).text or 0.0)
        except Exception as e:
            logging.error(f"Erreur CreditScoreService: {e}")

        # --- 3️⃣ Appel du service DebtRatio
        debt_ratio = 0.0
        try:
            monthly_debt = credit['debt'] / 12.0  # approximation si besoin
            soap_request = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:debtratio.service:v1">
               <soapenv:Body>
                  <urn:ComputeDebtRatio>
                     <urn:clientId>{clientId}</urn:clientId>
                     <urn:monthlyIncome>{financial['MonthlyIncome']}</urn:monthlyIncome>
                     <urn:monthlyDebtPayments>{monthly_debt}</urn:monthlyDebtPayments>
                  </urn:ComputeDebtRatio>
               </soapenv:Body>
            </soapenv:Envelope>
            """
            resp = requests.post(
                "http://ratio_endettement_service:8005/",  # Nom du conteneur Docker
                data=soap_request.encode("utf-8"),
                headers={"Content-Type": "text/xml;charset=UTF-8"},
                timeout=10
            )
            root = ET.fromstring(resp.content)
            ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/", "tns": "urn:debtratio.service:v1"}
            debt_ratio = float(root.find(".//tns:debtRatio", ns).text or 0.0)
        except Exception as e:
            logging.error(f"Erreur DebtRatioService: {e}")

        # --- 4️⃣ Appel du service DecisionService
        solvency_status = "unknown"
        report = ""
        try:
            soap_request = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:solvency.decision:v1">
            <soapenv:Body>
                <urn:MakeDecision>
                    <urn:clientId>{clientId}</urn:clientId>
                    <urn:creditScore>{credit_score}</urn:creditScore>
                    <urn:debtRatio>{debt_ratio}</urn:debtRatio>
                </urn:MakeDecision>
            </soapenv:Body>
            </soapenv:Envelope>
            """
            resp = requests.post(
                "http://decision_solvability_service:8006/",  # Nom du conteneur Docker
                data=soap_request.encode("utf-8"),
                headers={"Content-Type": "text/xml;charset=UTF-8"},
                timeout=10
            )
            root = ET.fromstring(resp.content)
            ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/", "tns": "urn:solvency.decision:v1"}
            solvency_status = root.find(".//tns:solvencyStatus", ns).text or "unknown"
            report = root.find(".//tns:report", ns).text or ""
        except Exception as e:
            logging.error(f"Erreur DecisionService: {e}")

        # --- 5️⃣ Retour final
        explanation = f"CreditScore={credit_score}, DebtRatio={debt_ratio}, DecisionReport={report}"
        return SolvencyResponse(
            solvencyStatus=solvency_status,
            creditScore=credit_score,
            creditScoreExplanation=explanation
        )

# --- Application SOAP
app = Application(
    [SolvencyOrchestrator],
    tns="urn:solvency.orchestrator:v1",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

wsgi_app = CORSMiddleware(WsgiApplication(app))

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    logging.info("🚀 Service d'orchestration prêt sur http://solvency_service:8000/?wsdl")
    server = make_server("0.0.0.0", 8000, wsgi_app)
    server.serve_forever()
