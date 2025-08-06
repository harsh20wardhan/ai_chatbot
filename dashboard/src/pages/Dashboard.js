import React, { useState, useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Divider,
  Paper,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Link,
  Chip,
} from '@mui/material';
import { botApi, analyticsApi } from '../services/api';

export default function Dashboard() {
  const [bots, setBots] = useState([]);
  const [recentBots, setRecentBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalBots: 0,
    activeBots: 0,
    totalMessages: 0,
    totalDocuments: 0,
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch all bots
        const botsData = await botApi.getBots();
        setBots(botsData);
        
        // Set recent bots (last 3)
        setRecentBots(botsData.slice(0, 3));
        
        // Set stats
        setStats({
          totalBots: botsData.length,
          activeBots: botsData.filter(bot => bot.status === 'active').length || 0,
          totalMessages: botsData.reduce((sum, bot) => sum + (bot.messages_count || 0), 0),
          totalDocuments: botsData.reduce((sum, bot) => sum + (bot.documents_count || 0), 0),
        });
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>

      {loading ? (
        <LinearProgress />
      ) : (
        <>
          {/* Stats Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Total Bots
                  </Typography>
                  <Typography variant="h3">{stats.totalBots}</Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Active Bots
                  </Typography>
                  <Typography variant="h3">{stats.activeBots}</Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Total Messages
                  </Typography>
                  <Typography variant="h3">{stats.totalMessages}</Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Total Documents
                  </Typography>
                  <Typography variant="h3">{stats.totalDocuments}</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Recent Bots */}
          <Typography variant="h5" gutterBottom>
            Recent Bots
          </Typography>
          
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {recentBots.length > 0 ? (
              recentBots.map((bot) => (
                <Grid item xs={12} sm={6} md={4} key={bot.id}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" component="div">
                        {bot.name}
                      </Typography>
                      <Typography color="textSecondary" sx={{ mb: 1.5 }}>
                        {bot.description || 'No description'}
                      </Typography>
                      <Divider sx={{ my: 1 }} />
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                        <Chip 
                          label={`${bot.messages_count || 0} messages`} 
                          size="small" 
                          color="primary" 
                          variant="outlined" 
                        />
                        <Chip 
                          label={`${bot.documents_count || 0} documents`} 
                          size="small" 
                          color="secondary" 
                          variant="outlined" 
                        />
                      </Box>
                    </CardContent>
                    <CardActions>
                      <Button 
                        size="small" 
                        component={RouterLink} 
                        to={`/bots/${bot.id}`}
                      >
                        Manage
                      </Button>
                      <Button 
                        size="small" 
                        component={RouterLink} 
                        to={`/bots/${bot.id}/widget`}
                      >
                        Widget Config
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))
            ) : (
              <Grid item xs={12}>
                <Paper sx={{ p: 3, textAlign: 'center' }}>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    You haven't created any bots yet.
                  </Typography>
                  <Button 
                    variant="contained" 
                    component={RouterLink} 
                    to="/bots"
                  >
                    Create Your First Bot
                  </Button>
                </Paper>
              </Grid>
            )}
          </Grid>

          {/* Quick Links */}
          <Typography variant="h5" gutterBottom>
            Quick Links
          </Typography>
          
          <Paper sx={{ p: 2 }}>
            <List>
              <ListItem button component={RouterLink} to="/bots">
                <ListItemText primary="Manage All Bots" />
              </ListItem>
              <Divider />
              <ListItem button component={RouterLink} to="/analytics">
                <ListItemText primary="View Analytics" />
              </ListItem>
              <Divider />
              <ListItem button component="a" href="#widget-docs" target="_blank">
                <ListItemText primary="Widget Documentation" />
              </ListItem>
            </List>
          </Paper>
        </>
      )}
    </Box>
  );
}