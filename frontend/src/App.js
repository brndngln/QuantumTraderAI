import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import TradeJournal from '../components/trade_journal/TradeJournal';
import SectorHeatmap from '../components/sector_heatmap/SectorHeatmap';
import StrategyFusion from '../components/strategy_fusion/StrategyFusion';
import LiquidationRadar from '../components/liquidation_radar/LiquidationRadar';

const theme = createTheme({
    palette: {
        primary: {
            main: '#1976d2',
        },
        secondary: {
            main: '#dc004e',
        },
        background: {
            default: '#f5f5f5',
        },
    },
});

function App() {
    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Router>
                <div className="app-container">
                    <Routes>
                        <Route path="/" element={<TradeJournal />} />
                        <Route path="/sector-heatmap" element={<SectorHeatmap />} />
                        <Route path="/strategy-fusion" element={<StrategyFusion />} />
                        <Route path="/liquidation-radar" element={<LiquidationRadar />} />
                    </Routes>
                </div>
            </Router>
        </ThemeProvider>
    );
}

export default App;
