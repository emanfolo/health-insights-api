import numpy as np

activity_multiplier = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "extremely_active": 1.9,
}


def calculate_normalized_protein_score(protein, kcal):
    optimal_protein_ratio = 0.3

    # Calculate protein ratio per calorie
    protein_ratio = protein * 4 / kcal

    # Calculate the protein score as the deviation from the optimal ratio
    protein_score = max(
        0, min(100, 100 - abs(optimal_protein_ratio - protein_ratio) * 100)
    )

    # Normalize the protein score to a range of [0, 5]
    return protein_score / 20


def calculate_nutrition_score(
    carbs, fat, protein, fiber, saturates, kcal, sugars, salt
):
    # Calculate % of calories that are coming from each macro
    carbs_ratio = carbs * 4 / kcal
    fat_ratio = fat * 9 / kcal
    protein_ratio = protein * 4 / kcal

    # Calculate score for other nutrients
    fiber_score = 0.1 * fiber
    saturates_score = -0.3 * saturates
    sugars_score = -0.2 * sugars
    salt_score = -0.1 * salt

    # Optimal ratios
    optimal_carbs_ratio = 0.5
    optimal_protein_ratio = 0.3
    optimal_fat_ratio = 0.2

    # Calculate individual scores for each ratio
    carbs_score = max(0, min(100, 100 - abs(optimal_carbs_ratio - carbs_ratio) * 100))
    protein_score = max(
        0, min(100, 100 - abs(optimal_protein_ratio - protein_ratio) * 100)
    )
    fat_score = max(0, min(100, 100 - abs(optimal_fat_ratio - fat_ratio) * 100))

    # Combine individual scores to get an overall score
    macros_score = (carbs_score + protein_score + fat_score) / 3
    overall_score = max(
        0,
        min(
            100,
            macros_score + saturates_score + sugars_score + salt_score + fiber_score,
        ),
    )
    rounded_score = round(overall_score)

    return rounded_score


# Revised Harris-Benedict Equation
def calculate_bmr(gender="male", weight=80, height=170, age=30):
    if gender == "male":
        return 13.397 * weight + 4.799 * height - 5.677 * age + 88.362
    elif gender == "female":
        return 9.247 * weight + 3.098 * height - 4.330 * age + 447.593
    else:
        return 2000


def weighted_random_choice(
    objects,
    weight_key,
    food_preferences,
    allergies,
    excluded_foods,
    goals,
    maxResults=3,
):
    try:
        # Convert food_preferences and allergies to lowercase sets for case-insensitive matching
        food_preferences_set = {preference.lower() for preference in food_preferences}
        allergies_set = {allergy.lower() for allergy in allergies}
        excluded_foods_set = {excluded_food.lower() for excluded_food in excluded_foods}

        # Calculate weights and adjust based on the condition
        weights = []
        recipes = []

        for obj in objects:
            weight = obj.get(weight_key, 1)

            # Check if any food_preference is a substring of obj.get("description")
            description = obj.get("description", "")
            if any(
                preference in description.lower() for preference in food_preferences_set
            ):
                print("I've found a match to one of your preferences")
                weight += 3  # Add 3 to the weight if a match is found

            # Normalize protein score, and add it to the weight
            if goals == "gain_muscle":
                normalized_nutrition_score = obj.get("protein_score", 0) / 20
                weight += normalized_nutrition_score

            # Check the NutriScore, normalize it and add it to the weight
            normalized_nutrition_score = obj.get("nutrition_score", 0) / 20
            weight += normalized_nutrition_score

            ingredients = obj.get("ingredients", [])
            # Check if any ingredient includes any allergy as a substring
            if any(
                allergy in ingredient.lower()
                for allergy in allergies_set
                for ingredient in ingredients
            ):
                continue

            # Check if any ingredient includes any excluded foods as a substring
            if any(
                excluded_food in ingredient.lower()
                for excluded_food in excluded_foods_set
                for ingredient in ingredients
            ):
                continue

            recipes.append(obj)
            weights.append(weight)

        # Normalize weights to make sure they sum up to 1
        weights_normalized = np.array(weights) / np.sum(weights)
        # Perform weighted random choice
        weighted_selected_item = np.random.choice(
            recipes, size=maxResults, replace=False, p=weights_normalized
        )

        return weighted_selected_item

    except Exception as e:
        # Handle the specific exception types you expect, log the error, or perform other actions
        print(f"An error occurred: {str(e)}")
        # You might want to return a default or handle the error in an appropriate way
        return None
