class ClientData:
   

    clients = {
        "client-001": {"name": "John Doe", "address": "123 Main St"},
        "client-002": {"name": "Alice Smith", "address": "456 Elm St"},
        "client-003": {"name": "Bob Johnson", "address": "789 Oak St"},
    }

    @classmethod
    def get_client_identity(cls, client_id: str):
        """Retourne le nom et l’adresse du client."""
        return cls.clients.get(client_id, {"name": "Inconnu", "address": "Non trouvé"})
