import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';
import { botApi, analyticsApi } from '../services/api';

// Register Chart.js components
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

export default function Analytics() {
  const [bots, setBots] = useState([]);
  const [selectedBot, setSelectedBot] = useState('');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [timeRange, setTimeRange] = useState('7d');

  useEffect(() => {
    const fetchBots = async () => {
      try {
        const botsData = await botApi.getBots();
        setBots(botsData);
        
        if (botsData.length > 0) {
          setSelectedBot(botsData[0].id);
        }
      } catch (error) {
        console.error('Error fetching bots:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchBots();
  }, []);

  useEffect(() => {
    if (selectedBot) {
      fetchBotStats();
    }
  }, [selectedBot, timeRange]);

  const fetchBotStats = async () => {
    try {
      setLoading(true);
      const statsData = await analyticsApi.getBotStats(selectedBot);
      setStats(statsData);
    } catch (error) {
      console.error('Error fetching bot stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBotChange = (event) => {
    setSelectedBot(event.target.value);
  };

  const handleTimeRangeChange = (event) => {
    setTimeRange(event.target.value);
  };

  // Prepare chart data
  const usageChartData = {
    labels: stats?.dailyUsage.map(item => {
      const date = new Date(item.date);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }) || [],
    datasets: [
      {
        label: 'Messages',
        data: stats?.dailyUsage.map(item => item.messages) || [],
        borderColor: 'rgb(53, 162, 235)',
        backgroundColor: 'rgba(53, 162, 235, 0.5)',
        tension: 0.3,
      },
    ],
  };

  const topQuestionsChartData = {
    labels: stats?.topQuestions.map(item => item.question) || [],
    datasets: [
      {
        label: 'Frequency',
        data: stats?.topQuestions.map(item => item.count) || [],
        backgroundColor: [
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)',
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  if (loading && !stats) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Analytics
      </Typography>

      <Box sx={{ mb: 4, display: 'flex', gap: 2 }}>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel id="bot-select-label">Bot</InputLabel>
          <Select
            labelId="bot-select-label"
            id="bot-select"
            value={selectedBot}
            label="Bot"
            onChange={handleBotChange}
          >
            {bots.map((bot) => (
              <MenuItem key={bot.id} value={bot.id}>
                {bot.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel id="time-range-label">Time Range</InputLabel>
          <Select
            labelId="time-range-label"
            id="time-range"
            value={timeRange}
            label="Time Range"
            onChange={handleTimeRangeChange}
          >
            <MenuItem value="7d">Last 7 days</MenuItem>
            <MenuItem value="30d">Last 30 days</MenuItem>
            <MenuItem value="90d">Last 90 days</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="textSecondary" gutterBottom>
                Total Messages
              </Typography>
              <Typography variant="h3">
                {stats?.totalMessages || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="textSecondary" gutterBottom>
                Unique Users
              </Typography>
              <Typography variant="h3">
                {stats?.uniqueUsers || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="textSecondary" gutterBottom>
                Avg. Response Time
              </Typography>
              <Typography variant="h3">
                {stats?.averageResponseTime?.toFixed(2) || 0}s
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="textSecondary" gutterBottom>
                Success Rate
              </Typography>
              <Typography variant="h3">
                98%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Usage Over Time
              </Typography>
              <Box sx={{ height: 300 }}>
                <Line 
                  data={usageChartData} 
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      y: {
                        beginAtZero: true,
                        title: {
                          display: true,
                          text: 'Message Count'
                        }
                      },
                      x: {
                        title: {
                          display: true,
                          text: 'Date'
                        }
                      }
                    }
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Questions
              </Typography>
              <Box sx={{ height: 300 }}>
                <Pie 
                  data={topQuestionsChartData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'bottom',
                        labels: {
                          boxWidth: 15,
                          font: {
                            size: 10
                          }
                        }
                      },
                      tooltip: {
                        callbacks: {
                          label: function(context) {
                            return context.label + ': ' + context.raw;
                          }
                        }
                      }
                    }
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Questions
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Question</TableCell>
                      <TableCell align="right">Count</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {stats?.topQuestions.map((question, index) => (
                      <TableRow key={index}>
                        <TableCell>{question.question}</TableCell>
                        <TableCell align="right">{question.count}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}