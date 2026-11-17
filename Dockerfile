FROM registry.access.redhat.com/ubi9/python-311:latest

WORKDIR /opt/app-root/src
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

EXPOSE 8080
USER 1001
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app.app:app"]
