from spyne import Application, rpc, ServiceBase, Unicode, Float, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# -------------------------------
# SOAP Models
# -------------------------------
class DecisionRequest(ComplexModel):
    clientId = Unicode
    creditScore = Float
    debtRatio = Float

class DecisionResponse(ComplexModel):
    solvencyStatus = Unicode
    report = Unicode

# -------------------------------
# Decision Service
# -------------------------------
class DecisionService(ServiceBase):

    @rpc(Unicode, Float, Float, _returns=DecisionResponse)
    def MakeDecision(ctx, clientId, creditScore, debtRatio):
        logging.info(f"Making decision for {clientId}")
        report_parts = []

        # Evaluate credit score
        if creditScore >= 700:
            report_parts.append(f"Credit score is good ({creditScore})")
        else:
            report_parts.append(f"Credit score is low ({creditScore})")

        # Evaluate debt ratio
        if debtRatio <= 40:
            report_parts.append(f"Debt ratio is acceptable ({debtRatio}%)")
        else:
            report_parts.append(f"Debt ratio is high ({debtRatio}%)")

        # Decision logic
        if creditScore >= 700 and debtRatio <= 40:
            status = "solvent"
        else:
            status = "not_solvent"

        report_parts.append(f"Overall decision: {status.upper()}")

        report = "; ".join(report_parts)
        logging.info(report)

        return DecisionResponse(solvencyStatus=status, report=report)

# -------------------------------
# SOAP Application
# -------------------------------
app = Application(
    [DecisionService],
    tns="urn:solvency.decision:v1",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

wsgi_app = WsgiApplication(app)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    logging.info("Decision Service ready on http://decision_solvability_service:8006/?wsdl")
    server = make_server("0.0.0.0", 8006, wsgi_app)
    server.serve_forever()
