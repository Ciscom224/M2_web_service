import sys, os, unittest

# ajouter le dossier racine au sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from business_services.credit_scoring_service import CreditScoringService, CreditScoreResult

class DummyContext:
    pass

class TestCreditScoringService(unittest.TestCase):
    def setUp(self):
        self.ctx = DummyContext()

    def test_high_credit_score(self):
        result = CreditScoringService.ComputeCreditScore(self.ctx, 1000.0, 0, False)
        expected = 1000 - 0.1*1000
        self.assertAlmostEqual(result.score, expected, places=2)

    def test_low_credit_score_due_to_bankruptcy(self):
        result = CreditScoringService.ComputeCreditScore(self.ctx, 5000.0, 2, True)
        expected = 1000 - 0.1*5000 - 50*2 - 200
        self.assertAlmostEqual(result.score, expected, places=2)

    def test_very_low_credit_score(self):
        result = CreditScoringService.ComputeCreditScore(self.ctx, 100000.0, 10, False)
        expected = 1000 - 0.1*100000 - 50*10
        self.assertAlmostEqual(result.score, expected, places=2)

if __name__ == "__main__":
    unittest.main()
