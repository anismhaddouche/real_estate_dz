from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import json
from time import sleep
from random import randint
from pathlib import Path

from prefect import task, flow 

@task 
def load_query(path):
    #TODO : description
	with open(path) as f:
		return gql(f.read())


@task
def def_var_page(page):
    #TODO : description

	return {
	  "mediaSize": "LARGE",
	  "q": None,
	  "filter": {
		"categorySlug": "immobilier-location",
		"origin": None,
		"hasPrice": True,
		"fields": [],
		"page": page,
		"count": 1000
	  }
	}

@flow()
def get_data(url="https://api.ouedkniss.com/graphql",query_path = Path("config/datas.graphql"),query_last_page_path = Path("config/pagination.graphql"),json_file_path = Path("data/0_raw_data.json")):
    
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
    
    
    # Select your transport with a defined url endpoint
    transport = AIOHTTPTransport(url=url)

    # Create a GraphQL client using the defined transport
    client = Client(transport=transport, fetch_schema_from_transport=False)

    operationName = "SearchQueryWithoutFilters"

    query_last_page = load_query(query_last_page_path)


    result_last_page = client.execute(query_last_page,operation_name=operationName,variable_values=def_var_page(1))

    lastPage = result_last_page['search']['announcements']['paginatorInfo']['lastPage']

    query = load_query(query_path)

    i = 1
    datas = []
    json_file = open(json_file_path, "a")  # append mode

    # while i <= lastPage:
    while i <= 300:

        result = client.execute(query,operation_name=operationName,variable_values=def_var_page(i))
        datas.append(result['search']['announcements']['data'])
        print(">",i,"/",lastPage)
        sleep(randint(1,2))
        
        i=i+1
        
    json.dump(datas,json_file)
    json_file.close()


if __name__ == "__main__":
    get_data()
    
    
# Sauvegarder les fichier json par mois 