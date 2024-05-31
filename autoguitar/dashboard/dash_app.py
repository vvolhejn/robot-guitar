import dash
import flask

from autoguitar.dashboard.event import parse_event
from autoguitar.dashboard.event_storage import EVENT_STORAGE
from autoguitar.dashboard.layout import LAYOUT

server = flask.Flask(__name__)


@server.route("/")
def home():
    return "Hello, Flask!"


@server.route("/api/event", methods=["POST"])
def event():
    data = flask.request.get_json()
    try:
        event = parse_event(data)
    except (KeyError, ValueError) as e:
        return f"Invalid event data. Error: {repr(e)}", 400

    EVENT_STORAGE.add_event(event)
    print(
        EVENT_STORAGE.get_events()[-1],
        f", total # events = {len(EVENT_STORAGE.get_events())   }",
    )

    return "Event received!"


app = dash.Dash(server=server, routes_pathname_prefix="/dash/")

app.layout = LAYOUT

if __name__ == "__main__":
    app.run_server(debug=True)
