FROM python:3.11-slim

WORKDIR usr/src/app

# Install wget
RUN apt-get update && apt-get install -y wget

# Install Chrome
RUN wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i /tmp/chrome.deb || apt-get install -f -y && \
    rm /tmp/chrome.deb

COPY . .

RUN pip install --root-user-action=ignore --upgrade pip
RUN pip install --root-user-action=ignore -r requirements.txt

CMD ["python", "bot.py"]
