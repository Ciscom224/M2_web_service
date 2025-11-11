# tests/test_property_evaluation.py
import pytest
from unittest.mock import Mock
from business_services.property_evaluation_service import (
    PropertyEvaluationService,
    PropertyEvaluationRequest,
    PropertyEvaluationInput
)

@pytest.fixture
def service():
    return PropertyEvaluationService()

# === CAS 1 : Maison neuve à Paris (APPROUVÉ) ===
def test_maison_neuve_paris(service):
    request = PropertyEvaluationRequest(
        request=PropertyEvaluationInput(
            amount=250000.0,
            duration_years=20,
            property_type="Maison",
            property_description="Maison neuve avec jardin",
            location="Paris"
        )
    )
    response = service.EvaluateProperty(Mock(), request)

    assert response.canProceed is True
    assert response.legalCompliance is True
    assert response.estimatedValue == 618750.0
    assert "618,750.00 €" in response.evaluationReport
    assert "Type maison : +20%" in response.evaluationReport
    assert "Localisation : x1.5" in response.evaluationReport
    assert "État excellent : +10%" in response.evaluationReport
    assert "Évaluation favorable" in response.evaluationReport



# === CAS 2 : Litige détecté (REFUS : non-conformité) ===
def test_litige_legal(service):
    request = PropertyEvaluationRequest(
        request=PropertyEvaluationInput(
            amount=400000.0,
            duration_years=15,
            property_type="Maison",
            property_description="Maison avec litige en cours",
            location="Lyon"
        )
    )
    response = service.EvaluateProperty(Mock(), request)

    assert response.canProceed is False
    assert response.legalCompliance is False
    assert "Non-conformité détectée" in response.evaluationReport
    assert "Refus : problème légal" in response.evaluationReport

# === CAS 3 : Durée invalide (REFUS : durée) ===
def test_duree_invalide(service):
    request = PropertyEvaluationRequest(
        request=PropertyEvaluationInput(
            amount=200000.0,
            duration_years=35,
            property_type="Maison",
            property_description="Maison neuve",
            location="Marseille"
        )
    )
    response = service.EvaluateProperty(Mock(), request)

    assert response.canProceed is False
    assert "Refus : durée invalide" in response.evaluationReport

# === CAS 4 : Valeur minimale non atteinte (REFUS : valeur faible) ===
def test_valeur_minimale_non_atteinte(service):
    request = PropertyEvaluationRequest(
        request=PropertyEvaluationInput(
            amount=500000.0,
            duration_years=20,
            property_type="Appartement",
            property_description="Appartement standard",
            location="Banlieue"
        )
    )
    response = service.EvaluateProperty(Mock(), request)

    assert response.canProceed is False
    assert "Refus : valeur faible" in response.evaluationReport

# === CAS 5 : Lyon, maison rénovée (APPROUVÉ) ===
def test_lyon_maison_renovee(service):
    request = PropertyEvaluationRequest(
        request=PropertyEvaluationInput(
            amount=300000.0,
            duration_years=25,
            property_type="maison",
            property_description="maison rénové",
            location="lyon"
        )
    )
    response = service.EvaluateProperty(Mock(), request)

    assert response.canProceed is True
    assert "Localisation : x1.2" in response.evaluationReport
    assert "État excellent : +10%" in response.evaluationReport