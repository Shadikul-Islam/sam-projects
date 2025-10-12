from pydantic import BaseModel, Field
from typing import Dict, Any

class NDJSONDocument(BaseModel):
    index: str = Field(..., alias="_index")
    id: str = Field(..., alias="_id")
    source: Dict[str, Any] = Field(..., alias="_source")

    class Config:
        allow_population_by_field_name = True
