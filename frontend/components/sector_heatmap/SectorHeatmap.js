import React, { useState, useEffect } from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Legend } from 'recharts';
import axios from 'axios';
import './SectorHeatmap.css';

const SectorHeatmap = () => {
    const [sectors, setSectors] = useState([]);
    const [selectedSector, setSelectedSector] = useState(null);

    useEffect(() => {
        fetchSectorData();
    }, []);

    const fetchSectorData = async () => {
        try {
            const response = await axios.get('/api/sector-sentiment');
            setSectors(response.data.sectors);
        } catch (error) {
            console.error('Error fetching sector data:', error);
        }
    };

    const formatSentiment = (sentiment) => {
        return (sentiment * 100).toFixed(1) + '%';
    };

    const getSentimentColor = (sentiment) => {
        const hue = (sentiment + 1) * 120;
        return `hsl(${hue}, 70%, 50%)`;
    };

    return (
        <div className="sector-heatmap-container">
            <h2>Sector Sentiment Heatmap</h2>

            {/* Radar Chart */}
            <div className="radar-chart-container">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" width={800} height={600} data={sectors}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="sector" />
                    <PolarRadiusAxis angle={30} domain={[0, 1]} />
                    <Radar
                        name="Sentiment"
                        dataKey="sentiment"
                        stroke="#8884d8"
                        fill="#8884d8"
                        fillOpacity={0.6}
                    />
                    <Legend />
                </RadarChart>
            </div>

            {/* Sector Details */}
            <div className="sector-details">
                <h3>Sector Breakdown</h3>
                <div className="sectors-grid">
                    {sectors.map((sector) => (
                        <div
                            key={sector.sector}
                            className="sector-card"
                            style={{
                                backgroundColor: getSentimentColor(sector.sentiment),
                                cursor: 'pointer'
                            }}
                            onClick={() => setSelectedSector(sector)}
                        >
                            <h4>{sector.sector}</h4>
                            <div className="sentiment-score">
                                <span>Sentiment:</span>
                                <span className="score">{formatSentiment(sector.sentiment)}</span>
                            </div>
                            <div className="metrics">
                                <div>
                                    <span>ETF Flow:</span>
                                    <span>{formatSentiment(sector.etf_flow)}</span>
                                </div>
                                <div>
                                    <span>News Tone:</span>
                                    <span>{formatSentiment(sector.news_tone)}</span>
                                </div>
                                <div>
                                    <span>Earnings:</span>
                                    <span>{formatSentiment(sector.earnings_sentiment)}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Selected Sector Details Modal */}
            {selectedSector && (
                <div className="sector-details-modal">
                    <div className="modal-content">
                        <h3>{selectedSector.sector} Details</h3>
                        <div className="sector-details-content">
                            <div className="detail-row">
                                <span>Sentiment Score:</span>
                                <span className="score">{formatSentiment(selectedSector.sentiment)}</span>
                            </div>
                            <div className="detail-row">
                                <span>Top Contributors:</span>
                                <div className="contributors">
                                    {selectedSector.top_contributors.map((contributor, index) => (
                                        <div key={index} className="contributor">
                                            <span>{contributor.name}</span>
                                            <span className="weight">{contributor.weight}%</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div className="detail-row">
                                <span>Recent Events:</span>
                                <div className="events">
                                    {selectedSector.recent_events.map((event, index) => (
                                        <div key={index} className="event">
                                            <span>{event.date}</span>
                                            <span>{event.description}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <button 
                            className="close-modal" 
                            onClick={() => setSelectedSector(null)}
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SectorHeatmap;
