"""Pętla kontrolna utrzymująca temperaturę w pomieszczeniu blisko zadanej wartości.

Klimatyzacje Midea mają wbudowaną histerezę rzędu kilku stopni - ustawienie
target_temperature na urządzeniu i zostawienie go samemu sobie daje amplitudę
temperatury w pokoju nawet ~4 stopnie. Zamiast tego co POLL_INTERVAL_SECONDS
mierzymy faktyczną temperaturę w pokoju i przestawiamy wewnętrzny target
klimatyzacji agresywnie w dół (żeby wymusić chłodzenie) albo w górę (żeby
chłodzenie zatrzymać), gdy odchylenie od zadanej temperatury przekroczy
DEVIATION. To trzyma temperaturę w pokoju w paśmie około 1 stopnia.
"""
import logging
import threading
import time

from midea_client import FAN_ONLY_MODE

logger = logging.getLogger(__name__)

DEVIATION = 0.4
POLL_INTERVAL_SECONDS = 60
DRYING_DURATION_SECONDS = 20 * 60

# Korekta zawyżenia pomiaru czujnika klimatyzacji względem realnej temperatury
# w pokoju (np. dla Biura: ustawienie 23 stopni jest osiągnięte realnie, gdy
# klimatyzacja pokazuje 24 - jej czujnik zawyża o tyle stopni).
SENSOR_TEMP_CORRECTION = 1.0


class DeviceController:
    def __init__(
        self,
        name,
        client,
        default_target_temp=24.0,
        deviation=DEVIATION,
        sensor_correction=SENSOR_TEMP_CORRECTION,
    ):
        self.name = name
        self.client = client
        self.deviation = deviation
        self.sensor_correction = sensor_correction

        self._state_lock = threading.Lock()
        self.target_temp = default_target_temp
        self.power_on = False
        self.indoor_temp = None
        self.last_error = None

        self._ac_internal_target = None
        self._stop_event = threading.Event()
        self._thread = None
        self._drying_timer = None
        self._drying_ends_at = None

    def status(self):
        with self._state_lock:
            drying = self._drying_timer is not None
            remaining = None
            if drying and self._drying_ends_at is not None:
                remaining = max(0, int(self._drying_ends_at - time.time()))
            return {
                "name": self.name,
                "power_on": self.power_on,
                "drying": drying,
                "drying_remaining_seconds": remaining,
                "target_temp": self.target_temp,
                "indoor_temp": self.indoor_temp,
                "last_error": self.last_error,
            }

    def turn_on(self):
        self._cancel_drying()
        with self._state_lock:
            if self.power_on:
                return
            target = self.target_temp

        ac_target = int(target)
        try:
            self.client.set_state(target_temperature=ac_target, running=True)
        except Exception as e:
            logger.error("%s: failed to turn on", self.name, exc_info=True)
            with self._state_lock:
                self.last_error = str(e)
            raise

        self._ac_internal_target = ac_target
        with self._state_lock:
            self.power_on = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("%s: turned on, target=%s", self.name, target)

    def turn_off_immediate(self):
        self._cancel_drying()
        with self._state_lock:
            if not self.power_on:
                return
            self.power_on = False
        self._stop_event.set()
        try:
            self.client.set_state(running=False)
        except Exception:
            logger.error("%s: failed to send power-off command", self.name, exc_info=True)
        logger.info("%s: turned off immediately", self.name)

    def turn_off_drying(self, duration_seconds=DRYING_DURATION_SECONDS):
        self._cancel_drying()
        self._stop_event.set()
        try:
            self.client.set_state(running=True, mode=FAN_ONLY_MODE)
        except Exception as e:
            logger.error("%s: failed to switch to fan-only for drying", self.name, exc_info=True)
            with self._state_lock:
                self.last_error = str(e)
            raise

        with self._state_lock:
            self.power_on = True
            self._drying_ends_at = time.time() + duration_seconds
        timer = threading.Timer(duration_seconds, self._finish_drying)
        timer.daemon = True
        self._drying_timer = timer
        timer.start()
        logger.info("%s: drying for %ds before power-off", self.name, duration_seconds)

    def _finish_drying(self):
        logger.info("%s: drying finished, powering off", self.name)
        with self._state_lock:
            self.power_on = False
            self._drying_timer = None
            self._drying_ends_at = None
        try:
            self.client.set_state(running=False)
        except Exception:
            logger.error("%s: failed to power off after drying", self.name, exc_info=True)

    def _cancel_drying(self):
        if self._drying_timer is not None:
            self._drying_timer.cancel()
            self._drying_timer = None
            self._drying_ends_at = None

    def set_target_temp(self, target_temp):
        with self._state_lock:
            self.target_temp = float(target_temp)
            power_on = self.power_on
        logger.info("%s: target temp set to %s", self.name, target_temp)
        if power_on:
            try:
                self._tick()
            except Exception:
                logger.error("%s: failed to apply new target temp immediately", self.name, exc_info=True)

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self._tick()
                with self._state_lock:
                    self.last_error = None
            except Exception as e:
                logger.error("%s: control loop error", self.name, exc_info=True)
                with self._state_lock:
                    self.last_error = str(e)
            self._stop_event.wait(POLL_INTERVAL_SECONDS)

    def _tick(self):
        raw_indoor_temp = self.client.read_indoor_temperature()
        corrected_indoor_temp = raw_indoor_temp - self.sensor_correction
        with self._state_lock:
            self.indoor_temp = corrected_indoor_temp
            target_temp = self.target_temp

        new_ac_target = None
        if corrected_indoor_temp > target_temp + self.deviation:
            new_ac_target = int(raw_indoor_temp - 2)
        elif corrected_indoor_temp < target_temp - self.deviation:
            new_ac_target = int(raw_indoor_temp + 3)

        if new_ac_target is not None and new_ac_target != self._ac_internal_target:
            logger.info(
                "%s: indoor(corrected)=%.1f target=%.1f -> setting AC target to %s",
                self.name, corrected_indoor_temp, target_temp, new_ac_target,
            )
            self.client.set_state(target_temperature=new_ac_target)
            self._ac_internal_target = new_ac_target
