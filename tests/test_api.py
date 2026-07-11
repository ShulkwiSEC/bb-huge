import os
import tempfile
import unittest
import warnings
from unittest.mock import patch

from app import create_app, db
from app.models import ReconJob
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

    def _login(self):
        return self.client.post("/login", data={"dev_key": self.app.config["DEV_KEY"]}, follow_redirects=True)

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

    def test_share_finding(self):
        # Create a program and finding
        program = self._post_json("/api/v1/programs", {"name": "Test Share Prog"}).get_json()
        pid = program["id"]
        finding = self._post_json(
            "/api/v1/findings",
            {
                "program_id": pid,
                "title": "SQL Injection in Search",
                "target": "api.example.test",
                "severity": "critical",
                "status": "confirmed",
                "description": "Exploit with sqlmap",
                "poc": "sqlmap -u ...",
            },
        ).get_json()
        fid = finding["id"]

        # Authenticate session
        with self.client.session_transaction() as sess:
            sess["authenticated"] = True

        # Mock privatebinapi.send
        from unittest.mock import patch
        mock_response = {
            "full_url": "https://privatebin.net/?testslug#key"
        }

        with patch("privatebinapi.send", return_value=mock_response) as mock_send:
            res = self.client.post(
                f"/findings/{fid}/share",
                data={
                    "passphrase": "test-password",
                    "expiration": "1week",
                    "burn_after_reading": "false"
                }
            )
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data["success"])
            self.assertEqual(data["url"], "https://privatebin.net/?testslug#key")
            self.assertEqual(data["passphrase"], "test-password")

            # Check that mock_send was called with the right data
            mock_send.assert_called_once_with(
                "https://privatebin.net/",
                text=mock_send.call_args[1]["text"],
                password="test-password",
                expiration="1week",
                formatting="markdown",
                burn_after_reading=False
            )
            self.assertIn("# Security Research Report — SQL Injection in Search", mock_send.call_args[1]["text"])

    def test_work_queue_next_claim_release_and_drop_off(self):
        program = self._post_json("/api/v1/programs", {"name": "Queue Co"}).get_json()
        pid = program["id"]
        hyp = self._post_json(
            f"/api/v1/programs/{pid}/hypotheses",
            {"title": "Possible SSRF via webhook URL"},
        ).get_json()

        # Not claimed yet -> shows up as next
        res = self._get(f"/api/v1/work-queue/next?kind=validate&program_id={pid}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["item"]["id"], hyp["id"])

        # Claim it
        claim = self._post_json(
            "/api/v1/work-queue/claim",
            {"kind": "validate", "id": hyp["id"], "claimed_by": "bountyforge:validator"},
        )
        self.assertEqual(claim.status_code, 200)
        self.assertEqual(claim.get_json()["item"]["claimed_by"], "bountyforge:validator")

        # No longer claimable -> next returns null
        res = self._get(f"/api/v1/work-queue/next?kind=validate&program_id={pid}")
        self.assertIsNone(res.get_json()["item"])

        # Double-claim is rejected
        dup = self._post_json(
            "/api/v1/work-queue/claim",
            {"kind": "validate", "id": hyp["id"], "claimed_by": "someone-else"},
        )
        self.assertEqual(dup.status_code, 409)

        # Claiming a nonexistent id 404s
        missing = self._post_json(
            "/api/v1/work-queue/claim",
            {"kind": "validate", "id": 999999, "claimed_by": "x"},
        )
        self.assertEqual(missing.status_code, 404)

        # Release puts it back in the pool
        release = self._post_json("/api/v1/work-queue/release", {"kind": "validate", "id": hyp["id"]})
        self.assertEqual(release.status_code, 200)
        self.assertIsNone(release.get_json()["item"]["claimed_by"])

        res = self._get(f"/api/v1/work-queue/next?kind=validate&program_id={pid}")
        self.assertEqual(res.get_json()["item"]["id"], hyp["id"])

        # Promoting moves status out of the ready-filter -> drops off the queue
        promote = self._post_json(
            f"/api/v1/hypotheses/{hyp['id']}/promote",
            {"target": "webhook.example.test", "severity": "high", "status": "confirmed"},
        )
        self.assertEqual(promote.status_code, 201)

        res = self._get(f"/api/v1/work-queue/next?kind=validate&program_id={pid}")
        self.assertIsNone(res.get_json()["item"])

    def test_work_queue_invalid_kind_rejected(self):
        res = self._get("/api/v1/work-queue/next?kind=bogus")
        self.assertEqual(res.status_code, 400)

    def test_session_save_upserts_and_redacts_by_default(self):
        program = self._post_json("/api/v1/programs", {"name": "Session Co"}).get_json()
        pid = program["id"]

        save = self._post_json(
            f"/api/v1/programs/{pid}/sessions",
            {
                "label": "user_a",
                "base_url": "https://app.example.test",
                "auth_type": "cookie",
                "cookies": {"session": "abc123"},
                "headers": {},
                "captured_by": "bb-import-har",
            },
        )
        self.assertEqual(save.status_code, 201)
        sid = save.get_json()["id"]
        self.assertEqual(save.get_json()["cookies"], {"session": "abc123"})

        # Default list redacts secrets
        listed = self._get(f"/api/v1/programs/{pid}/sessions")
        self.assertEqual(listed.status_code, 200)
        row = listed.get_json()[0]
        self.assertNotIn("cookies", row)
        self.assertNotIn("headers", row)

        # include_secret=1 reveals them
        listed_secret = self._get(f"/api/v1/programs/{pid}/sessions?include_secret=1")
        self.assertEqual(listed_secret.get_json()[0]["cookies"], {"session": "abc123"})

        # Re-saving the same label upserts in place (same id, not a new row)
        resave = self._post_json(
            f"/api/v1/programs/{pid}/sessions",
            {"label": "user_a", "cookies": {"session": "refreshed456"}},
        )
        self.assertEqual(resave.status_code, 201)
        self.assertEqual(resave.get_json()["id"], sid)
        all_sessions = self._get(f"/api/v1/programs/{pid}/sessions").get_json()
        self.assertEqual(len(all_sessions), 1)

    def test_session_active_lookup_is_per_label(self):
        program = self._post_json("/api/v1/programs", {"name": "Multi Account Co"}).get_json()
        pid = program["id"]
        self._post_json(f"/api/v1/programs/{pid}/sessions", {"label": "user_a", "cookies": {"session": "a-token"}})
        self._post_json(f"/api/v1/programs/{pid}/sessions", {"label": "user_b", "cookies": {"session": "b-token"}})

        res_a = self._get(f"/api/v1/programs/{pid}/sessions/active?label=user_a")
        self.assertEqual(res_a.status_code, 200)
        self.assertEqual(res_a.get_json()["cookies"], {"session": "a-token"})

        res_b = self._get(f"/api/v1/programs/{pid}/sessions/active?label=user_b")
        self.assertEqual(res_b.get_json()["cookies"], {"session": "b-token"})

        missing = self._get(f"/api/v1/programs/{pid}/sessions/active?label=nonexistent")
        self.assertEqual(missing.status_code, 404)

    def test_session_update_marks_invalid(self):
        program = self._post_json("/api/v1/programs", {"name": "Expiry Co"}).get_json()
        pid = program["id"]
        save = self._post_json(f"/api/v1/programs/{pid}/sessions", {"label": "default", "cookies": {"session": "x"}})
        sid = save.get_json()["id"]

        update = self._patch_json(f"/api/v1/sessions/{sid}", {"status": "invalid"})
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.get_json()["status"], "invalid")

        fetched = self._get(f"/api/v1/programs/{pid}/sessions/active?label=default")
        self.assertEqual(fetched.get_json()["status"], "invalid")

    def test_recon_batch_import_and_duplicate_skip(self):
        program = self._post_json("/api/v1/programs", {"name": "Recon Co"}).get_json()
        pid = program["id"]

        first = self._post_json(
            f"/api/v1/programs/{pid}/recon/batch",
            {"entries": [
                {"category": "subdomain", "value": "a.example.test", "source": "subfinder"},
                {"category": "subdomain", "value": "b.example.test", "source": "subfinder"},
                {"category": "subdomain", "value": ""},  # invalid -> error
            ]},
        )
        self.assertEqual(first.status_code, 201)
        body = first.get_json()
        self.assertEqual(body["total_created"], 2)
        self.assertEqual(body["total_errors"], 1)

        # Re-importing the same two values skips them as duplicates
        second = self._post_json(
            f"/api/v1/programs/{pid}/recon/batch",
            {"entries": [
                {"category": "subdomain", "value": "a.example.test"},
                {"category": "subdomain", "value": "c.example.test"},
            ]},
        )
        self.assertEqual(second.get_json()["total_created"], 1)
        self.assertEqual(second.get_json()["total_skipped_duplicates"], 1)

    def test_endpoints_batch_auto_creates_asset_and_skips_duplicates(self):
        program = self._post_json("/api/v1/programs", {"name": "Endpoint Co"}).get_json()
        pid = program["id"]

        first = self._post_json(
            f"/api/v1/programs/{pid}/endpoints/batch",
            {"endpoints": [
                {"identifier": "api.example.test", "path": "/v1/users", "method": "GET"},
                {"identifier": "api.example.test", "path": "/v1/orders", "method": "POST"},
            ]},
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.get_json()["total_created"], 2)

        # The asset was auto-created
        assets = self._get(f"/api/v1/programs/{pid}/assets").get_json()
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0]["identifier"], "api.example.test")
        self.assertEqual(assets[0]["kind"], "subdomain")

        # Re-importing the same (asset, method, path) is skipped
        second = self._post_json(
            f"/api/v1/programs/{pid}/endpoints/batch",
            {"endpoints": [{"identifier": "api.example.test", "path": "/v1/users", "method": "GET"}]},
        )
        self.assertEqual(second.get_json()["total_skipped_duplicates"], 1)

        # Cross-asset search finds it
        search = self._get(f"/api/v1/programs/{pid}/endpoints/search?q=orders")
        self.assertEqual(len(search.get_json()), 1)
        self.assertEqual(search.get_json()[0]["path"], "/v1/orders")

    def test_recon_summary_counts(self):
        program = self._post_json("/api/v1/programs", {"name": "Summary Co"}).get_json()
        pid = program["id"]
        self._post_json(
            f"/api/v1/programs/{pid}/recon/batch",
            {"entries": [
                {"category": "subdomain", "value": "x.example.test"},
                {"category": "subdomain", "value": "y.example.test"},
                {"category": "technology", "value": "React"},
            ]},
        )
        self._post_json(
            f"/api/v1/programs/{pid}/endpoints/batch",
            {"endpoints": [{"identifier": "x.example.test", "path": "/a"}]},
        )

        summary = self._get(f"/api/v1/programs/{pid}/recon/summary").get_json()
        self.assertEqual(summary["recon_by_category"]["subdomain"], 2)
        self.assertEqual(summary["recon_by_category"]["technology"], 1)
        self.assertEqual(summary["recon_total"], 3)
        self.assertEqual(summary["assets_total"], 1)
        self.assertEqual(summary["endpoints_total"], 1)

    def test_list_endpoints_and_assets_support_search_and_pagination(self):
        program = self._post_json("/api/v1/programs", {"name": "Paginate Co"}).get_json()
        pid = program["id"]
        self._post_json(
            f"/api/v1/programs/{pid}/endpoints/batch",
            {"endpoints": [
                {"identifier": "host1.example.test", "path": "/admin"},
                {"identifier": "host1.example.test", "path": "/login"},
            ]},
        )
        asset_id = self._get(f"/api/v1/programs/{pid}/assets").get_json()[0]["id"]

        filtered = self._get(f"/api/v1/assets/{asset_id}/endpoints?q=admin")
        self.assertEqual(len(filtered.get_json()), 1)
        self.assertEqual(filtered.get_json()[0]["path"], "/admin")

        limited = self._get(f"/api/v1/assets/{asset_id}/endpoints?limit=1")
        self.assertEqual(len(limited.get_json()), 1)

    def test_restart_scripts_rejects_wrong_dev_key(self):
        self._login()
        program = self._post_json("/api/v1/programs", {"name": "Restart Co"}).get_json()
        pid = program["id"]

        res = self.client.post(
            f"/programs/{pid}/scripts/restart",
            data={"confirm_key": "wrong-key"},
            follow_redirects=True,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Incorrect key", res.data)
        with self.app.app_context():
            self.assertEqual(ReconJob.query.filter_by(program_id=pid).count(), 0)

    def test_restart_scripts_blocks_while_already_running(self):
        self._login()
        program = self._post_json("/api/v1/programs", {"name": "Busy Co"}).get_json()
        pid = program["id"]
        with self.app.app_context():
            db.session.add(ReconJob(program_id=pid, status="running", triggered_by="test"))
            db.session.commit()

        res = self.client.post(
            f"/programs/{pid}/scripts/restart",
            data={"confirm_key": self.app.config["DEV_KEY"]},
            follow_redirects=True,
        )
        self.assertIn(b"already running", res.data)
        with self.app.app_context():
            self.assertEqual(ReconJob.query.filter_by(program_id=pid).count(), 1)

    def test_restart_scripts_success_creates_running_job(self):
        self._login()
        program = self._post_json("/api/v1/programs", {"name": "Kickoff Co"}).get_json()
        pid = program["id"]

        with patch("app.routes.programs.run_recon_job"):
            res = self.client.post(
                f"/programs/{pid}/scripts/restart",
                data={"confirm_key": self.app.config["DEV_KEY"]},
                follow_redirects=True,
            )
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"restarted", res.data)
        with self.app.app_context():
            job = ReconJob.query.filter_by(program_id=pid).first()
            self.assertIsNotNone(job)
            self.assertEqual(job.status, "running")

    def test_recon_job_tool_not_found_marks_job_failed(self):
        """The real subfinder/gau binaries aren't available in this test
        environment — exercise the realistic path where a tool is missing:
        the job must fail cleanly with a clear error, never hang silently."""
        from app.recon_runner import run_recon_job

        program = self._post_json("/api/v1/programs", {"name": "No Tools Co"}).get_json()
        pid = program["id"]
        self._post_json(f"/api/v1/programs/{pid}/assets", {"kind": "domain", "identifier": "example.test"})
        with self.app.app_context():
            job = ReconJob(program_id=pid, status="running", triggered_by="test")
            db.session.add(job)
            db.session.commit()
            job_id = job.id

        run_recon_job(self.app, job_id)

        with self.app.app_context():
            job = ReconJob.query.get(job_id)
            self.assertEqual(job.status, "failed")
            self.assertIsNotNone(job.error)
            self.assertIsNotNone(job.finished_at)

    def test_recon_job_mid_run_crash_never_leaves_job_stuck_running(self):
        """An unexpected exception mid-run must not leave status='running'
        forever — that would silently lock out every future restart via the
        already_running guard, with no diagnostic trail."""
        from app import recon_runner

        program = self._post_json("/api/v1/programs", {"name": "Crash Co"}).get_json()
        pid = program["id"]
        self._post_json(f"/api/v1/programs/{pid}/assets", {"kind": "domain", "identifier": "example.test"})
        with self.app.app_context():
            job = ReconJob(program_id=pid, status="running", triggered_by="test")
            db.session.add(job)
            db.session.commit()
            job_id = job.id

        with patch.object(recon_runner, "_run_tool", side_effect=RuntimeError("boom")):
            recon_runner.run_recon_job(self.app, job_id)

        with self.app.app_context():
            job = ReconJob.query.get(job_id)
            self.assertEqual(job.status, "failed")
            self.assertIn("boom", job.error)
            self.assertIsNotNone(job.finished_at)


if __name__ == "__main__":
    unittest.main()
