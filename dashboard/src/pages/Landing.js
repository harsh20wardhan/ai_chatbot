import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Container,
  Grid,
  Card,
  CardContent,
  CardActions,
  AppBar,
  Toolbar,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  useTheme,
  useMediaQuery,
  Paper,
  Chip,
  Divider,
  TextField,
  Snackbar,
  Alert,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Home as HomeIcon,
  AttachMoney as PricingIcon,
  ContactSupport as ContactIcon,
  Login as LoginIcon,
  PersonAdd as SignupIcon,
  Send as SendIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  LocationOn as LocationIcon,
  CheckCircle as CheckIcon,
  SmartToy as BotIcon,
  IntegrationInstructions as IntegrationIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import LogiQuadLogo from '../components/LogiQuadLogo';

export default function Landing() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [mobileOpen, setMobileOpen] = useState(false);
  const [contactForm, setContactForm] = useState({
    name: '',
    email: '',
    message: ''
  });
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleContactSubmit = async (e) => {
    e.preventDefault();
    // For now, just show success message
    // In production, this would send to LogiQuad's contact form
    setSnackbar({
      open: true,
      message: 'Thank you for your message! We\'ll get back to you soon.',
      severity: 'success'
    });
    setContactForm({ name: '', email: '', message: '' });
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const scrollToPricing = () => {
    const pricingSection = document.getElementById('pricing-section');
    if (pricingSection) {
      pricingSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const redirectToLogiQuadContact = () => {
    window.open('https://logiquad.com/contact-us/', '_blank');
  };

  const features = [
    {
      icon: <BotIcon sx={{ fontSize: 40 }} />,
      title: "AI-Powered Responses",
      description: "Advanced language models provide human-like conversations and intelligent responses"
    },
    {
      icon: <IntegrationIcon sx={{ fontSize: 40 }} />,
      title: "Easy Integration",
      description: "Simple widget that integrates with any website in minutes"
    },
    {
      icon: <ScheduleIcon sx={{ fontSize: 40 }} />,
      title: "24/7 Availability",
      description: "Provide instant support to customers anytime, anywhere"
    }
  ];

  const pricingPlans = [
    {
      name: "Starter",
      price: "$29",
      period: "per month",
      features: [
        "1 Bot",
        "1,000 messages/month",
        "Basic support",
        "Standard response time",
        "Basic analytics"
      ],
      popular: false
    },
    {
      name: "Professional",
      price: "$99",
      period: "per month",
      features: [
        "5 Bots",
        "10,000 messages/month",
        "Priority support",
        "Fast response time",
        "Advanced analytics",
        "Custom branding"
      ],
      popular: true
    },
    {
      name: "Enterprise",
      price: "Custom",
      period: "contact us",
      features: [
        "Unlimited bots",
        "Unlimited messages",
        "Dedicated support",
        "Custom integrations",
        "White-label solution",
        "SLA guarantee"
      ],
      popular: false
    }
  ];

  const drawer = (
    <Box>
      <List>
        <ListItem button onClick={() => navigate('/')}>
          <ListItemIcon><HomeIcon /></ListItemIcon>
          <ListItemText primary="Home" />
        </ListItem>
        <ListItem button onClick={scrollToPricing}>
          <ListItemIcon><PricingIcon /></ListItemIcon>
          <ListItemText primary="Pricing" />
        </ListItem>
        <ListItem button onClick={redirectToLogiQuadContact}>
          <ListItemIcon><ContactIcon /></ListItemIcon>
          <ListItemText primary="Contact" />
        </ListItem>
        <Divider />
        <ListItem button onClick={() => navigate('/login')}>
          <ListItemIcon><LoginIcon /></ListItemIcon>
          <ListItemText primary="Login" />
        </ListItem>
        <ListItem button onClick={() => navigate('/register')}>
          <ListItemIcon><SignupIcon /></ListItemIcon>
          <ListItemText primary="Sign Up" />
        </ListItem>
      </List>
    </Box>
  );

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <AppBar position="static" color="transparent" elevation={0} sx={{ bgcolor: 'white' }}>
        <Toolbar>
          <LogiQuadLogo sx={{ flexGrow: 1 }} />
          
          {isMobile ? (
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
            >
              <MenuIcon />
            </IconButton>
          ) : (
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button color="inherit" onClick={() => navigate('/')}>Home</Button>
              <Button color="inherit" onClick={scrollToPricing}>Pricing</Button>
              <Button color="inherit" onClick={redirectToLogiQuadContact}>Contact</Button>
              <Button variant="outlined" onClick={() => navigate('/login')}>Login</Button>
              <Button variant="contained" onClick={() => navigate('/register')}>Sign Up</Button>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Mobile Drawer */}
      <Drawer
        variant="temporary"
        anchor="right"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{ keepMounted: true }}
      >
        {drawer}
      </Drawer>

      {/* Hero Section */}
      <Box sx={{ 
        bgcolor: 'primary.main', 
        color: 'white', 
        py: 8,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <Container maxWidth="lg">
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography variant="h2" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
                AI-Powered Chatbots for Your Business
              </Typography>
              <Typography variant="h5" gutterBottom sx={{ mb: 3, opacity: 0.9 }}>
                Create intelligent chatbots that understand your business and provide instant customer support
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button 
                  variant="contained" 
                  size="large" 
                  onClick={() => navigate('/register')}
                  sx={{ bgcolor: 'white', color: 'primary.main', '&:hover': { bgcolor: 'grey.100' } }}
                >
                  Get Started Free
                </Button>
                <Button 
                  variant="outlined" 
                  size="large" 
                  onClick={scrollToPricing}
                  sx={{ borderColor: 'white', color: 'white', '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.1)' } }}
                >
                  View Pricing
                </Button>
              </Box>
            </Grid>
            <Grid item xs={12} md={6} sx={{ textAlign: 'center' }}>
              <Box sx={{ 
                fontSize: '120px', 
                opacity: 0.8,
                filter: 'drop-shadow(0 0 20px rgba(255,255,255,0.3))'
              }}>
                🤖
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography variant="h3" component="h2" align="center" gutterBottom sx={{ fontWeight: 700, mb: 6 }}>
          Why Choose LogiQuad Ai?
        </Typography>
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card sx={{ height: '100%', textAlign: 'center', p: 3 }}>
                <Box sx={{ color: 'primary.main', mb: 2 }}>
                  {feature.icon}
                </Box>
                <Typography variant="h5" component="h3" gutterBottom sx={{ fontWeight: 600 }}>
                  {feature.title}
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  {feature.description}
                </Typography>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Pricing Section */}
      <Box id="pricing-section" sx={{ bgcolor: 'grey.50', py: 8 }}>
        <Container maxWidth="lg">
          <Typography variant="h3" component="h2" align="center" gutterBottom sx={{ fontWeight: 700, mb: 6 }}>
            Simple, Transparent Pricing
          </Typography>
          <Grid container spacing={4} justifyContent="center">
            {pricingPlans.map((plan, index) => (
              <Grid item xs={12} md={4} key={index}>
                <Card sx={{ 
                  height: '100%', 
                  position: 'relative',
                  transform: plan.popular ? 'scale(1.05)' : 'none',
                  border: plan.popular ? '2px solid' : 'none',
                  borderColor: 'primary.main'
                }}>
                  {plan.popular && (
                    <Chip 
                      label="Most Popular" 
                      color="primary" 
                      sx={{ 
                        position: 'absolute', 
                        top: -12, 
                        left: '50%', 
                        transform: 'translateX(-50%)',
                        fontWeight: 600
                      }} 
                    />
                  )}
                  <CardContent sx={{ textAlign: 'center', pt: plan.popular ? 4 : 2 }}>
                    <Typography variant="h4" component="h3" gutterBottom sx={{ fontWeight: 700 }}>
                      {plan.name}
                    </Typography>
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="h3" component="span" sx={{ fontWeight: 700, color: 'primary.main' }}>
                        {plan.price}
                      </Typography>
                      <Typography variant="body1" component="span" color="text.secondary">
                        {plan.period}
                      </Typography>
                    </Box>
                    <List>
                      {plan.features.map((feature, featureIndex) => (
                        <ListItem key={featureIndex} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            <CheckIcon color="primary" />
                          </ListItemIcon>
                          <ListItemText primary={feature} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                  <CardActions sx={{ justifyContent: 'center', pb: 3 }}>
                    <Button 
                      variant={plan.popular ? "contained" : "outlined"} 
                      size="large"
                      onClick={() => plan.popular ? navigate('/register') : redirectToLogiQuadContact()}
                    >
                      {plan.popular ? 'Get Started' : 'Contact Sales'}
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Contact Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="h3" component="h2" gutterBottom sx={{ fontWeight: 700 }}>
              Get in Touch
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
              Have questions about our AI chatbot platform? We'd love to hear from you.
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: 'text.primary' }}>
                We are open from 9am — 5pm week days.
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} sm={4}>
                  <Box sx={{ 
                    p: 2, 
                    bgcolor: 'white', 
                    borderRadius: 2, 
                    border: '1px solid',
                    borderColor: 'grey.200',
                    textAlign: 'center'
                  }}>
                    <Box sx={{ 
                      width: 48, 
                      height: 48, 
                      mx: 'auto', 
                      mb: 2,
                      borderRadius: '50%',
                      border: '2px solid',
                      borderColor: 'primary.main',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <LocationIcon sx={{ color: 'primary.main' }} />
                    </Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                      India Office
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                      Office - We Work Futura, Kirtane Baugh,<br />
                      Magarpatta, Hadapsar, Pune, Maharashtra<br />
                      411036
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={12} sm={4}>
                  <Box sx={{ 
                    p: 2, 
                    bgcolor: 'white', 
                    borderRadius: 2, 
                    border: '1px solid',
                    borderColor: 'grey.200',
                    textAlign: 'center'
                  }}>
                    <Box sx={{ 
                      width: 48, 
                      height: 48, 
                      mx: 'auto', 
                      mb: 2,
                      borderRadius: '50%',
                      border: '2px solid',
                      borderColor: 'primary.main',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <EmailIcon sx={{ color: 'primary.main' }} />
                    </Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                      Email
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                      Business: sales@logiquad.com<br />
                      Career: hr@logiquad.com<br />
                      Information: info@logiquad.com
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={12} sm={4}>
                  <Box sx={{ 
                    p: 2, 
                    bgcolor: 'white', 
                    borderRadius: 2, 
                    border: '1px solid',
                    borderColor: 'grey.200',
                    textAlign: 'center'
                  }}>
                    <Box sx={{ 
                      width: 48, 
                      height: 48, 
                      mx: 'auto', 
                      mb: 2,
                      borderRadius: '50%',
                      border: '2px solid',
                      borderColor: 'primary.main',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <PhoneIcon sx={{ color: 'primary.main' }} />
                    </Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                      Phone
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                      India: +91 9699985583
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper elevation={3} sx={{ p: 4 }}>
              <Typography variant="h5" component="h3" gutterBottom sx={{ fontWeight: 600 }}>
                Send us a Message
              </Typography>
              <form onSubmit={handleContactSubmit}>
                <TextField
                  fullWidth
                  label="Name"
                  value={contactForm.name}
                  onChange={(e) => setContactForm(prev => ({ ...prev, name: e.target.value }))}
                  margin="normal"
                  required
                />
                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={contactForm.email}
                  onChange={(e) => setContactForm(prev => ({ ...prev, email: e.target.value }))}
                  margin="normal"
                  required
                />
                <TextField
                  fullWidth
                  label="Message"
                  multiline
                  rows={4}
                  value={contactForm.message}
                  onChange={(e) => setContactForm(prev => ({ ...prev, message: e.target.value }))}
                  margin="normal"
                  required
                />
                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                  fullWidth
                  sx={{ mt: 3 }}
                  endIcon={<SendIcon />}
                >
                  Send Message
                </Button>
              </form>
            </Paper>
          </Grid>
        </Grid>
      </Container>

      {/* Footer */}
      <Box sx={{ bgcolor: 'grey.900', color: 'white', py: 4 }}>
        <Container maxWidth="lg">
          <Grid container spacing={4}>
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
                LogiQuad Ai
              </Typography>
              <Typography variant="body2" color="grey.400">
                Empowering businesses with intelligent AI chatbots for better customer engagement and support.
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Quick Links
              </Typography>
              <List dense>
                <ListItem sx={{ px: 0 }}>
                  <Button color="inherit" onClick={() => navigate('/')}>Home</Button>
                </ListItem>
                <ListItem sx={{ px: 0 }}>
                  <Button color="inherit" onClick={scrollToPricing}>Pricing</Button>
                </ListItem>
                <ListItem sx={{ px: 0 }}>
                  <Button color="inherit" onClick={redirectToLogiQuadContact}>Contact</Button>
                </ListItem>
              </List>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Get Started
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Button variant="outlined" size="small" onClick={() => navigate('/login')}>
                  Login
                </Button>
                <Button variant="contained" size="small" onClick={() => navigate('/register')}>
                  Sign Up
                </Button>
              </Box>
            </Grid>
          </Grid>
          <Divider sx={{ my: 3, borderColor: 'grey.700' }} />
          <Typography variant="body2" color="grey.400" align="center">
            © 2024 LogiQuad Ai. All rights reserved.
          </Typography>
        </Container>
      </Box>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
