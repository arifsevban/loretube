import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tubeflow.history import HistoryStore
from tubeflow.jobs import JobManager
from tubeflow.security import TokenStore
from tubeflow.web import AppState, create_app


class HistoryClearTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.download_dir = self.root / "downloads"
        self.download_dir.mkdir()
        self.data_dir = self.root / "data"
        self.data_dir.mkdir()
        self.history_path = self.data_dir / "history.json"
        self.store = HistoryStore(self.history_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_clear_removes_history_and_associated_download(self) -> None:
        job_id = "a" * 32
        job_dir = self.download_dir / job_id
        job_dir.mkdir()
        (job_dir / "video.mp4").write_bytes(b"media")
        self.store.add({"id": job_id, "filename": "video.mp4"})

        result = self.store.clear(self.download_dir)

        self.assertTrue(result["saved"])
        self.assertEqual(result["removed_records"], 1)
        self.assertEqual(result["deleted_downloads"], 1)
        self.assertEqual(result["failed_downloads"], 0)
        self.assertFalse(job_dir.exists())
        self.assertEqual(self.store.list(), [])
        self.assertEqual(json.loads(self.history_path.read_text(encoding="utf-8")), [])

    def test_clear_does_not_delete_paths_from_invalid_history_ids(self) -> None:
        outside_dir = self.root / "outside"
        outside_dir.mkdir()
        marker = outside_dir / "keep.txt"
        marker.write_text("keep", encoding="utf-8")
        self.store.add({"id": "..", "filename": "keep.txt"})

        result = self.store.clear(self.download_dir)

        self.assertTrue(result["saved"])
        self.assertEqual(result["removed_records"], 1)
        self.assertTrue(marker.is_file())
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_delete_history_endpoint_clears_records_and_files(self) -> None:
        job_id = "b" * 32
        job_dir = self.download_dir / job_id
        job_dir.mkdir()
        (job_dir / "audio.mp3").write_bytes(b"media")
        self.store.add({"id": job_id, "filename": "audio.mp3"})

        project_dir = Path(__file__).resolve().parents[1]
        cfg = SimpleNamespace(
            download_dir=self.download_dir,
            max_concurrent=1,
            template_dir=project_dir / "templates",
            static_dir=project_dir / "static",
        )
        tokens = TokenStore(3600)
        jobs = JobManager(cfg, self.store, tokens)
        app = create_app(AppState(cfg, self.store, tokens, jobs, lan_ip=None))

        response = app.test_client().delete("/api/history")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["removed_records"], 1)
        self.assertEqual(response.json["deleted_downloads"], 1)
        self.assertFalse(job_dir.exists())
        self.assertEqual(self.store.list(), [])

    def test_clear_keeps_downloads_if_history_cannot_be_saved(self) -> None:
        job_id = "c" * 32
        job_dir = self.download_dir / job_id
        job_dir.mkdir()
        (job_dir / "video.mp4").write_bytes(b"media")
        store = HistoryStore(self.root / "missing" / "history.json")
        store.add({"id": job_id, "filename": "video.mp4"})

        result = store.clear(self.download_dir)

        self.assertFalse(result["saved"])
        self.assertTrue(job_dir.is_dir())
        self.assertEqual(len(store.list()), 1)


if __name__ == "__main__":
    unittest.main()
