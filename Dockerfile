FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install -r requirements.txt

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# this is where the flask server is going to run
EXPOSE $PORT
EXPOSE 8080

# CMD ["sh", "-c", "service nginx start && bokeh serve McCabeInteractive.py --allow-websocket-origin=* --use-xheaders & python app.py"]
CMD python app.py
