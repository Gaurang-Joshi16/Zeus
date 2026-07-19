from typing import Any, Dict, List

import sounddevice as sd


class AudioDeviceManager:
    @staticmethod
    def get_input_devices() -> List[Dict[str, Any]]:
        try:
            devices = sd.query_devices()
        except Exception:
            return []

        input_devices = []
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                input_devices.append(
                    {
                        "id": i,
                        "name": dev["name"],
                        "channels": dev["max_input_channels"],
                        "default": i == sd.default.device[0],
                    }
                )
        return input_devices

    @staticmethod
    def get_default_device_id() -> int:
        try:
            return sd.default.device[0]
        except Exception:
            return 0
