import pandas as pd
from prefect import task, flow
from pathlib import Path
import pickle
import numpy as np
import sklearn
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
import mlflow
import xgboost as xgb
from hyperopt import fmin, tpe, hp, STATUS_OK, Trials
from hyperopt.pyll import scope
import scipy


@task
def feature_engineering(
    path_cleaned_data=Path("data/1_cleaned_data.parquet"),
) -> pd.DataFrame:
    """
    Prepare the data for machines learning models. More precisely:
        - Choose the target and features
        - Drop all missing values
        - Dealing with outliers

    Args:
        path_cleaned_data: The path of the 1_cleaned_data file

    Returns:
        data: The cleaned dataframe.

    TODO:
        - improving outliers dealing methode
        - make some transformation on the target and some features
    """

    # Prepare data
    data_cleaned = pd.read_parquet(path_cleaned_data)

    # Keep only annoncement with "priceUnit == MILLION"
    data_cleaned = data_cleaned[data_cleaned["priceUnit"] == "MILLION"]

    # Delete ligne where the price == 1
    data_cleaned = data_cleaned[(data_cleaned["price"] > 1)]
    # Choose the target and features
    target = ["price"]
    features_num = ["location_duree", "superficie", "pieces", "etages"]
    features_cat = ["category", "wilaya", "commune"]

    # Create new data frame with selected features
    data = data_cleaned[["createdAt"] + features_num + features_cat + target]

    # Drop all missing values
    data.dropna(inplace=True)

    # Dealing with outliers
    factor = 1.5
    replace_with = None
    for feature in ["price", "superficie"]:
        Q1 = data[feature].quantile(0.25)
        Q3 = data[feature].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - factor * IQR
        upper_bound = Q3 + factor * IQR

        # Identify and potentially replace outliers
        outliers = (data[feature] < lower_bound) | (
            data[feature] > upper_bound
        )
        if replace_with is not None:
            data.loc[outliers, feature] = replace_with
        else:
            data = data[~outliers]

    data.sort_values(by="createdAt", ascending=True, inplace=True)
    return data


@task
def prepare_data(
    data: pd.DataFrame,
) -> (
    scipy.sparse._csr.csr_matrix,
    scipy.sparse._csr.csr_matrix,
    np.ndarray,
    np.ndarray,
    sklearn.feature_extraction.DictVectorizer,
):
    """
    Prepare the data for the XGboost model

    """

    # Calculate the number of rows for training and validation
    num_rows = data.shape[0]
    num_rows_train = int(0.8 * num_rows)
    # num_rows_val = num_rows - num_rows_train

    # Split the DataFrame into training and validation
    df_train = data[:num_rows_train]
    df_val = data[num_rows_train:]
    df_val.to_parquet("data/reference_data.parquet")

    categorical = ["category", "commune"]
    numerical = ["location_duree", "superficie", "pieces", "etages"]

    # Vectorize categorical values in order to prepare data for xgboost
    dv = DictVectorizer()
    train_dicts = df_train[categorical + numerical].to_dict(orient="records")
    X_train = dv.fit_transform(train_dicts)
    val_dicts = df_val[categorical + numerical].to_dict(orient="records")
    X_val = dv.transform(val_dicts)
    y_train = df_train["price"].values
    y_val = df_val["price"].values
    return X_train, X_val, y_train, y_val, dv


def objective(params, train, valid, y_val):
    """
    Create an objectif function for hyperopt in ordre to found best xgboost hyperparameters
    """
    with mlflow.start_run():
        mlflow.set_tag("model", "xgboost")
        mlflow.log_params(params)
        booster = xgb.train(
            params=params,
            dtrain=train,
            num_boost_round=1000,
            evals=[(valid, "validation")],
            early_stopping_rounds=50
            # early_stopping_rounds=2
        )
        y_pred = booster.predict(valid)
        rmse = mean_squared_error(y_val, y_pred, squared=False)
        mape = mean_absolute_percentage_error(y_val, y_pred)
        mlflow.log_metric("mape", mape)
        mlflow.log_metric("rmse", rmse)

    return {"loss": rmse, "mape": mape, "status": STATUS_OK}


@task(log_prints=True)
def found_best_model(
    X_train: scipy.sparse._csr.csr_matrix,
    X_val: scipy.sparse._csr.csr_matrix,
    y_train: np.ndarray,
    y_val: np.ndarray,
) -> dict:
    """
    Found the best xgboost hyperparameters
    """
    train = xgb.DMatrix(X_train, label=y_train)
    valid = xgb.DMatrix(X_val, label=y_val)

    search_space = {
        "max_depth": scope.int(hp.quniform("max_depth", 2, 200, 1)),
        "learning_rate": hp.loguniform("learning_rate", -10, 0),
        "reg_alpha": hp.loguniform("reg_alpha", -10, -1),
        "reg_lambda": hp.loguniform("reg_lambda", -10, -1),
        "min_child_weight": hp.loguniform("min_child_weight", -10, 3),
        "objective": "reg:squarederror",
        "seed": 42,
        "colsample_bytree": hp.uniform(
            "colsample_bytree", 0.6, 1.0
        ),  # Ajouter colsample_bytree
        "gamma": hp.loguniform("gamma", -5, 1),  # Ajouter gamma
    }

    # Saving best results
    best_params = fmin(
        fn=lambda params: objective(params, train, valid, y_val),
        space=search_space,
        algo=tpe.suggest,
        max_evals=50,
        trials=Trials(),
    )
    return best_params


@task(log_prints=True)
def train_best_model(
    X_train: scipy.sparse._csr.csr_matrix,
    X_val: scipy.sparse._csr.csr_matrix,
    y_train: np.ndarray,
    y_val: np.ndarray,
    dv: sklearn.feature_extraction.DictVectorizer,
    best_params: dict,
) -> None:
    """train a model with best hyperparams and write everything out"""
    train = xgb.DMatrix(X_train, label=y_train)
    valid = xgb.DMatrix(X_val, label=y_val)
    with mlflow.start_run():
        mlflow.log_params(best_params)
        booster = xgb.train(
            params=best_params,
            dtrain=train,
            num_boost_round=1000,
            evals=[(valid, "validation")],
            early_stopping_rounds=100,
        )

        y_pred = booster.predict(valid)
        rmse = mean_squared_error(y_val, y_pred, squared=False)
        mlflow.log_metric("rmse", rmse)
        mape = mean_absolute_percentage_error(y_val, y_pred)
        mlflow.log_metric("mape", mape)

        Path("models").mkdir(exist_ok=True)
        with open("models/DictVectorizer.b", "wb") as f_out:
            pickle.dump(dv, f_out)

        # with open ('models/xgboost.bin', 'wb') as f_out:
        #     pickle.dump ( booster, f_out)
        mlflow.log_artifact(
            "models/DictVectorizer.b", artifact_path="preprocessor"
        )
        mlflow.xgboost.log_model(booster, artifact_path="models_mlflow")

    # The commented code is saving the trained DictVectorizer object (`dv`) and the trained XGBoost
    # model (`booster`) as binary files using the pickle module.

    return None


@flow
def main_flow() -> None:
    """The main training pipeline"""

    # MLflow settings
    # mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("project-train-best-model-experiment")
    # Prepare data
    data = feature_engineering(
        path_cleaned_data=Path("data/1_cleaned_data.parquet")
    )
    X_train, X_val, y_train, y_val, dv = prepare_data(data)
    # Found best params
    best_params = found_best_model(X_train, X_val, y_train, y_val)
    best_params["max_depth"] = int(best_params["max_depth"])

    # # Train the best model
    train_best_model(X_train, X_val, y_train, y_val, dv, best_params)


if __name__ == "__main__":
    main_flow()
