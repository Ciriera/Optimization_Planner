import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  Snackbar,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Avatar,
  Divider,
} from '@mui/material';
import {
  Person,
  Add,
  Edit,
  Delete,
  DeleteSweep,
} from '@mui/icons-material';
import { instructorService, Instructor, InstructorCreateInput } from '../services/instructorService';
import { api } from '../services/authService';

interface ExtendedInstructorForm extends InstructorCreateInput {
  email?: string;
  department?: string;
  max_bitirme_projects?: number;
  max_ara_projects?: number;
}

const Instructors: React.FC = () => {
  const [instructors, setInstructors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [snack, setSnack] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({ open: false, message: '', severity: 'success' });

  // Dialog states
  const [openDialog, setOpenDialog] = useState(false);
  const [editingInstructor, setEditingInstructor] = useState<Instructor | null>(null);

  // Delete confirmation dialog states
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [instructorToDelete, setInstructorToDelete] = useState<Instructor | null>(null);

  // Bulk delete dialog state
  const [openBulkDeleteDialog, setOpenBulkDeleteDialog] = useState(false);
  const [bulkDeleting, setBulkDeleting] = useState(false);

  const [form, setForm] = useState<ExtendedInstructorForm>({
    name: '',
    type: 'assistant',
    email: '',
    department: 'Computer Engineering',
    max_bitirme_projects: 3,
    max_ara_projects: 5,
  });

  // Veri yenileme fonksiyonu
  const fetchInstructors = async () => {
    setLoading(true);
    try {
      // Hem instructors hem de projects verilerini çek
      const [instructorsRes, projectsRes, schedulesRes] = await Promise.all([
        api.get('/instructors/'),
        api.get('/projects/'),
        api.get('/schedules/')
      ]);

      const instructors = instructorsRes.data || [];
      const projects = projectsRes.data || [];
      const schedules = schedulesRes.data || [];

      // Debug: API'den gelen verileri kontrol et
      console.log('Instructors fetched:', instructors.length);
      console.log('Projects fetched:', projects.length);
      console.log('Sample project types:', projects.slice(0, 3).map((p: any) => ({ id: p.id, type: p.type, title: p.title })));

      // Her instructor için gerçek iş yükünü hesapla
      const instructorsWithWorkload = instructors.map((instructor: any) => {
        // Sorumlu olduğu projeler
        const responsibleProjects = projects.filter((p: any) =>
          p.responsible_instructor_id === instructor.id
        );

        // Jüri üyesi olduğu projeler (assistant_instructors içinde)
        const juryProjects = projects.filter((p: any) =>
          p.assistant_instructors?.some((ai: any) => ai.id === instructor.id)
        );

        // Tüm projeler (sorumlu + jüri üyesi)
        const allProjects = [...responsibleProjects, ...juryProjects];

        // Bitirme ve ara proje sayılarını hesapla (tüm olası type değerlerini kontrol et)
        const bitirmeCount = allProjects.filter((p: any) => {
          const type = (p.type || '').toString().toLowerCase();
          return type === 'final' || type === 'bitirme';
        }).length;

        const araCount = allProjects.filter((p: any) => {
          const type = (p.type || '').toString().toLowerCase();
          return type === 'interim' || type === 'ara';
        }).length;

        // Debug: Her instructor için proje sayılarını logla
        if (responsibleProjects.length > 0 || juryProjects.length > 0) {
          console.log(`Instructor: ${instructor.name}`, {
            responsible: responsibleProjects.length,
            jury: juryProjects.length,
            bitirme: bitirmeCount,
            ara: araCount,
            total: allProjects.length
          });
        }

        return {
          ...instructor,
          bitirme_count: bitirmeCount,
          ara_count: araCount,
          total_jury_count: allProjects.length // Toplam jüri üyeliği sayısı
        };
      });

      setInstructors(instructorsWithWorkload);
    } catch (err: any) {
      console.error('Error fetching instructors:', err);
      // Hata durumunda demo veriler göster
      setInstructors([
        {
          id: 1,
          name: 'Prof. Dr. Ahmet Yılmaz',
          role: 'Prof. Dr.',
          bitirme_count: 0,
          ara_count: 0,
          department: 'Computer Engineering'
        },
        {
          id: 2,
          name: 'Doç. Dr. Fatma Demir',
          role: 'Doç. Dr.',
          bitirme_count: 0,
          ara_count: 0,
          department: 'Software Engineering'
        },
        {
          id: 3,
          name: 'Dr. Öğr. Üyesi Mehmet Kaya',
          role: 'Dr. Öğr. Üyesi',
          bitirme_count: 0,
          ara_count: 0,
          department: 'Computer Engineering'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInstructors();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((f) => ({
      ...f,
      [name]: name.includes('max_') ? Number(value) : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      if (editingInstructor) {
        // Update instructor using API
        await api.put(`/instructors/${editingInstructor.id}`, form);
        setSnack({ open: true, message: 'Öğretim üyesi başarıyla güncellendi', severity: 'success' });
      } else {
        await instructorService.create(form);
        setSnack({ open: true, message: 'Öğretim üyesi başarıyla oluşturuldu', severity: 'success' });
      }
      handleCloseDialog();
      // Yeni instructor eklendikten veya güncellendikten sonra verileri yenile
      await fetchInstructors();
    } catch (e: any) {
      setSnack({ open: true, message: e?.response?.data?.detail || 'İşlem başarısız oldu', severity: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleOpenDialog = (instructor?: Instructor) => {
    if (instructor) {
      setEditingInstructor(instructor);
      setForm({
        name: instructor.name,
        type: instructor.type || 'assistant',
        email: '',
        department: 'Computer Engineering',
        max_bitirme_projects: 3,
        max_ara_projects: 5,
      });
    } else {
      setEditingInstructor(null);
      setForm({
        name: '',
        type: 'assistant',
        email: '',
        department: 'Computer Engineering',
        max_bitirme_projects: 3,
        max_ara_projects: 5,
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingInstructor(null);
    // Form'u temizle
    setForm({
      name: '',
      type: 'assistant',
      email: '',
      department: 'Computer Engineering',
      max_bitirme_projects: 3,
      max_ara_projects: 5,
    });
  };

  // Instructor silme dialog'unu aç
  const handleOpenDeleteDialog = (instructor: Instructor) => {
    setInstructorToDelete(instructor);
    setOpenDeleteDialog(true);
  };

  // Delete dialog'unu kapat
  const handleCloseDeleteDialog = () => {
    setOpenDeleteDialog(false);
    setInstructorToDelete(null);
  };

  // Instructor silme fonksiyonu
  const handleConfirmDelete = async () => {
    if (!instructorToDelete) return;

    try {
      setLoading(true);
      console.log(`Deleting instructor with ID: ${instructorToDelete.id}`);

      const response = await api.delete(`/instructors/${instructorToDelete.id}`);
      console.log('Delete response:', response);

      // Backend'den gelen detaylı silme bilgilerini göster
      const deleteResult = response.data;
      let message = 'Öğretim üyesi başarıyla silindi';

      if (deleteResult) {
        const { deleted_projects_count, removed_jury_count, instructor_name } = deleteResult;

        if (deleted_projects_count > 0 || removed_jury_count > 0) {
          message = `${instructor_name} silindi. ${deleted_projects_count} proje silindi, ${removed_jury_count} jüri üyeliği kaldırıldı.`;
        } else {
          message = `${instructor_name} başarıyla silindi.`;
        }
      }

      setSnack({ open: true, message, severity: 'success' });
      handleCloseDeleteDialog();
      // Silme işleminden sonra verileri yenile
      await fetchInstructors();
    } catch (e: any) {
      console.error('Delete error:', e);
      console.error('Error response:', e?.response);
      console.error('Error data:', e?.response?.data);

      let errorMessage = 'Silme işlemi başarısız oldu';

      if (e?.response?.data?.detail) {
        errorMessage = e.response.data.detail;
      } else if (e?.response?.status === 403) {
        errorMessage = 'Bu işlem için admin yetkisi gerekli';
      } else if (e?.response?.status === 404) {
        errorMessage = 'Öğretim üyesi bulunamadı';
      } else if (e?.response?.status === 500) {
        errorMessage = 'Sunucu hatası oluştu';
      } else if (e?.message) {
        errorMessage = e.message;
      }

      setSnack({ open: true, message: errorMessage, severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // Bulk delete all instructors
  const handleBulkDelete = async () => {
    try {
      setBulkDeleting(true);
      const response = await api.delete('/instructors/bulk/delete-all');
      const result = response.data;

      setSnack({
        open: true,
        message: `${result.deleted_instructors_count} öğretim üyesi ve ${result.deleted_projects_count} proje silindi.`,
        severity: 'success'
      });
      setOpenBulkDeleteDialog(false);
      await fetchInstructors();
    } catch (e: any) {
      console.error('Bulk delete error:', e);
      setSnack({
        open: true,
        message: e?.response?.data?.detail || 'Toplu silme işlemi başarısız oldu',
        severity: 'error'
      });
    } finally {
      setBulkDeleting(false);
    }
  };


  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Öğretim Üyesi Yönetimi
        </Typography>
        <Stack direction="row" spacing={2}>
          {instructors.length > 0 && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteSweep />}
              onClick={() => setOpenBulkDeleteDialog(true)}
              sx={{ borderRadius: 2 }}
            >
              Tümünü Sil
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => handleOpenDialog()}
            sx={{ borderRadius: 2 }}
          >
            Öğretim Üyesi Ekle
          </Button>
        </Stack>
      </Box>

      {/* Stats Card */}
      <Box sx={{ mb: 4 }}>
        <Card sx={{
          background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
          color: 'white',
          boxShadow: '0 4px 20px rgba(25, 118, 210, 0.3)'
        }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography variant="h6" sx={{
                  fontWeight: 500,
                  opacity: 0.9,
                  mb: 1
                }}>
                  Toplam Öğretim Üyesi
                </Typography>
                <Typography variant="h2" sx={{
                  fontWeight: 700,
                  color: 'white',
                  lineHeight: 1
                }}>
                  {instructors.length}
                </Typography>
                <Typography variant="body2" sx={{
                  opacity: 0.8,
                  mt: 1
                }}>
                  Aktif öğretim üyesi sayısı
                </Typography>
              </Box>
              <Box sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 80,
                height: 80,
                borderRadius: '50%',
                backgroundColor: 'rgba(255, 255, 255, 0.15)',
                backdropFilter: 'blur(10px)'
              }}>
                <Person sx={{ fontSize: 40, color: 'white' }} />
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Instructor List */}
      <Paper sx={{ p: 3 }}>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Öğretim Üyesi</TableCell>
                  <TableCell align="center">Bitirme Projesi</TableCell>
                  <TableCell align="center">Ara Proje</TableCell>
                  <TableCell align="center">Toplam Jüri Üyeliği</TableCell>
                  <TableCell align="center">İşlemler</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {instructors.map((instructor) => {
                  return (
                    <TableRow key={instructor.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                            {instructor.name.split(' ').map((n: string) => n[0]).join('').slice(0, 2)}
                          </Avatar>
                          <Box>
                            <Typography variant="body1" sx={{ fontWeight: 500 }}>
                              {instructor.name}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="h6" sx={{ fontWeight: 600, color: 'primary.main' }}>
                          {instructor.bitirme_count || 0}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="h6" sx={{ fontWeight: 600, color: 'secondary.main' }}>
                          {instructor.ara_count || 0}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="h6" sx={{ fontWeight: 600, color: 'success.main' }}>
                          {instructor.total_jury_count || 0}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(instructor)}
                          sx={{ mr: 1 }}
                        >
                          <Edit fontSize="small" />
                        </IconButton>
                        <IconButton size="small" color="error" onClick={() => handleOpenDeleteDialog(instructor)}>
                          <Delete fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {instructors.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                      <Typography color="text.secondary">
                        Henüz öğretim üyesi eklenmemiş.
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
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingInstructor ? 'Öğretim Üyesi Düzenle' : 'Yeni Öğretim Üyesi Ekle'}
        </DialogTitle>
        <DialogContent>
          <Box component="form" onSubmit={handleSubmit} sx={{ pt: 2 }}>
            <Stack spacing={3}>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                <TextField
                  label="Ad Soyad"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  required
                  fullWidth
                  placeholder="e.g. Prof. Dr. Ahmet Yılmaz"
                />
                <TextField
                  label="E-posta"
                  name="email"
                  type="email"
                  value={form.email}
                  onChange={handleChange}
                  fullWidth
                  placeholder="ahmet.yilmaz@university.edu.tr"
                />
              </Stack>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                <TextField
                  select
                  label="Akademik Rol"
                  name="type"
                  value={form.type}
                  onChange={handleChange}
                  required
                  fullWidth
                  SelectProps={{ native: true }}
                >
                  <option value="prof">Prof. Dr. (Profesör)</option>
                  <option value="associate">Doç. Dr. (Doçent)</option>
                  <option value="assistant">Dr. Öğr. Üyesi (Doktor Öğretim Üyesi)</option>
                  <option value="Öğr. Gör.">Öğr. Gör. (Öğretim Görevlisi)</option>
                  <option value="Arş. Gör.">Arş. Gör. (Araştırma Görevlisi)</option>
                </TextField>
                <TextField
                  select
                  label="Bölüm"
                  name="department"
                  value={form.department}
                  onChange={handleChange}
                  fullWidth
                  SelectProps={{ native: true }}
                >
                  <option value="Computer Engineering">Bilgisayar Mühendisliği</option>
                  <option value="Software Engineering">Yazılım Mühendisliği</option>
                  <option value="Electrical Engineering">Elektrik Mühendisliği</option>
                  <option value="Industrial Engineering">Endüstri Mühendisliği</option>
                </TextField>
              </Stack>
              <Divider />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Proje Yükü Limitleri
              </Typography>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                <TextField
                  type="number"
                  label="Maksimum Bitirme Projeleri"
                  name="max_bitirme_projects"
                  value={form.max_bitirme_projects}
                  onChange={handleChange}
                  fullWidth
                  inputProps={{ min: 1, max: 10 }}
                  helperText="Maksimum tez projesi sayısı"
                />
                <TextField
                  type="number"
                  label="Maksimum Ara Projeleri"
                  name="max_ara_projects"
                  value={form.max_ara_projects}
                  onChange={handleChange}
                  fullWidth
                  inputProps={{ min: 1, max: 15 }}
                  helperText="Maksimum dönem projesi sayısı"
                />
              </Stack>
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
            {saving ? 'Kaydediliyor...' : editingInstructor ? 'Güncelle' : 'Oluştur'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={openDeleteDialog}
        onClose={handleCloseDeleteDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{
          display: 'flex',
          alignItems: 'center',
          color: 'error.main',
          fontWeight: 600
        }}>
          <Delete sx={{ mr: 1 }} />
          Öğretim Görevlisi Silme Onayı
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                Seçmiş Olduğunuz Öğretim Görevlisini Silmeniz Durumunda Öğretim Görevlisinin Sorumlu Olduğu Projeler de silinecektir!
              </Typography>
            </Alert>

            {instructorToDelete && (
              <Paper sx={{ p: 2, bgcolor: 'grey.50', border: 1, borderColor: 'divider' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Person sx={{ mr: 1, color: 'text.secondary' }} />
                  <Typography variant="h6" sx={{ fontWeight: 500 }}>
                    {instructorToDelete.name}
                  </Typography>
                </Box>
                <Divider sx={{ my: 1 }} />
                <Stack spacing={1}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">
                      Bitirme Projeleri:
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main' }}>
                      {instructorToDelete.bitirme_count || 0}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">
                      Ara Projeler:
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: 'secondary.main' }}>
                      {instructorToDelete.ara_count || 0}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">
                      Toplam Jüri Üyeliği:
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.main' }}>
                      {instructorToDelete.total_jury_count || 0}
                    </Typography>
                  </Box>
                </Stack>
              </Paper>
            )}

            <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
              Bu işlem geri alınamaz. Devam etmek istediğinizden emin misiniz?
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={handleCloseDeleteDialog}
            variant="outlined"
            sx={{ minWidth: 100 }}
          >
            İptal
          </Button>
          <Button
            onClick={handleConfirmDelete}
            variant="contained"
            color="error"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : <Delete />}
            sx={{ minWidth: 100 }}
          >
            {loading ? 'Siliniyor...' : 'Sil'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Bulk Delete Confirmation Dialog */}
      <Dialog
        open={openBulkDeleteDialog}
        onClose={() => setOpenBulkDeleteDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{
          display: 'flex',
          alignItems: 'center',
          color: 'error.main',
          fontWeight: 600
        }}>
          <DeleteSweep sx={{ mr: 1 }} />
          Tüm Öğretim Üyelerini Sil
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="body1" sx={{ fontWeight: 600 }}>
                DİKKAT: Bu işlem geri alınamaz!
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Tüm öğretim üyeleri, projeleri ve ilişkili veriler kalıcı olarak silinecektir.
              </Typography>
            </Alert>

            <Paper sx={{ p: 2, bgcolor: 'grey.50', border: 1, borderColor: 'divider' }}>
              <Stack spacing={1}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    Silinecek Öğretim Üyesi:
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: 'error.main' }}>
                    {instructors.length}
                  </Typography>
                </Box>
              </Stack>
            </Paper>

            <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
              Bu işlemi onaylıyor musunuz?
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => setOpenBulkDeleteDialog(false)}
            variant="outlined"
            sx={{ minWidth: 100 }}
          >
            İptal
          </Button>
          <Button
            onClick={handleBulkDelete}
            variant="contained"
            color="error"
            disabled={bulkDeleting}
            startIcon={bulkDeleting ? <CircularProgress size={16} /> : <DeleteSweep />}
            sx={{ minWidth: 150 }}
          >
            {bulkDeleting ? 'Siliniyor...' : 'Tümünü Sil'}
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

export default Instructors;
