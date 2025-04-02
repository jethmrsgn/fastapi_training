from pydantic import BaseModel

# Response Model for Documentation

# Macros Reference
class MacroDetails(BaseModel):
    calories: int
    protein: float
    fats: float
    carbs: float

class MaintenanceMacros(BaseModel):
    moderate_carb: MacroDetails
    lower_carb: MacroDetails
    higher_carb: MacroDetails

class CuttingMacros(BaseModel):
    moderate_carb: MacroDetails
    lower_carb: MacroDetails
    higher_carb: MacroDetails

class BulkingMacros(BaseModel):
    moderate_carb: MacroDetails
    lower_carb: MacroDetails
    higher_carb: MacroDetails

class MacrosResponse(BaseModel):
    maintenance: MaintenanceMacros
    cutting: CuttingMacros
    bulking: BulkingMacros