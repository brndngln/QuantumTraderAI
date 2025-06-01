# Quantum AI Trader Frontend

This is the React-based frontend for the Quantum AI Trader platform. It provides a modern, responsive interface for interacting with the trading system's advanced features.

## Features

- Real-time Trade Journal with interactive charts and detailed trade analysis
- Sector Heatmap visualization with sentiment analysis
- AI Strategy Fusion dashboard showing agent performance and voting results
- Liquidation Radar for monitoring crypto market cascades
- Modern Material-UI design with responsive layout

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

The app will be available at `http://localhost:3000`

### Building for Production

```bash
npm run build
```

This will create a `build` directory with the production-ready files.

## Available Scripts

- `npm start`: Runs the app in development mode
- `npm test`: Launches the test runner
- `npm run build`: Builds the app for production
- `npm run eject`: Copies the configuration files and dependencies into your project

## API Integration

The frontend communicates with the backend API endpoints:
- `/api/trade-journal`: Trade journal data
- `/api/sector-sentiment`: Sector sentiment analysis
- `/api/agents`: Trading agents and strategy fusion
- `/api/liquidation-clusters`: Liquidation cascade detection

## License

This project is licensed under the MIT License - see the LICENSE file for details.
