import pickle
from pathlib import Path
import streamlit as st
from sklearn.feature_extraction import DictVectorizer
import xgboost as xgb


#TODO : retravailler la partie choix des features (importer les wilaya, commune et spécifier le type de chaque variable)




# Charger le modèle et le vectoriseur
Path_model = Path("xgboost.bin")
Path_vectorizer = Path("DictVectorizer.b")
with open(Path_model, "rb") as f_in:
    model = pickle.load(f_in)
with open(Path_vectorizer, "rb") as f_in:
    dv = pickle.load(f_in)

# Fonction de prédiction
def predict(features):
    X = dv.transform(features)
    pred = model.predict(X)
    return pred[0]

# Interface Streamlit
st.title("Price Estimation App")

st.write("Enter the features for prediction:")
# #data_to_predict =   {
#     "commune": 'Hydra',
#     "location_duree": 6,
#     "superficie": 250,
#     "pieces": 8,
#     "etages": 1,
#     "category": 'Appartement'
# }
feature1 = st.number_input("commune")
feature2 = st.number_input("location_duree")
feature3 = st.number_input("superficie")
feature4 = st.number_input("pieces")
feature5 = st.number_input("etages")
feature6 = st.number_input("category")

# ... Ajoutez des champs pour les autres caractéristiques ...

if st.button("Predict"):
    input_data = {
        'category':feature6,
        'commune': feature1,
        'location_duree': feature2,
        'superficie':feature3,
        'pieces':feature4,
        'etages':feature5
            
        # ... Ajoutez d'autres caractéristiques ici ...
    }
    
    prediction = predict([input_data])
    st.write(f"Predicted Price: {int(prediction)}")
