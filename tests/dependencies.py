"""Archive validation must reject filesystem escapes before extracting anything."""
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("visual_bootstrap", ROOT / "tools/bootstrap_dependencies.py")
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)

class ArchiveTests(unittest.TestCase):
    def test_resume_requires_matching_source_prefix_and_options(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CMakeCache.txt"
            with self.assertRaises(ValueError):
                bootstrap.verify_cmake_cache(path, Path("/source"), Path("/prefix"), [])
            path.write_text("CMAKE_HOME_DIRECTORY:INTERNAL=/source\nCMAKE_INSTALL_PREFIX:PATH=/prefix\nCMAKE_BUILD_TYPE:STRING=Release\n")
            self.assertEqual(len(bootstrap.verify_cmake_cache(path, Path("/source"), Path("/prefix"), ["-DCMAKE_BUILD_TYPE=Release"])), 64)
            for source, prefix, flags in [("/other", "/prefix", []), ("/source", "/other", []),
                                           ("/source", "/prefix", ["-DCMAKE_BUILD_TYPE=Debug"])]:
                with self.assertRaises(ValueError):
                    bootstrap.verify_cmake_cache(path, Path(source), Path(prefix), flags)

    def test_staging_refuses_outside_or_existing_destinations(self):
        spec = importlib.util.spec_from_file_location("visual_stage", ROOT / "tools/stage_package.py")
        stage = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stage)
        with self.assertRaises(ValueError):
            stage.stage(ROOT, ROOT)
        with self.assertRaises(ValueError):
            stage.refresh_opencv(ROOT)
        with self.assertRaises(ValueError):
            stage.refresh_geometry(ROOT)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                stage.stage(Path(directory), ROOT)
            stage.STAGING_ROOT = Path(directory) / "staging"
            stage.STAGING_ROOT.mkdir()
            candidate = stage.STAGING_ROOT / "package"
            self.assertEqual(stage.checked_stage(candidate), candidate.resolve())
            candidate.mkdir()
            (candidate / "sentinel").write_text("preserve")
            with self.assertRaises(ValueError):
                stage.checked_stage(candidate)
            self.assertEqual((candidate / "sentinel").read_text(), "preserve")
            try:
                (stage.STAGING_ROOT / "escape").symlink_to(Path(directory), target_is_directory=True)
            except OSError as error:
                self.skipTest(f"Cannot create a symbolic link on this platform: {error}")
            with self.assertRaises(ValueError):
                stage.checked_stage(stage.STAGING_ROOT / "escape" / "outside")

    def test_dependency_resources_and_build_intermediates_have_separate_roots(self):
        self.assertEqual(bootstrap.DEPENDENCY_ROOT, ROOT / "resources/dependencies")
        self.assertEqual(bootstrap.DEPENDENCY_BUILD_ROOT, ROOT / "build/dependency-build")

    def test_stage_upgrade_removes_retired_dnn_and_preserves_image_backend(self):
        spec = importlib.util.spec_from_file_location("visual_stage_retirement", ROOT / "tools/stage_package.py")
        stage = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stage)
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            (prefix / "lib").mkdir()
            headers = prefix / "include/opencv4/opencv2"
            (headers / "dnn").mkdir(parents=True)
            (headers / "dnn.hpp").write_text("obsolete")
            (headers / "dnn/model.hpp").write_text("obsolete")
            retired = prefix / "lib/libopencv_dnn.dylib"
            current = prefix / "lib/libopencv_core.dylib"
            retired.write_bytes(b"retired")
            current.write_bytes(b"current")
            stage.remove_retired_opencv(prefix)
            self.assertFalse(retired.exists())
            self.assertFalse((headers / "dnn").exists())
            self.assertFalse((headers / "dnn.hpp").exists())
            self.assertEqual(current.read_bytes(), b"current")

    def test_unsafe_members_never_escape_the_test_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, kind in [("release/../../escaped", tarfile.REGTYPE),
                               ("/absolute/file", tarfile.REGTYPE),
                               ("release/link", tarfile.SYMTYPE),
                               ("release/link", tarfile.LNKTYPE),
                               ("release/device", tarfile.CHRTYPE)]:
                with self.subTest(name=name, kind=kind):
                    archive = root / "bad.tar"
                    with tarfile.open(archive, "w") as tar:
                        entry = tarfile.TarInfo(name);entry.type=kind;entry.linkname="../../escaped"
                        tar.addfile(entry, io.BytesIO())
                    with self.assertRaises(ValueError):
                        bootstrap.extract(archive, root / "unpacked")
                    self.assertFalse((root / "escaped").exists())

    def test_official_manifest_uses_pinned_https_sources_and_checksums(self):
        manifest = json.loads((ROOT / "tools/dependencies.json").read_text())
        self.assertEqual({row["name"] for row in manifest}, {"FFmpeg", "OpenH264", "OpenUSD", "oneTBB", "OpenCV", "Assimp", "OCCT"})
        for row in manifest:
            self.assertTrue(row["url"].startswith("https://"))
            self.assertEqual(len(bytes.fromhex(row["sha256"])), 32)
            self.assertTrue(row["version"])

if __name__ == "__main__":
    unittest.main()
