# Import explicite des composants principaux
from .main import (
    PropertyEvaluationService,
    PropertyEvaluationRequest,
    PropertyEvaluationInput,
    PropertyEvaluationResponse
)

# Métadonnées du package
__version__ = "1.0.0"
__author__ = "Afdol FATOUMBI"
__description__ = "Service d'évaluation de la propriété immobilière avec estimation de valeur et conformité légale"

# Export public (facilite l'import)
__all__ = [
    "PropertyEvaluationService",
    "PropertyEvaluationRequest",
    "PropertyEvaluationInput",
    "PropertyEvaluationResponse"
]