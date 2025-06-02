import React, { useState, useEffect } from 'react';
import { useQuery, useSubscription } from '@apollo/client';
import { GET_SYSTEM_METRICS, MONITORING_SUBSCRIPTION } from '../graphql/queries';
import {
  Box,
  Flex,
  Text,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Progress,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  VStack,
  HStack,
  Sparklines,
  SparklinesLine,
  SparklinesBars,
  useColorModeValue,
} from '@chakra-ui/react';

interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: {
    in: number;
    out: number;
  };
  trades: number;
  errors: number;
  latency: number;
  uptime: number;
}

interface Alert {
  type: string;
  message: string;
  severity: 'info' | 'warning' | 'error';
  timestamp: string;
}

const MonitoringDashboard: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const { loading, error, data } = useQuery(GET_SYSTEM_METRICS);
  const { data: subscriptionData } = useSubscription(MONITORING_SUBSCRIPTION);

  useEffect(() => {
    if (subscriptionData?.newAlert) {
      setAlerts((prev) => [...prev, subscriptionData.newAlert]);
    }
  }, [subscriptionData]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  const metrics = data?.systemMetrics;

  const getColor = (value: number, max: number) => {
    const percentage = (value / max) * 100;
    if (percentage < 70) return 'green';
    if (percentage < 90) return 'yellow';
    return 'red';
  };

  return (
    <Box p={4}>
      <Text fontSize="2xl" fontWeight="bold" mb={4}>
        System Monitoring Dashboard
      </Text>

      {/* Resource Utilization */}
      <VStack spacing={4} align="stretch">
        <HStack spacing={4}>
          <Stat>
            <StatLabel>CPU Usage</StatLabel>
            <StatNumber>{metrics?.cpu}%</StatNumber>
            <StatHelpText>
              <Progress
                value={metrics?.cpu}
                colorScheme={getColor(metrics?.cpu, 100)}
                size="sm"
              />
            </StatHelpText>
          </Stat>
          <Stat>
            <StatLabel>Memory Usage</StatLabel>
            <StatNumber>{metrics?.memory}%</StatNumber>
            <StatHelpText>
              <Progress
                value={metrics?.memory}
                colorScheme={getColor(metrics?.memory, 100)}
                size="sm"
              />
            </StatHelpText>
          </Stat>
        </HStack>

        <HStack spacing={4}>
          <Stat>
            <StatLabel>Disk Usage</StatLabel>
            <StatNumber>{metrics?.disk}%</StatNumber>
            <StatHelpText>
              <Progress
                value={metrics?.disk}
                colorScheme={getColor(metrics?.disk, 100)}
                size="sm"
              />
            </StatHelpText>
          </Stat>
          <Stat>
            <StatLabel>Network Traffic</StatLabel>
            <StatNumber>
              {metrics?.network?.in} in / {metrics?.network?.out} out
            </StatNumber>
          </Stat>
        </HStack>
      </VStack>

      {/* Performance Metrics */}
      <Box mt={4}>
        <Text fontSize="lg" fontWeight="bold" mb={2}>Performance Metrics</Text>
        <Table variant="simple">
          <Thead>
            <Tr>
              <Th>Metrics</Th>
              <Th>Value</Th>
              <Th>Status</Th>
            </Tr>
          </Thead>
          <Tbody>
            <Tr>
              <Td>Trades Executed</Td>
              <Td>{metrics?.trades}</Td>
              <Td>
                <Badge colorScheme={getColor(metrics?.trades, 1000)}>
                  {metrics?.trades > 500 ? 'High' : 'Normal'}
                </Badge>
              </Td>
            </Tr>
            <Tr>
              <Td>Errors</Td>
              <Td>{metrics?.errors}</Td>
              <Td>
                <Badge colorScheme={getColor(metrics?.errors, 100)}>
                  {metrics?.errors > 10 ? 'Critical' : 'Normal'}
                </Badge>
              </Td>
            </Tr>
            <Tr>
              <Td>Latency</Td>
              <Td>{metrics?.latency}ms</Td>
              <Td>
                <Badge colorScheme={getColor(metrics?.latency, 100)}>
                  {metrics?.latency > 50 ? 'High' : 'Normal'}
                </Badge>
              </Td>
            </Tr>
          </Tbody>
        </Table>
      </Box>

      {/* Alerts */}
      <Box mt={4}>
        <Text fontSize="lg" fontWeight="bold" mb={2}>System Alerts</Text>
        <VStack spacing={2}>
          {alerts.map((alert, index) => (
            <Box
              key={index}
              p={3}
              borderRadius="md"
              bg={useColorModeValue('gray.50', 'gray.700')}
            >
              <HStack>
                <Badge colorScheme={alert.severity}>{alert.type}</Badge>
                <Text>{alert.message}</Text>
                <Text fontSize="sm" color="gray.500">
                  {new Date(alert.timestamp).toLocaleTimeString()}
                </Text>
              </HStack>
            </Box>
          ))}
        </VStack>
      </Box>

      {/* Uptime */}
      <Box mt={4}>
        <Text fontSize="lg" fontWeight="bold" mb={2}>System Uptime</Text>
        <Stat>
          <StatLabel>Uptime</StatLabel>
          <StatNumber>
            {Math.floor(metrics?.uptime / 3600)}h {Math.floor((metrics?.uptime % 3600) / 60)}m
          </StatNumber>
          <StatHelpText>Since last restart</StatHelpText>
        </Stat>
      </Box>

      {/* Performance Trend */}
      <Box mt={4}>
        <Text fontSize="lg" fontWeight="bold" mb={2}>Performance Trend</Text>
        <Sparklines data={[metrics?.latency || 0, metrics?.errors || 0, metrics?.trades || 0]}>
          <SparklinesLine color="green" />
          <SparklinesBars color="red" />
        </Sparklines>
      </Box>
    </Box>
  );
};

export default MonitoringDashboard;
