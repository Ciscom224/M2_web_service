from spyne import Application, rpc, ServiceBase, Unicode, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from spyne.error import Fault
import json, os

DB_PATH = "./clients.json"

class ClientIdentity(ComplexModel):
    name = Unicode
    address = Unicode

class ClientDirectoryService(ServiceBase):
    @rpc(Unicode, _returns=ClientIdentity)
    def GetClientIdentity(ctx, clientId):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if clientId not in data:
            raise Fault(f"Client {clientId} introuvable")
        return ClientIdentity(**data[clientId])

app = Application(
    [ClientDirectoryService],
    tns="urn:client.directory.service:v1",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)
wsgi_app = WsgiApplication(app)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    print("🚀 ClientDirectoryService sur http://0.0.0.0:8001/?wsdl")
    make_server("0.0.0.0", 8001, wsgi_app).serve_forever()
