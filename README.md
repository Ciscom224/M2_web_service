# Solvency Verification - TP SOA

## Prérequis
- Docker & Docker Compose (ou Python 3.10+ si tu lances en local)
- (si local) `pip install -r requirements.txt` pour chaque service

## Structure
- `schemas/` : solvency.xsd, solvency.wsdl
- `crud_service/` : code CRUD et métier
- `service_solvabilite.py` : service SOAP solvabilité (port 8000)
- `ie_service/` : service NLP (port 8001)
- `orchestrateur/` : service composite (port 8002)
- `docker-compose.yml` : pour démarrer tout

## Lancer localement (sans Docker)
```bash
python service_solvabilite.py
# dans un autre terminal (si extraction)


docker-compose build
docker-compose up







  # ... autres services business ...

  solvency_verification_service:
    build: ./orchestration_service
    ports:
      - "8007:8007"
    depends_on:
      - client_directory_service
      - financial_data_service
      - credit_bureau_service
    volumes:
      - ./db:/app/db


