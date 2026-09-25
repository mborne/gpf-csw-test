"""Minimal CSW 2.0.2 client used by the functional tests.

Stdlib only (urllib + string templating) on purpose: these tests exercise a
live, external service (the Geoplateforme CSW at data.geopf.fr) and must stay
runnable without installing anything.
"""

from __future__ import annotations

import os
import urllib.parse
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path

CSW_URL = os.environ.get("CSW_URL", "https://data.geopf.fr/csw")
TIMEOUT = float(os.environ.get("CSW_TIMEOUT", "30"))

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@dataclass
class CswResponse:
    status: int
    body: str


def _request(method: str, url: str, data: bytes | None = None, headers: dict | None = None) -> CswResponse:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return CswResponse(status=resp.status, body=resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        # An OWS exception can be carried by a non-2xx status too (seen with
        # the GET/KVP flavour of this bug), so we still return the body.
        return CswResponse(status=exc.code, body=exc.read().decode("utf-8", errors="replace"))


def get_records_kvp(constraint: str | None = None, extra_params: dict | None = None) -> CswResponse:
    """GetRecords over GET/KVP, optionally with a CQL_TEXT constraint."""
    params = {
        "SERVICE": "CSW",
        "VERSION": "2.0.2",
        "REQUEST": "GetRecords",
        "TYPENAMES": "csw:Record",
        "RESULTTYPE": "results",
        "ELEMENTSETNAME": "brief",
    }
    if constraint is not None:
        params["CONSTRAINTLANGUAGE"] = "CQL_TEXT"
        params["CONSTRAINT_LANGUAGE_VERSION"] = "1.1.0"
        params["CONSTRAINT"] = constraint
    params.update(extra_params or {})
    url = f"{CSW_URL}?{urllib.parse.urlencode(params)}"
    return _request("GET", url)


def get_capabilities() -> CswResponse:
    return get_records_kvp(constraint=None, extra_params={"REQUEST": "GetCapabilities"})


def _render_fixture(name: str, **kwargs) -> bytes:
    template = (FIXTURES_DIR / name).read_text(encoding="utf-8")
    return template.format(**kwargs).encode("utf-8")


def post_get_records_property_is_like(literal: str, wildcard: str = "%") -> CswResponse:
    """GetRecords over POST/XML with an ogc:Filter PropertyIsLike on AnyText."""
    body = _render_fixture("getrecords_property_is_like.xml.tpl", literal=literal, wildcard=wildcard)
    return _request("POST", CSW_URL, data=body, headers={"Content-Type": "application/xml"})


def post_get_records_property_is_equal_to(literal: str) -> CswResponse:
    """GetRecords over POST/XML with an ogc:Filter PropertyIsEqualTo on AnyText."""
    body = _render_fixture("getrecords_property_is_equal_to.xml.tpl", literal=literal)
    return _request("POST", CSW_URL, data=body, headers={"Content-Type": "application/xml"})
