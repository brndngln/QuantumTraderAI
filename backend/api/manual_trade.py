
from fastapi import APIRouter, Request
from backend.utils.trade_executor import execute_trade

router = APIRouter()

@router.post("/trade")
async def manual_trade(request: Request):
    data = await request.json()
    ticker = data.get("ticker")
    action = data.get("action")
    amount = data.get("amount", 10)
    result = execute_trade([{"ticker": ticker, "action": action, "amount": amount, "reason": "manual"}])
    return {"status": "executed", "result": result}
