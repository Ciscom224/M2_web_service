# import sys, os, unittest

# # ajouter le dossier racine au sys.path
# ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# if ROOT_DIR not in sys.path:
#     sys.path.insert(0, ROOT_DIR)

import pytest
from unittest.mock import Mock

from business_services.ratio_endettement_service import DebtRatioService, DebtRatioResult

# Fixture pytest pour réutiliser le service
@pytest.fixture
def service():
    return DebtRatioService()

# === Test 1 : ratio normal ===
def test_compute_ratio_normal(service):
    result = service.ComputeDebtRatio(Mock(), monthlyIncome=5000.0, monthlyDebtPayments=1000.0)
    assert isinstance(result, DebtRatioResult)
    # ((1000/12)/5000)*100 = 1.6667 %
    assert round(result.debtRatio, 4) == round((1000/12)/5000*100, 4)

# === Test 2 : revenu nul ===
def test_compute_ratio_zero_income(service):
    result = service.ComputeDebtRatio(Mock(), monthlyIncome=0.0, monthlyDebtPayments=1000.0)
    assert isinstance(result, DebtRatioResult)
    assert result.debtRatio == 0.0

# === Test 3 : dette nulle ===
def test_compute_ratio_zero_debt(service):
    result = service.ComputeDebtRatio(Mock(), monthlyIncome=4000.0, monthlyDebtPayments=0.0)
    assert isinstance(result, DebtRatioResult)
    assert result.debtRatio == 0.0
