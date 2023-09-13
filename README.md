# real estate dz 
This repository contains the final project of the MLOps Zoomcamp 2023, offered by DataTalksClub (https://datatalks.club). You can explore the project's structural design by following this <a href="docs/project_schema.png">link</a>.


## Project description

## Tips for improvement 
### Improve the prediction model (xgboost)
* Get more data (actually we have 7937 announcements)
* Improve the feature engineering 
* The model was trained with theses variabels ```    categorical  = ["category",	"commune"]
numerical = ["location_duree",	"superficie",	"pieces",	"etages"]```
we may improve the model by adding other variables


## TODO 

* Améliorer l'application  : par exemple pour local il n'a pas de nombre de chambre
* gérer les conflit de version affichées dans le message d'erreur de l'application (mlflow)
* réfléchir à comment copier le meilleur model dans docker de l'application 

    COPY ["mlruns/282919090807413278/d032f6cdaf864e5286ca13fe404433a7/artifacts","app_streamlit.py", "data/1_cleaned_data.parquet","./"]

* Rajouter un TB à graphana sur les annonces disponibles et essaye de rajouter le prédicteur des prix

## Credentials

* Grafana : admin, admin 
* adminer : postgres, exampl
<!-- docker run -it  --rm -p 9096:9096  mlopszoomcamp_2023_project:v1 -->