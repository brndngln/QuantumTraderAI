import React, { useState, useEffect } from 'react';
import { Line, Bar, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { format } from 'date-fns';
import { useQuery } from '@apollo/client';
import { GET_TRADE_DATA } from '../graphql/queries';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface TradeData {
  timestamp: string;
  price: number;
  volume: number;
  profit: number;
  risk: number;
  sentiment: number;
}

const TradeAnalytics: React.FC = () => {
  const [timeFrame, setTimeFrame] = useState<'1d' | '1w' | '1m' | '3m' | '6m' | '1y'>('1d');
  const [selectedMetrics, setSelectedMetrics] = useState<Set<string>>(new Set(['price', 'volume', 'profit']));
  const { loading, error, data } = useQuery(GET_TRADE_DATA, {
    variables: { timeFrame }
  });

  const timeFrames = {
    '1d': '1 Day',
    '1w': '1 Week',
    '1m': '1 Month',
    '3m': '3 Months',
    '6m': '6 Months',
    '1y': '1 Year'
  };

  const metrics = [
    { label: 'Price', value: 'price' },
    { label: 'Volume', value: 'volume' },
    { label: 'Profit', value: 'profit' },
    { label: 'Risk', value: 'risk' },
    { label: 'Sentiment', value: 'sentiment' }
  ];

  useEffect(() => {
    if (data?.tradeData) {
      updateChartData(data.tradeData);
    }
  }, [data]);

  const updateChartData = (tradeData: TradeData[]) => {
    // Update line chart
    const lineDatasets = Array.from(selectedMetrics).map(metric => ({
      label: metric.charAt(0).toUpperCase() + metric.slice(1),
      data: tradeData.map(d => d[metric as keyof TradeData]),
      fill: false,
      borderColor: getColorForMetric(metric),
      tension: 0.1,
      yAxisID: metric === 'sentiment' ? 'y2' : 'y'
    }));

    setLineChartData({
      labels: tradeData.map(d => format(new Date(d.timestamp), 'HH:mm')),
      datasets: lineDatasets
    });

    // Update bar chart
    const profitData = tradeData.map(d => d.profit);
    setBarChartData({
      labels: tradeData.map(d => format(new Date(d.timestamp), 'HH:mm')),
      datasets: [{
        label: 'Profit Distribution',
        data: profitData,
        backgroundColor: profitData.map(p => p >= 0 ? '#10b981' : '#ef4444'),
        borderColor: '#6b7280',
        borderWidth: 1
      }]
    });

    // Update pie chart
    const riskCategories = [
      { label: 'Low Risk', value: tradeData.filter(d => d.risk < 0.3).length },
      { label: 'Medium Risk', value: tradeData.filter(d => d.risk >= 0.3 && d.risk < 0.7).length },
      { label: 'High Risk', value: tradeData.filter(d => d.risk >= 0.7).length }
    ];
    setPieChartData({
      labels: riskCategories.map(c => c.label),
      datasets: [{
        data: riskCategories.map(c => c.value),
        backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
        hoverOffset: 4
      }]
    });
  };

  const getColorForMetric = (metric: string): string => {
    const colors = {
      price: '#2563eb',
      volume: '#10b981',
      profit: '#f59e0b',
      risk: '#ef4444',
      sentiment: '#8b5cf6'
    };
    return colors[metric] || '#6b7280';
  };

  const [lineChartData, setLineChartData] = useState({
    labels: [],
    datasets: []
  });

  const [barChartData, setBarChartData] = useState({
    labels: [],
    datasets: []
  });

  const [pieChartData, setPieChartData] = useState({
    labels: [],
    datasets: []
  });

  const handleMetricToggle = (metric: string) => {
    const newMetrics = new Set(selectedMetrics);
    if (newMetrics.has(metric)) {
      newMetrics.delete(metric);
    } else {
      newMetrics.add(metric);
    }
    setSelectedMetrics(newMetrics);
  };

  const renderMetricsSelector = () => (
    <div className="flex flex-wrap gap-2 mt-4">
      {metrics.map(metric => (
        <button
          key={metric.value}
          onClick={() => handleMetricToggle(metric.value)}
          className={`px-3 py-1 rounded ${
            selectedMetrics.has(metric.value)
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          {metric.label}
        </button>
      ))}
    </div>
  );

  const renderTimeFrameSelector = () => (
    <div className="flex gap-2 mt-4">
      {Object.entries(timeFrames).map(([value, label]) => (
        <button
          key={value}
          onClick={() => setTimeFrame(value as '1d' | '1w' | '1m' | '3m' | '6m' | '1y')}
          className={`px-3 py-1 rounded ${
            timeFrame === value ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );

  if (loading) return <div className="flex items-center justify-center h-screen">Loading...</div>;
  if (error) return <div className="flex items-center justify-center h-screen">Error: {error.message}</div>;

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Trade Analytics Dashboard</h1>
      
      {renderTimeFrameSelector()}
      {renderMetricsSelector()}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">Price & Volume Analysis</h2>
          <Line
            data={lineChartData}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                y: {
                  beginAtZero: true,
                  position: 'left',
                  title: {
                    display: true,
                    text: 'Price/Volume'
                  }
                },
                y2: {
                  beginAtZero: true,
                  position: 'right',
                  title: {
                    display: true,
                    text: 'Sentiment'
                  }
                }
              }
            }}
          />
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">Profit Distribution</h2>
          <Bar
            data={barChartData}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                y: {
                  beginAtZero: true
                }
              }
            }}
          />
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">Risk Exposure</h2>
          <Pie
            data={pieChartData}
            options={{
              responsive: true,
              maintainAspectRatio: false
            }}
          />
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">Sentiment Analysis</h2>
          <div className="text-center">
            <div className={`bg-${getSentimentColor(data?.tradeData?.[0]?.sentiment)}-500 rounded-full w-24 h-24 flex items-center justify-center text-white text-2xl font-bold`}>
              {Math.round(data?.tradeData?.[0]?.sentiment * 100)}%
            </div>
            <p className="mt-2">Current Market Sentiment</p>
          </div>
        </div>
      </div>
    </div>
  );
};

const getSentimentColor = (sentiment: number): string => {
  if (sentiment > 0.7) return 'green';
  if (sentiment > 0.3) return 'yellow';
  return 'red';
};

export default TradeAnalytics;
