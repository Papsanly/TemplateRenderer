FROM python:3.11-slim

WORKDIR usr/src/app

COPY . .

RUN pip install --root-user-action=ignore --upgrade pip
RUN pip install --root-user-action=ignore -r requirements.txt

CMD ["python", "bot.py"]
