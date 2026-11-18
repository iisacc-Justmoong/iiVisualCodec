#!/usr/bin/env python3
"""Assert the first-party Apache-2.0 grant and the preserved third-party notices."""

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRST_PARTY_DIRECTORIES = ("src", "tests", "cmake", "example", "tools", "docs")
EXCLUDED_PARTS = {"third_party", "build", "resources"}
SOURCE_SUFFIXES = {".h", ".hpp", ".c", ".cpp", ".md", ".cmake", ".in", ".py", ".txt"}

MIRRORS = (
    ("README.md", "docs/entrypoints/README.agent.json"),
    ("AGENT.md", "docs/entrypoints/AGENT.agent.json"),
    ("docs/License.md", "docs/License.agent.json"),
    ("docs/README.md", "docs/README.agent.json"),
    ("docs/Packaging.md", "docs/Packaging.agent.json"),
    ("docs/CAD.md", "docs/CAD.agent.json"),
)


class LicenseTextTest(unittest.TestCase):
    def test_root_license_is_apache_2(self):
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Apache License", text)
        self.assertIn("Version 2.0, January 2004", text)
        self.assertIn("http://www.apache.org/licenses/", text)
        self.assertIn("END OF TERMS AND CONDITIONS", text)
        self.assertNotIn("MIT License", text)
        self.assertNotIn("Permission is hereby granted", text)

    def test_notice_copyright(self):
        notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2026 iisacc", notice)
        self.assertIn("https://github.com/iisacc-Justmoong", notice)
        self.assertIn("Apache License", notice)
        self.assertIn("Version 2.0", notice)

    def test_readme_spdx(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## License", readme)
        self.assertIn("SPDX-License-Identifier: Apache-2.0", readme)
        self.assertIn("(SPDX `Apache-2.0`)", readme)
        self.assertIn("docs/License.md", readme)

    def test_korean_license_document(self):
        text = (ROOT / "docs/License.md").read_text(encoding="utf-8")
        self.assertIn("SPDX-License-Identifier: Apache-2.0", text)
        self.assertIn("Apache License 2.0", text)
        self.assertIn("Copyright (c) 2026 iisacc", text)
        self.assertIn("AGPL", text)

    def test_agent_policy(self):
        text = (ROOT / "AGENT.md").read_text(encoding="utf-8")
        self.assertIn("Apache License 2.0", text)
        self.assertIn("Copyright (c) 2026 iisacc", text)
        self.assertIn("AGPL", text)

    def test_first_party_claims_are_apache(self):
        packaging = (ROOT / "docs/Packaging.md").read_text(encoding="utf-8")
        self.assertIn("SDK 자체는 Apache-2.0이다.", packaging)
        self.assertNotIn("SDK 자체는 MIT", packaging)
        cad = (ROOT / "docs/CAD.md").read_text(encoding="utf-8")
        self.assertIn("iiVisualCodec 자체 라이선스는 Apache-2.0이다.", cad)
        self.assertNotIn("자체 라이선스는 MIT", cad)

    def test_package_metadata_and_install_rule(self):
        visual = (ROOT / "cmake/iiVisualCodecConfig.cmake.in").read_text(encoding="utf-8")
        image = (ROOT / "cmake/iiImageCodecConfig.cmake.in").read_text(encoding="utf-8")
        cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn('set(iiVisualCodec_SPDX_LICENSE "Apache-2.0")', visual)
        self.assertIn('set(iiImageCodec_SPDX_LICENSE "Apache-2.0")', image)
        self.assertIn("install(FILES README.md LICENSE NOTICE", cmake)
        for name in ("IIVISUALCODEC_CONFIG", "IIIMAGECODEC_CONFIG"):
            configured = os.environ.get(name)
            if not configured:
                continue
            generated = Path(configured).read_text(encoding="utf-8")
            if name == "IIVISUALCODEC_CONFIG":
                self.assertIn('set(iiVisualCodec_SPDX_LICENSE "Apache-2.0")', generated)
            else:
                self.assertIn('set(iiImageCodec_SPDX_LICENSE "Apache-2.0")', generated)

    def test_agent_mirrors_match_sources(self):
        for source, mirror in MIRRORS:
            raw = (ROOT / source).read_bytes()
            document = json.loads((ROOT / mirror).read_text(encoding="utf-8"))
            self.assertEqual(document["source"]["sha256"], hashlib.sha256(raw).hexdigest(), source)
            self.assertEqual(document["source"]["bytes"], len(raw), source)
            restored = "".join(block["raw"] for block in document["blocks"])
            self.assertEqual(restored, raw.decode("utf-8"), source)
        for source in ("README.md", "AGENT.md", "docs/License.md", "docs/Packaging.md", "docs/CAD.md"):
            self.assertIn("Apache", (ROOT / source).read_text(encoding="utf-8"), source)
        index = json.loads((ROOT / "docs/agent-index.json").read_text(encoding="utf-8"))
        by_source = {item["source"]: item for item in index["documents"]}
        self.assertIn("docs/License.md", by_source)
        for source, _mirror in MIRRORS:
            digest = hashlib.sha256((ROOT / source).read_bytes()).hexdigest()
            self.assertEqual(by_source[source]["source_sha256"], digest, source)

    def test_vendored_stb_license_is_unchanged(self):
        license_text = (ROOT / "third_party/stb/LICENSE").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2017 Sean Barrett", license_text)
        self.assertIn("ALTERNATIVE A - MIT License", license_text)
        header = (ROOT / "third_party/stb/stb_image.h").read_text(encoding="utf-8", errors="replace")
        self.assertIn("ALTERNATIVE A - MIT License", header)
        self.assertIn("Copyright (c) 2017 Sean Barrett", header)

    def test_no_first_party_mit_spdx_header(self):
        for path in first_party_source_files(ROOT):
            text = path.read_text(encoding="utf-8", errors="replace")
            self.assertNotIn("SPDX-License-Identifier: MIT", text, str(path))

    def test_spdx_scan_skips_dependency_staging_and_build_trees(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in (
                "resources/dependencies/sources/vendor.h",
                "resources/staging/include/vendor.h",
                "build/generated.h",
                "third_party/vendor/vendor.h",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("SPDX-License-Identifier: MIT\n", encoding="utf-8")
            self.assertEqual(list(first_party_source_files(root)), [])
            first_party = root / "src" / "codec.h"
            first_party.parent.mkdir()
            first_party.write_text("/* first party */\n", encoding="utf-8")
            self.assertEqual(list(first_party_source_files(root)), [first_party])


def first_party_source_files(root: Path):
    """Yield tracked first-party sources, never dependency, staging, or build trees."""
    candidates = []
    for directory in FIRST_PARTY_DIRECTORIES:
        base = root / directory
        if base.is_dir():
            candidates.extend(path for path in base.rglob("*") if path.is_file())
    if root.is_dir():
        candidates.extend(path for path in root.iterdir() if path.is_file())
    for path in candidates:
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.suffix.lower() not in SOURCE_SUFFIXES or path.name in {"LICENSE", "test_license.py"}:
            continue
        yield path


if __name__ == "__main__":
    unittest.main()
