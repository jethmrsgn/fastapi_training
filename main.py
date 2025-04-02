from fastapi import FastAPI,Query
from pydantic import BaseModel, Field
from response_models import MacrosResponse

from typing import Annotated
from enum import Enum
from math import ceil

class Gender(str,Enum):
    male = 'Male'
    female = 'Female'

class ActivityLevel(float,Enum):
    sedentary = 1.2
    light = 1.375
    moderate_active = 1.55
    very_active = 1.725
    super_active = 1.9

class TdeeCalculator(BaseModel):
    gender: Gender
    age: int = Field(gt=0, examples=[28])
    weight: float = Field(gt=0, description="value in kg", examples=[86.5])
    height:float = Field(gt=0, description="value in cm", examples=[169.5])
    activity_level: ActivityLevel = Field(gt=0, examples=[1.55])


app = FastAPI()


@app.post("/tdee/calculate")
def calculate_tdee(item:TdeeCalculator) -> int:
    item_dict = item.model_dump()
    gender = item_dict['gender']
    weight = item_dict['weight']
    height = item_dict['height']
    age = item_dict['age']
    activity_level = item_dict['activity_level']
    tdee = ((10 * weight + 6.25 * height - 5 * age) + (5 if gender == 'male' else -151)) * float(activity_level)
    return ceil(tdee)



@app.get("/tdee/macros", response_model=MacrosResponse)
def macros_reference(
    maintenance_calories: Annotated[int, Query(
        alias= 'maintenance-calories'
    )]):
    calorie_adjustment = {
		'maintenance': 0,
        'cutting': -500,
        'bulking': 500
	}
    macro_ratios = {
        "moderate_carb": (0.30, 0.35, 0.35),
        "lower_carb": (0.40, 0.40, 0.20),
        "higher_carb": (0.30, 0.20, 0.50),
    }

    calories_per_gram = {"protein": 4, "fats": 9, "carbs": 4}

    results = {}

    for adjustment_type, adjustment in calorie_adjustment.items():
        calories = maintenance_calories + adjustment
        results[adjustment_type] = {}
        for plan, (protein_ratio, fat_ratio, carb_ratio) in macro_ratios.items():
            protein_calories = calories * protein_ratio
            fat_calories = calories * fat_ratio
            carb_calories = calories * carb_ratio

            protein_grams = protein_calories / calories_per_gram["protein"]
            fat_grams = fat_calories / calories_per_gram["fats"]
            carb_grams = carb_calories / calories_per_gram["carbs"]

            results[adjustment_type][plan] = {
				"calories": ceil(calories),
				"protein": round(protein_grams, 2),
				"fats": round(fat_grams, 2),
				"carbs": round(carb_grams, 2),
			}
    return results