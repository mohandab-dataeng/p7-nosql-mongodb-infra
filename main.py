"""
Sript de transformatioin des datasets *.csv vers insert vers MongoDB ;
 
1. Import 
2. Mapping
3. Nettoyage
4. Cast
5. Resahpe
6. Chargement

"""

# ----- Librairies -----

import os
import polars as pl
from dotenv import load_dotenv
from pymongo import MongoClient
import glob

# ----- Import du dataset -----

load_dotenv()
uri = os.getenv("MONGO_URI")
client = MongoClient(uri)
client.admin.command('ping')

files = glob.glob("data/listings*.csv")

frames = []
for path in files:
    city = path.split("listings")[1].split(".")[0]
    df = pl.read_csv(path)
    df = df.with_columns(pl.lit(city).alias("city"))
    frames.append(df)
dfv0 = pl.concat(frames)

# ----- Mapping -----

TYPE_MAPPING = {
    "Int64": [
        "id",
        "scrape_id",
        "host_id",
        "accommodates",
        "minimum_nights",
        "maximum_nights",
        "minimum_minimum_nights",
        "maximum_minimum_nights",
        "minimum_maximum_nights",
        "maximum_maximum_nights",
        "availability_30",
        "availability_60",
        "availability_90",
        "availability_365",
        "number_of_reviews",
        "number_of_reviews_ltm",
        "number_of_reviews_l30d",
        "calculated_host_listings_count",
        "calculated_host_listings_count_entire_homes",
        "calculated_host_listings_count_private_rooms",
        "calculated_host_listings_count_shared_rooms",
        "bedrooms",
        "beds",
        "host_listings_count",
        "host_total_listings_count",
    ],
    "Float64Specific": [
        "price",
        "host_response_rate",
        "host_acceptance_rate",
    ],
    "Float64": [
        "latitude",
        "longitude",
        "minimum_nights_avg_ntm",
        "maximum_nights_avg_ntm",
        "bathrooms",
        "reviews_per_month",
        "review_scores_rating",
        "review_scores_accuracy",
        "review_scores_cleanliness",
        "review_scores_checkin",
        "review_scores_communication",
        "review_scores_location",
        "review_scores_value",
    ],
    "Boolean": [
        "host_is_superhost",
        "host_has_profile_pic",
        "host_identity_verified",
        "has_availability",
        "instant_bookable",
    ],
    "Date": [
        "last_scraped",
        "host_since",
        "calendar_last_scraped",
        "first_review",
        "last_review",
    ],
    "String": [
        "listing_url",
        "source",
        "name",
        "description",
        "neighborhood_overview",
        "picture_url",
        "host_url",
        "host_name",
        "host_location",
        "host_about",
        "host_response_time",
        "host_thumbnail_url",
        "host_picture_url",
        "host_neighbourhood",
        "neighbourhood",
        "neighbourhood_cleansed",
        "property_type",
        "room_type",
        "bathrooms_text",
        "license",
    ],
    "List": [
        "amenities",
        "host_verifications",
    ]
}

FIELD_MAPPING = {
    "availability": [
        "availability_30",
        "availability_60",
        "availability_90",
        "availability_365",
        "has_availability",
        "instant_bookable",
    ],
    "host": [
        "calculated_host_listings_count",
        "calculated_host_listings_count_entire_homes",
        "calculated_host_listings_count_private_rooms",
        "calculated_host_listings_count_shared_rooms",
        "host_about",
        "host_acceptance_rate",
        "host_has_profile_pic",
        "host_id",
        "host_identity_verified",
        "host_is_superhost",
        "host_listings_count",
        "host_location",
        "host_name",
        "host_neighbourhood",
        "host_picture_url",
        "host_response_rate",
        "host_response_time",
        "host_since",
        "host_thumbnail_url",
        "host_total_listings_count",
        "host_url",
        "host_verifications",
    ],
    "location": [
        "latitude",
        "longitude",
        "neighbourhood",
        "neighbourhood_cleansed",
        "neighborhood_overview",
    ],
    "night": [
        "maximum_maximum_nights",
        "maximum_minimum_nights",
        "maximum_nights",
        "maximum_nights_avg_ntm",
        "minimum_maximum_nights",
        "minimum_minimum_nights",
        "minimum_nights",
        "minimum_nights_avg_ntm",
    ],
    "property": [
        "accommodates",
        "amenities",
        "bathrooms",
        "bathrooms_text",
        "bedrooms",
        "beds",
        "property_type",
        "room_type",
    ],
    "review": [
        "first_review",
        "last_review",
        "number_of_reviews",
        "number_of_reviews_l30d",
        "number_of_reviews_ltm",
        "review_scores_accuracy",
        "review_scores_checkin",
        "review_scores_cleanliness",
        "review_scores_communication",
        "review_scores_location",
        "review_scores_rating",
        "review_scores_value",
        "reviews_per_month",
    ],
    "scraping": [
        "calendar_last_scraped",
        "last_scraped",
        "scrape_id",
        "source",
    ],
    "root": [
        "id",
        "city",
        "description",
        "license",
        "listing_url",
        "name",
        "picture_url",
        "price",
    ],
}

# ----- Nettoyage (NAN, duplcates, col, etc.) -----

def clean(dfv0:pl.DataFrame):
    dfv0 = dfv0.with_columns(
    pl.col(pl.String).str.strip_chars().replace("", None)
    )
    dfv0 = dfv0.unique(subset=["id"])
    empty_col = [c for c in dfv0.columns if dfv0[c].null_count() / dfv0.height > 0.99]
    dfv0 = dfv0.drop(empty_col)
    return dfv0

dfv1 = clean(dfv0)

# ----- Casting -----

def cast(dfv1:pl.DataFrame):
    dfv1 = dfv1.with_columns(
        *[pl.col(c).str.replace_all(r"[$,%]", "").cast(pl.Float64, strict=False) for c in TYPE_MAPPING["Float64Specific"]],
        *[pl.col(c).cast(pl.Int64, strict=False) for c in TYPE_MAPPING["Int64"]],
        *[pl.col(c).cast(pl.Float64, strict=False) for c in TYPE_MAPPING["Float64"]],
        *[pl.col(c).str.to_datetime() for c in TYPE_MAPPING["Date"]],
        *[(pl.col(c) == "t").alias(c) for c in TYPE_MAPPING["Boolean"]],
        pl.col("host_verifications").str.replace_all("'", '"').str.replace_all("None", "null").str.json_decode(dtype=pl.List(pl.String)),
        pl.col("amenities").str.json_decode(dtype=pl.List(pl.String)),
    )
    return dfv1

dfv2 = cast(dfv1)

# ----- Reshape -----

def reshape(dfv2:pl.DataFrame):
    MAPPING = {name:[c for c in cols if c in dfv2.columns] for name, cols in FIELD_MAPPING.items()}
    dfv2 = dfv2.with_columns(*[pl.struct(cols).alias(name) for name, cols in MAPPING.items() if name != "root"])
    dfv2 = dfv2.drop(*[c for name, cols in MAPPING.items() if name != "root" for c in cols])
    return dfv2

dfv3 = reshape(dfv2)

# ----- Chargement -----

def load(dfv3, client):
    db = client["airbnb"]
    collection = db["listings"]
    collection.drop()
    docs = dfv3.to_dicts()
    collection.insert_many(docs)
    return collection.count_documents({})

print(load(dfv3, client))