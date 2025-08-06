import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { Home as HomeIcon } from '@mui/icons-material';

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: 'calc(100vh - 200px)',
      }}
    >
      <Paper
        sx={{
          p: 5,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          maxWidth: 500,
          textAlign: 'center',
        }}
        elevation={3}
      >
        <Typography variant="h1" sx={{ mb: 2, fontSize: '6rem', fontWeight: 700, color: 'primary.main' }}>
          404
        </Typography>
        
        <Typography variant="h4" sx={{ mb: 2 }}>
          Page Not Found
        </Typography>
        
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
        </Typography>
        
        <Button
          variant="contained"
          startIcon={<HomeIcon />}
          onClick={() => navigate('/')}
          size="large"
        >
          Back to Home
        </Button>
      </Paper>
    </Box>
  );
}