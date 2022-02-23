FROM python:3.8.0-slim

# Copy local code to the container image
COPY . /app

# Sets the working directory
WORKDIR /app

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Upgrade PIP
RUN pip install --upgrade pip

#Install python libraries from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip3 install torchvision==0.2.2

ENV PYTHONUNBUFFERED True
ENV FLASK_APP main
ENV FLASK_ENV production
ENV PORT 8080
ENV GOOGLE_APPLICATION_CREDENTIALS ./service.json

# CMD ["python", "main.py"]
CMD exec gunicorn --bind :$PORT --workers 3 --threads 8 --timeout 0 main:app