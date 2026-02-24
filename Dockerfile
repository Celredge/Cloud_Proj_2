FROM python:3.14-slim

ENV PYTHONWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY src ./src

EXPOSE 5000

ENV FLASK_APP=src/app.py
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["python","-m","flask","run"]
