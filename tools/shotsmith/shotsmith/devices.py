"""Device profile registry.

Each profile defines the App Store Connect submission slot dimensions and a
default caption font size that produces legible output at that resolution.

Sizes pulled from Apple's App Store Connect screenshot specifications:
https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications/
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceProfile:
    name: str
    asc_category: str
    width: int                  # ASC submission slot width
    height: int                 # ASC submission slot height
    framed_width: int           # frames-cli output width (verify checks this)
    framed_height: int          # frames-cli output height
    default_caption_size: int


# framed_* values come from frames-cli's actual output dimensions.
# iPhone 6.9" framed = 1470x3000 (verified via Flara's lone surviving intermediate).
# iPad 13" framed = 2228x3084 (estimated from frames-cli's iPad scaling pattern;
#   verify warns rather than errors if real values differ on first frame run).
DEVICES: dict[str, DeviceProfile] = {
    "iphone": DeviceProfile(
        name="iPhone 6.9\" (iPhone 17 Pro Max)",
        asc_category="iPhone 6.9\" Display",
        width=1320,
        height=2868,
        framed_width=1470,
        framed_height=3000,
        default_caption_size=115,
    ),
    "ipad": DeviceProfile(
        name="iPad 13\" (iPad Pro 13-inch M5)",
        asc_category="iPad 13\" Display",
        width=2064,
        height=2752,
        framed_width=2228,
        framed_height=3084,
        default_caption_size=130,
    ),
}


def get(device_key: str) -> DeviceProfile:
    if device_key not in DEVICES:
        raise ValueError(
            f"Unknown device '{device_key}'. Known: {sorted(DEVICES.keys())}"
        )
    return DEVICES[device_key]
