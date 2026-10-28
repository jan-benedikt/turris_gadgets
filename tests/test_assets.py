"""Tests for bundled peripheral product images."""

from __future__ import annotations

import importlib.util
import struct
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parents[1]
CONSTANTS_PATH = ROOT / "custom_components" / "turris_gadgets" / "const.py"
DEVICE_IMAGE_DIR = (
    ROOT / "custom_components" / "turris_gadgets" / "frontend" / "devices"
)
FRONTEND_DIR = DEVICE_IMAGE_DIR.parent

SPEC = importlib.util.spec_from_file_location("turris_gadgets_const", CONSTANTS_PATH)
assert SPEC is not None
assert SPEC.loader is not None
constants = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(constants)


class DeviceImageTest(unittest.TestCase):
    """Keep the backend model map and bundled frontend assets in sync."""

    def test_all_configured_images_are_transparent_square_pngs(self) -> None:
        expected_names = {
            f"{model.lower()}.png" for model in constants.DEVICE_IMAGE_MODELS
        }
        self.assertEqual(
            {path.name for path in DEVICE_IMAGE_DIR.glob("*.png")}, expected_names
        )

        for filename in expected_names:
            with self.subTest(filename=filename):
                header = (DEVICE_IMAGE_DIR / filename).read_bytes()[:26]
                self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II", header[16:24]), (512, 512))
                self.assertEqual(header[25], 6, "PNG must contain an alpha channel")

    def test_bundled_logos_are_valid_svg_files(self) -> None:
        """Ensure both supplied logo variants are packaged with the panel."""
        for filename in ("turris_gadgets.svg", "turris_gadgets_color.svg"):
            with self.subTest(filename=filename):
                root = ET.parse(FRONTEND_DIR / filename).getroot()
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                self.assertEqual(root.attrib["viewBox"], "0 0 225 312")

    def test_color_logo_is_pure_vector(self) -> None:
        """Prevent embedded raster backgrounds from breaking the panel logo."""
        logo = (FRONTEND_DIR / "turris_gadgets_color.svg").read_text()
        self.assertNotIn("<image", logo)
        self.assertNotIn("data:image", logo)

    def test_custom_sidebar_iconset_is_packaged(self) -> None:
        """Keep the sidebar icon independent of Material Design Icons."""
        iconset = (FRONTEND_DIR / "turris-gadgets-iconset.js").read_text()
        self.assertIn('window.customIcons["turris-gadgets"]', iconset)
        self.assertIn("getIcon:", iconset)


if __name__ == "__main__":
    unittest.main()
