
# 🚀 QuantumTraderAI: Autonomous AI Trading Empire

QuantumTraderAI is an elite, modular, scalable AI trading engine designed to start at $100 and scale into millions. Powered by FastAPI, LSTM, Transformers, Redis, and Docker.

---

## 🌐 Deployments

### 📦 Backend (Railway)
1. Push this repo to GitHub
2. Connect GitHub to [Railway](https://railway.app)
3. Add your `.env` variables:
   - `TELEGRAM_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `TWELVE_DATA_API_KEY`
4. Railway builds your FastAPI + Redis stack automatically

---

### 🖥️ Frontend (Vercel)
1. Deploy `/frontend/` folder via [Vercel](https://vercel.com)
2. Set the root to `frontend`
3. Your live dashboard is now accessible globally

---

## 🔧 Features
- ✅ AI Strategies: Momentum, Reversion, LSTM, Transformer
- ✅ Meta-Learner: Self-tunes strategies based on PnL history
- ✅ Redis + Celery + Docker
- ✅ Mobile Command Center (React Native/Expo)
- ✅ Push Notifications + Telegram Alerts

---

## 📲 Mobile App (Optional)
Use `QuantumTraderMobile` folder with Expo to deploy the native app:
- Biometric unlock
- Signal charts
- Live trade trigger
- Push alert viewer

---

## 📂 Folder Structure
```
QuantumTraderAI/
├── backend/
│   ├── main.py
│   ├── ai_models/meta_learner.py
│   ├── strategies/
│   └── utils/
├── frontend/
│   └── index.html
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 💡 Meta-Learning Example
```python
from backend.ai_models.meta_learner import meta

print(meta.recommend_strategies())
print(meta.confidence_weight("LSTM"))
```
