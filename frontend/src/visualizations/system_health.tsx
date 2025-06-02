import React, { useState, useEffect } from 'react';
import { useQuery } from '@apollo/client';
import { GET_SYSTEM_HEALTH } from '../graphql/queries';
import { format } from 'date-fns';
import { Sparklines, SparklinesLine, SparklinesBars } from 'react-sparklines';

interface SystemHealthData {
  status: string;
  metrics: {
    performance: {
      winRate: number;
      avgProfit: number;
      maxDrawdown: number;
      sharpeRatio: number;
    };
    risk: {
      volatility: number;
      valueAtRisk: number;
      positionExposure: number;
    };
    dataQuality: {
      validityScore: number;
      latency: number;
      consistency: number;
    };
  };
  alerts: string[];
  lastCheck: string;
  uptime: number;
}

const SystemHealth: React.FC = () => {
  const { loading, error, data } = useQuery(GET_SYSTEM_HEALTH);
  const [statusColor, setStatusColor] = useState<string>('green');

  useEffect(() => {
    if (data?.systemHealth?.status) {
      setStatusColor(getStatusColor(data.systemHealth.status));
    }
  }, [data]);

  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'green';
      case 'warning':
        return 'yellow';
      case 'critical':
        return 'red';
      default:
        return 'gray';
    }
  };

  const formatMetric = (value: number): string => {
    if (value > 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value > 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toFixed(2);
  };

  if (loading) return <div className="flex items-center justify-center h-screen">Loading...</div>;
  if (error) return <div className="flex items-center justify-center h-screen">Error: {error.message}</div>;

  const healthData = data?.systemHealth;

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">System Health Dashboard</h1>

      {/* Status Card */}
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">System Status</h2>
          <div className={`px-4 py-2 rounded-full text-white font-semibold ${
            `bg-${statusColor}-500`
          }`}>
            {healthData?.status}
          </div>
        </div>
        <div className="mt-4">
          <p>Uptime: {Math.round(healthData?.uptime / 3600)} hours</p>
          <p>Last Check: {format(new Date(healthData?.lastCheck), 'HH:mm:ss')}</p>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Performance Metrics */}
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">Performance Metrics</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium">Win Rate</h3>
              <p className="text-2xl font-bold">{healthData?.metrics?.performance?.winRate?.toFixed(1)}%</p>
              <Sparklines data={[healthData?.metrics?.performance?.winRate || 0]}>
                <SparklinesLine color="green" />
              </Sparklines>
            </div>
            <div>
              <h3 className="text-sm font-medium">Avg Profit</h3>
              <p className="text-2xl font-bold">${formatMetric(healthData?.metrics?.performance?.avgProfit || 0)}</p>
              <Sparklines data={[healthData?.metrics?.performance?.avgProfit || 0]}>
                <SparklinesBars color="green" />
              </Sparklines>
            </div>
          </div>
        </div>

        {/* Risk Metrics */}
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">Risk Metrics</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium">Volatility</h3>
              <p className="text-2xl font-bold">{healthData?.metrics?.risk?.volatility?.toFixed(2)}</p>
              <Sparklines data={[healthData?.metrics?.risk?.volatility || 0]}>
                <SparklinesLine color="red" />
              </Sparklines>
            </div>
            <div>
              <h3 className="text-sm font-medium">Value at Risk</h3>
              <p className="text-2xl font-bold">${formatMetric(healthData?.metrics?.risk?.valueAtRisk || 0)}</p>
              <Sparklines data={[healthData?.metrics?.risk?.valueAtRisk || 0]}>
                <SparklinesBars color="red" />
              </Sparklines>
            </div>
          </div>
        </div>

        {/* Data Quality Metrics */}
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">Data Quality</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium">Validity Score</h3>
              <p className="text-2xl font-bold">{healthData?.metrics?.dataQuality?.validityScore?.toFixed(1)}%</p>
              <Sparklines data={[healthData?.metrics?.dataQuality?.validityScore || 0]}>
                <SparklinesLine color="blue" />
              </Sparklines>
            </div>
            <div>
              <h3 className="text-sm font-medium">Latency</h3>
              <p className="text-2xl font-bold">{healthData?.metrics?.dataQuality?.latency?.toFixed(1)}s</p>
              <Sparklines data={[healthData?.metrics?.dataQuality?.latency || 0]}>
                <SparklinesBars color="blue" />
              </Sparklines>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts Section */}
      {healthData?.alerts?.length > 0 && (
        <div className="mt-4">
          <h2 className="text-lg font-semibold mb-4">Active Alerts</h2>
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <ul className="list-disc list-inside">
              {healthData.alerts.map((alert, index) => (
                <li key={index} className="mb-2">
                  <span className="font-medium">{alert}</span>
                  <span className="text-sm text-gray-600">
                    {format(new Date(healthData.lastCheck), 'HH:mm:ss')}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemHealth;
