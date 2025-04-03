from fastapi import FastAPI, Query, Depends,HTTPException
from sqlmodel import Session, SQLModel, create_engine, select, Field
from sqlalchemy.sql.sqltypes import Text
from response_models import MacrosResponse
import pydantic
import json

from typing import Annotated,Dict,Any
from enum import Enum
from math import ceil

class UserHistory(SQLModel,table=True):
    id: int = Field(default=None, primary_key=True)
    user_name: str = Field(index=True)
    age: int
    weight: float
    height: float
    activity_level:float
    macros: str  # Store macros as JSON string

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

class Gender(str,Enum):
    male = 'Male'
    female = 'Female'

class ActivityLevel(float,Enum):
    sedentary = 1.2
    light = 1.375
    moderate_active = 1.55
    very_active = 1.725
    super_active = 1.9

class TdeeCalculator(pydantic.BaseModel):
    gender: Gender
    age: int = pydantic.Field(gt=0, examples=[28])
    weight: float = pydantic.Field(gt=0, description="value in kg", examples=[86.5])
    height:float = pydantic.Field(gt=0, description="value in cm", examples=[169.5])
    activity_level: ActivityLevel = pydantic.Field(gt=0, examples=[1.55])


app = FastAPI()
@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/tdee/calculate", tags=['TDEE'])
def calculate_tdee(item:TdeeCalculator) -> int:
    item_dict = item.model_dump()
    gender = item_dict['gender']
    weight = item_dict['weight']
    height = item_dict['height']
    age = item_dict['age']
    activity_level = item_dict['activity_level']
    tdee = ((10 * weight + 6.25 * height - 5 * age) + (5 if gender == 'male' else -151)) * float(activity_level)
    return ceil(tdee)



@app.get("/tdee/macros", response_model=MacrosResponse, tags=['TDEE'])
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


@app.post('/user/create',tags=['User'])
def create_user(user: UserHistory, session:SessionDep) -> UserHistory:
    user.macros = json.dumps(user.macros)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.get("/user/history",tags=['User'])
def read_hero(user_name: Annotated[str ,Query(alias='username')], session: SessionDep) -> list[UserHistory]:
    statement = select(UserHistory).where(UserHistory.user_name == user_name)
    user = session.exec(statement)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
