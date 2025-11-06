from spyne import ComplexModel, Unicode, Float, Integer, Boolean

class ClientIdentity(ComplexModel):
    __namespace__ = "urn:solvency.verification.service:v1"
    name = Unicode
    address = Unicode

class Financials(ComplexModel):
    __namespace__ = "urn:solvency.verification.service:v1"
    MonthlyIncome = Float
    Expenses = Float

class CreditHistory(ComplexModel):
    __namespace__ = "urn:solvency.verification.service:v1"
    debt = Float
    late = Integer
    hasBankruptcy = Boolean

class Explanations(ComplexModel):
    __namespace__ = "urn:solvency.verification.service:v1"
    creditScoreExplanation = Unicode
    incomeVsExpensesExplanation = Unicode
    creditHistoryExplanation = Unicode

class SolvencyResponse(ComplexModel):
    """Réponse structurée du service de solvabilité"""
    __namespace__ = "urn:solvency.verification.service:v1"

    clientIdentity = ClientIdentity
    financials = Financials
    creditHistory = CreditHistory
    creditScore = Integer
    solvencyStatus = Unicode  # "solvent" ou "not_solvent"
    explanations = Explanations
