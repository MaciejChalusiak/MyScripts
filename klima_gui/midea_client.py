"""Bezpośrednia komunikacja z klimatyzacją Midea przez bibliotekę midea-beautiful-air.

Zastępuje wcześniejsze odpalanie `midea-beautiful-air-cli` przez subprocess -
na RPi Zero każdy fork nowego procesu Pythona (import całej biblioteki od nowa)
zajmuje kilka sekund i zbędnie obciąża jedyny rdzeń CPU.
"""
import logging
import threading

from midea_beautiful import appliance_state

logger = logging.getLogger(__name__)

COOL_MODE = 2
FAN_ONLY_MODE = 5


class MideaClient:
    def __init__(self, address, token, key):
        self._address = address
        self._token = token
        self._key = key
        self._appliance = None
        self._lock = threading.Lock()

    def _ensure_connected(self):
        if self._appliance is None:
            self._appliance = appliance_state(
                address=self._address, token=self._token, key=self._key
            )
        return self._appliance

    def read_indoor_temperature(self):
        with self._lock:
            appliance = self._ensure_connected()
            appliance.refresh()
            return appliance.state.indoor_temperature

    def set_state(self, target_temperature=None, running=None, mode=COOL_MODE):
        with self._lock:
            appliance = self._ensure_connected()
            kwargs = {"mode": mode}
            if target_temperature is not None:
                kwargs["target_temperature"] = target_temperature
            if running is not None:
                kwargs["running"] = running
            appliance.set_state(**kwargs)
