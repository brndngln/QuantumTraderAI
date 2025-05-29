
def execute_trade(signals):
    executed = []
    for signal in signals:
        executed.append({**signal, "status": "executed"})
    return executed
