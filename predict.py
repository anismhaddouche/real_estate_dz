import pickle
from pathlib import Path 
import mlflow
from flask import Flask, request, jsonify


# # def load_model_vect(Path_model = Path("xgboost.bin"),Path_vectorizer = Path("DictVectorizer.b")): 
# #     with open (Path_model, "rb") as f_in:
# #         model = pickle.load(f_in)
# #     with open (Path_vectorizer, "rb") as f_in:
# #         dv = pickle.load(f_in)
# #     print(model,dv)
# #     return model, dv


# Path_model = Path("xgboost.bin")
# Path_vectorizer = Path("DictVectorizer.b")
# with open (Path_model, "rb") as f_in:
#     model = pickle.load(f_in)
# with open (Path_vectorizer, "rb") as f_in:
#     dv = pickle.load(f_in)  

EXPERIMENT_NAME = "project-train-best-model-experiment"   

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


def predict(features) : 
    X = dv.transform(features)
    pred = model.predict(X)
    return pred[0]

app = Flask("price-estimation")

@app.route("/predict", methods=['POST'])
def predict_endpoint():
    data_to_predict = request.get_json()
    pred = predict(data_to_predict)
    result  = {'Price': int(pred) }
    return jsonify(result)
    

if __name__ == "__main__":
    app.run(debug=True,host='localhost',port=9696)

