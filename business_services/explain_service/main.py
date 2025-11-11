from spyne import Application, rpc, ServiceBase, Float, Integer, Boolean, Unicode, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import logging

# -------------------------------------------------------
# 🔹 Configuration des logs
# -------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# -------------------------------------------------------
# 🧱 Modèle SOAP de réponse
# -------------------------------------------------------
class ExplanationResponse(ComplexModel):
    """Contient les explications détaillées d’une évaluation de solvabilité."""
    __namespace__ = "urn:explain.service:v1"

    creditScoreExplanation = Unicode
    incomeVsExpensesExplanation = Unicode
    creditHistoryExplanation = Unicode

# -------------------------------------------------------
# 🧠 Service SOAP principal : ExplainService
# -------------------------------------------------------
class ExplainService(ServiceBase):
    """
    Service d’explication de solvabilité.
    Analyse le score de crédit, les revenus/dépenses et l’historique de crédit
    pour produire des explications compréhensibles par un agent humain.
    """

    @rpc(
        Float,     # score
        Float,     # monthlyIncome
        Float,     # monthlyExpenses
        Float,     # debt
        Integer,   # latePayments
        Boolean,   # hasBankruptcy
        _returns=ExplanationResponse
    )
    def Explain(ctx, score, monthlyIncome, monthlyExpenses, debt, latePayments, hasBankruptcy):
        logging.info("🧩 Analyse en cours dans ExplainService...")

        # --- 1️⃣ Analyse du score
        if score >= 800:
            score_exp = f"Excellent score ({score:.2f}). Risque de défaut très faible."
        elif score >= 600:
            score_exp = f"Score moyen ({score:.2f}). Profil modérément risqué."
        else:
            score_exp = f"Score faible ({score:.2f}). Risque de non-remboursement élevé."

        # --- 2️⃣ Revenu vs Dépenses
        disposable_income = monthlyIncome - monthlyExpenses
        if disposable_income > 1000:
            income_exp = (
                f"Les revenus mensuels ({monthlyIncome:.2f} €) "
                f"dépassent largement les dépenses ({monthlyExpenses:.2f} €). "
                "Bonne capacité de remboursement."
            )
        elif disposable_income > 0:
            income_exp = (
                f"Les revenus ({monthlyIncome:.2f} €) couvrent juste les dépenses "
                f"({monthlyExpenses:.2f} €). Marges financières limitées."
            )
        else:
            income_exp = (
                f"Les dépenses ({monthlyExpenses:.2f} €) dépassent les revenus ({monthlyIncome:.2f} €). "
                "Risque financier important."
            )

        # --- 3️⃣ Historique de crédit
        history_parts = []
        if debt > 5000:
            history_parts.append(f"Dette importante ({debt:.2f} €).")
        if latePayments > 0:
            history_parts.append(f"{latePayments} paiement(s) en retard.")
        if hasBankruptcy:
            history_parts.append("Antécédent de faillite enregistré.")
        if not history_parts:
            history_parts.append("Aucun incident majeur dans l’historique de crédit.")
        credit_exp = " ".join(history_parts)

        logging.info("✅ Explication générée avec succès.")

        # --- 4️⃣ Retour du résultat SOAP
        return ExplanationResponse(
            creditScoreExplanation=score_exp,
            incomeVsExpensesExplanation=income_exp,
            creditHistoryExplanation=credit_exp
        )

# -------------------------------------------------------
# 🌐 Application SOAP
# -------------------------------------------------------
app = Application(
    [ExplainService],
    tns="urn:explain.service:v1",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = WsgiApplication(app)

# -------------------------------------------------------
# 🚀 Lancement du serveur
# -------------------------------------------------------
if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    logging.info("🚀 Explanation Service prêt sur http://0.0.0.0:8005/?wsdl")
    server = make_server("0.0.0.0", 8005, wsgi_app)
    server.serve_forever()
