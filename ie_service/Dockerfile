FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y gcc
RUN pip install -U spacy
RUN python -m spacy download en_core_web_sm
RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 8004
CMD ["python", "main.py"]
