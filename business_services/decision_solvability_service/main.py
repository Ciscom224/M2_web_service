from spyne import Application, rpc, ServiceBase, Unicode, Float, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import xml.etree.ElementTree as ET
import logging
import requests
# -------------------------------
# 🔹 Configuration des logs
# -------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# -------------------------------
#Modèles SOAP
# -------------------------------
class DecisionResponse(ComplexModel):
    solvencyStatus = Unicode

# -------------------------------
#Service SOAP de Décision
# -------------------------------
class DecisionService(ServiceBase):

    @rpc(Float, Float,Float, _returns=DecisionResponse)
    def MakeDecision(ctx, creditScore, monthlyIncome, monthlyDebtPayments):
        """
        Évalue la solvabilité du client selon le score et le ratio d’endettement.
        """
        logging.info(f"🧮 Évaluation décisionnelle : score={creditScore}")

# ---Appel du service DebtRatio
        debtRatio = 0.0
        try:
          
            soap_request = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                              xmlns:urn="urn:debtratio.service:v1">
               <soapenv:Body>
                  <urn:ComputeDebtRatio>
                     <urn:monthlyIncome>{monthlyIncome}</urn:monthlyIncome>
                     <urn:monthlyDebtPayments>{monthlyDebtPayments}</urn:monthlyDebtPayments>
                  </urn:ComputeDebtRatio>
               </soapenv:Body>
            </soapenv:Envelope>
            """
            resp = requests.post(
                "http://ratio_endettement_service:8004/",
                data=soap_request.encode("utf-8"),
                headers={"Content-Type": "text/xml;charset=UTF-8"},
                timeout=10
            )
            root = ET.fromstring(resp.content)
            ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/", "tns": "urn:debtratio.service:v1"}
            debtRatio = float(root.find(".//tns:debtRatio", ns).text or 0.0)
        except Exception as e:
            logging.error(f"Erreur DebtRatioService: {e}")

        logging.info(f"ration={debtRatio}")
        # Décision finale
        if creditScore >= 700 and debtRatio <= 40:
            status = "solvent"
        else:
            status = "not_solvent"

        return DecisionResponse(
            solvencyStatus=status,
        )

# -------------------------------
# Application SOAP
# -------------------------------
app = Application(
    [DecisionService],
    tns="urn:solvency.decision:v1",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = WsgiApplication(app)

# -------------------------------
# Lancement du serveur
# -------------------------------
if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    logging.info("🚀 Decision Service prêt sur http://0.0.0.0:8003/?wsdl")
    server = make_server("0.0.0.0", 8003, wsgi_app)
    server.serve_forever()
