from fastapi import FastAPI, HTTPException
from pymongo.mongo_client import MongoClient
from pydantic import BaseModel, Field
from pymongo.server_api import ServerApi
import requests
from datetime import datetime
from typing import Dict


app = FastAPI()

uri = "mongodb+srv://evilarthas656:ZR9UcstpgXaUQZVB@cluster0.il8b38k.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


client = MongoClient(uri, server_api=ServerApi('1'))
db = client.currency_conversion

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


class ConversionRequest(BaseModel):
    amount: float = Field(gt=0, description="Значение должно быть больше нуля")

class ConversionResponse(BaseModel):
    converted_amounts: Dict[str, float] = Field(
        description="Конвертированные значения в разных валютах"
    )

class HistoryItem(BaseModel):
    amount_usd: float
    timestamp: datetime

class HistoryResponse(BaseModel):
    history: list[HistoryItem]


@app.post("/convert")
async def convert(conversion_request: ConversionRequest):
    amount = conversion_request.amount

    api_url = "https://open.er-api.com/v6/latest/USD"
    response = requests.get(api_url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Произошла ошибка при получении данных")

    rates = response.json().get("rates", {})
    
    converted_amounts = {currency: amount * rate for currency, rate in rates.items()}
    

    request_data = {
        "amount_usd": amount, 
        "timestamp": datetime.utcnow()
    }
    db.requests.insert_one(request_data)

    return {"converted_amounts": converted_amounts}

@app.get("/history", response_model=HistoryResponse)
async def get_history():
    history = list(db.requests.find({}, {"_id": 0}))
    history_response = [
        HistoryItem(**item) for item in history
    ]
    return {"history": history_response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

