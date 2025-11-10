# Données in-memory (revenu mensuel et mensualités de dettes)
client_financial_data = {
    'C001': {'monthlyIncome': 5000, 'monthlyDebtPayments': 1500},
    'C002': {'monthlyIncome': 3000, 'monthlyDebtPayments': 1200},
}

# Fonction get qui retourne uniquement les informations financières
def get_client_financial_data(clientId):
    return client_financial_data.get(clientId, {'monthlyIncome': 0, 'monthlyDebtPayments': 0})

# Exemple d'utilisation
print(get_client_financial_data('C001'))
# Output: {'monthlyIncome': 5000, 'monthlyDebtPayments': 1500}

print(get_client_financial_data('C003'))
# Output: {'monthlyIncome': 0, 'monthlyDebtPayments': 0}

