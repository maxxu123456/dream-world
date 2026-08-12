#!/usr/bin/env python3
import zlib
import base64
from datetime import datetime
from datetime import timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import pkcs12, load_der_private_key, BestAvailableEncryption
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key

class CertificateGenerator:

    issuer_certificate_string = "eNp9lNuyqjgQhu95irm3dokoHi4TEk4aNBBAuAPRIOBZCPL0G5e1Zq+ZqZpcdqr/Tvf/dX796g/EhuX8pWGXWbqlAYbfwV8SsSw0ZZoGRksOhAUBt6BRAAfy8paXR2MhZAiorwOkwQLhFQGlAUY+hjnRgoC0Eu6AC7kT9JlMq7J8p+TX9JTJqTJpLQT2n7sL02X1mp7dKj25jWUsThbWn/HWvkqRgrkXqgWhQmg8QgGlKyycNZNxqyPgfQQI034KYAcSzxIWiGxpeYmtvNk5gJZQz50i8mGdKrhOT1WdGUEdG/M6UhZPAidbxIBC0K4lBVZIR7t1cNlKiJF3UDjo76DgMW21Dtif6hEDVcCISwSmXy+0sLhuo61zSUL1LGXGoiYuEOjzfBOLzItD95kqakk8LEzxFV/iNl/3CXIcqmX6gk18hDANg5eUhE5u4aqOXpNW70Dw3TOqsmviwXUgE+6bdhNroP3u+2fb0v/2bRkHAmRD826GZ6VjRPHbUgAmhvO29UiXUOIUxaq8cRfEcrHijeaFOyPquizn6UQE7fi1TXYvmBeHyPM2bmovzVXhogl7ni+zk51OJPNg7LEiKy5bdA8gBlNTni6aod9MydZdDTS+3AB9tqvjKfNJ4pbyKps14fO4qZMiDqJaKumJE81SqqOjWc0Qbs8g2bvuphuMcwzY4Kjfh+tNFWwYXy9ojxYF8DKxIOt6ev2HkLS3Na7MILAEQOABecXzksO8yTVAZWy2UcbGsEorhzENmr0L1e6k925QTpXehcyoTm8nMsMX5kdsDWGE9dWRdObZEVSFNwXe6krfkNnwah6TrB+u+nbL9AiWeIoFT6ZAN59bv5u3dzNr54fRUuUL9HCCgMZD7xIZ3tUyNn0iIfQhtA9QBhZ2IPkdZqTf1PeGaZAsA0XvEqOq47HbpAXmPcKfu5xs2R+beapEnIajStqdqiLyoJ2eSIsQWH5AejAgqxvKsE+g9SXQY7T6KdCPp7UKwKWfe69RHGLFyamhNpGn1n/QVYtUUfqhAuF85nSA2kSsELhJF+3I7UtUJqYr79ClWSnOK9X+nSw3/6B0bD++CZW+EYUfRCEwwmJiGDf3tDvYLpqfj+6TneFw2ewOxmIyw3d4HFGrLx9yvk6Q5HpTlSgvbgO22k/vo0N43dO7utgfn/e4Xo9alIAktnewGqj5nRm75H7iaLEJBo983jJdugeXdp6y5X6sDmaDmyw/p91TKPrKmD4ebbTY38D5WT67fONjW/X1OLNHg46GYYZa6etbxQ7671f7GypgwnI="
    issuer_private_key_string = "eNod0Em2a0AAANAFGRBNYVgK0QalfWaIPproZfX/nH+XcG1dR4mnSxCaUu3JKUe5WLR1rND+Q+gwb3NO3ws5e0YXcydZcUtNV/35votzw9SsDstssI0TPxg5q1XPUqEpGgfib4UnATQKiAcZHsBOsEWg2nShyhd7CoLQznBPWW/+iLfW3bMujf723htqG+n0p30h/SClZIRZibH7I5hGgQHRqgvpuJ/IDWpH9HQZelCC0xPK8uXZ87jcwvAl64ufS7EqDw4HZfb6fi81sZvq02Xx84aBxLRvYg+ASqvaLsqPb9CrjrxW0koV02lUS9bWCSuQctd+t4w/3BwIjy0ZUdeOqEKzl95s4Sgcw66TQ55RWT5f78KalHncOiUv2Gk9VoV8tHw7sYC9RsH3m2xH6QeAFirI8+Qff3Lmmgrp3rqZbymH8skaH7Cku2uPPCe0xn2oP3uM7pOqtbvUKFyUyZ9tKqj7StW5zJ2UgvpYMeuc7INHAohV2CuQM0H0TU3f/wzd42bWlkx50Fc5eWTmBGCsMe95I05TreXUNFNLiisySELsXkZC8JNhR3KaLsmrWI4fa6iNpzrP1TOg/6StsTjERretEDEB7gZ28+mhQAs7T6MzgI1W5a+hUvdFVGB43qZr5eOJ07g/FVIZ7xCYsGlcooISBawqUerOMyT4ivKwCC8XMn0wDNXSVb/+FtVXuzmmoQKx6C2OiW921ctlpI7+L7QPxl9RWjM8QsdL544sSHNmIW+3mVEWW8H9+3/s59kaKT97p4oFm+9Jc1hKrMu5/lhDrSe0QqBnwRnZx0jKRqdxHG7Z6lflnu0SfxCFKIwe2laBvNJzVHPlTayy/g/JGQy0"
    
    certificate = None
    private_key = None

    def __init__(self):
        if CertificateGenerator.certificate is None:
            certificate_decoded = self.decode_and_deflate(CertificateGenerator.issuer_certificate_string)
            private_key_decoded = self.decode_and_deflate(CertificateGenerator.issuer_private_key_string)

            CertificateGenerator.certificate = x509.load_pem_x509_certificate(certificate_decoded)
            CertificateGenerator.private_key = load_der_private_key(base64.b64decode(private_key_decoded), None)

    def generate_certificate_key_store(self):
        rsa_key = generate_private_key(65537, 1024)

        public_key = rsa_key.public_key()

        not_before = datetime.now()
        not_after  = datetime.now() + timedelta(weeks=2600)

        cert_builder = x509.CertificateBuilder() \
                        .issuer_name(CertificateGenerator.certificate.subject) \
                        .serial_number(1) \
                        .not_valid_before(not_before) \
                        .not_valid_after(not_after) \
                        .subject_name(x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, "*.*.*")])) \
                        .public_key(public_key) \
                        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(CertificateGenerator.certificate.public_key()), False) \
                        .sign(CertificateGenerator.private_key, hashes.SHA1())

        return pkcs12.serialize_key_and_certificates(b'server', rsa_key, cert_builder, [CertificateGenerator.certificate], BestAvailableEncryption(b'password'))

    def decode_and_deflate(self, b64_str: str):
        decoded_str = base64.b64decode(b64_str)
        return zlib.decompress(decoded_str)