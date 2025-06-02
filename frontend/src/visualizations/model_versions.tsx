import React, { useState, useEffect } from 'react';
import { useQuery } from '@apollo/client';
import { GET_MODEL_VERSIONS } from '../graphql/queries';
import {
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Button,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Select,
  FormControl,
  FormLabel,
  Text,
  Box,
  Badge,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
} from '@chakra-ui/react';

interface ModelVersion {
  version: string;
  created_at: string;
  metrics: {
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
  };
  parameters: {
    model_type: string;
    input_size: number;
    hidden_size: number;
    num_layers: number;
  };
  status: string;
  notes: string;
}

const ModelVersions: React.FC = () => {
  const { loading, error, data } = useQuery(GET_MODEL_VERSIONS);
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState(false);
  const [comparisonVersion, setComparisonVersion] = useState<string | null>(null);

  const handleCompare = (version: string) => {
    setSelectedVersion(version);
    setIsCompareModalOpen(true);
  };

  const handleRollback = async (version: string) => {
    // Implementation for rollback
    console.log('Rolling back to version:', version);
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  const versions = data?.modelVersions || [];

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Model Version Management</h1>

      <TableContainer>
        <Table variant="simple">
          <Thead>
            <Tr>
              <Th>Version</Th>
              <Th>Status</Th>
              <Th>Created At</Th>
              <Th>Accuracy</Th>
              <Th>Actions</Th>
            </Tr>
          </Thead>
          <Tbody>
            {versions.map((version: ModelVersion) => (
              <Tr key={version.version}>
                <Td>{version.version}</Td>
                <Td>
                  <Badge colorScheme={getStatusColor(version.status)}>
                    {version.status}
                  </Badge>
                </Td>
                <Td>{format(new Date(version.created_at), 'yyyy-MM-dd HH:mm')}</Td>
                <Td>
                  <Stat>
                    <StatLabel>Accuracy</StatLabel>
                    <StatNumber>{version.metrics.accuracy.toFixed(2)}%</StatNumber>
                    <StatHelpText>
                      Precision: {version.metrics.precision.toFixed(2)}%
                    </StatHelpText>
                  </Stat>
                </Td>
                <Td>
                  <Button
                    size="sm"
                    colorScheme="blue"
                    onClick={() => handleCompare(version.version)}
                    mr={2}
                  >
                    Compare
                  </Button>
                  <Button
                    size="sm"
                    colorScheme="green"
                    onClick={() => handleRollback(version.version)}
                  >
                    Rollback
                  </Button>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </TableContainer>

      <Modal isOpen={isCompareModalOpen} onClose={() => setIsCompareModalOpen(false)}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Compare Model Versions</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <FormControl mb={4}>
              <FormLabel>Select Version to Compare With</FormLabel>
              <Select
                value={comparisonVersion}
                onChange={(e) => setComparisonVersion(e.target.value)}
              >
                {versions.map((version: ModelVersion) => (
                  <option key={version.version} value={version.version}>
                    {version.version}
                  </option>
                ))}
              </Select>
            </FormControl>

            {comparisonVersion && (
              <Box>
                <Text fontSize="lg" mb={4}>
                  Comparing {selectedVersion} with {comparisonVersion}
                </Text>
                <div className="grid grid-cols-2 gap-4">
                  <Box p={4} border="1px" borderColor="gray.200" borderRadius="md">
                    <h3 className="font-semibold mb-2">Current Version</h3>
                    <MetricsDisplay version={selectedVersion} versions={versions} />
                  </Box>
                  <Box p={4} border="1px" borderColor="gray.200" borderRadius="md">
                    <h3 className="font-semibold mb-2">Comparison Version</h3>
                    <MetricsDisplay version={comparisonVersion} versions={versions} />
                  </Box>
                </div>
              </Box>
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </div>
  );
};

const MetricsDisplay: React.FC<{ version: string; versions: ModelVersion[] }> = ({
  version,
  versions,
}) => {
  const model = versions.find((v) => v.version === version);
  
  if (!model) return null;

  return (
    <div>
      <div className="mb-4">
        <h4 className="text-sm font-medium">Performance Metrics</h4>
        <div className="grid grid-cols-2 gap-2">
          <Stat>
            <StatLabel>Accuracy</StatLabel>
            <StatNumber>{model.metrics.accuracy.toFixed(2)}%</StatNumber>
          </Stat>
          <Stat>
            <StatLabel>Precision</StatLabel>
            <StatNumber>{model.metrics.precision.toFixed(2)}%</StatNumber>
          </Stat>
          <Stat>
            <StatLabel>Recall</StatLabel>
            <StatNumber>{model.metrics.recall.toFixed(2)}%</StatNumber>
          </Stat>
          <Stat>
            <StatLabel>F1 Score</StatLabel>
            <StatNumber>{model.metrics.f1_score.toFixed(2)}</StatNumber>
          </Stat>
        </div>
      </div>

      <div className="mb-4">
        <h4 className="text-sm font-medium">Model Architecture</h4>
        <div className="space-y-2">
          <p>
            <span className="font-medium">Type:</span> {model.parameters.model_type}
          </p>
          <p>
            <span className="font-medium">Input Size:</span>{' '}
            {model.parameters.input_size}
          </p>
          <p>
            <span className="font-medium">Hidden Size:</span>{' '}
            {model.parameters.hidden_size}
          </p>
          <p>
            <span className="font-medium">Layers:</span>{' '}
            {model.parameters.num_layers}
          </p>
        </div>
      </div>

      {model.notes && (
        <div>
          <h4 className="text-sm font-medium">Notes</h4>
          <p className="text-sm text-gray-600">{model.notes}</p>
        </div>
      )}
    </div>
  );
};

const getStatusColor = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'active':
      return 'green';
    case 'inactive':
      return 'gray';
    case 'deprecated':
      return 'red';
    default:
      return 'blue';
  }
};

export default ModelVersions;
