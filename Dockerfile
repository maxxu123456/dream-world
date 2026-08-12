# Dream World self-host image.
# Runs both servers from minibug1021/dreamworld-reawakened:
#   - Game Sync server (DNS 53/udp, HTTP 80, TLS 443) for a physical DS
#   - Dream World website (8080) for the Flash game
#
# Build:  docker build -t dream-world .
# Run:    see README for the one-line docker run command.

FROM python:3.12-slim

# git to clone the server, a JRE for the JPEXS Flash patcher the web server uses.
RUN apt-get update \
 && apt-get install -y --no-install-recommends git default-jre-headless \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

# Pin nothing: the upstream project moves fast and expects to be run from HEAD.
RUN git clone --recursive https://github.com/minibug1021/dreamworld-reawakened.git server

RUN python3 -m pip install --no-cache-dir \
      -r server/requirements.txt \
      -r server/game_sync_server/requirements.txt

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 53/udp DNS, 80 + 443 Game Sync HTTP/TLS, 8080 Dream World site
EXPOSE 53/udp 80 443 8080

ENTRYPOINT ["/entrypoint.sh"]
