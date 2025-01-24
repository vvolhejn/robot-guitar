import datetime
import json
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_PATH = (
    Path(__file__).parents[2]
    / "data"
    / "tuning_data_selected"
    / "2024-12-05_13-29-29-good.jsonl"
)


def _parse_event(d: dict) -> dict:
    event = d["event"]

    res = {
        "timestamp": datetime.datetime.fromisoformat(event["network_timestamp"]),
    }
    if "frequency" in event:
        res["frequency"] = event["frequency"]
    else:
        motor_status = [x for x in event["status"] if x["motor_number"] == 0]
        assert len(motor_status) == 1
        motor_status = motor_status[0]

        res["steps"] = motor_status["cur_steps"]
        res["target_steps"] = motor_status["target_steps"]

    return res


def _get_derivative(series: pd.Series) -> pd.Series:
    return series.diff() / series.index.to_series().diff().dt.total_seconds()


def _propagate_from_last_stable(df: pd.DataFrame, column: str) -> pd.Series:
    x = df.copy()
    # There are typically multiple stable points after one another.
    # Get the first one of each sequence
    x["first_stable"] = x["stable"].astype(int).diff(1) == 1
    # Number the sequences. Unstable points after a stable series still belong to it.
    x["sequence_index"] = x["first_stable"].cumsum()
    last_stable = pd.Series(np.nan, index=x.index, dtype=float)

    for i, row in x.iterrows():
        # Find the last stable point before the current one.
        # Don't include the current sequence.
        previous_stable_points = x.loc[
            (x["sequence_index"] < row["sequence_index"]) & x["stable"]
        ]
        if previous_stable_points.empty:
            continue

        last_position = previous_stable_points.iloc[-1].name
        last_stable[i] = x.loc[last_position, column]

    return last_stable


def _get_loose_steps(df: pd.DataFrame, max_difference: int) -> pd.Series:
    df = df.copy()
    loose_steps = pd.Series(np.nan, index=df.index)
    loose_steps.iloc[0] = df.iloc[0]["steps"]

    last_loose_steps = df.iloc[0]["steps"]

    for i, row in df.iloc[1:].iterrows():
        last_loose_steps = np.clip(
            last_loose_steps,
            row["steps"] - max_difference,
            row["steps"] + max_difference,
        )
        loose_steps[i] = last_loose_steps

    return loose_steps


def get_dataset(
    path: Path | None = None,
    # 300 seems to be a good default for LSMD when predicting squared frequency.
    # It matters less when predicting frequency directly,
    # the model probably just ignores it
    loose_steps_max_difference: int = 300,
) -> pd.DataFrame:
    if path is None:
        path = DEFAULT_PATH

    with path.open() as f:
        json_lines = [json.loads(d) for d in f.readlines()]

    df = pd.DataFrame([_parse_event(d) for d in json_lines])

    df.loc[df["frequency"].notna(), "timestamp"] -= pd.Timedelta("150ms")

    # The events are not strictly sorted by timestamp because of network delays
    df = df.sort_values("timestamp").set_index("timestamp")

    df["steps"] = df["steps"].interpolate(method="time", limit_direction="both")
    # Target steps change discretely, so don't interpolate
    df["target_steps"] = df["target_steps"].ffill()

    # ensure every row has all the columns
    df = df.loc[~df["frequency"].isna()]

    # remove outliers
    df = df.loc[_get_derivative(df["frequency"]).abs() <= 100]

    df["steps_derivative"] = _get_derivative(df["steps"])
    df["frequency_derivative"] = _get_derivative(df["frequency"])

    smoothed_derivative = (
        df["steps_derivative"].rolling(window=pd.Timedelta("250ms")).mean()
    )

    df["stable"] = smoothed_derivative.abs() < 100

    df["last_stable_steps"] = _propagate_from_last_stable(df, "steps").bfill()
    df["last_stable_frequency"] = _propagate_from_last_stable(df, "frequency").bfill()

    df["loose_steps"] = _get_loose_steps(df, max_difference=loose_steps_max_difference)

    fraction_train = 0.6
    n_train = int(fraction_train * len(df))
    df["split"] = "train"
    df.loc[df.index[n_train:], "split"] = "test"

    return df


def get_sklearn_datasets(
    df: pd.DataFrame, x_columns: list[str], y_column: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    stable_df = df.loc[df["stable"] == True].copy()
    train_data = stable_df[stable_df["split"] == "train"]
    test_data = stable_df[stable_df["split"] == "test"]

    X_train = train_data[x_columns].values
    y_train = train_data[y_column].values
    X_test = test_data[x_columns].values
    y_test = test_data[y_column].values

    return X_train, y_train, X_test, y_test
