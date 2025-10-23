import os
import json
import logging
from spyne import Application, rpc, ServiceBase, Unicode, ComplexModel, Decimal, Integer, Boolean
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

logging.basicConfig(level=logging.INFO)

# --- Modèle de données ---
class CreditHistory(ComplexModel):
    debt = Decimal
    latePayments = Integer
    hasBankruptcy = Boolean

# --- Définition du service ---
class CreditBureauService(ServiceBase):
    @rpc(Unicode, _returns=CreditHistory)
    def GetClientCreditHistory(ctx, clientId):
        logging.info(f"Requête pour clientId={clientId}")

        DB_PATH = "./credit_history.json"

        if not os.path.exists(DB_PATH):
            logging.error(f"Fichier non trouvé : {DB_PATH}")
            raise ValueError("Base de données introuvable")

        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if clientId not in data:
            logging.error(f"Client {clientId} introuvable dans la base.")
            raise ValueError(f"Client {clientId} introuvable")

        record = data[clientId]
        logging.info(f"✅ Données trouvées : {record}")

        return CreditHistory(
            debt=record["debt"],
            latePayments=record["latePayments"],
            hasBankruptcy=record["hasBankruptcy"]
        )

# --- Application SOAP ---
application = Application(
    [CreditBureauService],
    tns="urn:credit.bureau.service:v1",
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

app = WsgiApplication(application)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    logging.info("🚀 Service CreditBureauService en écoute sur http://localhost:8003")
    server = make_server("0.0.0.0", 8003, app)
    server.serve_forever()
