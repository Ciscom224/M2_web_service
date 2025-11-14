from spyne import Application, rpc, ServiceBase, Unicode, Float, Integer, Boolean, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import logging

# -------------------------------------------------------
# 🔹 Configuration des logs
# -------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# -------------------------------------------------------
# 🧱 Modèle d'entrée : identique à la sortie du IE_Service
# -------------------------------------------------------
class ExtractionResult(ComplexModel):
    amount = Float
    duration_years = Integer
    property_type = Unicode
    property_description = Unicode
    location = Unicode

# -------------------------------------------------------
# 🧾 Modèle de sortie du service PropertyEvaluation
# -------------------------------------------------------
class PropertyEvaluationResponse(ComplexModel):
    estimatedValue = Float
    legalCompliance = Boolean
    evaluationReport = Unicode
    canProceed = Boolean


# -------------------------------------------------------
# 🧠 Service d’évaluation de propriété
# -------------------------------------------------------
class PropertyEvaluationService(ServiceBase):

    @rpc(ExtractionResult, _returns=PropertyEvaluationResponse)
    def EvaluateProperty(ctx, data):
        logging.info(f"🏠 Évaluation pour un prêt de {data.amount} € à {data.location}")

        report_parts = []

        # === 1️⃣ Estimation de la valeur ===
        base_value = data.amount / 0.8 if data.amount else 0
        estimated_value = base_value

        # Type de bien
        if "maison" in data.property_type.lower():
            estimated_value *= 1.2
            report_parts.append("Type maison : +20%")
        elif "appartement" in data.property_type.lower():
            estimated_value *= 0.9
            report_parts.append("Type appartement : -10%")

        # Localisation
        loc = data.location.lower()
        loc_factor = 1.0
        if "paris" in loc: loc_factor = 1.5
        elif "lyon" in loc: loc_factor = 1.2
        elif "marseille" in loc: loc_factor = 1.1
        elif "banlieue" in loc: loc_factor = 0.85
        estimated_value *= loc_factor
        report_parts.append(f"Localisation : x{loc_factor}")

        # État du bien
        desc = data.property_description.lower()
        if any(w in desc for w in ["neuf", "rénové"]):
            estimated_value *= 1.1
            report_parts.append("État excellent : +10%")
        elif "rénover" in desc:
            estimated_value *= 0.8
            report_parts.append("À rénover : -20%")

        report_parts.append(f"Valeur estimée : {estimated_value:,.2f} €")

        # === 2️⃣ Vérification légale ===
        legal_issues = any(w in desc or w in loc for w in ["litige", "illégal"])
        legal_compliance = not legal_issues
        report_parts.append("Conforme légalement" if legal_compliance else "Non-conformité détectée")

        # === 3️⃣ Décision d’évaluation ===
        min_value = data.amount * 1.1
        duration_ok = 10 <= data.duration_years <= 30
        can_proceed = legal_compliance and (estimated_value >= min_value) and duration_ok

        if can_proceed:
            report_parts.append("✅ Évaluation favorable")
        else:
            reasons = []
            if estimated_value < min_value: reasons.append("valeur estimée insuffisante")
            if not duration_ok: reasons.append("durée de prêt invalide")
            if not legal_compliance: reasons.append("non-conformité légale")
            report_parts.append(f"❌ Refus : {', '.join(reasons)}")

        report = "; ".join(report_parts)
        logging.info(report)

        return PropertyEvaluationResponse(
            estimatedValue=round(estimated_value, 2),
            legalCompliance=legal_compliance,
            evaluationReport=report,
            canProceed=can_proceed
        )


# -------------------------------------------------------
# 🌐 Application SOAP
# -------------------------------------------------------
app = Application(
    [PropertyEvaluationService],
    tns="urn:property.evaluation:v1",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = WsgiApplication(app)


# -------------------------------------------------------
# 🚀 Lancement du serveur
# -------------------------------------------------------
if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    logging.info("🚀 Property Evaluation Service prêt sur http://0.0.0.0:8006/?wsdl")
    server = make_server("0.0.0.0", 8006, wsgi_app)
    server.serve_forever()
