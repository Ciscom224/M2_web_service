from spyne import Application, rpc, ServiceBase, Unicode, Float, Integer, Boolean, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import logging
import random

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ApprovalInput(ComplexModel):
    clientId = Unicode
    requestedAmount = Float
    duration_years = Integer
    solvencyStatus = Unicode
    estimatedPropertyValue = Float
    propertyCanProceed = Boolean

class ApprovalRequest(ApprovalInput):
    pass

class ApprovalResponse(ComplexModel):
    approved = Boolean
    interestRate = Float
    maxLoanAmount = Float
    decisionReport = Unicode

class ApprovalService(ServiceBase):
    @rpc(ApprovalRequest, _returns=ApprovalResponse)
    def MakeApprovalDecision(ctx, request):
        data = request
        client_id = data.clientId
        amount = data.requestedAmount
        duration = data.duration_years
        solvency = data.solvencyStatus
        prop_value = data.estimatedPropertyValue
        prop_ok = data.propertyCanProceed

        logging.info(f"Approbation pour {client_id}: {amount}€ sur {duration} ans")

        report = []
        approved = False
        interest_rate = 0.0
        max_loan = 0.0

        if solvency != "solvent":
            report.append("REFUS: Client non solvable")
            return ApprovalResponse(approved=False, interestRate=0.0, maxLoanAmount=0.0, decisionReport="; ".join(report))

        if not prop_ok:
            report.append("REFUS: Bien non conforme")
            return ApprovalResponse(approved=False, interestRate=0.0, maxLoanAmount=0.0, decisionReport="; ".join(report))

        ltv = amount / prop_value
        report.append(f"LTV: {ltv:.1%}")

        if ltv > 0.9:
            report.append("Risque très élevé (LTV > 90%)")
        elif ltv > 0.8:
            report.append("Risque modéré (LTV > 80%)")
        else:
            report.append("Risque faible (LTV ≤ 80%)")

        if duration > 25:
            report.append("Durée > 25 ans : risque accru")
        if amount > 500000:
            report.append("Montant élevé : contrôle renforcé")

        risk_score = random.uniform(0.0, 1.0)
        report.append(f"Score de risque prédictif: {risk_score:.3f}")

        if ltv <= 0.8 and risk_score < 0.3 and duration <= 25:
            approved = True
            interest_rate = 1.8 + (ltv * 2) + (risk_score * 3)
            max_loan = prop_value * 0.9
            report.append("APPROUVÉ : Conditions optimales")
        elif ltv <= 0.9 and risk_score < 0.6:
            approved = True
            interest_rate = 2.5 + (ltv * 3) + (risk_score * 4)
            max_loan = prop_value * 0.8
            report.append("APPROUVÉ avec conditions")
        else:
            approved = False
            report.append("REFUS : Risque trop élevé")
            if risk_score > 0.7:
                report.append("Conseil: Améliorer votre historique de paiement")
            if ltv > 0.9:
                report.append("Conseil: Augmenter l'apport personnel")
            if duration > 25:
                report.append("Conseil: Réduire la durée du prêt")

        if approved:
            report.append(f"Taux d'intérêt: {interest_rate:.2f}%")
            report.append(f"Montant maximum accordé: {max_loan:,.2f} €")

        final_report = "; ".join(report)
        logging.info(final_report)

        return ApprovalResponse(approved=approved, interestRate=round(interest_rate, 2), maxLoanAmount=round(max_loan, 2), decisionReport=final_report)

app = Application(
    [ApprovalService],
    tns="urn:approval.decision:v1",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

wsgi_app = WsgiApplication(app)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    logging.info("Approval Service ready on http://0.0.0.0:8008/?wsdl")
    server = make_server("0.0.0.0", 8008, wsgi_app)
    server.serve_forever()
