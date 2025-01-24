import logging

import dash
import flask
import requests

from autoguitar.dashboard.event_storage import EVENT_STORAGE
from autoguitar.dashboard.layout import LAYOUT

PORT = 8111

server = flask.Flask(__name__)
logger = logging.getLogger(__name__)


@server.route("/")
def home():
    return "Hello, Flask!"


@server.route("/api/event", methods=["POST"])
def event():
    data = flask.request.get_json()

    kind = data["kind"]
    value = data["value"]

    EVENT_STORAGE.add_event(kind=kind, value=value)
    print(
        EVENT_STORAGE.get_events()[-1],
        f", total # events = {len(EVENT_STORAGE.get_events())   }",
    )

    return "Event received!"


def post_event(kind: str, value: dict):
    try:
        response = requests.post(
            f"http://localhost:{PORT}/api/event",
            json={"kind": kind, "value": value},
            timeout=2,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Failed to post event: {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to post event: {e}")


if __name__ == "__main__":
    app = dash.Dash(server=server, routes_pathname_prefix="/dash/")
    app.layout = LAYOUT
    app.run(debug=True, port=PORT)
