import json
import argparse
from pathlib import Path


class GNS3AParser:
    def __init__(self, path: str):
        self.path = Path(path)
        self.data = self._load()

    def _load(self):
        with open(self.path, "r") as f:
            return json.load(f)

    def get_base_info(self):
        version_name = self._get_version_name()

        return {
            "name": f"{self.data.get('name', 'Dell OS10')} {version_name}".strip(),
            "category": self.data.get("category"),
            "symbol": self.data.get("symbol", ":/symbols/classic/router.svg"),
            "usage": self.data.get("usage"),
            "first_port_name": self.data.get("first_port_name"),
            "port_name_format": self.data.get("port_name_format"),
            "linked_clone": self.data.get("linked_clone", True),
            "on_close": self.data.get("on_close", "power_off"),
        }

    def _get_version_name(self):
        versions = self.data.get("versions", [])
        if versions:
            return versions[0].get("name", "")
        return ""

    def get_qemu_config(self):
        qemu = self.data.get("qemu", {})

        return {
            "template_type": "qemu",

            # Networking
            "adapter_type": qemu.get("adapter_type"),
            "adapters": qemu.get("adapters"),

            # VM resources
            "ram": qemu.get("ram"),
            "cpus": 1,

            # Disk interfaces
            "hda_disk_interface": qemu.get("hda_disk_interface"),
            "hdb_disk_interface": qemu.get("hdb_disk_interface"),
            "hdc_disk_interface": qemu.get("hdc_disk_interface"),

            # Console
            "console_type": qemu.get("console_type"),

            # Boot
            "boot_priority": qemu.get("boot_priority"),

            # Explicit QEMU binary
            "qemu_path": "qemu-system-x86_64",
        }

    def get_images(self):
        versions = self.data.get("versions", [])

        if not versions:
            raise ValueError("No versions found in appliance")

        images = versions[0].get("images", {})

        return {
            "hda_disk_image": images.get("hda_disk_image"),
            "hdb_disk_image": images.get("hdb_disk_image"),
            "hdc_disk_image": images.get("hdc_disk_image"),
        }

    def build_template_payload(self):
        payload = {}

        payload.update(self.get_base_info())
        payload.update(self.get_qemu_config())
        payload.update(self.get_images())

        payload["template_type"] = "qemu"
        payload["compute_id"] = "local"
        payload["category"] = self.data.get("category", "router")

        return payload


def main():
    parser = argparse.ArgumentParser(
        description="Build a GNS3 template payload from a .gns3a file"
    )
    parser.add_argument("file", help="Path to the .gns3a file")
    args = parser.parse_args()

    payload = GNS3AParser(args.file).build_template_payload()
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()