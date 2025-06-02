import { extendTheme } from '@chakra-ui/react';
import { mode } from '@chakra-ui/theme-utils';

const config = {
  initialColorMode: 'system',
  useSystemColorMode: true,
};

const styles = {
  global: (props: any) => ({
    body: {
      bg: mode('gray.50', 'gray.900')(props),
      color: mode('gray.900', 'white')(props),
    },
  }),
};

const colors = {
  brand: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',
    600: '#0284c7',
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
  },
};

const components = {
  Button: {
    defaultProps: {
      colorScheme: 'brand',
    },
    variants: {
      solid: (props: any) => ({
        bg: mode('brand.500', 'brand.300')(props),
        color: mode('white', 'gray.900')(props),
        _hover: {
          bg: mode('brand.600', 'brand.400')(props),
        },
      }),
    },
  },
  Input: {
    defaultProps: {
      variant: 'filled',
    },
    variants: {
      filled: (props: any) => ({
        field: {
          bg: mode('gray.100', 'gray.700')(props),
          color: mode('gray.900', 'white')(props),
          _hover: {
            bg: mode('gray.200', 'gray.600')(props),
          },
          _focus: {
            boxShadow: 'outline',
          },
        },
      }),
    },
  },
};

const theme = extendTheme({
  config,
  styles,
  colors,
  components,
});

export default theme;
