FROM python:3.10.2-slim-bullseye

LABEL org.opencontainers.image.source = "https://github.com/penguin-statistics/ArkPlanner"

COPY . .

RUN apt-get update && apt-get install -y \
    tini
# Tini is now available at /usr/bin/tini

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8020

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD [ "python", "-m", "sanic", "server.app", "--host=0.0.0.0", "--port=8020", "--workers=2" ]