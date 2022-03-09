FROM python:3.10.2-slim-bullseye

RUN rm -rf ArkPlannerWeb

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8020

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD [ "python", "-m", "sanic", "server.app", "--host=127.0.0.1", "--port=8020", "--workers=4" ]