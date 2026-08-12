#!/usr/bin/env python3
import logging

import io
import warnings
import threading
import socketserver
from flask import Flask
from typing import NamedTuple

from werkzeug.serving import make_server

from wsgiref.simple_server import WSGIServer, WSGIRequestHandler

from tlslite.x509 import X509
from tlslite import X509CertChain
from tlslite import TLSSocketServerMixIn
from tlslite.sessioncache import SessionCache
from tlslite.utils.keyfactory import parsePEMKey
from tlslite.handshakesettings import HandshakeSettings

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.x509 import Certificate

from paths import GAME_SYNC_ROOT
from configuration import Configuration
from network.http.nas_handler import NasHandler
from network.http.pgl_handler import PglHandler
from network.http.dls_handler import DlsHandler
from entralinked.model.user.user_manager import UserManager
from utility.certificate_generator import CertificateGenerator

logger = logging.getLogger(__name__)

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=".*PKCS#12 bundle could not be parsed as DER.*"
)

class TLSRequestBodyFixMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        content_length = environ.get("CONTENT_LENGTH")
        if content_length:
            try:
                content_length = int(content_length)
            except ValueError:
                content_length = 0
        else:
            content_length = 0

        if content_length > 0:
            wsgi_input = environ.get("wsgi.input")
            if wsgi_input:
                body = b""
                remaining = content_length

                while remaining > 0:
                    chunk = wsgi_input.read(remaining)
                    if not chunk:
                        break
                    body += chunk
                    remaining -= len(chunk)

                environ["wsgi.input"] = io.BytesIO(body)
                environ["CONTENT_LENGTH"] = str(len(body))

        return self.wsgi_app(environ, start_response)

class KeyStore(NamedTuple):
    private_key: PrivateKeyTypes
    certificate: Certificate

class ThreadedWSGIServer(socketserver.ThreadingMixIn, WSGIServer):
    pass

class TLSServer(TLSSocketServerMixIn, ThreadedWSGIServer):
    allow_reuse_address = True

    def __init__(self, private_key, certificate, app):
        super().__init__(("0.0.0.0", 443), WSGIRequestHandler)
        self.privateKey = private_key
        self.certChain = certificate
        self.session_cache = SessionCache()
        self.set_app(app)

    def set_app(self, app):
        self.app = app

    def get_app(self):
        return self.app

    def handshake(self, connection):
        settings = HandshakeSettings()
        settings.minVersion = (3, 0)
        settings.maxVersion = (3, 1)
        settings.cipherNames = ["rc4"]
        settings.macNames = ["md5", "sha"]
        settings.keyExchangeNames = ["rsa"]

        connection.handshakeServer(
            privateKey=self.privateKey,
            certChain=self.certChain,
            settings=settings,
            sessionCache=self.session_cache
        )

        return True

class HttpServer:
    def __init__(self, context, port: int = 80):
        self.app = Flask(__name__)
        self.app.wsgi_app = TLSRequestBodyFixMiddleware(self.app.wsgi_app)
        self.context = context

        self.server_http  = None
        self.server_https = None
        self.thread_http  = None
        self.thread_https = None
        self.port = port

        self.app.url_map.strict_slashes = False

        self.configuration: Configuration = self.context.configuration
        self.user_manager: UserManager = self.context.user_manager

        self.nas_handler = NasHandler(self.context)
        self.pgl_handler = PglHandler(self.context)
        self.dls_handler = DlsHandler(self.context)

        self.app.register_blueprint(self.nas_handler.add_handlers())
        self.app.register_blueprint(self.pgl_handler.add_handlers())
        self.app.register_blueprint(self.dls_handler.add_handlers())

        @self.app.route("/")
        def conntest():
            return "Test", 200, {"X-Organization": "Nintendo"}

    def add_handler(self, handler):
        self.app.register_blueprint(handler)

    def create_key_store(self):
        cert_path = GAME_SYNC_ROOT / "entralinked" / "data" / "server.p12"

        if cert_path.exists():
            cert_data = cert_path.read_bytes()
        else:
            cert_data = CertificateGenerator().generate_certificate_key_store()
            cert_path.write_bytes(cert_data)

        private_key, leaf_cert, _ = pkcs12.load_key_and_certificates(cert_data, b'password')

        pem_key = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        ).decode("UTF-8")

        CertificateGenerator()
        issuer_cert = CertificateGenerator.certificate

        pem_certs = (
            leaf_cert.public_bytes(serialization.Encoding.PEM).decode("UTF-8") +
            issuer_cert.public_bytes(serialization.Encoding.PEM).decode("UTF-8")
        )

        return KeyStore(pem_key, pem_certs)

    def create_tls_server(self, key_store: KeyStore):
        private_key = parsePEMKey(key_store.private_key, private=True)

        pem_certs = key_store.certificate.strip().split("-----END CERTIFICATE-----")

        x509_list = []
        for pem in pem_certs:
            if not pem.strip():
                continue
            reconstructed_pem = pem + "-----END CERTIFICATE-----"

            cert_obj = X509()
            cert_obj.parse(reconstructed_pem)
            x509_list.append(cert_obj)

        certificate = X509CertChain(x509_list)

        return TLSServer(private_key, certificate, self.app)

    def start(self):
        if self.server_http or self.server_https:
            return True

        logger.info("Starting HTTP server ...")

        self.server_http = make_server("0.0.0.0", self.port, self.app)
        self.thread_http = threading.Thread(target=self.server_http.serve_forever, daemon=True)
        self.thread_http.start()

        logger.info("Starting HTTPS server ...")

        self.server_https = self.create_tls_server(self.create_key_store())
        self.thread_https = threading.Thread(target=self.server_https.serve_forever, daemon=True)
        self.thread_https.start()

        return True

    def stop(self):
        if (not self.server_http) and (not self.server_https):
            return True

        self.server_http.shutdown()
        self.thread_http.join()
        self.server_http = None
        self.thread_http = None

        logger.info("Stopping HTTP server ...")

        self.server_https.shutdown()
        self.thread_https.join()
        self.server_https = None
        self.thread_https = None

        logger.info("Stopping HTTPS server ...")

        return True
