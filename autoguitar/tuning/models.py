import warnings

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from autoguitar.tuning.dataset import get_sklearn_datasets


def get_rmse_cents(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root mean squared error in cents.

    Makes sense for comparing frequencies, though not for steps.
    """
    return np.sqrt(np.mean((1200 * np.log2(y_true / y_pred)) ** 2))


def get_linear_regression(
    df: pd.DataFrame, x_columns: list[str], squared_frequency: bool
):
    """Predict frequency -> steps."""
    df = df.copy()
    df["frequency_squared"] = df["frequency"] ** 2
    y_column = "frequency_squared" if squared_frequency else "frequency"

    X_train, y_train, _X_test, _y_test = get_sklearn_datasets(
        df, x_columns=x_columns, y_column=y_column
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    warnings.filterwarnings("ignore", message="X has feature names")

    frequency_predicted = model.predict(df[x_columns])
    if squared_frequency:
        frequency_predicted = frequency_predicted**0.5

    test_mask = (df["split"] == "test") & df["stable"]
    rmse = get_rmse_cents(
        df.loc[test_mask, "frequency"],
        frequency_predicted[test_mask],
    )

    return model, rmse, frequency_predicted


def naive_linear_regression(df: pd.DataFrame):
    """Linearly predict steps -> frequency.

    This doesn't make sense from a physics perspective because it's rather
    steps -> frequency ** 2, but it's a good baseline.
    """
    return get_linear_regression(df, x_columns=["steps"], squared_frequency=False)


def physics_linear_regression(df: pd.DataFrame, extra_columns: list[str] | None = None):
    """Linearly predict frequency**2 -> steps."""
    return get_linear_regression(
        df,
        x_columns=["steps"] + (extra_columns or []),
        squared_frequency=True,
    )
