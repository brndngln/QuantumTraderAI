
from fastapi import FastAPI
from backend.strategies.momentum import momentum_strategy
from backend.strategies.mean_reversion import mean_reversion_strategy
from backend.utils.data_loader import load_realtime_data
from backend.utils.trade_executor import execute_trade
from backend.config.settings import settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "QuantumTraderAI is live"}

@app.get("/run")
def run_all_strategies():
    data = load_realtime_data()
    momentum_signals = momentum_strategy(data)
    mean_reversion_signals = mean_reversion_strategy(data)
    trades = execute_trade(momentum_signals + mean_reversion_signals)
    return {"trades_executed": trades}
