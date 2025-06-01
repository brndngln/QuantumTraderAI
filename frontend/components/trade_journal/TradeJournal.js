import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import axios from 'axios';
import './TradeJournal.css';

const TradeJournal = () => {
    const [trades, setTrades] = useState([]);
    const [summary, setSummary] = useState(null);
    const [selectedTrade, setSelectedTrade] = useState(null);

    useEffect(() => {
        fetchTrades();
        fetchSummary();
    }, []);

    const fetchTrades = async () => {
        try {
            const response = await axios.get('/api/trade-journal');
            setTrades(response.data.trades);
        } catch (error) {
            console.error('Error fetching trades:', error);
        }
    };

    const fetchSummary = async () => {
        try {
            const response = await axios.get('/api/trade-summary');
            setSummary(response.data);
        } catch (error) {
            console.error('Error fetching summary:', error);
        }
    };

    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleString();
    };

    const formatProfit = (profit) => {
        return profit >= 0 ? `+$${profit.toFixed(2)}` : `-$${Math.abs(profit).toFixed(2)}`;
    };

    return (
        <div className="trade-journal-container">
            <h2>Trade Journal</h2>
            
            {/* Summary Card */}
            <div className="summary-card">
                {summary && (
                    <>
                        <h3>Today's Summary</h3>
                        <div className="summary-metrics">
                            <div className="metric">
                                <span>Total PnL:</span>
                                <span className={summary.total_profit >= 0 ? 'positive' : 'negative'}>
                                    {formatProfit(summary.total_profit)}
                                </span>
                            </div>
                            <div className="metric">
                                <span>Win Rate:</span>
                                <span>{(summary.win_rate * 100).toFixed(1)}%</span>
                            </div>
                            <div className="metric">
                                <span>Avg Profit:</span>
                                <span>{formatProfit(summary.avg_profit)}</span>
                            </div>
                        </div>
                    </>
                )}
            </div>

            {/* Trades Table */}
            <div className="trades-table">
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Symbol</th>
                            <th>Entry</th>
                            <th>Exit</th>
                            <th>Profit</th>
                            <th>Reason</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {trades.map((trade) => (
                            <tr
                                key={trade.id}
                                onClick={() => setSelectedTrade(trade)}
                                className={trade.profit >= 0 ? 'win' : 'loss'}
                            >
                                <td>{formatTimestamp(trade.timestamp)}</td>
                                <td>{trade.symbol}</td>
                                <td>${trade.entry_price}</td>
                                <td>${trade.exit_price}</td>
                                <td className={trade.profit >= 0 ? 'positive' : 'negative'}>
                                    {formatProfit(trade.profit)}
                                </td>
                                <td>{trade.reason}</td>
                                <td>
                                    <button className="details-btn">Details</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Trade Details Modal */}
            {selectedTrade && (
                <div className="trade-details-modal">
                    <div className="modal-content">
                        <h3>Trade Details</h3>
                        <div className="trade-details">
                            <div className="detail-row">
                                <span>Symbol:</span>
                                <span>{selectedTrade.symbol}</span>
                            </div>
                            <div className="detail-row">
                                <span>Entry Time:</span>
                                <span>{formatTimestamp(selectedTrade.entry_time)}</span>
                            </div>
                            <div className="detail-row">
                                <span>Exit Time:</span>
                                <span>{formatTimestamp(selectedTrade.exit_time)}</span>
                            </div>
                            <div className="detail-row">
                                <span>Entry Price:</span>
                                <span>${selectedTrade.entry_price}</span>
                            </div>
                            <div className="detail-row">
                                <span>Exit Price:</span>
                                <span>${selectedTrade.exit_price}</span>
                            </div>
                            <div className="detail-row">
                                <span>Profit:</span>
                                <span className={selectedTrade.profit >= 0 ? 'positive' : 'negative'}>
                                    {formatProfit(selectedTrade.profit)}
                                </span>
                            </div>
                            <div className="detail-row">
                                <span>Reason:</span>
                                <span>{selectedTrade.reason}</span>
                            </div>
                            <div className="detail-row">
                                <span>Strategy:</span>
                                <span>{selectedTrade.strategy}</span>
                            </div>
                            <div className="detail-row">
                                <span>Confidence:</span>
                                <span>{(selectedTrade.confidence * 100).toFixed(1)}%</span>
                            </div>
                        </div>
                        <button 
                            className="close-modal" 
                            onClick={() => setSelectedTrade(null)}
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TradeJournal;
