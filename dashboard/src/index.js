import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import './index.css';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { grey } from '@mui/material/colors';
import CssBaseline from '@mui/material/CssBaseline';

const theme = createTheme({
  palette: {
    mode: 'light',
    // Aligned with LogiQuad’s brand feel: blue primary + green accent
    primary: { main: '#2563eb' },
    secondary: { main: '#22c55e' },
    success: { main: '#16a34a' },
    info: { main: '#0ea5e9' },
    warning: { main: '#f59e0b' },
    background: { default: '#f8fafc', paper: '#ffffff' },
    divider: grey[200],
    text: { primary: '#0f172a', secondary: '#475569' },
  },
  shape: {
    borderRadius: 12,
  },
  typography: {
    fontFamily: 'Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, Apple Color Emoji, Segoe UI Emoji',
    h1: { fontSize: '2.25rem', fontWeight: 700, letterSpacing: '-0.02em' },
    h2: { fontSize: '1.875rem', fontWeight: 700, letterSpacing: '-0.02em' },
    h3: { fontSize: '1.5rem', fontWeight: 700 },
    h4: { fontSize: '1.25rem', fontWeight: 700 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#f8fafc',
          backgroundImage:
            'radial-gradient(60% 60% at 0% 0%, rgba(99,102,241,0.08) 0%, rgba(99,102,241,0) 60%), radial-gradient(50% 50% at 100% 0%, rgba(34,197,94,0.08) 0%, rgba(34,197,94,0) 50%)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          fontWeight: 600,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 10px 30px rgba(2, 6, 23, 0.06)',
          border: '1px solid #eef2f7',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backdropFilter: 'blur(8px)',
          backgroundColor: 'rgba(255,255,255,0.8)',
          boxShadow: '0 6px 20px rgba(2, 6, 23, 0.08)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: '1px solid #eef2f7',
          backgroundImage: 'none',
          backgroundColor: '#ffffff',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          '&.Mui-selected': {
            backgroundColor: 'rgba(99, 102, 241, 0.08)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600 },
      },
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <App />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
);