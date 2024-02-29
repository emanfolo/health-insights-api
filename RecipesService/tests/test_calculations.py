import sys
from unittest.mock import patch
import numpy as np
from os.path import dirname, abspath, join
sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'utils'))
from calculations import calculate_normalized_protein_score, calculate_nutrition_score, calculate_bmr, weighted_random_choice
import unittest


class TestCalculateNormalizedProteinScore(unittest.TestCase):

    def test_optimal_protein(self):
        # Test case where the protein ratio is optimal
        self.assertAlmostEqual(
            calculate_normalized_protein_score(30, 400), 
            5, 
            places=2,
            msg="Should return 5 for optimal protein ratio"
        )

    def test_high_protein(self):
        # Test case where the protein content is very high
        self.assertAlmostEqual(
            calculate_normalized_protein_score(200, 400), 
            0.0, 
            places=2,
            msg="Should return 0 for when protein ratio is too high"
        )

    def test_low_protein(self):
        # Test case where the protein content is very low
        self.assertAlmostEqual(
            calculate_normalized_protein_score(0, 400), 
            3.5, 
            places=2,
            msg="Should return 3.5 for low protein ratio"
        )

    def test_zero_calories(self):
        # Test case where calorie content is zero to prevent division by zero error
        with self.assertRaises(ZeroDivisionError, msg="Should raise ZeroDivisionError when kcal is 0"):
            calculate_normalized_protein_score(30, 0)

class TestCalculateNutritionScore(unittest.TestCase):

    def test_optimal_macros(self):
        # Scenario with optimal macros and no negative nutrients
        score = calculate_nutrition_score(
            carbs=250, fat=56, protein=112, fiber=30, saturates=20, kcal=2000, sugars=25, salt=2
        )
        self.assertGreater(score, 80, "Should return 100 for optimal macros and high fiber")

    def test_high_sugar_salt(self):
        # Scenario with optimal macros but high sugar and salt
        score = calculate_nutrition_score(
            carbs=250, fat=56, protein=112, fiber=30, saturates=20, kcal=2000, sugars=100, salt=10
        )
        self.assertLess(score, 100, "Should return less than 100 for high sugar and salt")

    def test_low_macros(self):
        # Scenario with very low macros contributing to calories
        score = calculate_nutrition_score(
            carbs=50, fat=10, protein=20, fiber=30, saturates=5, kcal=2000, sugars=25, salt=2
        )
        self.assertLess(score, 100, "Should return less than 100 for low macros")

    def test_zero_calories(self):
        # Scenario with zero calories
        score = calculate_nutrition_score(
            carbs=0, fat=0, protein=0, fiber=0, saturates=0, kcal=0, sugars=0, salt=0
        )
        self.assertEqual(score, 0, "Should return 0 when kcal is 0")

class TestCalculateBMR(unittest.TestCase):
    def test_bmr_male(self):
        # Test BMR calculation for a male
        self.assertAlmostEqual(
            calculate_bmr(gender="male", weight=80, height=170, age=30),
            1805.64,
            places=1,
            msg="BMR calculation for male is incorrect"
        )

    def test_bmr_female(self):
        # Test BMR calculation for a female
        self.assertAlmostEqual(
            calculate_bmr(gender="female", weight=70, height=160, age=25),
            1482.31,
            places=1,
            msg="BMR calculation for female is incorrect"
        )

    def test_bmr_unknown_gender(self):
        # Test BMR calculation with an unknown gender
        self.assertEqual(
            calculate_bmr(gender="other", weight=80, height=170, age=30),
            2000,
            msg="BMR calculation for unknown gender should default to 2000"
        )

class TestWeightedRandomChoice(unittest.TestCase):
    @patch('numpy.random.choice')
    def test_weighted_random_choice(self, mock_choice):
        # Setup mock objects and parameters
        objects = [
            {"description": "High protein meal", "protein_score": 80, "nutrition_score": 70, "ingredients": ["chicken", "rice"]},
            {"description": "Vegan delight", "protein_score": 60, "nutrition_score": 90, "ingredients": ["tofu", "vegetables"]},
        ]
        weight_key = "protein_score"
        food_preferences = ["chicken"]
        allergies = ["nuts"]
        excluded_foods = ["pork"]
        goals = "gain_muscle"
        
        # Mock np.random.choice to return the first object for predictability
        mock_choice.return_value = [objects[0]]
        
        # Expected selection based on mocked np.random.choice
        expected = [objects[0]]

        # Call the function
        result = weighted_random_choice(
            objects,
            weight_key,
            food_preferences,
            allergies,
            excluded_foods,
            goals
        )
        
        # Verify that the result matches the expected outcome
        self.assertEqual(list(result), expected, "The function should return the first object based on the mock setup")

if __name__ == '__main__':
    unittest.main()
