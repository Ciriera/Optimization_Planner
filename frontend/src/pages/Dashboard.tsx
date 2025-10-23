import React, { useEffect, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  IconButton,
  Avatar,
  Stack,
  Fade,
  CircularProgress,
  Alert,
  AlertTitle,
  LinearProgress,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemAvatar,
  Badge,
  Tooltip,
} from '@mui/material';
import {
  Assignment,
  People,
  Science,
  Schedule,
  Dashboard as DashboardIcon,
  TrendingUp,
  CheckCircle,
  Warning,
  Error,
  Info,
  Refresh,
  Analytics,
  Speed,
  Group,
  Room,
  AccessTime,
  Star,
  StarBorder,
  FilterList,
  Search,
  Download,
  CloudDownload,
  GetApp,
  CalendarToday,
  Assessment,
  School,
  Timeline,
  BarChart,
  PieChart,
  Person,
  Visibility,
  Print,
  Share,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/authService';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({ projects: 0, instructors: 0, algorithms: 0, schedules: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.get('/projects/'),
      api.get('/instructors/'),
      api.get('/algorithms/list'),
      api.get('/schedules/'),
    ])
      .then(([projectsRes, instructorsRes, algorithmsRes, schedulesRes]) => {
        setStats({
          projects: projectsRes.data.length,
          instructors: instructorsRes.data.length,
          algorithms: algorithmsRes.data.length,
          schedules: schedulesRes.data.length,
        });
      })
      .catch((err) => {
        setError(err?.response?.data?.detail || 'Failed to fetch dashboard data');
      })
      .finally(() => setLoading(false));
  }, []);

  const recentActivities = [
    {
      id: 1,
      action: 'System initialized',
      timestamp: 'Just now',
      type: 'info',
    },
  ];

  return (
    <Box sx={{ minHeight: 'calc(100vh - 64px)', p: 3 }}>
      {/* Header Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, mb: 1 }}>
          Welcome back, {user?.full_name}! 👋
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Proje Planlama ve Optimizasyon Sistemi Dashboard
        </Typography>
      </Box>

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <Box sx={{ textAlign: 'center' }}>
            <CircularProgress size={48} sx={{ mb: 2 }} />
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
              Dashboard Yükleniyor...
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Sistem verileri alınıyor, lütfen bekleyin
            </Typography>
          </Box>
        </Box>
      )}

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          <AlertTitle>Veri Yükleme Hatası</AlertTitle>
          {error}
        </Alert>
      )}

      {/* Main Content */}
      {!loading && !error && (
        <Box>
          {/* Stats Cards */}
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, 1fr)',
                md: 'repeat(4, 1fr)',
              },
              gap: 3,
              mb: 4,
            }}
          >
            <Card sx={{ minHeight: 120 }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom sx={{ fontSize: '0.875rem' }}>
                      Toplam Proje
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main', mb: 0.5 }}>
                      {stats.projects}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Sistemdeki tüm projeler
                    </Typography>
                  </Box>
                  <Assignment sx={{ fontSize: 48, color: 'primary.main', opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>

            <Card sx={{ minHeight: 120 }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom sx={{ fontSize: '0.875rem' }}>
                      Eğitmenler
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 600, color: 'secondary.main', mb: 0.5 }}>
                      {stats.instructors}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Aktif öğretim üyeleri
                    </Typography>
                  </Box>
                  <People sx={{ fontSize: 48, color: 'secondary.main', opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>

            <Card sx={{ minHeight: 120 }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom sx={{ fontSize: '0.875rem' }}>
                      Algoritmalar
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main', mb: 0.5 }}>
                      {stats.algorithms}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Optimizasyon algoritmaları
                    </Typography>
                  </Box>
                  <Science sx={{ fontSize: 48, color: 'success.main', opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>

            <Card sx={{ minHeight: 120 }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom sx={{ fontSize: '0.875rem' }}>
                      Programlar
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 600, color: 'warning.main', mb: 0.5 }}>
                      {stats.schedules}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Aktif programlar
                    </Typography>
                  </Box>
                  <Schedule sx={{ fontSize: 48, color: 'warning.main', opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Main Content Grid - More Compact */}
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                lg: '3fr 2fr',
              },
              gap: 2,
              flex: 1,
            }}
          >
            {/* Quick Actions */}
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
                Hızlı İşlemler
              </Typography>

              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: {
                    xs: '1fr',
                    sm: 'repeat(2, 1fr)',
                  },
                  gap: 1.5,
                }}
              >
                <Card 
                  onClick={() => navigate('/projects')} 
                  role="button" 
                  tabIndex={0} 
                  sx={{ 
                    cursor: 'pointer', 
                    minHeight: 100,
                    transition: 'all 0.2s ease',
                    '&:hover': { 
                      boxShadow: 4,
                      transform: 'translateY(-2px)'
                    } 
                  }}
                >
                  <CardContent sx={{ p: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Assignment sx={{ mr: 1.5, color: 'primary.main', fontSize: 24 }} />
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        Proje Oluştur
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                      Yeni proje ataması başlat
                    </Typography>
                  </CardContent>
                </Card>

                <Card 
                  onClick={() => navigate('/algorithms')} 
                  role="button" 
                  tabIndex={0} 
                  sx={{ 
                    cursor: 'pointer', 
                    minHeight: 100,
                    transition: 'all 0.2s ease',
                    '&:hover': { 
                      boxShadow: 4,
                      transform: 'translateY(-2px)'
                    } 
                  }}
                >
                  <CardContent sx={{ p: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Science sx={{ mr: 1.5, color: 'success.main', fontSize: 24 }} />
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        Algoritma Çalıştır
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                      Optimizasyon algoritması yürüt
                    </Typography>
                  </CardContent>
                </Card>

                <Card 
                  onClick={() => navigate('/planner')} 
                  role="button" 
                  tabIndex={0} 
                  sx={{ 
                    cursor: 'pointer', 
                    minHeight: 100,
                    transition: 'all 0.2s ease',
                    '&:hover': { 
                      boxShadow: 4,
                      transform: 'translateY(-2px)'
                    } 
                  }}
                >
                  <CardContent sx={{ p: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <CalendarToday sx={{ mr: 1.5, color: 'info.main', fontSize: 24 }} />
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        Planlayıcı
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                      Proje programlarını görüntüle
                    </Typography>
                  </CardContent>
                </Card>

                <Card 
                  onClick={() => navigate('/instructors')} 
                  role="button" 
                  tabIndex={0} 
                  sx={{ 
                    cursor: 'pointer', 
                    minHeight: 100,
                    transition: 'all 0.2s ease',
                    '&:hover': { 
                      boxShadow: 4,
                      transform: 'translateY(-2px)'
                    } 
                  }}
                >
                  <CardContent sx={{ p: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <People sx={{ mr: 1.5, color: 'secondary.main', fontSize: 24 }} />
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        Eğitmen Yönetimi
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                      Eğitmen bilgilerini güncelle
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            </Paper>

            {/* Recent Activities */}
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
                Son Aktiviteler
              </Typography>
              <Box>
                {recentActivities.map((activity) => (
                  <Box key={activity.id} sx={{ 
                    mb: 1.5, 
                    p: 2, 
                    bgcolor: 'grey.50', 
                    borderRadius: 1.5,
                    border: '1px solid',
                    borderColor: 'grey.200',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      bgcolor: 'grey.100',
                      borderColor: 'grey.300'
                    }
                  }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                      <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.8rem' }}>
                        {activity.action}
                      </Typography>
                      <Chip
                        label={activity.type}
                        size="small"
                        color="primary"
                        variant="outlined"
                        sx={{ fontSize: '0.7rem', height: 20 }}
                      />
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                      {activity.timestamp}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Paper>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default Dashboard;
