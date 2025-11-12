# import sys
# import os
# from unittest.mock import Mock
# import pytest

from business_services.credit_scoring_service import CreditScoringService, CreditScoreResult

@pytest.fixture
def service():
    return CreditScoringService()

def test_high_credit_score(service):
    result = service.ComputeCreditScore(Mock(), 1000.0, 0, False)
    expected = 1000 - 0.1*1000 - 50*0 - 0
    assert abs(result.score - expected) < 1e-2

def test_low_credit_score_due_to_bankruptcy(service):
    result = service.ComputeCreditScore(Mock(), 5000.0, 2, True)
    expected = 1000 - 0.1*5000 - 50*2 - 200
    assert abs(result.score - expected) < 1e-2

