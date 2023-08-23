# mlopszoomcamp_2023_project
This repository contains the final project of the MLOps Zoomcamp 2023, offered by DataTalksClub (https://datatalks.club). You can explore the project's structural design by following this <a href="docs/project_schema.png">link</a>.


## Project description 

## Tips for improvement 
### Improve the prediction model (xgboost)
* Get more data (actually we have 7937 announcements)
* Improve the feature engineering 
* The model was trained with theses variabels ```    categorical  = ["category",	"commune"]
numerical = ["location_duree",	"superficie",	"pieces",	"etages"]```
we may improve the model by adding other variables

## Gabarit 

"""
    Brief description of what the function does.

    Args:
        parameter_name (parameter_type): Description of the parameter.

    Returns:
        json_file_path: the raw data.
    
    Raises:
        ExceptionType: Description of exceptions raised (if applicable).

    Example:
        An example usage of the function.

    TODO:
        - rajouter une condition pour uniquement fetcher les données manquantes 
        - demander à adel de mettre une description plus claire 
    """
## TODO : 
Créer un dashboard 
suivre ce lien pour faire des prédiction https://github.com/DataTalksClub/mlops-zoomcamp/blob/main/04-deployment/batch/score.ipynb`

### Etapes de deployement 
* créer le modéle 
* le mettre dans une application flask 
* Packager le tout sur docker 
* étapes en détails:
  * cérer un ev virtuelle avec pipevn dans  un nouveau dossier appeler deployement 
  * prendre les version de sklearn (xgboost aussi ? ) de la ou j'ai entrainer le modéle 
  * créer une fonction predict qui charge le model fait du feature engineering si besoin et retourn la prediction 

## Credentials :
* Grafana : admin, admin 
* adminer : postgres, example
<!-- docker run -it  --rm -p 9096:9096  mlopszoomcamp_2023_project:v1 -->