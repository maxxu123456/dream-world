#!/usr/bin/env python3
import os
import sys
import json
import time
import socket
import signal
import logging
from pathlib import Path
from dataclasses import asdict
from dataclasses import dataclass

ROOT_DIR = Path(__file__).resolve().parent

project_root = ROOT_DIR / "entralinked"
sys.path.insert(0, str(project_root))

from configuration import Configuration
from model.dlc.dlc import DlcList
from model.user.user_manager import UserManager
from model.player.player_manager import PlayerManager

from network.dns.server import DnsServer
from network.http.http_server import HttpServer
from network.gamespy.server import GameSpyServer

from utility.db_manager import db

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

@dataclass
class Context:
    configuration: Configuration
    user_manager: UserManager
    player_manager: PlayerManager
    dlc_list: DlcList

class GameSync:
    def __init__(self):
        begin_time = int(time.time() * 1000)
        self.initialized = False

        self.configuration = self._load_config_file()
        logger.info(f"Using configuration {self.configuration}")

        self.context = Context(self.configuration, UserManager(), PlayerManager(), DlcList())

        host_address = None
        host_name = getattr(self.configuration, 'host_name', 'local')

        if host_name in ("local", "localhost"):
            host_address = self._get_local_host()
        else:
            try:
                host_address = socket.gethostbyname(host_name)
            except socket.gaierror as e:
                host_address = self._get_local_host()
                logger.error(f"Could not resolve host name - falling back to {host_address} ", exc_info=e)

        if host_address is None:
            logger.critical("ABORTING - hostAddress is null!")
            sys.exit(1)

        self.host_address = host_address

        self.dns_server = DnsServer(self.host_address)
        self.gamespy_server = GameSpyServer(self.context)
        self.http_server = HttpServer(self.context)

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        started = self.start_servers()

        if started:
            time_taken = int(time.time() * 1000) - begin_time
            logger.info(f"Startup complete! Took a total of {time_taken} milliseconds")
            logger.info(f"Configure your DS to use the following DNS server: {self.host_address}")
        else:
            self.stop_servers()

        self.initialized = True

    def _get_local_host(self) -> str:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"

    def _load_config_file(self) -> Configuration:
        logger.info("Loading configuration ...")
        configuration = None

        try:
            config_file = "config.json"

            if not os.path.exists(config_file):
                logger.info("No configuration file exists - default configuration will be used")
                configuration = Configuration()
            else:
                with open(config_file, 'r', encoding="UTF-8") as f:
                    data = json.load(f)
                    configuration = Configuration(**data)

            with open(config_file, 'w', encoding="UTF-8") as f:
                json.dump(asdict(configuration), f, indent=4)

        except Exception as e:
            logger.error("Could not load configuration - default configuration will be used", exc_info=e)
            configuration = Configuration()

        return configuration

    def start_servers(self) -> bool:
        logger.info("Starting servers ...")
        try:
            self.dns_server.start()
            self.http_server.start()
            self.gamespy_server.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start servers: {e}")
            return False

    def stop_servers(self):
        logger.info("Stopping servers ...")

        if self.http_server:
            try:
                self.http_server.stop()
            except Exception:
                pass

        if self.gamespy_server:
            try:
                self.gamespy_server.stop()
            except Exception:
                pass

        if self.dns_server:
            try:
                self.dns_server.stop()
            except Exception:
                pass

        db.close()

    def run_forever(self):
        if not self.initialized:
            return

        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            pass

    def _signal_handler(self, sig, frame):
        self.stop_servers()
        sys.exit(0)

if __name__ == "__main__":
    app = GameSync()
    app.run_forever()
