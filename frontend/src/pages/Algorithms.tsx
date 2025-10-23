import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Button,
  Tabs,
  Tab,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Science,
  Speed,
  Psychology,
  TrendingUp,
  CheckCircle,
  Error,
  Pending,
  Analytics,
  Recommend,
} from '@mui/icons-material';
import { algorithmService, Algorithm } from '../services/algorithmService';
import { api } from '../services/authService';
import { useNavigate } from 'react-router-dom';
import { useAlgorithmProgress } from '../hooks/useAlgorithmProgress';
import { useAuth } from '../contexts/AuthContext';
import SlotInsufficiencyDialog from '../components/SlotInsufficiencyDialog';

const Algorithms: React.FC = () => {
  const { user } = useAuth();
  const [algorithms, setAlgorithms] = useState<Algorithm[]>([]);
  const [algorithmRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [tabValue, setTabValue] = useState(0);
  
  // Execution state
  const [executing, setExecuting] = useState(false);
  const [snack, setSnack] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({ 
    open: false, 
    message: '', 
    severity: 'success' 
  });
  
  // Algorithm recommendation state
  const [recommendation, setRecommendation] = useState<any>(null);
  const [recommendationLoading, setRecommendationLoading] = useState(false);
  
  // Algorithm parameters state
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<Algorithm | null>(null);
  const [showParameters, setShowParameters] = useState(false);
  const [algorithmParams, setAlgorithmParams] = useState<Record<string, any>>({});
  
  // Classroom count selection state
  const [selectedClassroomCount, setSelectedClassroomCount] = useState<number>(7);
  
  // Optimize classroom count state
  const [optimizeClassroomCount, setOptimizeClassroomCount] = useState<boolean>(false);
  const [optimizing, setOptimizing] = useState<boolean>(false);
  
  // Slot insufficiency dialog state
  const [showSlotDialog, setShowSlotDialog] = useState(false);
  const [slotDialogData, setSlotDialogData] = useState({
    classroomCount: 7,
    projectCount: 0,
    availableSlots: 0,
    requiredSlots: 0,
  });
  
  // Save classroom count to localStorage when changed
  useEffect(() => {
    try {
      localStorage.setItem('selected_classroom_count', selectedClassroomCount.toString());
    } catch {}
  }, [selectedClassroomCount]);

  // Check slot sufficiency when classroom count changes
  useEffect(() => {
    if (selectedClassroomCount) {
      checkSlotSufficiency();
    }
  }, [selectedClassroomCount]);
  
  // Real-time progress tracking
  const {
    isConnected,
    connectionStatus,
    currentProgress,
    isRunning,
    progress,
    status,
    message,
    lastResult,
    lastError,
    connect,
    subscribeToAlgorithm,
  } = useAlgorithmProgress({ autoConnect: true });
  
  const navigate = useNavigate();

  // Slot insufficiency check function
  const checkSlotSufficiency = async () => {
    try {
      // Get project count from API
      const projectsResponse = await api.get('/projects/');
      const projects = projectsResponse.data;
      const projectCount = projects.length;
      
      // Calculate available slots (16 timeslots * classroom count)
      const availableSlots = 16 * selectedClassroomCount;
      const requiredSlots = projectCount;
      
      // Check if there's a shortage
      if (requiredSlots > availableSlots) {
        setSlotDialogData({
          classroomCount: selectedClassroomCount,
          projectCount,
          availableSlots,
          requiredSlots,
        });
        setShowSlotDialog(true);
        return false; // Insufficient slots
      }
      
      return true; // Sufficient slots
    } catch (error) {
      console.error('Error checking slot sufficiency:', error);
      return true; // Continue on error
    }
  };

  useEffect(() => {
    setLoading(true);
    api.get('/algorithms/list')
      .then((res) => {
        const items = Array.isArray(res.data)
          ? res.data.map((item: any) => algorithmService.getAlgorithmDisplayInfo(item))
          : [];
        setAlgorithms(items);
      })
      .catch((err) => {
        setError(err?.response?.data?.detail || 'Failed to fetch algorithms data');
      })
      .finally(() => setLoading(false));
  }, []);

  const getAlgorithmIcon = (category: string) => {
    switch (category) {
      case 'Bio-inspired':
        return <Psychology sx={{ fontSize: 40, color: 'primary.main' }} />;
      case 'Search-based':
        return <Speed sx={{ fontSize: 40, color: 'secondary.main' }} />;
      case 'Multi-objective':
        return <TrendingUp sx={{ fontSize: 40, color: 'success.main' }} />;
      case 'Mathematical':
        return <Analytics sx={{ fontSize: 40, color: 'warning.main' }} />;
      case 'Hybrid':
        return <Science sx={{ fontSize: 40, color: 'error.main' }} />;
      default:
        return <Science sx={{ fontSize: 40, color: 'info.main' }} />;
    }
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'Low': return 'success';
      case 'Medium': return 'warning';
      case 'High': return 'error';
      default: return 'info';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'Bio-inspired': return 'primary';
      case 'Search-based': return 'secondary';
      case 'Multi-objective': return 'success';
      case 'Mathematical': return 'warning';
      case 'Metaheuristic': return 'info';
      case 'Hybrid': return 'error';
      default: return 'default';
    }
  };

  // Poll algorithm status until completed/failed
  const pollUntilComplete = async (runId: number, timeoutMs = 60000, intervalMs = 1500) => {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      try {
        const res = await api.get(`/algorithms/results/${runId}`);
        const status = res.data?.status;
        if (status === 'completed') return { status: 'completed' };
        if (status === 'failed') return { status: 'failed' };
      } catch (e) {
        // ignore intermittent errors
      }
      await new Promise((r) => setTimeout(r, intervalMs));
    }
    return { status: 'timeout' } as const;
  };

  // Optimize classroom count function
  const handleOptimizeClassroomCount = async (algorithm: Algorithm) => {
    try {
      setOptimizing(true);
      setSnack({ open: true, message: 'Optimal sınıf sayısı hesaplanıyor...', severity: 'success' });
      
      const response = await api.post('/algorithms/optimize-classroom-count', {
        algorithm: algorithm.type || algorithm.name,
        params: algorithmParams
      });
      
      const result = response.data;
      const optimalCount = result.optimal_classroom_count;
      const optimalScore = result.optimal_score;
      
      // Set the optimal classroom count and update UI
      setSelectedClassroomCount(optimalCount);
      
      setSnack({ 
        open: true, 
        message: `Optimal sınıf sayısı: ${optimalCount} (Skor: ${optimalScore.toFixed(2)}) - Algoritma çalıştırılıyor...`, 
        severity: 'success' 
      });
      
      // Wait a bit for UI to update, then execute with optimal classroom count
      setTimeout(async () => {
        try {
          setExecuting(true);
          
          // Check slot sufficiency before executing
          const hasSufficientSlots = await checkSlotSufficiency();
          if (!hasSufficientSlots) {
            setExecuting(false);
            setOptimizing(false);
            return; // Stop execution if insufficient slots
          }
          
          // WebSocket bağlantısını kontrol et
          if (!isConnected) {
            setSnack({ open: true, message: 'WebSocket baglantisi yok, baglanmaya calisiliyor...', severity: 'error' });
            // Kullanıcı ID'sini al (auth context'ten)
            const userId = user?.id || 1; // Fallback to 1 if user not available
            await connect(userId);
          }
          
          // Execute with optimal classroom count
          const execRes = await api.post('/algorithms/execute', {
            algorithm: algorithm.type || algorithm.name,
            params: {
              classroom_count: optimalCount  // Use optimal classroom count
            },
            data: {
              projects: [],
              instructors: [],
              classrooms: [],
              timeslots: []
            }
          });
          const run = execRes.data;

          setSnack({ open: true, message: `${algorithm.displayName} optimal sınıf sayısı (${optimalCount}) ile başlatıldı...`, severity: 'success' });

          // Real-time progress tracking için algoritmaya abone ol
          subscribeToAlgorithm(run.id);

          // Poll status (fallback) - WebSocket ile birlikte çalışır
          const pollRes = await pollUntilComplete(run.id);
          if (pollRes.status !== 'completed') {
            const msg = pollRes.status === 'failed' ? 'Algoritma başarısız oldu' : 'Zaman aşımı: sonuç alınamadı';
            setSnack({ open: true, message: msg, severity: 'error' });
            return;
          }

          // Navigate to planner (force refresh) - schedules already persisted by backend
          try { localStorage.setItem('planner_refresh', '1'); } catch {}
          setSnack({ open: true, message: 'Optimal dağıtım tamamlandi, Planner\'a yonlendiriliyor...', severity: 'success' });
          navigate('/planner');
          
        } catch (err: any) {
          setSnack({ open: true, message: err?.response?.data?.detail || 'Algoritma calistirilamadi', severity: 'error' });
        } finally {
          setExecuting(false);
          setOptimizing(false);
        }
      }, 1500);
      
    } catch (err: any) {
      setSnack({ 
        open: true, 
        message: err?.response?.data?.detail || 'Sınıf sayısı optimizasyonu başarısız', 
        severity: 'error' 
      });
      setOptimizing(false);
    }
  };

  // Real-time progress tracking ile çalıştırma
  const handleExecuteDirect = async (algorithm: Algorithm) => {
    try {
      setExecuting(true);
      
      // Check slot sufficiency before executing
      const hasSufficientSlots = await checkSlotSufficiency();
      if (!hasSufficientSlots) {
        setExecuting(false);
        return; // Stop execution if insufficient slots
      }
      
      // WebSocket bağlantısını kontrol et
      if (!isConnected) {
        setSnack({ open: true, message: 'WebSocket baglantisi yok, baglanmaya calisiliyor...', severity: 'error' });
        // Kullanıcı ID'sini al (auth context'ten)
        const userId = user?.id || 1; // Fallback to 1 if user not available
        await connect(userId);
      }
      
      // 1) Execute
      const execRes = await api.post('/algorithms/execute', {
        algorithm: algorithm.type || algorithm.name,
        params: {
          classroom_count: selectedClassroomCount
        },
        data: {
          projects: [],
          instructors: [],
          classrooms: [],
          timeslots: []
        }
      });
      const run = execRes.data;

      setSnack({ open: true, message: `${algorithm.displayName} başlatıldı...`, severity: 'success' });

      // 2) Real-time progress tracking için algoritmaya abone ol
      subscribeToAlgorithm(run.id);

      // 3) Poll status (fallback) - WebSocket ile birlikte çalışır
      const pollRes = await pollUntilComplete(run.id);
      if (pollRes.status !== 'completed') {
        const msg = pollRes.status === 'failed' ? 'Algoritma başarısız oldu' : 'Zaman aşımı: sonuç alınamadı';
        setSnack({ open: true, message: msg, severity: 'error' });
        return;
      }

      // 4) Navigate to planner (force refresh) - schedules already persisted by backend
      try { localStorage.setItem('planner_refresh', '1'); } catch {}
      setSnack({ open: true, message: 'Dagitim tamamlandi, Planner\'a yonlendiriliyor...', severity: 'success' });
      navigate('/planner');
    } catch (err: any) {
      setSnack({ open: true, message: err?.response?.data?.detail || 'Algoritma calistirilamadi', severity: 'error' });
    } finally {
      setExecuting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'failed':
        return <Error sx={{ color: 'error.main' }} />;
      case 'running':
        return <CircularProgress size={20} />;
      default:
        return <Pending sx={{ color: 'warning.main' }} />;
    }
  };

  // Algorithm recommendation function
  const handleGetRecommendation = async () => {
    try {
      setRecommendationLoading(true);
      const response = await api.post('/algorithms/recommend', {
        problem_data: {
          projects: [], // Will be populated from current state
          instructors: [],
          classrooms: [],
          timeslots: [],
          is_makeup: false
        }
      });
      setRecommendation(response.data);
      setSnack({ 
        open: true, 
        message: `Önerilen algoritma: ${response.data.recommended_algorithm}`, 
        severity: 'success' 
      });
    } catch (err: any) {
      setSnack({ 
        open: true, 
        message: err?.response?.data?.detail || 'Algoritma önerisi alınamadı', 
        severity: 'error' 
      });
    } finally {
      setRecommendationLoading(false);
    }
  };

  // Algorithm parameter configuration
  const handleConfigureAlgorithm = (algorithm: Algorithm) => {
    setSelectedAlgorithm(algorithm);
    setAlgorithmParams({}); // Reset parameters
    setShowParameters(true);
  };

  const handleExecuteWithParams = async (algorithm: Algorithm, params: Record<string, any>) => {
    try {
      setExecuting(true);
      // Execute with custom parameters
      const execRes = await api.post('/algorithms/execute', {
        algorithm: algorithm.name,
        params: {
          ...params,
          classroom_count: selectedClassroomCount
        }
      });
      const run = execRes.data;

      setSnack({ open: true, message: `${algorithm.displayName} başlatıldı...`, severity: 'success' });

      // Poll status
      const pollRes = await pollUntilComplete(run.id);
      if (pollRes.status !== 'completed') {
        const msg = pollRes.status === 'failed' ? 'Algoritma başarısız oldu' : 'Zaman aşımı: sonuç alınamadı';
        setSnack({ open: true, message: msg, severity: 'error' });
        return;
      }

      // Schedules already persisted by backend; navigate to planner with refresh
      setSnack({ open: true, message: 'Dagitim tamamlandi, Planner\'a yonlendiriliyor...', severity: 'success' });
      navigate('/planner');
    } catch (err: any) {
      setSnack({ open: true, message: err?.response?.data?.detail || 'Algoritma calistirilamadi', severity: 'error' });
    } finally {
      setExecuting(false);
      setShowParameters(false);
    }
  };

  const getAlgorithmStats = () => {
    const total = algorithms.length;
    const bioInspired = algorithms.filter(a => a.category === 'Bio-inspired').length;
    const searchBased = algorithms.filter(a => a.category === 'Search-based').length;
    const mathematical = algorithms.filter(a => a.category === 'Mathematical').length;
    const multiObjective = algorithms.filter(a => a.category === 'Multi-objective').length;
    const metaheuristic = algorithms.filter(a => a.category === 'Metaheuristic').length;
    
    return { total, bioInspired, searchBased, mathematical, multiObjective, metaheuristic };
  };

  const stats = getAlgorithmStats();

  // Filter algorithms based on selected tab
  const getFilteredAlgorithms = () => {
    switch (tabValue) {
      case 0: return algorithms; // All
      case 1: return algorithms.filter(a => a.category === 'Metaheuristic');
      case 2: return algorithms.filter(a => a.category === 'Bio-inspired');
      case 3: return algorithms.filter(a => a.category === 'Search-based');
      case 4: return algorithms.filter(a => a.category === 'Mathematical');
      case 5: return algorithms.filter(a => a.category === 'Multi-objective');
      default: return algorithms;
    }
  };

  const filteredAlgorithms = getFilteredAlgorithms();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, mb: 4 }}>
          Algorithms
        </Typography>
        <Alert severity="error" action={
          <Button color="inherit" size="small" onClick={() => setLoading(true)}>
            Retry
          </Button>
        }>
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Algorithm Optimization Center
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          {/* Classroom Count Selection */}
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel sx={{ color: optimizeClassroomCount ? 'primary.main' : 'inherit' }}>
              {optimizeClassroomCount ? 'Optimal Sınıf Sayısı' : 'Sınıf Sayısı'}
            </InputLabel>
            <Select
              value={selectedClassroomCount}
              onChange={(e) => setSelectedClassroomCount(Number(e.target.value))}
              label={optimizeClassroomCount ? 'Optimal Sınıf Sayısı' : 'Sınıf Sayısı'}
              disabled={optimizeClassroomCount}
              sx={{
                backgroundColor: optimizeClassroomCount ? 'primary.light' : 'inherit',
                '& .MuiSelect-select': {
                  color: optimizeClassroomCount ? 'primary.contrastText' : 'inherit'
                }
              }}
            >
              <MenuItem value={5}>5 Sınıf</MenuItem>
              <MenuItem value={6}>6 Sınıf</MenuItem>
              <MenuItem value={7}>7 Sınıf</MenuItem>
            </Select>
          </FormControl>
          
          {/* Optimize Classroom Count Checkbox */}
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <input
                type="checkbox"
                id="optimize-classroom-count"
                checked={optimizeClassroomCount}
                onChange={(e) => setOptimizeClassroomCount(e.target.checked)}
                style={{ margin: 0 }}
              />
              <label htmlFor="optimize-classroom-count" style={{ fontSize: '0.875rem', color: 'rgba(0, 0, 0, 0.6)' }}>
                Optimize Sınıf Sayısı
              </label>
            </Box>
            {optimizeClassroomCount && (
              <Typography variant="caption" color="primary" sx={{ fontSize: '0.75rem', mt: 0.5, display: 'block' }}>
                Sınıf sayısı otomatik olarak optimize edilecek
              </Typography>
            )}
          </FormControl>
          
          {/* Real-time progress indicator */}
          {isRunning && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircularProgress size={20} />
              <Typography variant="body2" color="text.secondary">
                {progress.toFixed(1)}% - {message}
              </Typography>
            </Box>
          )}
          
          {/* WebSocket connection status */}
          <Chip
            label={connectionStatus}
            color={connectionStatus === 'connected' ? 'success' : connectionStatus === 'connecting' ? 'warning' : 'error'}
            size="small"
            variant="outlined"
          />
          
          <Button
            variant="contained"
            startIcon={<Recommend />}
            sx={{ borderRadius: 2 }}
            onClick={handleGetRecommendation}
            disabled={recommendationLoading}
          >
            {recommendationLoading ? 'Getting Recommendation...' : 'Get Recommendation'}
          </Button>
        </Box>
      </Box>

      {/* Algorithm Categories Tabs */}
      <Paper sx={{ mb: 4 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
            <Tab label={`All (${stats.total})`} />
            <Tab label={`Metasezgisel (${stats.metaheuristic})`} />
            <Tab label={`Bio-inspired (${stats.bioInspired})`} />
            <Tab label={`Search-based (${stats.searchBased})`} />
            <Tab label={`Mathematical (${stats.mathematical})`} />
            <Tab label={`Multi-objective (${stats.multiObjective})`} />
          </Tabs>
        </Box>
      </Paper>

      {/* Algorithm Grid */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(3, 1fr)' }, gap: 3, mb: 4 }}>
        {(filteredAlgorithms || []).map((algorithm) => (
          <Card
            key={algorithm.name}
            sx={{
              height: '100%',
              transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 4,
              },
              cursor: (executing || optimizing) ? 'not-allowed' : 'pointer',
              opacity: (executing || optimizing) ? 0.6 : 1,
            }}
            onClick={() => {
              if (!executing && !optimizing) {
                if (optimizeClassroomCount) {
                  handleOptimizeClassroomCount(algorithm);
                } else {
                  handleExecuteDirect(algorithm);
                }
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                {getAlgorithmIcon(algorithm.category)}
                <Box sx={{ ml: 2, flexGrow: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                    {algorithm.displayName}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                    <Chip
                      label={algorithm.category}
                      color={getCategoryColor(algorithm.category) as any}
                      size="small"
                      variant="outlined"
                    />
                    <Chip
                      label={algorithm.complexity}
                      color={getComplexityColor(algorithm.complexity) as any}
                      size="small"
                    />
                  </Box>
                </Box>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {algorithm.description}
              </Typography>
              {optimizeClassroomCount && (
                <Box sx={{ 
                  backgroundColor: 'primary.light', 
                  color: 'primary.contrastText', 
                  p: 1, 
                  borderRadius: 1, 
                  mb: 2,
                  fontSize: '0.75rem'
                }}>
                  🎯 Bu algoritma için optimal sınıf sayısı otomatik bulunacak
                </Box>
              )}
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                  Recommended for:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                  {Array.isArray(algorithm.recommendedFor) && algorithm.recommendedFor.map((item: any, index: number) => (
                    <Chip
                      key={index}
                      label={typeof item === 'string' ? item : String(item)}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                  ))}
                </Box>
              </Box>
              <Box sx={{ display: 'flex', gap: 1, mt: 'auto' }}>
                <Button
                  variant="contained"
                  size="small"
                  sx={{ flexGrow: 1 }}
                  disabled={executing || optimizing}
                  onClick={(e) => { 
                    e.stopPropagation(); 
                    if (!executing && !optimizing) {
                      if (optimizeClassroomCount) {
                        handleOptimizeClassroomCount(algorithm);
                      } else {
                        handleExecuteDirect(algorithm);
                      }
                    }
                  }}>
{optimizing ? 'Optimizing...' : executing ? 'Running...' : optimizeClassroomCount ? 'Find Optimal & Run' : 'Run'}
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  disabled={executing || optimizing}
                  onClick={(e) => { e.stopPropagation(); !executing && !optimizing && handleConfigureAlgorithm(algorithm); }}>
                  Configure
                </Button>
              </Box>
            </CardContent>
          </Card>
        ))}
      </Box>

      {/* Recent Algorithm Runs */}
      {algorithmRuns.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            Recent Algorithm Runs
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Algorithm</TableCell>
                  <TableCell align="center">Status</TableCell>
                  <TableCell align="center">Success Rate</TableCell>
                  <TableCell align="center">Execution Time</TableCell>
                  <TableCell align="center">Started</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {algorithmRuns.slice(0, 5).map((run) => (
                  <TableRow key={run.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {getStatusIcon(run.status)}
                        <Typography variant="body2" sx={{ ml: 1, fontWeight: 500 }}>
                          {algorithmService.getAlgorithmDisplayInfo(run.algorithm).displayName}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={run.status}
                        color={run.status === 'completed' ? 'success' : run.status === 'failed' ? 'error' : 'warning'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="center">
                      {run.success_rate ? `${(run.success_rate * 100).toFixed(1)}%` : '-'}
                    </TableCell>
                    <TableCell align="center">
                      {run.execution_time ? `${run.execution_time.toFixed(2)}s` : '-'}
                    </TableCell>
                    <TableCell align="center">
                      {new Date(run.created_at).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Algorithm Recommendation Dialog */}
      {recommendation && (
        <Dialog open={true} onClose={() => setRecommendation(null)} maxWidth="md" fullWidth>
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Recommend color="primary" />
              <Typography variant="h6">Algorithm Recommendation</Typography>
            </Box>
          </DialogTitle>
          <DialogContent>
            <Box sx={{ mb: 3 }}>
              <Typography variant="h5" sx={{ mb: 2, color: 'primary.main' }}>
                Recommended: {recommendation.recommended_algorithm}
              </Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>
                Confidence Score: {(recommendation.confidence_score * 100).toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                {recommendation.reasoning}
              </Typography>
            </Box>

            <Accordion>
              <AccordionSummary expandIcon={<TrendingUp />}>
                <Typography variant="subtitle1">Problem Analysis</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                  <Box sx={{ flex: '1 1 45%' }}>
                    <Typography variant="body2"><strong>Dataset Size:</strong> {recommendation.problem_analysis?.dataset_size}</Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 45%' }}>
                    <Typography variant="body2"><strong>Complexity:</strong> {(recommendation.problem_analysis?.complexity_score * 100).toFixed(1)}%</Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 45%' }}>
                    <Typography variant="body2"><strong>Project Count:</strong> {recommendation.problem_analysis?.project_count}</Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 45%' }}>
                    <Typography variant="body2"><strong>Instructor Count:</strong> {recommendation.problem_analysis?.instructor_count}</Typography>
                  </Box>
                </Box>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<Analytics />}>
                <Typography variant="subtitle1">All Algorithm Scores</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {Object.entries(recommendation.all_scores || {}).map(([algo, score]: [string, any]) => (
                    <Box key={algo} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2">{algo}</Typography>
                      <Chip 
                        label={`${(score * 100).toFixed(1)}%`} 
                        color={algo === recommendation.recommended_algorithm ? 'primary' : 'default'}
                        size="small"
                      />
                    </Box>
                  ))}
                </Box>
              </AccordionDetails>
            </Accordion>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setRecommendation(null)}>Close</Button>
            <Button 
              variant="contained" 
              onClick={() => {
                const recommendedAlgo = algorithms.find(a => a.name === recommendation.recommended_algorithm);
                if (recommendedAlgo) {
                  handleExecuteDirect(recommendedAlgo);
                  setRecommendation(null);
                }
              }}
            >
              Run Recommended Algorithm
            </Button>
          </DialogActions>
        </Dialog>
      )}

      {/* Algorithm Parameters Dialog */}
      <Dialog open={showParameters} onClose={() => setShowParameters(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Typography variant="h6">Configure {selectedAlgorithm?.displayName}</Typography>
        </DialogTitle>
        <DialogContent>
          {selectedAlgorithm && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                {selectedAlgorithm.description}
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {/* Common Parameters */}
                <Box>
                  <Typography variant="subtitle1" sx={{ mb: 2 }}>Common Parameters</Typography>
                </Box>
                
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <TextField
                    fullWidth
                    label="Max Iterations"
                    type="number"
                    value={algorithmParams.max_iterations || 1000}
                    onChange={(e) => setAlgorithmParams(prev => ({ ...prev, max_iterations: parseInt(e.target.value) }))}
                  />
                  
                  <TextField
                    fullWidth
                    label="Time Limit (seconds)"
                    type="number"
                    value={algorithmParams.time_limit || 60}
                    onChange={(e) => setAlgorithmParams(prev => ({ ...prev, time_limit: parseInt(e.target.value) }))}
                  />
                </Box>

                {/* Algorithm-specific parameters */}
                {selectedAlgorithm.name.includes('genetic') && (
                  <>
                    <Box>
                      <Typography variant="subtitle1" sx={{ mb: 2 }}>Genetic Algorithm Parameters</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <TextField
                        fullWidth
                        label="Population Size"
                        type="number"
                        value={algorithmParams.population_size || 50}
                        onChange={(e) => setAlgorithmParams(prev => ({ ...prev, population_size: parseInt(e.target.value) }))}
                      />
                      <TextField
                        fullWidth
                        label="Mutation Rate"
                        type="number"
                        value={algorithmParams.mutation_rate || 0.1}
                        onChange={(e) => setAlgorithmParams(prev => ({ ...prev, mutation_rate: parseFloat(e.target.value) }))}
                      />
                    </Box>
                  </>
                )}

                {selectedAlgorithm.name.includes('simulated_annealing') && (
                  <>
                    <Box>
                      <Typography variant="subtitle1" sx={{ mb: 2 }}>Simulated Annealing Parameters</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <TextField
                        fullWidth
                        label="Initial Temperature"
                        type="number"
                        value={algorithmParams.initial_temperature || 100}
                        onChange={(e) => setAlgorithmParams(prev => ({ ...prev, initial_temperature: parseFloat(e.target.value) }))}
                      />
                      <TextField
                        fullWidth
                        label="Cooling Rate"
                        type="number"
                        value={algorithmParams.cooling_rate || 0.95}
                        onChange={(e) => setAlgorithmParams(prev => ({ ...prev, cooling_rate: parseFloat(e.target.value) }))}
                      />
                    </Box>
                  </>
                )}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowParameters(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={() => selectedAlgorithm && handleExecuteWithParams(selectedAlgorithm, algorithmParams)}
            disabled={executing}
          >
            {executing ? 'Running...' : 'Run with Parameters'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar 
        open={snack.open} 
        autoHideDuration={3000} 
        onClose={() => setSnack(prev => ({ ...prev, open: false }))}
      >
        <Alert 
          severity={snack.severity} 
          sx={{ width: '100%' }}
          onClose={() => setSnack(prev => ({ ...prev, open: false }))}
        >
          {snack.message}
        </Alert>
      </Snackbar>

      {/* Slot Insufficiency Dialog */}
      <SlotInsufficiencyDialog
        open={showSlotDialog}
        onClose={() => setShowSlotDialog(false)}
        onContinue={() => {
          setShowSlotDialog(false);
          // Continue with algorithm execution
          if (selectedAlgorithm) {
            handleExecuteDirect(selectedAlgorithm);
          }
        }}
        classroomCount={slotDialogData.classroomCount}
        projectCount={slotDialogData.projectCount}
        availableSlots={slotDialogData.availableSlots}
        requiredSlots={slotDialogData.requiredSlots}
      />
    </Box>
  );
};

export default Algorithms;
