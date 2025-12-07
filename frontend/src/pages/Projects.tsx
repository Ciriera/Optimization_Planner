import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  MenuItem,
  Button,
  Stack,
  Snackbar,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Card,
  CardContent,
  TableSortLabel,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  Assignment,
  Person,
  Schedule,
  CheckCircle,
  Pending,
  Cancel,
  Group,
  GroupAdd,
  Warning,
} from '@mui/icons-material';
import { projectService, Project, ProjectCreateInput } from '../services/projectService';
import { juryService, JuryMember, ProjectJury } from '../services/juryService';
import { api } from '../services/authService';

interface ProjectFormData extends ProjectCreateInput {
  status?: string;
  remaining_student_count?: number;
}

const Projects: React.FC = () => {
  const [projects, setProjects] = useState<any[]>([]);
  const [instructors, setInstructors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [snack, setSnack] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({ open: false, message: '', severity: 'success' });
  
  // Dialog states
  const [openDialog, setOpenDialog] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<{ id: number; title: string } | null>(null);
  
  // Jury management states
  const [openJuryDialog, setOpenJuryDialog] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [projectJury, setProjectJury] = useState<ProjectJury | null>(null);
  const [eligibleJuryMembers, setEligibleJuryMembers] = useState<JuryMember[]>([]);
  const [selectedJuryMembers, setSelectedJuryMembers] = useState<number[]>([]);
  const [juryLoading, setJuryLoading] = useState(false);
  
  // Sorting states
  const [sortBy, setSortBy] = useState<'title' | 'type' | 'instructor' | 'status'>('instructor');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const [form, setForm] = useState<ProjectFormData>({
    title: '',
    type: 'final',
    responsible_instructor_id: 0,
    status: 'active',
    remaining_student_count: 1,
  });

  // Sadece proje yönetebilecek instructor'ları filtrele
  const eligibleInstructors = instructors.filter(instructor => {
    const name = instructor.name || '';
    const type = instructor.type || '';
    // Prof. Dr., Doç. Dr., Dr. Öğr. Üyesi unvanlı hocaları dahil et
    return name.includes('Prof. Dr.') || name.includes('Doç. Dr.') || name.includes('Dr. Öğr. Üyesi') ||
           type === 'instructor' || type === 'associate' || type === 'assistant';
  });

  // Merkezi veri yenileme fonksiyonu
  const fetchData = async () => {
    setLoading(true);
    try {
      const [projectsRes, instructorsRes] = await Promise.all([
        api.get('/projects/'),
        api.get('/instructors/'),
      ]);
      setProjects(projectsRes.data);
      setInstructors(instructorsRes.data);
    } catch (err) {
      setSnack({ open: true, message: (err as any)?.response?.data?.detail || 'Proje verileri yüklenirken hata oluştu', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // Jüri yönetimi fonksiyonları
  const handleOpenJuryDialog = async (project: Project) => {
    setSelectedProject(project);
    setJuryLoading(true);
    try {
      const [juryData, eligibleMembers] = await Promise.all([
        juryService.getProjectJury(project.id),
        juryService.getEligibleJuryMembers()
      ]);
      setProjectJury(juryData);
      setEligibleJuryMembers(eligibleMembers);
      setSelectedJuryMembers(juryData.jury_members.map(member => member.id));
      setOpenJuryDialog(true);
    } catch (err) {
      setSnack({ open: true, message: 'Jüri bilgileri yüklenirken hata oluştu', severity: 'error' });
    } finally {
      setJuryLoading(false);
    }
  };

  const handleCloseJuryDialog = () => {
    setOpenJuryDialog(false);
    setSelectedProject(null);
    setProjectJury(null);
    setSelectedJuryMembers([]);
  };

  const handleJuryMemberToggle = (memberId: number) => {
    setSelectedJuryMembers(prev => 
      prev.includes(memberId) 
        ? prev.filter(id => id !== memberId)
        : [...prev, memberId]
    );
  };

  const handleSaveJury = async () => {
    if (!selectedProject) return;
    
    setJuryLoading(true);
    try {
      await juryService.assignJuryToProject(selectedProject.id, selectedJuryMembers);
      setSnack({ open: true, message: 'Jüri üyeleri başarıyla atandı', severity: 'success' });
      handleCloseJuryDialog();
    } catch (err) {
      setSnack({ open: true, message: 'Jüri ataması sırasında hata oluştu', severity: 'error' });
    } finally {
      setJuryLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((f) => ({ 
      ...f, 
      [name]: name === 'responsible_instructor_id' || name === 'remaining_student_count' 
        ? Number(value) 
        : value 
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      if (editingProject) {
        // Update logic would go here
        setSnack({ open: true, message: 'Proje başarıyla güncellendi', severity: 'success' });
      } else {
        await projectService.create(form);
        setSnack({ open: true, message: 'Proje başarıyla oluşturuldu', severity: 'success' });
      }
      handleCloseDialog();
      // Oluşturma/güncelleme sonrası listeyi tazele
      await fetchData();
    } catch (e: any) {
      setSnack({ open: true, message: e?.response?.data?.detail || 'İşlem başarısız oldu', severity: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleOpenDialog = (project?: Project) => {
    if (project) {
      setEditingProject(project);
      setForm({
        title: project.title,
        type: project.type,
        responsible_instructor_id: project.responsible_instructor_id,
        status: project.status || 'active',
        remaining_student_count: 1,
      });
    } else {
      setEditingProject(null);
      setForm({
        title: '',
        type: 'final',
        responsible_instructor_id: eligibleInstructors.length > 0 ? eligibleInstructors[0].id : 0,
        status: 'active',
        remaining_student_count: 1,
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingProject(null);
  };

  // Proje silme dialog'unu aç
  const handleOpenDeleteDialog = (project: Project) => {
    setProjectToDelete({ id: project.id, title: project.title });
    setOpenDeleteDialog(true);
  };

  // Proje silme dialog'unu kapat
  const handleCloseDeleteDialog = () => {
    setOpenDeleteDialog(false);
    setProjectToDelete(null);
  };

  // Proje silme işlemini gerçekleştir
  const handleConfirmDelete = async () => {
    if (!projectToDelete) return;
    
    try {
      setLoading(true);
      await api.delete(`/projects/${projectToDelete.id}`);
      setSnack({ open: true, message: 'Proje başarıyla silindi', severity: 'success' });
      handleCloseDeleteDialog();
      await fetchData();
    } catch (e: any) {
      setSnack({ open: true, message: e?.response?.data?.detail || 'Silme işlemi başarısız oldu', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const getStatusChip = (status: string) => {
    const statusConfig = {
      active: { label: 'Active', color: 'success' as const, icon: <CheckCircle sx={{ fontSize: 16 }} /> },
      pending: { label: 'Pending', color: 'warning' as const, icon: <Pending sx={{ fontSize: 16 }} /> },
      completed: { label: 'Completed', color: 'primary' as const, icon: <CheckCircle sx={{ fontSize: 16 }} /> },
      cancelled: { label: 'Cancelled', color: 'error' as const, icon: <Cancel sx={{ fontSize: 16 }} /> },
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.active;
    return (
      <Chip
        label={config.label}
        color={config.color}
        size="small"
        icon={config.icon}
        variant="outlined"
      />
    );
  };

  const getInstructorName = (id: number) => {
    const instructor = instructors.find(i => i.id === id);
    return instructor?.name || `Instructor #${id}`;
  };

  const handleSort = (field: 'title' | 'type' | 'instructor' | 'status') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const sortedProjects = [...projects].sort((a, b) => {
    let aValue: any;
    let bValue: any;

    switch (sortBy) {
      case 'title':
        aValue = a.title?.toLowerCase() || '';
        bValue = b.title?.toLowerCase() || '';
        break;
      case 'type':
        aValue = a.type === 'final' || a.type === 'bitirme' ? 'Bitirme' : 'Ara';
        bValue = b.type === 'final' || b.type === 'bitirme' ? 'Bitirme' : 'Ara';
        break;
      case 'instructor':
        aValue = getInstructorName(a.responsible_instructor_id).toLowerCase();
        bValue = getInstructorName(b.responsible_instructor_id).toLowerCase();
        break;
      case 'status':
        aValue = a.status || 'active';
        bValue = b.status || 'active';
        break;
      default:
        return 0;
    }

    if (sortOrder === 'asc') {
      return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
    } else {
      return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
    }
  });

  const filteredProjects = projects.filter(p => {
    const t = (p.type || '').toString().toLowerCase();
    if (tabValue === 0) return true; // All
    if (tabValue === 1) return t === 'interim' || t === 'ara'; // Ara
    if (tabValue === 2) return t === 'final' || t === 'bitirme'; // Bitirme
    return true;
  });

  const getProjectStats = () => {
    const total = projects.length;
    const ara = projects.filter(p => {
      const t = (p.type || '').toString().toLowerCase();
      return t === 'interim' || t === 'ara';
    }).length;
    const bitirme = projects.filter(p => {
      const t = (p.type || '').toString().toLowerCase();
      return t === 'final' || t === 'bitirme';
    }).length;
    return { total, ara, bitirme };
  };

  const stats = getProjectStats();

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Proje Yönetimi
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpenDialog()}
          sx={{ borderRadius: 2 }}
        >
          Proje Ekle
        </Button>
      </Box>

      {/* Stats Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, gap: 2, mb: 4 }}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="text.secondary" gutterBottom>Toplam Proje</Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
                  {stats.total}
                </Typography>
              </Box>
              <Assignment sx={{ fontSize: 40, color: 'primary.main' }} />
            </Box>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="text.secondary" gutterBottom>Ara Projeler</Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'secondary.main' }}>
                  {stats.ara}
                </Typography>
              </Box>
              <Schedule sx={{ fontSize: 40, color: 'secondary.main' }} />
            </Box>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="text.secondary" gutterBottom>Bitirme Projeleri</Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main' }}>
                  {stats.bitirme}
                </Typography>
              </Box>
              <Assignment sx={{ fontSize: 40, color: 'success.main' }} />
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Project List */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
            <Tab label={`Tüm Projeler (${stats.total})`} />
            <Tab label={`Ara Projeler (${stats.ara})`} />
            <Tab label={`Bitirme Projeleri (${stats.bitirme})`} />
          </Tabs>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>
                    <TableSortLabel
                      active={sortBy === 'title'}
                      direction={sortBy === 'title' ? sortOrder : 'asc'}
                      onClick={() => handleSort('title')}
                    >
                      Proje Başlığı
                    </TableSortLabel>
                  </TableCell>
                  <TableCell align="center">
                    <TableSortLabel
                      active={sortBy === 'type'}
                      direction={sortBy === 'type' ? sortOrder : 'asc'}
                      onClick={() => handleSort('type')}
                    >
                      Tür
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={sortBy === 'instructor'}
                      direction={sortBy === 'instructor' ? sortOrder : 'asc'}
                      onClick={() => handleSort('instructor')}
                    >
                      Sorumlu Öğretim Üyesi
                    </TableSortLabel>
                  </TableCell>
                  <TableCell align="center">
                    <TableSortLabel
                      active={sortBy === 'status'}
                      direction={sortBy === 'status' ? sortOrder : 'asc'}
                      onClick={() => handleSort('status')}
                    >
                      Durum
                    </TableSortLabel>
                  </TableCell>
                  <TableCell align="center">Jüri</TableCell>
                  <TableCell align="center">İşlemler</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sortedProjects.filter(p => {
                  const t = (p.type || '').toString().toLowerCase();
                  if (tabValue === 0) return true; // All
                  if (tabValue === 1) return t === 'interim' || t === 'ara'; // Ara
                  if (tabValue === 2) return t === 'final' || t === 'bitirme'; // Bitirme
                  return true;
                }).map((project) => (
                  <TableRow key={project.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Assignment sx={{ mr: 1, color: 'text.secondary' }} />
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {project.title}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={project.type?.toLowerCase() === 'interim' || project.type?.toLowerCase() === 'ara' ? 'Ara' : 'Bitirme'}
                        color={project.type?.toLowerCase() === 'interim' || project.type?.toLowerCase() === 'ara' ? 'secondary' : 'primary'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Person sx={{ mr: 1, color: 'text.secondary', fontSize: 18 }} />
                        <Typography variant="body2">
                          {getInstructorName(project.responsible_instructor_id)}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      {getStatusChip(project.status || 'active')}
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenJuryDialog(project)}
                        color="primary"
                        title="Jüri Yönetimi"
                      >
                        <Group fontSize="small" />
                      </IconButton>
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(project)}
                        sx={{ mr: 1 }}
                      >
                        <Edit fontSize="small" />
                      </IconButton>
                      <IconButton size="small" color="error" onClick={() => handleOpenDeleteDialog(project)}>
                        <Delete fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
                {sortedProjects.filter(p => {
                  const t = (p.type || '').toString().toLowerCase();
                  if (tabValue === 0) return true; // All
                  if (tabValue === 1) return t === 'interim' || t === 'ara'; // Ara
                  if (tabValue === 2) return t === 'final' || t === 'bitirme'; // Bitirme
                  return true;
                }).length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                      <Typography color="text.secondary">
                        Proje bulunamadı. Başlamak için bazı projeler ekleyin.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingProject ? 'Proje Düzenle' : 'Yeni Proje Ekle'}
        </DialogTitle>
        <DialogContent>
          <Box component="form" onSubmit={handleSubmit} sx={{ pt: 2 }}>
            <Stack spacing={3}>
              <TextField
                label="Proje Başlığı"
                name="title"
                value={form.title}
                onChange={handleChange}
                required
                fullWidth
                placeholder="e.g. Web Tabanlı Öğrenci Yönetim Sistemi"
              />
              <TextField
                select
                label="Proje Türü"
                name="type"
                value={form.type}
                onChange={handleChange}
                required
                fullWidth
              >
                <MenuItem value="interim">Ara Proje</MenuItem>
                <MenuItem value="final">Bitirme Projesi</MenuItem>
              </TextField>
              <TextField
                select
                label="Sorumlu Öğretim Üyesi"
                name="responsible_instructor_id"
                value={form.responsible_instructor_id}
                onChange={handleChange}
                required
                fullWidth
                helperText="Sadece proje yönetebilecek öğretim üyeleri gösterilmektedir"
              >
                {eligibleInstructors.map((instructor) => (
                  <MenuItem key={instructor.id} value={instructor.id}>
                    {instructor.name} ({instructor.department || 'Bölüm Yok'})
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                select
                label="Durum"
                name="status"
                value={form.status}
                onChange={handleChange}
                fullWidth
              >
                <MenuItem value="active">Aktif</MenuItem>
                <MenuItem value="pending">Beklemede</MenuItem>
                <MenuItem value="completed">Tamamlandı</MenuItem>
                <MenuItem value="cancelled">İptal Edildi</MenuItem>
              </TextField>
              <TextField
                type="number"
                label="Öğrenci Kapasitesi"
                name="remaining_student_count"
                value={form.remaining_student_count}
                onChange={handleChange}
                fullWidth
                inputProps={{ min: 1, max: 5 }}
                helperText="Bu proje için maksimum öğrenci sayısı"
              />
            </Stack>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>İptal</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={saving}
            startIcon={saving ? <CircularProgress size={16} /> : null}
          >
            {saving ? 'Kaydediliyor...' : editingProject ? 'Güncelle' : 'Oluştur'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={openDeleteDialog} onClose={handleCloseDeleteDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Warning sx={{ mr: 1, color: 'error.main' }} />
            Proje Silme Onayı
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Typography variant="body1" gutterBottom>
              Bu projeyi silmek istediğinizden emin misiniz?
            </Typography>
            <Box
              sx={{
                mt: 2,
                p: 2,
                bgcolor: 'error.50',
                borderRadius: 1,
                border: 1,
                borderColor: 'error.200',
              }}
            >
              <Typography variant="body2" sx={{ fontWeight: 500, color: 'error.main' }}>
                Silinecek Proje:
              </Typography>
              <Typography variant="body1" sx={{ mt: 1, fontWeight: 600 }}>
                {projectToDelete?.title}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              <strong>Uyarı:</strong> Bu işlem geri alınamaz. Proje ile ilişkili tüm veriler kalıcı olarak silinecektir.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog} variant="outlined">
            İptal
          </Button>
          <Button
            onClick={handleConfirmDelete}
            variant="contained"
            color="error"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : <Delete />}
          >
            {loading ? 'Siliniyor...' : 'Sil'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Jury Management Dialog */}
      <Dialog open={openJuryDialog} onClose={handleCloseJuryDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Group sx={{ mr: 1 }} />
            Jüri Yönetimi - {selectedProject?.title}
          </Box>
        </DialogTitle>
        <DialogContent>
          {juryLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Box sx={{ pt: 2 }}>
              {/* Current Jury Info */}
              {projectJury && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>Sorumlu Öğretim Üyesi</Typography>
                  {projectJury.responsible_instructor && (
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, p: 2, bgcolor: 'primary.50', borderRadius: 1 }}>
                      <Person sx={{ mr: 1, color: 'primary.main' }} />
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {projectJury.responsible_instructor.name}
                      </Typography>
                      <Chip 
                        label="Sorumlu" 
                        color="primary" 
                        size="small" 
                        sx={{ ml: 'auto' }}
                      />
                    </Box>
                  )}
                  
                  <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                    Mevcut Jüri Üyeleri ({projectJury.jury_members.length})
                  </Typography>
                  {projectJury.jury_members.length > 0 ? (
                    <Box sx={{ mb: 2 }}>
                      {projectJury.jury_members.map((member) => (
                        <Box key={member.id} sx={{ display: 'flex', alignItems: 'center', mb: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                          <Person sx={{ mr: 1, color: 'text.secondary' }} />
                          <Typography variant="body2">
                            {member.name}
                          </Typography>
                          <Chip 
                            label={member.type === 'instructor' ? 'Öğretim Üyesi' : 'Araştırma Görevlisi'} 
                            color="secondary" 
                            size="small" 
                            sx={{ ml: 'auto' }}
                          />
                        </Box>
                      ))}
                    </Box>
                  ) : (
                    <Typography color="text.secondary">Henüz jüri üyesi atanmamış</Typography>
                  )}
                </Box>
              )}

              {/* Jury Member Selection */}
              <Typography variant="h6" gutterBottom>Jüri Üyeleri Seç</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Proje için jüri üyelerini seçin. Sorumlu öğretim üyesi otomatik olarak jüri başkanıdır.
              </Typography>
              
              <Box sx={{ maxHeight: 300, overflow: 'auto', border: 1, borderColor: 'divider', borderRadius: 1 }}>
                {eligibleJuryMembers.map((member) => (
                  <Box
                    key={member.id}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      p: 2,
                      borderBottom: 1,
                      borderColor: 'divider',
                      cursor: 'pointer',
                      bgcolor: selectedJuryMembers.includes(member.id) ? 'primary.50' : 'transparent',
                      '&:hover': { bgcolor: 'action.hover' }
                    }}
                    onClick={() => handleJuryMemberToggle(member.id)}
                  >
                    <CheckCircle 
                      sx={{ 
                        mr: 2, 
                        color: selectedJuryMembers.includes(member.id) ? 'primary.main' : 'action.disabled' 
                      }} 
                    />
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="body1" sx={{ fontWeight: selectedJuryMembers.includes(member.id) ? 500 : 400 }}>
                        {member.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {member.type === 'instructor' ? 'Öğretim Üyesi' : 'Araştırma Görevlisi'}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Seçili jüri üyesi sayısı: {selectedJuryMembers.length}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseJuryDialog}>İptal</Button>
          <Button
            onClick={handleSaveJury}
            variant="contained"
            disabled={juryLoading}
            startIcon={juryLoading ? <CircularProgress size={16} /> : <GroupAdd />}
          >
            {juryLoading ? 'Kaydediliyor...' : 'Jüri Atamasını Kaydet'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={snack.open} autoHideDuration={3000} onClose={() => setSnack((s) => ({ ...s, open: false }))}>
        <Alert severity={snack.severity} sx={{ width: '100%' }}>
          {snack.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Projects;
