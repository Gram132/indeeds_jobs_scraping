FROM python:3.10-slim

# Install Chrome
RUN apt-get update && apt-get install -y \
    wget gnupg unzip ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get update && apt-get install -y google-chrome-stable

# Set up Python env
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY kick_downloader.py .

CMD ["python", "kick_downloader.py"]
