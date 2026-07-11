import json
import logging
import os
import signal

from flask import Flask, jsonify, render_template, request

from device_controller import DeviceController
from midea_client import MideaClient
from my_secrets import devices_secrets

logging.basicConfig(
    level="INFO",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")

DEFAULT_TARGET_TEMPS = {
    "Biuro": 24.0,
    "Salon": 24.0,
    "Sypialnia": 24.0,
}

app = Flask(__name__)
controllers = {}


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        logger.error("Failed to read state file, starting fresh", exc_info=True)
        return {}


def save_state():
    state = {
        name: {"power_on": c.power_on, "target_temp": c.target_temp}
        for name, c in controllers.items()
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def build_controllers():
    saved_state = load_state()
    for name, secrets in devices_secrets.items():
        if not isinstance(secrets, dict) or "addr" not in secrets:
            continue
        client = MideaClient(secrets["addr"], secrets["token"], secrets["key"])
        default_target = DEFAULT_TARGET_TEMPS.get(name, 24.0)
        saved = saved_state.get(name, {})
        controller = DeviceController(
            name, client, default_target_temp=saved.get("target_temp", default_target)
        )
        controllers[name] = controller
        if saved.get("power_on"):
            logger.info("%s: restoring power-on state from previous run", name)
            controller.turn_on()


@app.route("/")
def index():
    return render_template("index.html", device_names=list(controllers.keys()))


@app.route("/api/status")
def api_status():
    return jsonify({name: c.status() for name, c in controllers.items()})


@app.route("/api/devices/<name>/power", methods=["POST"])
def api_power(name):
    controller = controllers.get(name)
    if controller is None:
        return jsonify({"error": "unknown device"}), 404
    body = request.get_json(force=True)
    turn_on = bool(body.get("on"))
    off_mode = body.get("mode", "immediate")
    try:
        if turn_on:
            controller.turn_on()
        elif off_mode == "drying":
            controller.turn_off_drying()
        else:
            controller.turn_off_immediate()
    except Exception as e:
        return jsonify({"error": str(e), **controller.status()}), 502
    save_state()
    return jsonify(controller.status())


@app.route("/api/devices/<name>/target", methods=["POST"])
def api_target(name):
    controller = controllers.get(name)
    if controller is None:
        return jsonify({"error": "unknown device"}), 404
    target_temp = request.get_json(force=True).get("target_temp")
    if target_temp is None:
        return jsonify({"error": "missing target_temp"}), 400
    controller.set_target_temp(target_temp)
    save_state()
    return jsonify(controller.status())


def handle_terminate(signum, frame):
    logger.info("Received termination signal, shutting down (devices stay in current state)")
    raise SystemExit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_terminate)
    build_controllers()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
