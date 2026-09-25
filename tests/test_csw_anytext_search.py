"""Functional tests for full text search (AnyText) on the Geoplateforme CSW
service (https://data.geopf.fr/csw).

These describe what a *working* service should do. `CswFullTextSearchTests`
currently FAILS: it documents the bug reported in
https://github.com/mborne/gpf-catalogue/issues/7 (see docs/bug-filter.md for
the full write-up). A red run here means the bug is still present; a green
run means IGN has fixed it.

They hit the *live* external service on purpose (there is nothing to mock:
the bug lives in that service). Run with:

    python3 -m unittest discover -s tests -v

or, with uv:

    uv run pytest -v

Set CSW_URL to point at another CSW endpoint if needed.
"""

import re
import unittest

from csw_client import (
    get_capabilities,
    get_records_kvp,
    post_get_records_property_is_equal_to,
    post_get_records_property_is_like,
)

EXCEPTION_REPORT_RE = re.compile(r"<ows:ExceptionReport\b")
NUMBER_MATCHED_RE = re.compile(r'numberOfRecordsMatched="(\d+)"')

KNOWN_ISSUE = (
    "known issue: see docs/bug-filter.md and "
    "https://github.com/mborne/gpf-catalogue/issues/7"
)


class CswBaselineTests(unittest.TestCase):
    """Sanity checks: confirm the service is up and that "normal" queries
    work, so that a failure in CswFullTextSearchTests below can't be blamed
    on a bad request or a network hiccup instead of the server."""

    def test_get_capabilities_is_reachable(self):
        response = get_capabilities()
        self.assertEqual(response.status, 200)
        self.assertIn("Capabilities", response.body)

    def test_getrecords_kvp_without_constraint_returns_results(self):
        response = get_records_kvp(constraint=None)
        self.assertEqual(response.status, 200)
        self.assertNotRegex(response.body, EXCEPTION_REPORT_RE)

    def test_post_property_is_equal_to_anytext_returns_results(self):
        response = post_get_records_property_is_equal_to(literal="pont")
        self.assertEqual(response.status, 200)
        self.assertNotRegex(response.body, EXCEPTION_REPORT_RE)
        self.assertRegex(response.body, NUMBER_MATCHED_RE)

    def test_post_property_is_like_without_wildcard_returns_results(self):
        """PropertyIsLike works fine as long as the literal has no '%'."""
        response = post_get_records_property_is_like(literal="pont")
        self.assertEqual(response.status, 200)
        self.assertNotRegex(response.body, EXCEPTION_REPORT_RE)


class CswFullTextSearchTests(unittest.TestCase):
    """Expected behaviour of full text search over AnyText: a PropertyIsLike
    filter using the '%' wildcard should return matching records with a
    normal csw:GetRecordsResponse, whichever way the request is sent
    (POST/XML filter or GET/KVP CQL_TEXT constraint).

    As of 2026-09-25, every test below fails against
    https://data.geopf.fr/csw -- see docs/bug-filter.md.
    """

    def test_property_is_like_with_wildcard_returns_matching_records(self):
        # This is the exact query from the original report:
        # constraint=AnyText like '%pont%'
        response = post_get_records_property_is_like(literal="%pont%")

        self.assertEqual(response.status, 200, KNOWN_ISSUE)
        self.assertNotRegex(response.body, EXCEPTION_REPORT_RE, KNOWN_ISSUE)
        match = NUMBER_MATCHED_RE.search(response.body)
        self.assertIsNotNone(match, KNOWN_ISSUE)
        self.assertGreaterEqual(int(match.group(1)), 1, KNOWN_ISSUE)

    def test_property_is_like_with_leading_wildcard_only_does_not_crash(self):
        response = post_get_records_property_is_like(literal="%pont")
        self.assertEqual(response.status, 200, KNOWN_ISSUE)
        self.assertNotRegex(response.body, EXCEPTION_REPORT_RE, KNOWN_ISSUE)

    def test_property_is_like_with_trailing_wildcard_only_does_not_crash(self):
        response = post_get_records_property_is_like(literal="pont%")
        self.assertEqual(response.status, 200, KNOWN_ISSUE)
        self.assertNotRegex(response.body, EXCEPTION_REPORT_RE, KNOWN_ISSUE)

    def test_property_is_like_with_wildcard_and_no_match_does_not_crash(self):
        """A query that matches nothing should return 0 results, not an
        exception -- the bug isn't specific to the word "pont"."""
        response = post_get_records_property_is_like(literal="%xyz%")
        self.assertEqual(response.status, 200, KNOWN_ISSUE)
        self.assertNotRegex(response.body, EXCEPTION_REPORT_RE, KNOWN_ISSUE)

    def test_get_kvp_cql_like_constraint_returns_results(self):
        """The GET/KVP flavour of the same query should behave the same way
        as the POST/XML one, not fail earlier with an empty HTTP 500."""
        response = get_records_kvp(constraint="AnyText like '%pont%'")
        self.assertEqual(response.status, 200, KNOWN_ISSUE)
        self.assertNotRegex(response.body, EXCEPTION_REPORT_RE, KNOWN_ISSUE)


if __name__ == "__main__":
    unittest.main()
