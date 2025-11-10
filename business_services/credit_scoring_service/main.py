# credit_scoring_service.py
from spyne import Application, rpc, ServiceBase, Float, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
from spyne import Integer, Boolean


class CreditScoreResult(ComplexModel):
    score = Float

class CreditScoringService(ServiceBase):
    @rpc(Float, Integer, Boolean, _returns=CreditScoreResult)
    def ComputeCreditScore(ctx, debt, latePayments, hasBankruptcy):
        score = 1000 - 0.1*debt - 50*latePayments - (200 if hasBankruptcy else 0)
        return CreditScoreResult(score=score)

application = Application([CreditScoringService],
                          tns='urn:creditscore.service:v1',
                          in_protocol=Soap11(validator='lxml'),
                          out_protocol=Soap11())

wsgi_app = WsgiApplication(application)

if __name__ == "__main__":
    server = make_server("0.0.0.0", 8002, wsgi_app)
    print("CreditScoringService running at http://credit_scoring_service:8002/?wsdl")
    server.serve_forever()
