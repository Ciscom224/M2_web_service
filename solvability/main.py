
from spyne import Application, rpc, ServiceBase, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

from client_directory_data import ClientData
from credit_data import CreditData
from finance_data import FinancialData

class SolvencyVerificationService(ServiceBase):
    @rpc(Unicode, _returns=Unicode)
    def VerifySolvency(ctx, clientId):
        """Récupère toutes les données d’un client depuis les classes internes."""

        # Récupération des données depuis les classes simulées
        client = ClientData.get_client_identity(clientId)
        financial = FinancialData.get_client_financials(clientId)
        credit = CreditData.get_credit_history(clientId)

        # 🧾 Construction du résumé
        result = f"""
        🔍 Données du client ({clientId}) :

        👤 Identité :
        - Nom : {client['name']}
        - Adresse : {client['address']}

        💰 Données financières :
        - Revenu mensuel : {financial['MonthlyIncome']}
        - Dépenses mensuelles : {financial['Expenses']}

        🧾 Historique de crédit :
        - Dette totale : {credit['debt']}
        - Retards : {credit['late']}
        - Faillite : {credit['hasBankruptcy']}
        """

        print(result)
        return result


# -------------------------------
# 🌐 Configuration du service SOAP
# -------------------------------
app = Application(
    [SolvencyVerificationService],
    tns="urn:solvency.verification.service:v1",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)
wsgi_app = WsgiApplication(app)


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    print("🚀 Orchestrateur local prêt sur http://0.0.0.0:8000/?wsdl")
    server = make_server("0.0.0.0", 8000, wsgi_app)
    server.serve_forever()