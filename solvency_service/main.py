from spyne import Application, rpc, ServiceBase, Unicode, Float
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import requests
import logging
import xml.etree.ElementTree as ET

# Imports internes
from data.client_directory_data import ClientData
from data.credit_data import CreditData
from data.finance_data import FinancialData
from data.models import (
    SolvencyResponse,
    ClientIdentity,
    Financials,
    CreditHistory,
    Explanations,
    PropertyEvaluationResponse,
    ApprovalResponse
)

# -------------------------------------------------------
# 🔹 Configuration des logs
# -------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# -------------------------
# Middleware CORS
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


# ---------- Fonctions utilitaires de parsing (robustes) ----------
def find_with_ns_or_local(root, name, ns=None):
    """
    Essaie de trouver <prefix:name> en utilisant les namespaces fournis,
    sinon cherche par local-name() (ignore namespace).
    Retourne le premier élément trouvé ou None.
    """
    if ns:
        # cherche avec namespace si possible
        try:
            elem = root.find(".//tns:" + name, ns)
            if elem is not None:
                return elem
        except Exception:
            pass
    # fallback : ignore namespace
    return root.find(".//*[local-name()='%s']" % name)


def text_of(elem):
    if elem is None or elem.text is None:
        return None
    return elem.text.strip()


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

        if not client or client.get("name") == "Inconnu":
            return SolvencyResponse(
                solvencyStatus="error",
                creditScore=0,
                explanations=Explanations(
                    creditScoreExplanation="Client introuvable dans la base interne.",
                    incomeVsExpensesExplanation="",
                    creditHistoryExplanation=""
                )
            )

        # 2️⃣ Appel du service IE (Extraction des infos)
        extraction = {
            "amount": 0.0,
            "duration_years": 0,
            "property_type": "Inconnu",
            "property_description": "",
            "location": "Inconnue"
        }
        try:
            soap_request = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:tns="urn:ie.service:v7">
   <soapenv:Body>
      <tns:extractInformation>
         <tns:text>{demandeTexte}</tns:text>
      </tns:extractInformation>
   </soapenv:Body>
</soapenv:Envelope>"""

            resp = requests.post(
                "http://ie_service:8001/",
                data=soap_request.encode("utf-8"),
                headers={"Content-Type": "text/xml;charset=UTF-8"},
                timeout=10
            )
            logging.info(f"IE service status: {resp.status_code}")
            logging.debug(f"IE raw response: {resp.content.decode('utf-8', errors='ignore')}")

            root = ET.fromstring(resp.content)
            ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/", "tns": "urn:ie.service:v7"}

            # Spyne renvoie souvent <extractInformationResponse> (pas necessarily a "Result" wrapper)
            resp_elem = find_with_ns_or_local(root, "extractInformationResponse", ns)
            if resp_elem is None:
                # fallback : chercher les champs directement
                resp_elem = root

            # Lecture robuste des champs
            amount_txt = text_of(find_with_ns_or_local(resp_elem, "amount", ns))
            dur_txt = text_of(find_with_ns_or_local(resp_elem, "duration_years", ns))
            ptype_txt = text_of(find_with_ns_or_local(resp_elem, "property_type", ns))
            pdesc_txt = text_of(find_with_ns_or_local(resp_elem, "property_description", ns))
            loc_txt = text_of(find_with_ns_or_local(resp_elem, "location", ns))

            extraction["amount"] = float(amount_txt) if amount_txt else 0.0
            extraction["duration_years"] = int(dur_txt) if dur_txt else 0
            extraction["property_type"] = ptype_txt or "Inconnu"
            extraction["property_description"] = pdesc_txt or ""
            extraction["location"] = loc_txt or "Inconnue"

            logging.info(f"🏠 Extraction réussie : {extraction}")
        except Exception as e:
            logging.error(f"Erreur IE_Service: {e}")
            logging.debug("IE raw content (on exception): %s", resp.content.decode('utf-8', errors='ignore') if 'resp' in locals() else 'n/a')

        # 3️⃣ Appel du service PropertyEvaluation (envoi correct du bon élément racine)
        property_eval = PropertyEvaluationResponse(
            estimatedValue=0.0,
            legalCompliance=False,
            evaluationReport="Aucune évaluation disponible.",
            canProceed=False
        )
        try:
            # Construire le SOAP correctement : utiliser le préfixe tns défini dans xmlns:tns
            soap_request = f"""
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                                xmlns:tns="urn:property.evaluation:v1">
                <soapenv:Body>
                        <tns:EvaluateProperty>
                            <tns:data>
                                <tns:amount>{extraction['amount']}</tns:amount>
                                <tns:duration_years>{extraction['duration_years']}</tns:duration_years>
                                <tns:property_type>{extraction['property_type']}</tns:property_type>
                                <tns:property_description>{extraction['property_description']}</tns:property_description>
                                <tns:location>{extraction['location']}</tns:location>
                            </tns:data>
                        </tns:EvaluateProperty>
                </soapenv:Body>
                </soapenv:Envelope>
                """

            resp = requests.post(
                "http://property_evaluation_service:8006/",
                data=soap_request.encode("utf-8"),
                headers={"Content-Type": "text/xml;charset=UTF-8"},
                timeout=10
            )

            logging.info(f"PropertyEvaluation status: {resp.status_code}")

            root = ET.fromstring(resp.content)
            ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/", "tns": "urn:property.evaluation:v1"}

           
            result = find_with_ns_or_local(root, "EvaluatePropertyResponse", ns)
            if result is None:
               
                result = find_with_ns_or_local(root, "EvaluatePropertyResult", ns) or root

            if result is not None:
                est_txt = text_of(find_with_ns_or_local(result, "estimatedValue", ns))
                legal_txt = text_of(find_with_ns_or_local(result, "legalCompliance", ns))
                report_txt = text_of(find_with_ns_or_local(result, "evaluationReport", ns))
                canproceed_txt = text_of(find_with_ns_or_local(result, "canProceed", ns))

                property_eval = PropertyEvaluationResponse(
                    estimatedValue=float(est_txt) if est_txt else 0.0,
                    legalCompliance=(legal_txt == "true"),
                    evaluationReport=report_txt or "",
                    canProceed=(canproceed_txt == "true")
                )
                logging.info(f"🏡 Évaluation immobilière : {property_eval.evaluationReport}")
            else:
                logging.error("❌ Impossible de trouver EvaluatePropertyResponse/Result dans la réponse SOAP.")
        except Exception as e:
            logging.error(f"Erreur PropertyEvaluationService: {e}")
            logging.debug("Property raw content on exception: %s", resp.content.decode('utf-8', errors='ignore') if 'resp' in locals() else 'n/a')


        

        # 4️⃣ Appel du service CreditScore
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
            score_elem = find_with_ns_or_local(root, "score", ns)
            credit_score = int(float(text_of(score_elem) or 0))
        except Exception as e:
            logging.error(f"Erreur CreditScoreService: {e}")

        # 5️⃣ Appel du service DecisionService
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
            solvency_status = text_of(find_with_ns_or_local(root, "solvencyStatus", ns)) or "unknown"
        except Exception as e:
            logging.error(f"Erreur DecisionService: {e}")

        # 6️⃣ Appel du service ExplanationService
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
            explanations.creditScoreExplanation = text_of(find_with_ns_or_local(root, "creditScoreExplanation", ns)) or ""
            explanations.incomeVsExpensesExplanation = text_of(find_with_ns_or_local(root, "incomeVsExpensesExplanation", ns)) or ""
            explanations.creditHistoryExplanation = text_of(find_with_ns_or_local(root, "creditHistoryExplanation", ns)) or ""
        except Exception as e:
            logging.error(f"Erreur ExplanationService: {e}")


# appel du service approbation
        
        approval_response = None
        try:
            soap_request = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                              xmlns:urn="urn:approval.decision:v1">
               <soapenv:Body>
                  <urn:MakeApprovalDecision>
                     <urn:amount>{extraction['amount']}</urn:amount>
                     <urn:duration>{extraction['duration_years']}</urn:duration>
                     <urn:solvency>{solvency_status}</urn:solvency>
                     <urn:prop_value>{property_eval.estimatedValue}</urn:prop_value>
                     <urn:prop_ok>{str(property_eval.canProceed).lower()}</urn:prop_ok>
                  </urn:MakeApprovalDecision>
               </soapenv:Body>
            </soapenv:Envelope>
            """
            
            resp = requests.post(
                "http://approbation_service:8007/",
                data=soap_request.encode("utf-8"),
                headers={"Content-Type": "text/xml;charset=UTF-8"},
                timeout=10
            )

            root = ET.fromstring(resp.content)
            ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
                  "tns": "urn:approval.decision:v1"}

            result = find_with_ns_or_local(root, "MakeApprovalDecisionResult", ns) or root

            approval_response = ApprovalResponse(
                approved=(text_of(find_with_ns_or_local(result, "approved", ns)) == "true"),
                interestRate=float(text_of(find_with_ns_or_local(result, "interestRate", ns)) or 0.0),
                maxLoanAmount=float(text_of(find_with_ns_or_local(result, "maxLoanAmount", ns)) or 0.0),
                decisionReport=text_of(find_with_ns_or_local(result, "decisionReport", ns)) or ""
            )
            logging.info(f" sortie : {approval_response}")
            logging.info(f"✅ Décision finale : {approval_response.decisionReport}")

        except Exception as e:
            logging.error(f"Erreur ApprovalService: {e}")
            approval_response = ApprovalResponse(
                approved=False,
                interestRate=0.0,
                maxLoanAmount=0.0,
                decisionReport="Erreur de communication avec le service d'approbation."
            )
        # 7️⃣ Construction du retour structuré
       
        return SolvencyResponse(
            clientIdentity=ClientIdentity(name=client["name"], address=client["address"]),
            financials=Financials(MonthlyIncome=financial["MonthlyIncome"], Expenses=financial["Expenses"]),
            creditHistory=CreditHistory(
                debt=credit["debt"], late=credit["late"], hasBankruptcy=credit["hasBankruptcy"]
            ),
            creditScore=credit_score,
            solvencyStatus=solvency_status,
            explanations=explanations,
            propertyEvaluation=property_eval,
            approvalResponse=approval_response
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
