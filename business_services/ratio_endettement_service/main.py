# debt_ratio_service.py
from spyne import Application, rpc, ServiceBase, Unicode, Float, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server

# ----------------------
# Modèle de retour
# ----------------------
class DebtRatioResult(ComplexModel):
    debtRatio = Float  # Ratio en pourcentage

# ----------------------
# Service pour calculer le ratio d'endettement
# ----------------------
class DebtRatioService(ServiceBase):

    @rpc(Float, Float, _returns=DebtRatioResult)
    def ComputeDebtRatio(ctx, monthlyIncome, monthlyDebtPayments):
        if monthlyIncome <= 0:
            ratio = 0.0  # éviter division par zéro
        else:
            ratio = ((monthlyDebtPayments/12.0) / monthlyIncome) * 100
        return DebtRatioResult(debtRatio=ratio)

# ----------------------
# Définition du service SOAP
# ----------------------
application = Application([DebtRatioService],
                          tns='urn:debtratio.service:v1',
                          in_protocol=Soap11(validator='lxml'),
                          out_protocol=Soap11())

wsgi_app = WsgiApplication(application)

# ----------------------
# Serveur
# ----------------------
if __name__ == "__main__":
    print(f"DebtRatioService running at http://ratio_endettement_service:{8004}?wsdl")
    server = make_server("0.0.0.0", 8004, wsgi_app)
    server.serve_forever()
