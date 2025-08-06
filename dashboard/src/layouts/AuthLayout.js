import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { Box, Container, Paper, Typography } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

export default function AuthLayout() {
  const { user, loading } = useAuth();
  
  // If user is already authenticated, redirect to dashboard
  if (user && !loading) {
    return <Navigate to="/" replace />;
  }
  
  return (
    <Box
      sx={{
        display: 'flex',
        minHeight: '100vh',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={3}
          sx={{
            p: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            borderRadius: 2,
          }}
        >
          <Typography component="h1" variant="h4" sx={{ mb: 3 }}>
            AI Chatbot Platform
          </Typography>
          
          <Outlet />
        </Paper>
      </Container>
    </Box>
  );
}