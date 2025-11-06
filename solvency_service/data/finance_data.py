class FinancialData:
    """Simule une source de données financière in-memory."""

    financials = {
        "client-001": {"MonthlyIncome": 4000.0, "Expenses": 2500.0},
        "client-002": {"MonthlyIncome": 3000.0, "Expenses": 2800.0},
        "client-003": {"MonthlyIncome": 6000.0, "Expenses": 4000.0},
    }

    @classmethod
    def get_client_financials(cls, client_id: str):
        """Retourne les données financières d’un client."""
        return cls.financials.get(
            client_id,
            {"MonthlyIncome": 0.0, "Expenses": 0.0}  # valeurs par défaut
        )
