from prefect import task, flow
from pathlib import Path
import pandas as pd
import json

def get_commune(x: list):
    """get the commune column"""
    # x = list_to_dict(x)
    try:
        commune = x[0]["name"]
    except:
        commune = None
    return commune

def get_wilaya(x: list):
    """get the wilaya column"""
    # x = list_to_dict(x)
    try:
        wilaya = x[0]["region"]["name"]
    except:
        wilaya = None
    return wilaya

def get_medias(column: pd.Series) -> pd.Series:
    """
    In this dataset medias means urls of the announcements.
    We create a new column containing a list of available urls
    """

    media_all = []
    for index, _ in column.items():
        media_raw = []
        for _, media in enumerate(column.loc[index]):
            try:
                media_raw.append(media["mediaUrl"])
            except:
                media_raw.append(None)
        media_all.append(media_raw)
    return pd.Series(media_all)

def get_specs(column: pd.Series) -> pd.DataFrame:
    """
    Extract the following specification from the column "specs" :
    location_duree, superficie,	pieces,	asset-in-a-promotional-site	property-specifications,
    papers,	etages	sale-by-real-estate-agent,	property-payment-conditions
    """

    specs_all = []
    # Loop on all rows
    for index, _ in column.items():
        specs_raw = {}
        if column.loc[index] != None :
            for i, spec in enumerate(column.loc[index]):
                label = spec["specification"]["codename"]
                try:
                    value = spec["value"]
                    if len(value) == 1:
                        value = value[0]
                except:
                    value = None
                # TODO: améliorer la prise en charge str(value)
                specs_raw[label] = str(value)
            specs_all.append(specs_raw)
    return pd.DataFrame(specs_all)


def clean_priceType(priceType: pd.Series) -> pd.Series:
    """Convert to a categorical type"""
    return priceType.astype("category")

def clean_priceUnit(priceUnit: pd.Series) -> pd.Series:
    """Convert to a categorical type"""
    return priceUnit.astype("category")

def clean_id(id: pd.Series) -> pd.Series:
    """convert the id to int"""
    return id.astype("int")

def clean_category(category: pd.Series) -> pd.Series:
    """Convert to a categorical type"""
    return category.astype("category")

def clean_createdAt(createdAt: pd.Series) -> pd.Series:
    """Convert to a datetime type"""
    return pd.to_datetime(createdAt)

def clean_slug(slug: pd.Series) -> pd.Series:
    """Convert to a string type"""
    return slug.astype("string")

def clean_wilaya(wilaya: pd.Series) -> pd.Series:
    """Convert to a string type"""
    return wilaya.astype("category")

def clean_commune(commune: pd.Series) -> pd.Series:
    """Convert to a string type"""
    return commune.astype("category")

def clean_location_duree(location_duree: pd.Series) -> pd.Series:
    """Convert to a int"""
    return location_duree.str.extract("(\\d)").astype("Int64")

def clean_superficie(superficie: pd.Series) -> pd.Series:
    """Convert to int ...."""
    return superficie.str.extract("(\\d+)").astype("Int64")

def clean_pieces(pieces: pd.Series) -> pd.Series:
    """Convert to int and ..."""
    return pieces.str.extract("(\\d{1,2})").astype("Int64")

def clean_asset_in_a_promotional_site(asset_in_a_promotional_site: pd.Series) -> pd.Series:
    """Convert to a bool type"""
    return asset_in_a_promotional_site.astype("bool")


def clean_property_specifications(property_specifications: pd.Series) -> pd.Series:
    """ staff"""
    #TODO : amelioration amelioration by converting to bool
    return property_specifications.astype("category")

def clean_papers(papers: pd.Series) ->  pd.Series:
    """ desc"""
    #TODO : amelioration by converting to bool
    return papers.astype("category")

def clean_etages(etages: pd.Series) -> pd.Series:
    """Convert to integer and keep only digits """
    #TODO: prendre en compte RDC
    return etages.str.extract("(\\d{1,2})").astype("Int64")

def clean_sale_by_real_estate_agent(sale_by_real_estate_agent: pd.Series) -> pd.Series:
    """" Convert to a bool type """
    return sale_by_real_estate_agent.astype("bool")

def clean_property_payment_conditions(clean_property_payment_conditions: pd.Series) -> pd.Series:
    """desc """
    return clean_property_payment_conditions.astype('category')
 
def clean_medias(medias: pd.Series) -> pd.Series:
    """desc"""
    return medias
def clean_description(description: pd.Series) -> pd.Series:
    return description.astype("string")

def clean_price(price: pd.Series) -> pd.Series:
    # return price.astype("int")
    return price



@task()
def get_asset(raw_data_path = Path("data/0_raw_data.json")) -> pd.DataFrame:
    """Preprocesses the data of announcements.

    Args:
        data: Raw data.
    Returns:
        asset: Intermediate data as a table

    """
    # Convert Data, which is a list of lists, into one flatten list
    with open(raw_data_path, 'r') as json_file:
        raw_data = json.load(json_file)

    asset = pd.DataFrame([item for sublist in raw_data for item in sublist])
    # Convert each raw of 'category', which is a dict (eg : {"name": "Appartement"}), to a sting  (eg :"Appartement")
    category = asset["category"].apply(lambda x: x["name"])
    # Get the commune
    commune = asset["cities"].apply(lambda x: get_commune(x)).rename("commune")
    # Get the wilaya
    wilaya = asset["cities"].apply(lambda x: get_wilaya(x)).rename("wilaya")
    # Get the Store name
    store = asset["store"].apply(lambda x: x.get("slug") if x is not None else None)
    # Get medias (urls)
    medias = get_medias(asset["medias"])
    # Get some specification in a DataFrame
    specs = get_specs(asset["specs"])
    specs["medias"] = medias
    # Create the outout DataFrame
    df = pd.DataFrame(
        [
            asset["id"],
            category,
            asset["slug"],
            asset["description"],
            asset["price"],
            asset["priceType"],
            asset["priceUnit"],
            wilaya,
            commune,
            asset["createdAt"],
            asset["likeCount"],
            asset["isFromStore"],
            store,
        ]
    ).T
    asset = df.join(specs)
    return asset



@flow()
def clean_asset() -> pd.DataFrame:
    """Clean each column according to its specific clean function"""
    
    asset = get_asset()
    
    jobs = {
        "priceType": clean_priceType,
        "priceUnit": clean_priceUnit,
        "id": clean_id,
        "category": clean_category,
        "createdAt": clean_createdAt,
        "slug": clean_slug,
        "wilaya": clean_wilaya,
        "commune": clean_commune,
        "location_duree": clean_location_duree,
        "superficie": clean_superficie,
        "pieces": clean_pieces,
        "asset-in-a-promotional-site": clean_asset_in_a_promotional_site,
        "property-specifications": clean_property_specifications,
        "papers": clean_papers,
        "etages": clean_etages,
        "sale-by-real-estate-agent":clean_sale_by_real_estate_agent,
        "property-payment-conditions": clean_property_payment_conditions,
        "medias": clean_medias,
        "description":clean_description,
        "price":clean_price

    }

    for column, func in jobs.items():
        asset[column] = func(asset[column])
    asset_cleaned = asset
    asset_cleaned.to_parquet("data/1_cleaned_data.parquet")
    return None



if __name__ == "__main__":
    clean_asset()
    
    
# @flow()
# def clean_data(raw_data = Path("data/0_raw_data.json")):
    
    
    
    
#     cleaned_data = None
#     return cleaned_data
