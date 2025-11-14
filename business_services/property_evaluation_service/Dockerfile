FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir spyne==2.14.0 lxml

EXPOSE 8006

CMD ["python", "main.py"]