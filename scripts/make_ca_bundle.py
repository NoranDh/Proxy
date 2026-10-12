"""
Write a CA bundle = certifi roots + roots trusted by the Windows certificate store.

Needed on machines where an antivirus (e.g. Avast HTTPS scanning) re-signs HTTPS
traffic: Python only trusts certifi, so calls to OpenAI fail with
CERTIFICATE_VERIFY_FAILED. Point SSL_CERT_FILE at the bundle this writes.

Usage: python scripts/make_ca_bundle.py certs/ca-bundle.pem
"""
import ssl
import sys
from pathlib import Path

import certifi

out = Path(sys.argv[1])
out.parent.mkdir(parents=True, exist_ok=True)

pem = Path(certifi.where()).read_text(encoding="utf-8")
seen = set()
for store in ("ROOT", "CA"):
    for der, enc, trust in ssl.enum_certificates(store):
        if enc != "x509_asn" or der in seen:
            continue
        seen.add(der)
        pem += "\n" + ssl.DER_cert_to_PEM_cert(der)

out.write_text(pem, encoding="utf-8")
print(f"Wrote {out} ({len(seen)} Windows-store certificates added)")
