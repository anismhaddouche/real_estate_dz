import pickle
from pathlib import Path 
from flask import Flask, request, jsonify


# def load_model_vect(Path_model = Path("xgboost.bin"),Path_vectorizer = Path("DictVectorizer.b")): 
#     with open (Path_model, "rb") as f_in:
#         model = pickle.load(f_in)
#     with open (Path_vectorizer, "rb") as f_in:
#         dv = pickle.load(f_in)
#     print(model,dv)
#     return model, dv


Path_model = Path("xgboost.bin")
Path_vectorizer = Path("DictVectorizer.b")
with open (Path_model, "rb") as f_in:
    model = pickle.load(f_in)
with open (Path_vectorizer, "rb") as f_in:
    dv = pickle.load(f_in)  


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
    app.run(debug=True,host='0.0.0.0',port=9696)

