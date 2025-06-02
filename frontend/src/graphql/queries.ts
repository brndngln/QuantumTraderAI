export const GET_TRADE_DATA = `query GetTradeData($timeFrame: String!) {
  tradeData(timeFrame: $timeFrame) {
    timestamp
    price
    volume
    profit
    risk
    sentiment
  }
}

export const GET_SYSTEM_HEALTH = `query GetSystemHealth {
  systemHealth {
    status
    metrics {
      performance {
        winRate
        avgProfit
        maxDrawdown
        sharpeRatio
      }
      risk {
        volatility
        valueAtRisk
        positionExposure
      }
      dataQuality {
        validityScore
        latency
        consistency
      }
    }
    alerts
    lastCheck
    uptime
  }
}

export const GET_MODEL_VERSIONS = `query GetModelVersions {
  modelVersions {
    version
    created_at
    metrics {
      accuracy
      precision
      recall
      f1_score
    }
    parameters {
      model_type
      input_size
      hidden_size
      num_layers
    }
    status
    notes
  }
}

export const GET_RECENT_TRADES = `query GetRecentTrades($limit: Int!) {
  recentTrades(limit: $limit) {
    id
    symbol
    entryPrice
    exitPrice
    profit
    riskLevel
    sentimentScore
    timestamp
    strategyUsed
    reason
  }
}`
