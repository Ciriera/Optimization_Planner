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
  FormControlLabel,
  Checkbox,
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
    } catch { }
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
            // Kullanıcı ID'sini al (auth context'ten)
            const userId = user?.id || 1; // Fallback to 1 if user not available
            await connect(userId);
          }

          // Execute with optimal classroom count
          const execRes = await api.post('/algorithms/execute', {
            algorithm: algorithm.type || algorithm.name,
            params: {
              classroom_count: optimalCount,  // Use optimal classroom count
              jury_refinement_layer: true  // Force enable jury refinement
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

          // Execute response'unda zaten completed dönmüşse polling gerekmez
          let finalStatus = run.status;

          if (finalStatus !== 'completed' && finalStatus !== 'failed') {
            // Poll status (fallback) - WebSocket ile birlikte çalışır
            const pollRes = await pollUntilComplete(run.id);
            finalStatus = pollRes.status;
          }

          if (finalStatus !== 'completed') {
            const msg = finalStatus === 'failed' ? 'Algoritma başarısız oldu' : 'Zaman aşımı: sonuç alınamadı';
            setSnack({ open: true, message: msg, severity: 'error' });
            return;
          }

          // Navigate to planner (force refresh) - schedules already persisted by backend
          try { localStorage.setItem('planner_refresh', '1'); } catch { }
          setSnack({ open: true, message: 'Optimal dağıtım tamamlandi, Planner\'a yonlendiriliyor...', severity: 'success' });
          navigate('/planner');

        } catch (err: any) {
          const errorMsg = err?.response?.data?.detail || err?.response?.data?.message || err?.message || 'Algoritma çalıştırılamadı';
          console.error('Algorithm execution error:', err);
          setSnack({
            open: true,
            message: `Hata: ${errorMsg}`,
            severity: 'error'
          });
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
        // Kullanıcı ID'sini al (auth context'ten)
        const userId = user?.id || 1; // Fallback to 1 if user not available
        await connect(userId);
      }

      // 1) Execute
      let execRes;
      try {
        execRes = await api.post('/algorithms/execute', {
          algorithm: algorithm.type || algorithm.name,
          params: {
            classroom_count: selectedClassroomCount,
            jury_refinement_layer: true  // Force enable jury refinement
          },
          data: {
            projects: [],
            instructors: [],
            classrooms: [],
            timeslots: []
          }
        });
      } catch (err: any) {
        // Backend'den gelen detaylı hata mesajını al
        // FastAPI error format: {detail: "..."} veya middleware format: {error: {...}}
        const responseData = err?.response?.data || {};
        const backendDetail =
          responseData.detail ||           // FastAPI HTTPException format
          responseData.message ||          // Middleware error format
          (responseData.error && (typeof responseData.error === 'string'
            ? responseData.error
            : responseData.error.detail || responseData.error.message)) || // Nested error format
          err?.message ||
          'Algoritma çalıştırılırken bir hata oluştu';

        // Detaylı error logging
        console.error('=== Algorithm Execution Error ===');
        console.error('Error object:', err);
        console.error('Response:', err?.response);
        console.error('Response status:', err?.response?.status);
        console.error('Response data (full):', JSON.stringify(responseData, null, 2));
        console.error('Response data (error):', responseData.error);
        console.error('Response data (detail):', responseData.detail);
        console.error('Response data (message):', responseData.message);
        console.error('Extracted error message:', backendDetail);
        console.error('===============================');

        // Kullanıcıya gösterilecek mesaj
        let displayMessage = backendDetail;
        if (backendDetail.includes('Errno 22') || backendDetail.includes('Invalid argument')) {
          displayMessage = 'Dosya işlemi hatası: Rapor dosyaları yazılırken bir sorun oluştu. Backend log\'larını kontrol edin.';
        } else if (backendDetail.includes('Veri yükleme hatası') || backendDetail.includes('NoneType') || backendDetail.includes('AttributeError')) {
          displayMessage = 'Veri yükleme hatası: Veritabanında projeler, öğretmenler veya sınıflar eksik olabilir.';
        } else if (backendDetail.includes('Veri formatı hatası') || backendDetail.includes('KeyError')) {
          displayMessage = 'Veri formatı hatası: Gerekli veri alanları eksik.';
        } else if (backendDetail.includes('Veritabanı bağlantı hatası') || backendDetail.includes('database') || backendDetail.includes('connection')) {
          displayMessage = 'Veritabanı bağlantı hatası: Backend veritabanına bağlanamıyor.';
        } else if (backendDetail.includes('Algorithm execution failed')) {
          // Backend'den gelen detaylı mesajı göster
          displayMessage = backendDetail.replace('Algorithm execution failed: ', '');
        }

        setSnack({
          open: true,
          message: displayMessage || 'Algoritma çalıştırılırken bir hata oluştu. Lütfen console log\'larına bakın.',
          severity: 'error'
        });
        setExecuting(false);
        return;
      }
      const run = execRes.data;

      setSnack({ open: true, message: `${algorithm.displayName} başlatıldı...`, severity: 'success' });

      // 2) Real-time progress tracking için algoritmaya abone ol
      subscribeToAlgorithm(run.id);

      // 3) Execute response'unda zaten completed dönmüşse polling gerekmez
      // Bu, backend'in senkron çalıştığı durumlarda loop'u önler
      let finalStatus = run.status;

      if (finalStatus !== 'completed' && finalStatus !== 'failed') {
        // Poll status (fallback) - WebSocket ile birlikte çalışır
        const pollRes = await pollUntilComplete(run.id);
        finalStatus = pollRes.status;
      }

      if (finalStatus !== 'completed') {
        const msg = finalStatus === 'failed' ? 'Algoritma başarısız oldu' : 'Zaman aşımı: sonuç alınamadı';
        setSnack({ open: true, message: msg, severity: 'error' });
        return;
      }

      // 4) Navigate to planner (force refresh) - schedules already persisted by backend
      try { localStorage.setItem('planner_refresh', '1'); } catch { }
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
        algorithm: algorithm.type || algorithm.name,
        params: {
          ...params,
          classroom_count: selectedClassroomCount,
          jury_refinement_layer: true  // Force enable jury refinement
        }
      });
      const run = execRes.data;

      setSnack({ open: true, message: `${algorithm.displayName} başlatıldı...`, severity: 'success' });

      // Execute response'unda zaten completed dönmüşse polling gerekmez
      let finalStatus = run.status;

      if (finalStatus !== 'completed' && finalStatus !== 'failed') {
        // Poll status (fallback) - WebSocket ile birlikte çalışır
        const pollRes = await pollUntilComplete(run.id);
        finalStatus = pollRes.status;
      }

      if (finalStatus !== 'completed') {
        const msg = finalStatus === 'failed' ? 'Algoritma başarısız oldu' : 'Zaman aşımı: sonuç alınamadı';
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

  // Algorithms to exclude from the UI
  const excludedAlgorithms = ['SIMPLEX_ARA', 'simplex_ara', 'hungarian', 'bitirme_priority_scheduler'];

  // Filter out excluded algorithms
  const availableAlgorithms = algorithms.filter(a =>
    !excludedAlgorithms.includes(a.name) &&
    !excludedAlgorithms.includes(a.type || '')
  );

  const getAlgorithmStats = () => {
    const total = availableAlgorithms.length;
    const bioInspired = availableAlgorithms.filter(a => a.category === 'Bio-inspired').length;
    const searchBased = availableAlgorithms.filter(a => a.category === 'Search-based').length;
    const mathematical = availableAlgorithms.filter(a => a.category === 'Mathematical').length;
    const multiObjective = availableAlgorithms.filter(a => a.category === 'Multi-objective').length;
    const metaheuristic = availableAlgorithms.filter(a => a.category === 'Metaheuristic').length;

    return { total, bioInspired, searchBased, mathematical, multiObjective, metaheuristic };
  };

  const stats = getAlgorithmStats();

  // Development Journey algorithms (experimental/research)
  const developmentJourneyAlgorithms = ['bat_algorithm', 'dragonfly_algorithm', 'a_star_search', 'deep_search', 'nsga_ii_enhanced', 'greedy'];

  // Filter algorithms based on selected tab
  const getFilteredAlgorithms = () => {
    switch (tabValue) {
      case 0: return availableAlgorithms; // All
      case 1: return availableAlgorithms.filter(a => a.category === 'Metaheuristic');
      case 2: return availableAlgorithms.filter(a => a.category === 'Bio-inspired');
      case 3: return availableAlgorithms.filter(a => a.category === 'Search-based');
      case 4: return availableAlgorithms.filter(a => a.category === 'Mathematical');
      case 5: return availableAlgorithms.filter(a => a.category === 'Multi-objective');
      default: return availableAlgorithms;
    }
  };

  const filteredAlgorithms = getFilteredAlgorithms();

  // Separate algorithms into two groups
  const optimizedAlgorithms = filteredAlgorithms.filter(a =>
    !developmentJourneyAlgorithms.includes(a.name) &&
    !developmentJourneyAlgorithms.includes(a.type || '')
  );

  const devJourneyAlgorithms = filteredAlgorithms.filter(a =>
    developmentJourneyAlgorithms.includes(a.name) ||
    developmentJourneyAlgorithms.includes(a.type || '')
  );

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
              <MenuItem value={8}>8 Sınıf</MenuItem>
              <MenuItem value={9}>9 Sınıf</MenuItem>
              <MenuItem value={10}>10 Sınıf</MenuItem>
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

      {/* Optimized Algorithms Section */}
      {optimizedAlgorithms.length > 0 && (
        <>
          <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <CheckCircle sx={{ color: 'success.main' }} />
            Optimized Algorithms
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(3, 1fr)' }, gap: 3, mb: 4 }}>
            {optimizedAlgorithms.map((algorithm, index) => (
              <Card
                key={algorithm.type || algorithm.name || `optimized-${index}`}
                sx={{
                  height: '100%',
                  transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                  cursor: (executing || optimizing) ? 'not-allowed' : 'pointer',
                  opacity: (executing || optimizing) ? 0.6 : 1,
                  borderLeft: '4px solid',
                  borderLeftColor: 'success.main',
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
        </>
      )}

      {/* Development Journey Section */}
      {devJourneyAlgorithms.length > 0 && (
        <>
          <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, mt: 4, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Science sx={{ color: 'warning.main' }} />
            Development Journey
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Bu algoritmalar araştırma ve geliştirme sürecinde deneysel olarak test edilmiştir.
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(3, 1fr)' }, gap: 3, mb: 4 }}>
            {devJourneyAlgorithms.map((algorithm, index) => (
              <Card
                key={algorithm.type || algorithm.name || `dev-${index}`}
                sx={{
                  height: '100%',
                  transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                  cursor: (executing || optimizing) ? 'not-allowed' : 'pointer',
                  opacity: (executing || optimizing) ? 0.6 : 1,
                  borderLeft: '4px solid',
                  borderLeftColor: 'warning.main',
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
                      color="warning"
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
        </>
      )}

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

                {/* Priority Selection */}
                <FormControl fullWidth>
                  <InputLabel>Proje Önceliği</InputLabel>
                  <Select
                    value={algorithmParams.project_priority || 'none'}
                    onChange={(e) => setAlgorithmParams(prev => ({ ...prev, project_priority: e.target.value }))}
                    label="Proje Önceliği"
                  >
                    <MenuItem value="final_exam_priority">Bitirme Projesi Öncelikli</MenuItem>
                    <MenuItem value="midterm_priority">Ara Proje Öncelikli</MenuItem>
                    <MenuItem value="none">Önceliksiz</MenuItem>
                  </Select>
                </FormControl>



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
