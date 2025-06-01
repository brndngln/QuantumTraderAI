import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Legend } from 'recharts';
import axios from 'axios';
import './StrategyFusion.css';

const StrategyFusion = () => {
    const [agents, setAgents] = useState([]);
    const [selectedAgent, setSelectedAgent] = useState(null);
    const [votingResults, setVotingResults] = useState(null);

    useEffect(() => {
        fetchAgents();
        fetchVotingResults();
    }, []);

    const fetchAgents = async () => {
        try {
            const response = await axios.get('/api/agents');
            setAgents(response.data.agents);
        } catch (error) {
            console.error('Error fetching agents:', error);
        }
    };

    const fetchVotingResults = async () => {
        try {
            const response = await axios.get('/api/voting-results');
            setVotingResults(response.data);
        } catch (error) {
            console.error('Error fetching voting results:', error);
        }
    };

    const formatPerformance = (performance) => {
        return performance >= 0 ? `+${performance.toFixed(2)}%` : `${performance.toFixed(2)}%`;
    };

    const getAgentColor = (confidence) => {
        const hue = confidence * 120;
        return `hsl(${hue}, 70%, 50%)`;
    };

    return (
        <div className="strategy-fusion-container">
            <h2>AI Strategy Fusion</h2>

            {/* Voting Results */}
            <div className="voting-results">
                {votingResults && (
                    <>
                        <h3>Current Voting Results</h3>
                        <div className="vote-summary">
                            <div className="vote-card">
                                <h4>Signal Distribution</h4>
                                <PieChart width={400} height={400}>
                                    <Pie
                                        data={votingResults.signal_distribution}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={80}
                                        fill="#8884d8"
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {votingResults.signal_distribution.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={getAgentColor(entry.confidence)} />
                                        ))}
                                    </Pie>
                                    <Legend />
                                </PieChart>
                            </div>
                            <div className="vote-card">
                                <h4>Voting Strategy</h4>
                                <div className="strategy-info">
                                    <div>
                                        <span>Current Strategy:</span>
                                        <span>{votingResults.current_strategy}</span>
                                    </div>
                                    <div>
                                        <span>Confidence:</span>
                                        <span>{(votingResults.confidence * 100).toFixed(1)}%</span>
                                    </div>
                                    <div>
                                        <span>Expected Return:</span>
                                        <span className={votingResults.expected_return >= 0 ? 'positive' : 'negative'}>
                                            {formatPerformance(votingResults.expected_return)}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>

            {/* Agent Performance */}
            <div className="agent-performance">
                <h3>Agent Performance</h3>
                <div className="agents-grid">
                    {agents.map((agent) => (
                        <div
                            key={agent.id}
                            className="agent-card"
                            style={{
                                backgroundColor: getAgentColor(agent.confidence),
                                cursor: 'pointer'
                            }}
                            onClick={() => setSelectedAgent(agent)}
                        >
                            <h4>{agent.name}</h4>
                            <div className="agent-metrics">
                                <div>
                                    <span>Win Rate:</span>
                                    <span>{(agent.win_rate * 100).toFixed(1)}%</span>
                                </div>
                                <div>
                                    <span>Sharpe:</span>
                                    <span>{agent.sharpe_ratio.toFixed(2)}</span>
                                </div>
                                <div>
                                    <span>Weight:</span>
                                    <span>{(agent.weight * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Selected Agent Details Modal */}
            {selectedAgent && (
                <div className="agent-details-modal">
                    <div className="modal-content">
                        <h3>{selectedAgent.name} Details</h3>
                        <div className="agent-details-content">
                            <div className="detail-row">
                                <span>Strategy Type:</span>
                                <span>{selectedAgent.strategy_type}</span>
                            </div>
                            <div className="detail-row">
                                <span>Performance Metrics:</span>
                                <div className="metrics">
                                    <div>
                                        <span>Win Rate:</span>
                                        <span>{(selectedAgent.win_rate * 100).toFixed(1)}%</span>
                                    </div>
                                    <div>
                                        <span>Sharpe Ratio:</span>
                                        <span>{selectedAgent.sharpe_ratio.toFixed(2)}</span>
                                    </div>
                                    <div>
                                        <span>Max Drawdown:</span>
                                        <span>{selectedAgent.max_drawdown.toFixed(2)}%</span>
                                    </div>
                                </div>
                            </div>
                            <div className="detail-row">
                                <span>Recent Signals:</span>
                                <div className="signals">
                                    {selectedAgent.recent_signals.map((signal, index) => (
                                        <div key={index} className="signal">
                                            <span>{signal.timestamp}</span>
                                            <span>{signal.type}</span>
                                            <span>{signal.confidence}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <button 
                            className="close-modal" 
                            onClick={() => setSelectedAgent(null)}
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default StrategyFusion;
