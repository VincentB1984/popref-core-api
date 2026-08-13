from __future__ import annotations

import time
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

import local_app


class PoprefLocalApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(local_app.app)
        local_app.SESSIONS.clear()
        local_app.JOBS.clear()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.excel_path = Path(self.tmpdir.name) / "reference.xlsx"
        with pd.ExcelWriter(self.excel_path, engine="openpyxl") as writer:
            pd.DataFrame(
                {
                    "Code géographique": ["01001", "01002", "2A004"],
                    "Nom": ["L'Abergement-Clémenciat", "L'Abergement-de-Varey", "Ajaccio"],
                }
            ).to_excel(writer, sheet_name="COM", index=False)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def upload_excel(self) -> dict:
        with self.excel_path.open("rb") as handle:
            response = self.client.post(
                "/api/import",
                files={"excel": (self.excel_path.name, handle, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(len(body["communes"]), 3)
        self.assertIn({"code": "01001", "name": "L'Abergement-Clémenciat", "label": "L'Abergement-Clémenciat (01001)"}, body["communes"])
        self.assertIn({"code": "2A004", "name": "Ajaccio", "label": "Ajaccio (2A004)"}, body["communes"])
        return body

    def test_import_and_asset_upload(self) -> None:
        body = self.upload_excel()
        response = self.client.post(
            "/api/assets",
            data={"session_id": body["session_id"]},
            files={"assets": ("carte_france_2012_2017.png", b"fake-png", "image/png")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["uploaded"], 1)

    @patch("local_app.generate_html")
    @patch("local_app.build_payload")
    def test_generate_poll_and_download(self, build_payload, generate_html) -> None:
        body = self.upload_excel()
        build_payload.return_value = {
            "commune_name": "L'Abergement-Clémenciat",
            "commune_code": "01001",
            "region_name": "Auvergne-Rhône-Alpes",
            "region_code": "84",
            "insee_diagnostics": {},
        }

        def write_html(_payload: str, destination: str) -> None:
            Path(destination).write_text("<html><body>Dossier Popref</body></html>", encoding="utf-8")

        generate_html.side_effect = write_html
        response = self.client.post(
            "/api/generate",
            json={"session_id": body["session_id"], "commune": "01001", "include_insee": False},
        )
        self.assertEqual(response.status_code, 200, response.text)
        job_id = response.json()["job_id"]
        for _ in range(30):
            status = self.client.get(f"/api/jobs/{job_id}").json()
            if status["status"] != "running" and status["status"] != "pending":
                break
            time.sleep(0.05)
        self.assertEqual(status["status"], "done", status)
        download = self.client.get(f"/api/jobs/{job_id}/download")
        self.assertEqual(download.status_code, 200)
        self.assertIn(b"Dossier Popref", download.content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
