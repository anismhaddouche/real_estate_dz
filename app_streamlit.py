import streamlit as st
import pandas as pd
import mlflow
import xgboost as xgb
import pickle


with open(f"preprocessor/DictVectorizer.b", "rb") as f_in:
    dv = pickle.load(f_in)
model = mlflow.pyfunc.load_model("models_mlflow")


# Chargement du DataFrame cleaned_data contenant les valeurs possibles pour les variables catégorielles
cleaned_data = pd.read_parquet(
    "1_cleaned_data.parquet"
)  # Remplacez par le chemin correct

# Filtrer les communes par wilaya
communes_by_wilaya = cleaned_data.groupby("wilaya")["commune"].unique()


# Fonction pour prédire le prix en utilisant le modèle chargé
def predict_price(features_dict):
    X = dv.transform(features_dict)
    return model.predict(X)[0]


# Titre de l'application
st.title("Application de Prédiction de Prix")

# Interface utilisateur pour saisir les valeurs des variables
st.header("Veuillez saisir les valeurs des variables :")

# Filtrer les communes par wilaya sélectionnée
wilaya = st.selectbox("Wilaya", cleaned_data["wilaya"].unique())

communes_in_selected_wilaya = communes_by_wilaya[wilaya]
commune = st.selectbox("Commune", communes_in_selected_wilaya)
# Variables catégorielles
category = st.selectbox("Catégorie", cleaned_data["category"].unique())

# Variables numériques
location_duree = st.slider(
    "Durée de la location (en mois)", min_value=1, max_value=36, value=12
)
superficie = st.number_input("Superficie (m²)", value=100)
pieces = st.number_input("Nombre de pièces", value=3)
etages = st.number_input("Nombre d'étages", value=1)


# Bouton pour effectuer la prédiction
if st.button("Prédire le Prix"):
    # Créer un dictionnaire avec les valeurs saisies par l'utilisateur
    user_input = {
        "location_duree": location_duree,
        "superficie": superficie,
        "pieces": pieces,
        "etages": etages,
        "category": category,
        "wilaya": wilaya,
        "commune": commune,
    }

    # Effectuer la prédiction
    predicted_price = predict_price(user_input)

    # Afficher le résultat de la prédiction
    st.success(f"Le prix prédit est : {predicted_price:.2f} DA")
