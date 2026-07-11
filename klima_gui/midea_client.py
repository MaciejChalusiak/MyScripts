"""Bezpośrednia komunikacja z klimatyzacją Midea przez bibliotekę midea-beautiful-air.

Zastępuje wcześniejsze odpalanie `midea-beautiful-air-cli` przez subprocess -
na RPi Zero każdy fork nowego procesu Pythona (import całej biblioteki od nowa)
zajmuje kilka sekund i zbędnie obciąża jedyny rdzeń CPU.
"""
import logging
import threading

from midea_beautiful import appliance_state
from midea_beautiful.exceptions import MideaError

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

    def _run_with_retry(self, action):
        # Połączenie TCP jest trzymane otwarte między wywołaniami (patrz
        # docstring modułu), więc od czasu do czasu strumień protokołu 8370
        # się rozjeżdża (np. niepełny odczyt poprzedniej odpowiedzi) i
        # kolejna komenda kończy się "Failed to decrypt response" - komenda
        # mogła przy tym w ogóle nie dotrzeć do urządzenia. Zrzucamy wtedy
        # połączenie, żeby wymusić świeży handshake, i próbujemy raz jeszcze.
        with self._lock:
            try:
                appliance = self._ensure_connected()
                return action(appliance)
            except MideaError:
                logger.warning(
                    "%s: communication error, reconnecting and retrying once",
                    self._address, exc_info=True,
                )
                self._appliance = None
                appliance = self._ensure_connected()
                return action(appliance)

    def read_indoor_temperature(self):
        def _read(appliance):
            appliance.refresh()
            return appliance.state.indoor_temperature

        return self._run_with_retry(_read)

    def set_state(self, target_temperature=None, running=None, mode=COOL_MODE):
        def _set(appliance):
            kwargs = {"mode": mode}
            if target_temperature is not None:
                kwargs["target_temperature"] = target_temperature
            if running is not None:
                kwargs["running"] = running
            appliance.set_state(**kwargs)

        self._run_with_retry(_set)
