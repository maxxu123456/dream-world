# Dream World self-host image, fully self-contained.
# The whole upstream server and its assets are vendored in ./server, including
# the pre-patched Flash files, so no upstream assets are fetched at run time.
#
# Runs both servers:
#   - Game Sync server (DNS 53/udp, HTTP 80, TLS 443, GameSpy 29900/tcp) for a DS
#   - Dream World website (8080) for the Flash game

FROM python:3.12-slim

WORKDIR /opt/server
COPY server/ /opt/server/

RUN python3 -m pip install --no-cache-dir \
      -r requirements.txt \
      -r game_sync_server/requirements.txt

COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/healthcheck.py /healthcheck.py
RUN chmod +x /entrypoint.sh

# 53/udp DNS, 80 + 443 Game Sync HTTP/TLS, 29900/tcp GameSpy login, 8080 site.
EXPOSE 53/udp 80 443 29900 8080

# Game Sync must be healthy before the first tuck-in; the website intentionally
# starts only after the DS has uploaded usable player data.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=5 \
  CMD ["python3", "/healthcheck.py"]

ENTRYPOINT ["/entrypoint.sh"]
