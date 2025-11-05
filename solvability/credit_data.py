class CreditData:
    """Simule l’historique de crédit d’un client."""

    credit_history = {
        "client-001": {"debt": 5000.0, "late": 2, "hasBankruptcy": False},
        "client-002": {"debt": 2000.0, "late": 0, "hasBankruptcy": False},
        "client-003": {"debt": 10000.0, "late": 5, "hasBankruptcy": True},
    }

    @classmethod
    def get_credit_history(cls, client_id: str):
        """Retourne l’historique de crédit du client."""
        return cls.credit_history.get(
            client_id,
            {"debt": 0.0, "late": 0, "hasBankruptcy": False}  # valeurs par défaut
        )
