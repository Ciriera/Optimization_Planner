import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
  Fade,
  Chip,
} from '@mui/material';
import {
  LockOutlined,
  Email,
  Visibility,
  VisibilityOff,
  AutoGraph,
  Psychology,
  Speed,
  Analytics,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const features = [
    { icon: <AutoGraph />, text: 'Advanced Optimization' },
    { icon: <Psychology />, text: 'AI-Powered Scheduling' },
    { icon: <Speed />, text: 'Real-time Analytics' },
    { icon: <Analytics />, text: 'Multi-Algorithm Support' },
  ];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        width: '100vw',
        display: 'flex',
        position: 'relative',
        overflow: 'hidden',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
      }}
    >
      {/* Animated Background Elements */}
      <Box
        sx={{
          position: 'absolute',
          top: '10%',
          left: '5%',
          width: '400px',
          height: '400px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%)',
          filter: 'blur(40px)',
          animation: 'float 8s ease-in-out infinite',
          '@keyframes float': {
            '0%, 100%': { transform: 'translateY(0) translateX(0)' },
            '50%': { transform: 'translateY(-30px) translateX(20px)' },
          },
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          bottom: '10%',
          right: '10%',
          width: '350px',
          height: '350px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(147, 51, 234, 0.15) 0%, transparent 70%)',
          filter: 'blur(40px)',
          animation: 'float2 10s ease-in-out infinite',
          '@keyframes float2': {
            '0%, 100%': { transform: 'translateY(0) translateX(0)' },
            '50%': { transform: 'translateY(25px) translateX(-20px)' },
          },
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          right: '30%',
          width: '200px',
          height: '200px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, transparent 70%)',
          filter: 'blur(30px)',
          animation: 'float3 6s ease-in-out infinite',
          '@keyframes float3': {
            '0%, 100%': { transform: 'translateY(0)' },
            '50%': { transform: 'translateY(-20px)' },
          },
        }}
      />

      {/* Left Side - Branding */}
      <Fade in timeout={800}>
        <Box
          sx={{
            flex: 1,
            display: { xs: 'none', md: 'flex' },
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'flex-end',
            pr: 6,
            position: 'relative',
            zIndex: 1,
          }}
        >
          <Box sx={{ maxWidth: '500px' }}>
            <Box
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 1.5,
                mb: 4,
                px: 2,
                py: 1,
                borderRadius: 2,
                background: 'rgba(59, 130, 246, 0.1)',
                border: '1px solid rgba(59, 130, 246, 0.2)',
              }}
            >
              <Box
                sx={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  background: '#10b981',
                  boxShadow: '0 0 10px #10b981',
                  animation: 'pulse 2s ease-in-out infinite',
                  '@keyframes pulse': {
                    '0%, 100%': { opacity: 1, transform: 'scale(1)' },
                    '50%': { opacity: 0.7, transform: 'scale(1.1)' },
                  },
                }}
              />
              <Typography sx={{ color: '#94a3b8', fontSize: '0.85rem', fontWeight: 500 }}>
                Optimization Engine v2.0
              </Typography>
            </Box>

            <Typography
              variant="h2"
              sx={{
                fontWeight: 800,
                color: '#ffffff',
                mb: 2,
                lineHeight: 1.2,
                background: 'linear-gradient(135deg, #ffffff 0%, #94a3b8 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Optimization
              <br />
              Planner
            </Typography>

            <Typography
              variant="h6"
              sx={{
                color: '#64748b',
                mb: 5,
                fontWeight: 400,
                lineHeight: 1.6,
              }}
            >
              Intelligent project scheduling and resource optimization
              powered by advanced algorithms and AI
            </Typography>

            {/* Feature Pills */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
              {features.map((feature, index) => (
                <Fade in timeout={1000 + index * 200} key={index}>
                  <Chip
                    icon={React.cloneElement(feature.icon, {
                      sx: { color: '#3b82f6 !important', fontSize: '1.1rem' }
                    })}
                    label={feature.text}
                    sx={{
                      background: 'rgba(59, 130, 246, 0.1)',
                      border: '1px solid rgba(59, 130, 246, 0.2)',
                      color: '#e2e8f0',
                      fontWeight: 500,
                      fontSize: '0.85rem',
                      py: 2.5,
                      px: 0.5,
                      '& .MuiChip-icon': {
                        ml: 1,
                      },
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        background: 'rgba(59, 130, 246, 0.2)',
                        transform: 'translateY(-2px)',
                      },
                    }}
                  />
                </Fade>
              ))}
            </Box>
          </Box>
        </Box>
      </Fade>

      {/* Right Side - Login Form */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-start',
          pl: { xs: 3, md: 6 },
          pr: { xs: 3, md: 0 },
          position: 'relative',
          zIndex: 1,
        }}
      >
        <Fade in timeout={600}>
          <Box
            sx={{
              width: '100%',
              maxWidth: '400px',
              p: 4,
              borderRadius: 4,
              background: 'rgba(30, 41, 59, 0.7)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
            }}
          >
            {/* Logo/Icon */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Box
                sx={{
                  width: 64,
                  height: 64,
                  mx: 'auto',
                  mb: 3,
                  borderRadius: 3,
                  background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 10px 30px -5px rgba(59, 130, 246, 0.4)',
                }}
              >
                <LockOutlined sx={{ color: '#ffffff', fontSize: 32 }} />
              </Box>

              <Typography
                variant="h5"
                sx={{
                  fontWeight: 700,
                  color: '#ffffff',
                  mb: 1,
                }}
              >
                Welcome Back
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  color: '#64748b',
                }}
              >
                Sign in to access your dashboard
              </Typography>
            </Box>

            {/* Error Alert */}
            {error && (
              <Fade in>
                <Alert
                  severity="error"
                  sx={{
                    mb: 3,
                    borderRadius: 2,
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#fca5a5',
                    '& .MuiAlert-icon': {
                      color: '#f87171',
                    },
                  }}
                >
                  {error}
                </Alert>
              </Fade>
            )}

            {/* Login Form */}
            <Box component="form" onSubmit={handleSubmit}>
              <TextField
                fullWidth
                id="email"
                label="Email Address"
                name="email"
                autoComplete="email"
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Email sx={{ color: '#64748b' }} />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  mb: 2.5,
                  '& .MuiOutlinedInput-root': {
                    background: 'rgba(15, 23, 42, 0.5)',
                    borderRadius: 2,
                    '& fieldset': {
                      borderColor: 'rgba(255, 255, 255, 0.1)',
                    },
                    '&:hover fieldset': {
                      borderColor: 'rgba(59, 130, 246, 0.5)',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#3b82f6',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: '#64748b',
                  },
                  '& .MuiInputLabel-root.Mui-focused': {
                    color: '#3b82f6',
                  },
                  '& .MuiInputBase-input': {
                    color: '#e2e8f0',
                  },
                }}
              />

              <TextField
                fullWidth
                name="password"
                label="Password"
                type={showPassword ? 'text' : 'password'}
                id="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LockOutlined sx={{ color: '#64748b' }} />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                        sx={{ color: '#64748b' }}
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    background: 'rgba(15, 23, 42, 0.5)',
                    borderRadius: 2,
                    '& fieldset': {
                      borderColor: 'rgba(255, 255, 255, 0.1)',
                    },
                    '&:hover fieldset': {
                      borderColor: 'rgba(59, 130, 246, 0.5)',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#3b82f6',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: '#64748b',
                  },
                  '& .MuiInputLabel-root.Mui-focused': {
                    color: '#3b82f6',
                  },
                  '& .MuiInputBase-input': {
                    color: '#e2e8f0',
                  },
                }}
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loading}
                sx={{
                  py: 1.5,
                  borderRadius: 2,
                  fontSize: '1rem',
                  fontWeight: 600,
                  textTransform: 'none',
                  background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                  boxShadow: '0 10px 30px -5px rgba(59, 130, 246, 0.4)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 15px 35px -5px rgba(59, 130, 246, 0.5)',
                  },
                  '&:disabled': {
                    background: 'rgba(59, 130, 246, 0.3)',
                  },
                }}
              >
                {loading ? (
                  <CircularProgress size={24} sx={{ color: '#ffffff' }} />
                ) : (
                  'Sign In'
                )}
              </Button>
            </Box>

            {/* Demo Account Info */}
            <Box
              sx={{
                mt: 4,
                pt: 3,
                borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                textAlign: 'center',
              }}
            >
              <Chip
                label="Demo hesabı otomatik dolduruldu"
                size="small"
                sx={{
                  background: 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  color: '#6ee7b7',
                  fontSize: '0.75rem',
                }}
              />
            </Box>
          </Box>
        </Fade>
      </Box>
    </Box>
  );
};

export default Login;
