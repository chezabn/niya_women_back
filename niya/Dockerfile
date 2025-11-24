FROM python:3.10.12

WORKDIR /app

# Installer les dépendances système nécessaires pour mysqlclient et compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
 && rm -rf /var/lib/apt/lists/*

COPY niya/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY niya .

EXPOSE 5001

CMD ["gunicorn", "niya.wsgi:application", "--bind", "0.0.0.0:5001"]
