import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from autoguitar.tuning.dataset import get_sklearn_datasets


def get_rmse_cents(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root mean squared error in cents.

    Makes sense for comparing frequencies, though not for steps.
    """
    return np.sqrt(np.mean((1200 * np.log2(y_true / y_pred)) ** 2))


def naive_linear_regression(df: pd.DataFrame):
    """Linearly predict steps -> frequency.

    This doesn't make sense from a physics perspective because it's rather
    steps -> frequency ** 2, but it's a good baseline.
    """
    X_train, y_train, _X_test, _y_test = get_sklearn_datasets(
        df, x_columns=["steps"], y_column="frequency"
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    frequency_predicted = model.predict(df[["steps"]])

    test_mask = (df["split"] == "test") & df["stable"]
    rmse = get_rmse_cents(
        df.loc[test_mask, "frequency"],
        frequency_predicted[test_mask],
    )

    return model, rmse, frequency_predicted


def physics_linear_regression(df: pd.DataFrame, extra_columns: list[str] | None = None):
    """Linearly predict frequency**2 -> steps."""
    df = df.copy()
    df["frequency_squared"] = df["frequency"] ** 2

    x_columns = ["steps"] + (extra_columns or [])

    X_train, y_train, _X_test, _y_test = get_sklearn_datasets(
        df, x_columns=x_columns, y_column="frequency_squared"
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    frequency_predicted = model.predict(df[x_columns]) ** 0.5

    test_mask = (df["split"] == "test") & df["stable"]
    rmse = get_rmse_cents(
        df.loc[test_mask, "frequency"],
        frequency_predicted[test_mask],
    )

    return model, rmse, frequency_predicted
