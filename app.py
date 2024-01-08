from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from utils.calculations import (
    calculate_bmr,
    weighted_random_choice,
    activity_multiplier,
)
from bson.regex import Regex
import os
from dotenv import load_dotenv

load_dotenv()



app = Flask(__name__)

cors = CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "https://wellnessmate.vercel.app"]}})


# user_variable_name = "USERNAME"
# user = os.environ.get(user_variable_name)
# password_variable_name = "PASSWORD"
# password = os.environ.get(password_variable_name)
uri = f'mongodb+srv://emanUser:viewingPassword@wellnessmate.fqctlmb.mongodb.net/?retryWrites=true&w=majority'

# Database and Collection names
DATABASE_NAME = "WellnessDatabase"
COLLECTION_NAME = "Recipes"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi("1"))

db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]


@app.route("/mealplan", methods=["POST"])
@cross_origin()
def create_mealplan():
    data = request.json
    # User Details
    user_details = data.get("userDetails")
    print(user_details)

    # Define the keys that need to exist
    required_keys = ["gender", "weight", "height", "age", "activity_level"]

    # Check if all required keys exist in the user_details dictionary
    all_keys_exist = all(key in user_details for key in required_keys)

    # Calculate Target Calories if all keys exist
    if all_keys_exist:
        target_calories = calculate_bmr(
            user_details["gender"],
            user_details["weight"],
            user_details["height"],
            user_details["age"],
        ) * (activity_multiplier[user_details["activity_level"]] or 1.375)
    else:
        # Handle the case where not all required keys exist
        target_calories = 2000  # Or set to some default value or handle accordingly

    target_breakfast_calories = target_calories * 0.2 or 500
    breakfast_search_keyword = "breakfast"

    target_meal_calories = target_calories * 0.3 or 750
    target_snack_calories = target_calories * 0.1 or 250

    mealplan_goals = user_details.get("goals", "lose_weight")

    eating_frequency = user_details.get("eating_frequency")
    breakfast_quantity = 1 if eating_frequency.get("breakfast") == "Yes" else 0
    meal_quantity = int(eating_frequency.get("meals", "2"))
    snack_quantity = int(eating_frequency.get("snacks", "2"))

    breakfast_query = {
        "$and": [
            {"kcal": {"$gt": target_breakfast_calories * 0.8}},
            {"kcal": {"$lt": target_breakfast_calories}},
            {
                "$or": [
                    {
                        "subcategory": {"$regex": Regex(breakfast_search_keyword, "i")}
                    },  # Case-insensitive subcategory search
                    {
                        "description": {"$regex": Regex(breakfast_search_keyword, "i")}
                    },  # Case-insensitive OR condition for description
                ]
            },
        ]
    }

    meal_query = {
        "$and": [
            {"kcal": {"$gt": target_meal_calories * 0.8}},
            {"kcal": {"$lt": target_meal_calories}},
        ]
    }
    snack_query = {
        "$and": [
            {"kcal": {"$gt": target_snack_calories * 0.3}},
            {"kcal": {"$lt": target_snack_calories}},
        ]
    }

    breakfast_results = list(collection.find(breakfast_query))
    # Convert ObjectId to string for JSON serialization
    for result in breakfast_results:
        result["_id"] = str(result["_id"])

    meal_results = list(collection.find(meal_query))
    # Convert ObjectId to string for JSON serialization
    for result in meal_results:
        result["_id"] = str(result["_id"])

    snack_results = list(collection.find(snack_query))
    # Convert ObjectId to string for JSON serialization
    for result in snack_results:
        result["_id"] = str(result["_id"])

    breakfast_choice = weighted_random_choice(
        breakfast_results,
        "rating",
        user_details["food_preferences"],
        user_details["allergies"],
        user_details["excluded_foods"],
        mealplan_goals,
        breakfast_quantity,
    )
    meal_choices = weighted_random_choice(
        meal_results,
        "rating",
        user_details["food_preferences"],
        user_details["allergies"],
        user_details["excluded_foods"],
        mealplan_goals,
        meal_quantity,
    )
    snack_choices = weighted_random_choice(
        snack_results,
        "rating",
        user_details["food_preferences"],
        user_details["allergies"],
        user_details["excluded_foods"],
        mealplan_goals,
        snack_quantity,
    )

    response_data = {
        "breakfast": breakfast_choice.tolist(),
        "meals": meal_choices.tolist(),
        "snacks": snack_choices.tolist(),
    }

    return response_data


def find_similar_recipes(recipe, limit=3):
    # Use the text index for similarity search
    # Customize the query as needed based on your text index configuration
    query = {
        "$text": {
            "$search": recipe["name"]
        },  # You can change this to another field if needed
        "id": {"$ne": recipe["id"]},  # Exclude the current recipe
    }

    # Sort the results by text search score to get the most similar recipes first
    cursor = collection.find(query, {"_id": 0}).sort(
        [("score", {"$meta": "textScore"})]
    )

    # Limit the number of recommendations
    recommendations = list(cursor.limit(limit))

    # Convert ObjectId to string for JSON serialization in recommendations
    # for rec in recommendations:
    #     rec["_id"] = str(rec["_id"])

    return recommendations


@app.route("/recipe", methods=["POST"])
@cross_origin()
def get_recipe():
    data = request.json
    recipe_id = data.get("id")

    if not recipe_id:
        return jsonify({"error": "No ID provided"}), 400

    try:
        # Find the requested recipe by ID
        document = collection.find_one({"id": recipe_id})

        if document:
            # Convert ObjectId to string for JSON serialization
            document["_id"] = str(document["_id"])

            # Use the text index to find similar recipes
            recommendations = find_similar_recipes(document, 3)

            # Construct the response object
            response = {"recipe": document, "recommendations": recommendations}
            return jsonify(response)
        else:
            return jsonify({"error": "Recipe not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/explore", methods=["GET"])
@cross_origin()
def explore():
    query = {}

    results = list(collection.find(query).limit(20))

    # Convert ObjectId to string for JSON serialization
    for result in results:
        result["_id"] = str(result["_id"])

    return jsonify(results)


@app.route("/search", methods=["POST"])
@cross_origin()
def search():
    search_data = request.get_json()

    # Extract search term, prep boundary, cooking boundary, calorie boundary, protein boundary, and nutri score boundary
    search_term = search_data.get("searchTerm")
    prep_boundary = search_data.get("prepBoundary")
    cooking_boundary = search_data.get("cookingBoundary")
    calorie_boundary = search_data.get("calorieBoundary")
    protein_boundary = search_data.get("proteinBoundary")
    nutri_score_boundary = search_data.get("nutriScoreBoundary")

    # Initialize an empty query
    query = {}

    # Add search criteria to the query if search_term is not empty
    if search_term:
        # Text-based search using $text and $search
        query["$or"] = [
            {"description": {"$regex": search_term}},
            {"name": {"$regex": search_term}},
            # {"$text": {"$search": search_term}}  # Adding the text-based search criteria
        ]

    # Add cooking_boundary condition if it's a number and not null
    if isinstance(cooking_boundary, (int, float)):
        query["times.Cooking"] = {"$lte": cooking_boundary}

    # Add prep_boundary condition if it's a number and not null
    if isinstance(prep_boundary, (int, float)):
        query["times.Preparation"] = {"$lte": prep_boundary}

    # Add calorie_boundary condition if it's a number and not null
    if isinstance(calorie_boundary, (int, float)):
        query["kcal"] = {"$lte": calorie_boundary}

    # Add protein_boundary condition if it's a number and not null
    if isinstance(protein_boundary, (int, float)):
        query["protein"] = {"$gte": protein_boundary}

    # Add nutri_score_boundary condition if it's a number and not null
    if isinstance(nutri_score_boundary, (int, float)):
        query["nutritional_score"] = {"$gte": nutri_score_boundary}

    results = list(collection.find(query).limit(20))

    # Convert ObjectId to string for JSON serialization
    for result in results:
        result["_id"] = str(result["_id"])

    return jsonify(results)


# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=5000)
