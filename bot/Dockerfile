FROM python:3.8

WORKDIR /bot_app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD python full_connected_bot.py
