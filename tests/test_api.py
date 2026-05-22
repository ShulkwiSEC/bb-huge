import os
import tempfile
import unittest
import warnings

from app import create_app, db
from sqlalchemy.exc import LegacyAPIWarning

warnings.filterwarnings("ignore", category=LegacyAPIWarning)


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    DEV_KEY = "test-dev-key"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "txt", "md", "xml", "json", "html", "zip"}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_NAME = "bb_huge_test"


class V2ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = os.path.join(self.tmpdir.name, "test.db")
        upload_dir = os.path.join(self.tmpdir.name, "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        class Config(TestConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
            UPLOAD_FOLDER = upload_dir

        self.app = create_app(Config)
        self.client = self.app.test_client()
        self.headers = {"X-Dev-Key": Config.DEV_KEY, "Content-Type": "application/json"}

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.tmpdir.cleanup()

    def _post_json(self, path, payload):
        return self.client.post(path, json=payload, headers=self.headers)

    def _patch_json(self, path, payload):
        return self.client.patch(path, json=payload, headers=self.headers)

    def _put_json(self, path, payload):
        return self.client.put(path, json=payload, headers=self.headers)

    def _get(self, path):
        return self.client.get(path, headers=self.headers)

    def test_program_brief_includes_new_entities(self):
        program = self._post_json("/api/v1/programs", {"name": "Acme", "platform": "private"}).get_json()
        pid = program["id"]
        self._put_json(f"/api/v1/programs/{pid}/context", {"data": {"auth": "cookie"}})
        self._post_json(f"/api/v1/programs/{pid}/observations", {"title": "Odd redirect", "category": "auth"})
        self._post_json(f"/api/v1/programs/{pid}/hypotheses", {"title": "Possible auth bypass"})

        res = self._get(f"/api/v1/programs/{pid}/brief")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["program"]["name"], "Acme")
        self.assertEqual(data["counts"]["open_observations"], 1)
        self.assertEqual(data["counts"]["open_hypotheses"], 1)
        self.assertEqual(data["target_context"]["data"]["auth"], "cookie")

    def test_observation_to_hypothesis_to_finding_promotion_flow(self):
        program = self._post_json("/api/v1/programs", {"name": "Target"}).get_json()
        pid = program["id"]
        observation = self._post_json(
            f"/api/v1/programs/{pid}/observations",
            {
                "title": "Profile ID changes leak data",
                "summary": "Changing numeric id changes returned profile.",
                "category": "access_control",
                "confidence": "medium",
            },
        ).get_json()

        promoted_hypothesis = self._post_json(
            f"/api/v1/observations/{observation['id']}/promote",
            {
                "weakness_hint": "IDOR",
                "cwe": "CWE-639",
                "severity_hint": "high",
                "attack_path": "Swap profile ids across accounts",
                "impact_hypothesis": "Read another user's data",
            },
        )
        self.assertEqual(promoted_hypothesis.status_code, 201)
        hypothesis = promoted_hypothesis.get_json()["hypothesis"]
        self.assertEqual(promoted_hypothesis.get_json()["observation"]["status"], "promoted")

        promoted_finding = self._post_json(
            f"/api/v1/hypotheses/{hypothesis['id']}/promote",
            {
                "target": "api.example.test",
                "severity": "high",
                "status": "confirmed",
                "confidence": "high",
                "description": "Confirmed across two accounts",
                "poc": "1. Login as A\n2. Request B's profile",
            },
        )
        self.assertEqual(promoted_finding.status_code, 201)
        finding = promoted_finding.get_json()["finding"]
        self.assertEqual(finding["hypothesis_id"], hypothesis["id"])
        self.assertEqual(promoted_finding.get_json()["hypothesis"]["status"], "promoted")

    def test_similarity_and_report_pack(self):
        program = self._post_json("/api/v1/programs", {"name": "Example Program"}).get_json()
        pid = program["id"]
        finding = self._post_json(
            "/api/v1/findings",
            {
                "program_id": pid,
                "title": "IDOR in profile endpoint",
                "target": "api.example.test",
                "severity": "high",
                "status": "confirmed",
                "cwe": "CWE-639",
                "description": "Changing profile id reveals another user's profile.",
                "poc": "Swap ids",
            },
        ).get_json()

        evidence = self._post_json(
            "/api/v1/evidence",
            {
                "program_id": pid,
                "finding_id": finding["id"],
                "evidence_type": "http_exchange",
                "title": "GET /api/profile/42",
                "request_method": "GET",
                "request_url": "https://api.example.test/api/profile/42",
                "response_status": 200,
                "response_body_text": '{"id":42}',
            },
        )
        self.assertEqual(evidence.status_code, 201)

        similarity = self._post_json(
            "/api/v1/similarity/check",
            {
                "program_id": pid,
                "title": "IDOR profile endpoint",
                "target": "api.example.test",
                "cwe": "CWE-639",
                "description": "profile id reveals another user profile",
            },
        )
        self.assertEqual(similarity.status_code, 200)
        similarity_json = similarity.get_json()
        self.assertTrue(similarity_json["exact_matches"] or similarity_json["likely_duplicates"])

        report_pack = self._get(f"/api/v1/findings/{finding['id']}/report-pack")
        self.assertEqual(report_pack.status_code, 200)
        report_json = report_pack.get_json()
        self.assertEqual(report_json["finding"]["id"], finding["id"])
        self.assertEqual(len(report_json["evidence_summary"]["finding_evidence"]), 1)


if __name__ == "__main__":
    unittest.main()
