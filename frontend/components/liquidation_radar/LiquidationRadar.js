import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import axios from 'axios';
import './LiquidationRadar.css';

const LiquidationRadar = () => {
    const [clusters, setClusters] = useState([]);
    const [selectedCluster, setSelectedCluster] = useState(null);
    const [impactAnalysis, setImpactAnalysis] = useState(null);

    useEffect(() => {
        fetchClusters();
        fetchImpactAnalysis();
    }, []);

    const fetchClusters = async () => {
        try {
            const response = await axios.get('/api/liquidation-clusters');
            setClusters(response.data.clusters);
        } catch (error) {
            console.error('Error fetching clusters:', error);
        }
    };

    const fetchImpactAnalysis = async () => {
        try {
            const response = await axios.get('/api/liquidation-impact');
            setImpactAnalysis(response.data);
        } catch (error) {
            console.error('Error fetching impact analysis:', error);
        }
    };

    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleString();
    };

    const formatImpact = (impact) => {
        return impact >= 0 ? `+${impact.toFixed(2)}%` : `${impact.toFixed(2)}%`;
    };

    const getClusterColor = (confidence) => {
        const hue = confidence * 120;
        return `hsl(${hue}, 70%, 50%)`;
    };

    return (
        <div className="liquidation-radar-container">
            <h2>Liquidation Cascade Radar</h2>

            {/* Impact Analysis Summary */}
            <div className="impact-summary">
                {impactAnalysis && (
                    <>
                        <h3>Market Impact Analysis</h3>
                        <div className="impact-metrics">
                            <div className="metric">
                                <span>Current Impact:</span>
                                <span className={impactAnalysis.impact >= 0 ? 'positive' : 'negative'}>
                                    {formatImpact(impactAnalysis.impact)}
                                </span>
                            </div>
                            <div className="metric">
                                <span>Confidence:</span>
                                <span>{(impactAnalysis.confidence * 100).toFixed(1)}%</span>
                            </div>
                            <div className="metric">
                                <span>Clusters:</span>
                                <span>{impactAnalysis.clusters}</span>
                            </div>
                        </div>
                    </>
                )}
            </div>

            {/* Liquidation Clusters Chart */}
            <div className="clusters-chart">
                <BarChart
                    width={800}
                    height={600}
                    data={clusters}
                    margin={{
                        top: 5,
                        right: 30,
                        left: 20,
                        bottom: 5,
                    }}
                >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar
                        dataKey="volume"
                        fill="#8884d8"
                        onClick={(event) => {
                            const cluster = clusters.find(c => 
                                c.timestamp === event.activePayload[0].payload.timestamp
                            );
                            setSelectedCluster(cluster);
                        }}
                    />
                </BarChart>
            </div>

            {/* Cluster Details */}
            <div className="cluster-details">
                <h3>Recent Liquidation Clusters</h3>
                <div className="clusters-grid">
                    {clusters.map((cluster) => (
                        <div
                            key={cluster.timestamp}
                            className="cluster-card"
                            style={{
                                backgroundColor: getClusterColor(cluster.confidence),
                                cursor: 'pointer'
                            }}
                            onClick={() => setSelectedCluster(cluster)}
                        >
                            <h4>{formatTimestamp(cluster.timestamp)}</h4>
                            <div className="cluster-info">
                                <div>
                                    <span>Type:</span>
                                    <span>{cluster.type}</span>
                                </div>
                                <div>
                                    <span>Size:</span>
                                    <span>{cluster.size.toLocaleString()} USD</span>
                                </div>
                                <div>
                                    <span>Price Impact:</span>
                                    <span className={cluster.impact >= 0 ? 'positive' : 'negative'}>
                                        {formatImpact(cluster.impact)}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Selected Cluster Details Modal */}
            {selectedCluster && (
                <div className="cluster-details-modal">
                    <div className="modal-content">
                        <h3>Liquidation Cluster Details</h3>
                        <div className="cluster-details-content">
                            <div className="detail-row">
                                <span>Timestamp:</span>
                                <span>{formatTimestamp(selectedCluster.timestamp)}</span>
                            </div>
                            <div className="detail-row">
                                <span>Type:</span>
                                <span>{selectedCluster.type}</span>
                            </div>
                            <div className="detail-row">
                                <span>Size:</span>
                                <span>{selectedCluster.size.toLocaleString()} USD</span>
                            </div>
                            <div className="detail-row">
                                <span>Price Impact:</span>
                                <span className={selectedCluster.impact >= 0 ? 'positive' : 'negative'}>
                                    {formatImpact(selectedCluster.impact)}
                                </span>
                            </div>
                            <div className="detail-row">
                                <span>Confidence:</span>
                                <span>{(selectedCluster.confidence * 100).toFixed(1)}%</span>
                            </div>
                            <div className="detail-row">
                                <span>Related Events:</span>
                                <div className="events">
                                    {selectedCluster.events.map((event, index) => (
                                        <div key={index} className="event">
                                            <span>{event.type}</span>
                                            <span>{event.description}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <button 
                            className="close-modal" 
                            onClick={() => setSelectedCluster(null)}
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LiquidationRadar;
