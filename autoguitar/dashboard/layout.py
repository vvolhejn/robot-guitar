import dash
import librosa
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback

from autoguitar.dashboard.event import TunerEvent
from autoguitar.dashboard.event_storage import EVENT_STORAGE, AnnotatedEvent

NOTES_ON_Y_AXIS = "Notes on y-axis"

LAYOUT = dash.html.Div(
    children=[
        dash.dcc.Checklist(
            id="y-axis-dropdown",
            options=[NOTES_ON_Y_AXIS],
            value=[],
        ),
        dash.dcc.Graph(id="pitch-graph"),
        dash.html.Div(id="debug-div", children="This is the Dash app."),
        dash.dcc.Interval(id="interval-component", interval=1 * 1000, n_intervals=0),
    ]
)


def events_to_df(events: list[AnnotatedEvent]) -> pd.DataFrame:
    rows = []
    for event in events:
        if isinstance(event.event, TunerEvent):
            rows.append(
                {
                    "datetime": event.datetime,
                    "kind": "tuner",
                    "frequency": event.event.frequency,
                    "target_frequency": event.event.target_frequency,
                    "steps_to_move": event.event.steps_to_move,
                    "cur_steps": event.event.cur_steps,
                }
            )

    return pd.DataFrame(rows)


def make_frequency_plot(df: pd.DataFrame, use_note_labels: bool = False):
    fig = px.line(
        df,
        x="datetime",
        y=["frequency", "target_frequency"],
        title="Frequency over time",
    )

    fig.update_layout(
        xaxis=dict(title="Datetime"),
        title="Frequency over Time",
    )

    if use_note_labels:
        y_ticks = [librosa.midi_to_hz(y) for y in range(0, 128)]
        y_tick_labels = [librosa.hz_to_note(freq) for freq in y_ticks]

        fig.update_layout(
            yaxis=dict(
                tickmode="array",
                tickvals=y_ticks,
                ticktext=y_tick_labels,
                title="Musical Notes",
            ),
            # log scale y
            yaxis_type="log",
            xaxis=dict(title="Time (s)"),
            title="Frequency over Time",
        )
    else:
        fig.update_layout(
            yaxis=dict(title="Frequency (Hz)"),
        )

    return fig


@callback(
    Output("pitch-graph", "figure"),
    Output("debug-div", "children"),
    Input("interval-component", "n_intervals"),
    Input("y-axis-dropdown", "value"),
)
def update_graph(n: int, y_axis_values: list[str]):
    print(y_axis_values)
    events = EVENT_STORAGE.get_events()

    df = events_to_df(events)

    if df.empty:
        return (px.line(title="Frequency over time"), "No events yet.")

    fig = make_frequency_plot(df, use_note_labels=y_axis_values == [NOTES_ON_Y_AXIS])
    # This makes it so that if you zoom in, the zoom level is preserved on updates. See
    # https://community.plotly.com/t/preserving-ui-state-like-zoom-in-dcc-graph-with-uirevision-with-dash/15793/19
    fig.layout.update({"uirevision": "some fixed value"})

    return fig, f"Number of events: {len(events)}"
