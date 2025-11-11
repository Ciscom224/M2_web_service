# 🧩 Solvency Verification - TP SOA

## 📘 Description
Ce projet implémente une architecture **orientée services (SOA)** pour la vérification de solvabilité.  
Chaque composant est un **service indépendant** conteneurisé avec Docker, communiquant via **SOAP** sur un réseau interne Docker.

---

## ⚙️ Prérequis
Avant de lancer le projet, assure-toi d’avoir :
- **Docker** et **Docker Compose** installés  
- (Optionnel pour tests locaux) **Python 3.10+** et les dépendances installées :  
  ```bash
  pip install -r requirements.txt


## 🧱 Structure du projet
.
├── docker-compose.yml
├── solvency_service/                     # Service principal d'orchestration (port 8000)
├── ie_service/                           # Service d’extraction d’information NLP (port 8001)
├── business_services/
│   ├── credit_scoring_service/           # Calcul du score de crédit (port 8002)
│   ├── decision_solvability_service/     # Prise de décision sur la solvabilité (port 8003)
│   ├── ratio_endettement_service/        # Calcul du ratio d’endettement (port 8004)
│   ├── explain_service/                  # Génération d'explications (port 8005)
│   └── property_evaluation_service/      # Évaluation du bien immobilier (port 8006)
└── schemas/
    ├── solvency.xsd
    └── solvency.wsdl


| Service                        | Port | Wsdl                      |  URL Service                       |
| ------------------------------ | ---- | ------------------------- | -----------------------------------|
| `ie_service`                   | 8001 | http://0.0.0.0:8001/?wsdl | http://ie_service:8001/            |
| `credit_scoring_service`       | 8002 | http://0.0.0.0:8002/?wsdl | http://credit_scoring_service:8002/|
| `decision_solvability_service` | 8003 | http://0.0.0.0:8003/?wsdl | http://decision_solvability_service:8003/
| `ratio_endettement_service`    | 8004 | http://0.0.0.0:8004/?wsdl | http://ratio_endettement_service:8004/
| `explain_service`              | 8005 | http://0.0.0.0:8005/?wsdl | http://explain_service:8005/
| `property_evaluation_service`  | 8006 | http://0.0.0.0:8006/?wsdl | http://property_evaluation_service:8006/
| `solvency_service`             | 8000 | http://0.0.0.0:8000/?wsdl |

## 🚀 Lancer le projet avec Docker
### Construction des images
```bash
  docker-compose build
```
### Démarrage de l’architecture complète
```bash
  docker-compose up


