"""The committed sample is a fictional mixed report, not a live scan."""

import json
import pathlib
import unittest

from securecheck.constants import DISCLAIMER, SCHEMA

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sample-securecheck-report.json"


class SampleReportTests(unittest.TestCase):
    def test_sample_is_a_fictional_mixed_report(self):
        report = json.loads(SAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["disclaimer"], DISCLAIMER)
        self.assertEqual(report["domain"], "example-smme.co.za")
        self.assertIn("Fictional sample", report["sample_note"])
        self.assertIn("No domain was contacted", report["sample_note"])
        self.assertIn("does not prove ownership", report["authorisation_note"])
        statuses = {item["id"]: item["status"] for item in report["checks"]}
        self.assertEqual(
            statuses,
            {
                "tls": "ok",
                "headers": "attention",
                "privacy": "missing",
                "email": "attention",
                "admin_paths": "attention",
            },
        )
        blob = json.dumps(report)
        self.assertIn("HEAD /wp-admin returned 200.", blob)
        self.assertIn("p=none", blob)
        self.assertIn("Content-Security-Policy", blob)
        self.assertNotIn("critical vulnerability", blob.lower())
