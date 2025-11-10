import os
import json
import logging
from spyne import Application, rpc, ServiceBase, Unicode, ComplexModel, Decimal
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

logging.basicConfig(level=logging.INFO)

# --- Modèle de données ---
class Financials(ComplexModel):
    monthlyIncome = Decimal
    monthlyExpenses = Decimal

# --- Définition du service ---
class FinancialDataService(ServiceBase):
    @rpc(Unicode, _returns=Financials)
    def GetClientFinancials(ctx, clientId):
        logging.info(f"📥 Requête reçue pour clientId={clientId}")

        DB_PATH = "./financials.json"

        if not os.path.exists(DB_PATH):
            logging.error(f"❌ Fichier non trouvé : {DB_PATH}")
            raise ValueError("Base de données introuvable")

        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if clientId not in data:
            logging.error(f"❌ Client {clientId} introuvable dans la base.")
            raise ValueError(f"Client {clientId} introuvable")

        record = data[clientId]
        logging.info(f"✅ Données trouvées : {record}")

        return Financials(
            monthlyIncome=record["monthlyIncome"],
            monthlyExpenses=record["monthlyExpenses"]
        )
    
    

# --- Application SOAP ---
application = Application(
    [FinancialDataService],
    tns="urn:financial.data.service:v1",
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

app = WsgiApplication(application)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    logging.info("🚀 Service FinancialDataService en écoute sur http://localhost:8002/?wsdl")
    server = make_server("0.0.0.0", 8002, app)
    server.serve_forever()
