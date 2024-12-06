import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

from autoguitar.tuning.dataset import get_sklearn_datasets


def get_rmse_cents(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root mean squared error in cents.

    Makes sense for comparing frequencies, though not for steps.
    """
    return np.sqrt(np.mean((1200 * np.log2(y_true / y_pred)) ** 2))


def naive_linear_regression(df: pd.DataFrame):
    """Linearly predict frequency -> steps.

    This doesn't make sense from a physics perspective because it's rather
    frequency**2 -> steps, but it's a good baseline.
    """
    X_train, y_train, X_test, y_test = get_sklearn_datasets(df, x_columns=["frequency"])

    model = LinearRegression()
    model.fit(X_train, y_train)

    test_predictions = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, test_predictions))

    steps_predicted = model.predict(df[["frequency"]])

    return model, rmse, steps_predicted


def physics_linear_regression(df: pd.DataFrame):
    """Linearly predict frequency**2 -> steps."""
    df = df.copy()
    df["frequency_squared"] = df["frequency"] ** 2
    X_train, y_train, X_test, y_test = get_sklearn_datasets(
        df, x_columns=["frequency_squared"]
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    test_predictions = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, test_predictions))

    steps_predicted = model.predict(df[["frequency"]] ** 2)

    return model, rmse, steps_predicted
