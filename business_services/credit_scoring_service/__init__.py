# __init__.py pour le package credit_scoring_service

# Import explicite des composants principaux du service
from .main import CreditScoringService, CreditScoreResult

# Métadonnées du package
__version__ = "2.0.0"
__author__ = "Latifa Mankai"
__description__ = "Service de calcul de score de crédit"

# Export public (facilite l'import depuis l'extérieur)
__all__ = [
    "CreditScoringService",
    "CreditScoreResult"
]