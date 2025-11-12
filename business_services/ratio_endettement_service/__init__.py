# __init__.py pour le package debt_ratio_service

# Import explicite des composants principaux du service
from .main import DebtRatioService, DebtRatioResult

# Métadonnées du package
__version__ = "3.0.0"
__author__ = "Latifa Mankai"
__description__ = "Service de calcul Ratio"

# Export public (facilite l'import depuis l'extérieur)
__all__ = [
    DebtRatioService, 
    DebtRatioResult
]

