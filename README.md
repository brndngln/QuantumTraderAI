
# 🚀 QuantumTraderAI: Elite AI Trading Platform

QuantumTraderAI is an advanced AI trading platform featuring 12 elite enhancements, built with FastAPI, Redis, Celery, Railway, and Vercel. It provides real-time trading insights, advanced analytics, and intelligent decision-making capabilities.

---

## 🌐 Deployments

### 📦 Backend (Railway)
1. Push this repo to GitHub
2. Connect GitHub to [Railway](https://railway.app)
3. Add your `.env` variables:
   - API Keys: `TELEGRAM_TOKEN`, `TWELVE_DATA_API_KEY`, `ALPHA_VANTAGE_API_KEY`
   - Broker: `BINANCE_API_KEY`, `BINANCE_SECRET_KEY`
   - Database: `REDIS_URL`, `DATABASE_URL`
   - Security: `JWT_SECRET`, `SENTRY_DSN`
4. Railway builds your FastAPI + Redis stack automatically

---

### 🖥️ Frontend (Vercel)
1. Deploy `/frontend/` folder via [Vercel](https://vercel.com)
2. Set the root to `frontend`
3. Configure environment variables in Vercel dashboard
4. Your live dashboard is now accessible globally

---

## 🔧 Features
- ✅ Real-time Trade Journal with AI explainability
- ✅ Cross-timeframe Signal Correlation Engine
- ✅ Sector Sentiment Analysis
- ✅ Trade Cooldown + Adrenaline Controller
- ✅ Adaptive Leverage Scaling
- ✅ Live Broker Health Monitoring
- ✅ Global Macro Heatmap AI
- ✅ AI Trade Fusion Layer
- ✅ Alpha Drop Radar
- ✅ Synthetic Market Generator
- ✅ Liquidation Cascade Detection
- ✅ AI Explainability Engine

---

## 📲 Mobile App (Optional)
Use `QuantumTraderMobile` folder with Expo to deploy the native app:
- Biometric unlock
- Signal charts
- Live trade trigger
- Push alert viewer
- AI trade analysis
- Portfolio tracking

---

## 📂 Folder Structure
```
QuantumTraderAI/
├── backend/
│   ├── main.py
│   ├── ai_models/
│   │   ├── meta_learner.py
│   │   ├── quantum_features.py
│   │   ├── quantum_optimizer.py
│   │   └── quantum_risk.py
│   ├── strategies/
│   ├── analytics/
│   │   └── sector_sentiment.py
│   ├── utils/
│   │   ├── trade_journal.py
│   │   ├── timeframe_alignment.py
│   │   └── cooldown_manager.py
│   ├── risk/
│   │   └── leverage_scaler.py
│   ├── monitor/
│   │   └── broker_health.py
│   ├── crypto/
│   │   └── liquidation_radar.py
│   └── explainability/
│       └── explain_trade.py
├── frontend/
│   ├── components/
│   │   ├── trade_journal/
│   │   ├── sector_heatmap/
│   │   ├── strategy_fusion/
│   │   └── liquidation_radar/
│   ├── src/
│   └── public/
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 💡 Key Features

### 1. Real-time Trade Journal AI
- Automatic logging of trades with detailed analysis
- Daily summaries and performance metrics
- AI-powered trade explainability
- Chart screenshot generation

### 2. Cross-timeframe Signal Correlation
- Multi-timeframe analysis
- Signal alignment across timeframes
- Configurable logic per strategy
- Redis-based state management

### 3. Sector Sentiment Index
- Live sector heatmaps
- Fused ETF flow, news tone, earnings pulse
- Volume anomaly detection
- Social sentiment analysis

### 4. Trade Cooldown Controller
- Prevents overtrading loops
- Emotional intensity thresholds
- Redis-based state tracking
- Configurable cooldown periods

### 5. Adaptive Leverage Scaling
- Dynamic position sizing
- Performance-based adjustments
- Vault buffer integration
- Strategy tier considerations

### 6. Broker Health Monitor
- API latency tracking
- Execution cost analysis
- Consistency monitoring
- Route optimization

### 7. Global Macro Heatmap
- Economic data fusion
- Rate hike predictions
- Inflation tracking
- Currency strength analysis

### 8. AI Trade Fusion
- Multi-agent voting system
- Strategy performance tracking
- Confidence scoring
- Risk-adjusted decision making

### 9. Alpha Drop Radar
- Institutional signal detection
- Whale wallet tracking
- Block trade analysis
- Options activity monitoring

### 10. Synthetic Market Generator
- Market condition simulation
- News impact modeling
- Economic data integration
- Historical price correlation

### 11. Liquidation Cascade Detection
- Crypto market monitoring
- Volume anomaly detection
- Price impact analysis
- Risk assessment

### 12. AI Explainability Engine
- Trade decision breakdown
- Strategy performance metrics
- Risk factor analysis
- Confidence scoring

---

## 🛠️ Setup Instructions

### Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
mv .env.example .env

# Run migrations
python -m alembic upgrade head

# Start the server
uvicorn backend.main:app --reload
```

### Frontend Setup
```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm start
```

### Production Deployment
1. Push to GitHub
2. Connect to Railway for backend
3. Connect to Vercel for frontend
4. Configure environment variables
5. Set up Redis and database
6. Deploy worker services

---

## 🔒 Security
- JWT authentication
- Rate limiting
- CORS configuration
- Environment variable encryption
- API key management
- Audit logging

---

## 📈 Performance
- Redis caching
- Asynchronous processing
- Load balancing
- Auto-scaling
- Health checks

---

## 📱 Mobile Integration
- Push notifications
- Biometric authentication
- Offline support
- Real-time updates
- Portfolio tracking

---

## 🤝 Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
