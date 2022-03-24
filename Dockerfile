FROM python:3.9-slim

COPY req.txt .
RUN pip3 install --user -r req.txt

WORKDIR /app

COPY ./main.py .
COPY ./bot_api.py .
COPY ./credentials.json .
COPY ./fb.json .

ENV PATH=/root/.local:$PATH

CMD ["python3", "-u", "./main.py"]