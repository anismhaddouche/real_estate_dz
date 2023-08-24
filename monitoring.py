import mlflow
import pickle
import pandas as pd 
import datetime
import time
import logging 
import pickle
from pathlib import Path
import psycopg

from prefect import task, flow,get_run_logger

from evidently.report import Report
from evidently import ColumnMapping
from evidently.metrics import ColumnDriftMetric, DatasetDriftMetric, DatasetMissingValuesMetric

# logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

SEND_TIMEOUT = 10
EXPERIMENT_NAME = "project-train-best-model-experiment"   

# create_table_statement = """
# drop table if exists dummy_metrics;
# create table dummy_metrics(
# 	timestamp timestamp,
# 	prediction_drift float,
# 	num_drifted_columns integer,
# 	share_missing_values float
# )
# """

create_table_statement = """
create table if not exists dummy_metrics(
    timestamp timestamp,
    prediction_drift float,
    num_drifted_columns integer,
    share_missing_values float
)
"""

num_features = ['location_duree', 'superficie', 'pieces', 'etages']
cat_features = ['category', 'wilaya']
   
# Create evidently report 
column_mapping = ColumnMapping(
    prediction='price_pred',
    numerical_features=num_features,
    categorical_features=cat_features,
    target=None
)

report = Report(metrics = [
    ColumnDriftMetric(column_name='price_pred'),
    DatasetDriftMetric(),
    DatasetMissingValuesMetric()
])



def load_best_model_dictvec(experiment_name : str):
    """ Load the best model which is saved as in artifacts/models_mlflow""" 
    experiment = mlflow.get_experiment_by_name(experiment_name)
    EXPERIMENT_ID = experiment.experiment_id
    df = mlflow.search_runs([EXPERIMENT_ID], order_by=["metrics.rmse"])
    RUN_ID  = df[df["tags.mlflow.log-model.history"].notna()]['run_id'].values[0]
    best_model = f'runs:/{RUN_ID}/models_mlflow'
    with open(f"mlruns/{EXPERIMENT_ID}/{RUN_ID}/artifacts/preprocessor/DictVectorizer.b","rb") as f_in:
       dv = pickle.load(f_in)
    print(f"Loading the model of run  = {RUN_ID}")
    return dv, mlflow.pyfunc.load_model(best_model)

dv, model = load_best_model_dictvec(EXPERIMENT_NAME)


@task
def prep_db():
	with psycopg.connect("host=localhost port=5432 user=postgres password=example", autocommit=True) as conn:
		res = conn.execute("SELECT 1 FROM pg_database WHERE datname='test'")
		if len(res.fetchall()) == 0:
			conn.execute("create database test;")
		with psycopg.connect("host=localhost port=5432 dbname=test user=postgres password=example") as conn:
			conn.execute(create_table_statement)
 
@task   
def prep_data(model,dv) -> (pd.DataFrame,pd.DataFrame):
    data = pd.read_parquet('data/reference_data.parquet')
    data['createdAt'] = data['createdAt'].dt.tz_localize(None)
    data = data.reset_index(drop=True)
    data.sort_values(by="createdAt", ascending=True,inplace=True)
    total_rows = len(data)
    num_rows_first_df = int(total_rows * 0.8)
    num_rows_second_df = total_rows - num_rows_first_df
    X = data[num_features+cat_features]
    X = X.to_dict('records')
    data['price_pred'] = model.predict(dv.transform(X))
    reference_data = data.head(num_rows_first_df)
    raw_data = data.drop('price_pred',axis = 1).tail(num_rows_second_df)
    return raw_data, reference_data 
 
 
@task(log_prints=False)
def calculate_metrics_postgresql(curr, current_data, reference_data):
    X = current_data[num_features+cat_features]
    X = X.to_dict('records')
    current_data['price_pred'] = model.predict(dv.transform(X))
    report.run(reference_data = reference_data, current_data = current_data,
    column_mapping=column_mapping)
    result = report.as_dict()
    prediction_drift = result['metrics'][0]['result']['drift_score']
    num_drifted_columns = result['metrics'][1]['result']['number_of_drifted_columns']
    share_missing_values = result['metrics'][2]['result']['current']['share_of_missing_values']
    try:
        
        curr.execute(
            "insert into dummy_metrics(timestamp, prediction_drift, num_drifted_columns, share_missing_values) values (%s, %s, %s, %s)",
            (current_data["createdAt"].max(), prediction_drift, num_drifted_columns, share_missing_values)
        )
    except:
        curr.execute(
            "insert into dummy_metrics(timestamp, prediction_drift, num_drifted_columns, share_missing_values) values (%s, %s, %s, %s)",
            (current_data["createdAt"].max(), None, None, None)
        )
    return None



@flow()
def batch_monitoring_backfill(batch_size :int)-> None:
    logger = get_run_logger() 
    prep_db()
    raw_data, reference_data = prep_data(model,dv)
    num_batches = (len(raw_data) + batch_size - 1) // batch_size
	# Initialiser les variables
    start_index = 0
    end_index = 0
    last_send = datetime.datetime.now() - datetime.timedelta(seconds=10)
    with psycopg.connect("host=localhost port=5432 dbname=test user=postgres password=example", autocommit=True) as conn:
        for i in range(num_batches):
            end_index = start_index + batch_size
            current_data = raw_data.iloc[start_index:end_index]
            with conn.cursor() as curr:
                calculate_metrics_postgresql(curr, current_data, reference_data)
            start_index = end_index
            new_send = datetime.datetime.now()
            seconds_elapsed = (new_send - last_send).total_seconds()
            if seconds_elapsed < SEND_TIMEOUT:
                time.sleep(SEND_TIMEOUT - seconds_elapsed)
            while last_send < new_send:
                last_send = last_send + datetime.timedelta(seconds=10)
            logger.info(f"data of the batch {i}/{num_batches} was sent")




if __name__ == "__main__":
    batch_monitoring_backfill(batch_size = 50)