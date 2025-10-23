import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Alert,
  AlertTitle,
  Stack,
  Chip,
  Divider,
} from '@mui/material';
import {
  Warning,
  School,
  Schedule,
  Assignment,
  Info,
} from '@mui/icons-material';

interface SlotInsufficiencyDialogProps {
  open: boolean;
  onClose: () => void;
  onContinue: () => void;
  classroomCount: number;
  projectCount: number;
  availableSlots: number;
  requiredSlots: number;
}

const SlotInsufficiencyDialog: React.FC<SlotInsufficiencyDialogProps> = ({
  open,
  onClose,
  onContinue,
  classroomCount,
  projectCount,
  availableSlots,
  requiredSlots,
}) => {
  const shortage = requiredSlots - availableSlots;
  const coveragePercentage = Math.round((availableSlots / requiredSlots) * 100);

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
        }
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              backgroundColor: 'warning.light',
              color: 'warning.contrastText',
            }}
          >
            <Warning sx={{ fontSize: 28 }} />
          </Box>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 600, color: 'text.primary' }}>
              Yetersiz Slot Uyarısı
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Seçilen sınıf sayısı ile tüm projeler atanamayacaktır
            </Typography>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ pt: 2 }}>
        <Alert severity="warning" sx={{ mb: 3, borderRadius: 2 }}>
          <AlertTitle sx={{ fontWeight: 600 }}>
            Slot Yetersizliği Tespit Edildi
          </AlertTitle>
          <Typography variant="body2">
            Mevcut sınıf sayısı ile tüm projelerin atanması mümkün değil. 
            Bazı projeler atanamayacak veya algoritma optimizasyonu gerekebilir.
          </Typography>
        </Alert>

        {/* Slot Hesaplama Detayları */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            Slot Hesaplama Detayları
          </Typography>
          
          <Stack spacing={2}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <School color="primary" />
                <Typography variant="body1">Sınıf Sayısı</Typography>
              </Box>
              <Chip 
                label={`${classroomCount} Sınıf`} 
                color="primary" 
                variant="outlined"
              />
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Schedule color="secondary" />
                <Typography variant="body1">Zaman Dilimi Sayısı</Typography>
              </Box>
              <Chip 
                label="16 Saat" 
                color="secondary" 
                variant="outlined"
              />
            </Box>

            <Divider />

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Assignment color="info" />
                <Typography variant="body1">Toplam Proje Sayısı</Typography>
              </Box>
              <Chip 
                label={`${projectCount} Proje`} 
                color="info" 
                variant="outlined"
              />
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Info color="success" />
                <Typography variant="body1">Mevcut Slot Sayısı</Typography>
              </Box>
              <Chip 
                label={`${availableSlots} Slot`} 
                color="success" 
                variant="outlined"
              />
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Warning color="warning" />
                <Typography variant="body1">Gerekli Slot Sayısı</Typography>
              </Box>
              <Chip 
                label={`${requiredSlots} Slot`} 
                color="warning" 
                variant="outlined"
              />
            </Box>
          </Stack>
        </Box>

        {/* Sonuç Özeti */}
        <Box sx={{ 
          p: 2, 
          backgroundColor: 'grey.50', 
          borderRadius: 2,
          border: '1px solid',
          borderColor: shortage > 0 ? 'warning.main' : 'success.main',
        }}>
          <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
            Sonuç Özeti
          </Typography>
          
          {shortage > 0 ? (
            <Box>
              <Typography variant="body1" color="warning.main" sx={{ mb: 1 }}>
                ⚠️ <strong>{shortage} proje</strong> atanamayacaktır
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sadece <strong>%{coveragePercentage}</strong> proje atanabilecektir
              </Typography>
            </Box>
          ) : (
            <Box>
              <Typography variant="body1" color="success.main" sx={{ mb: 1 }}>
                ✅ Tüm projeler atanabilecektir
              </Typography>
              <Typography variant="body2" color="text.secondary">
                <strong>%{coveragePercentage}</strong> kapasite kullanılacaktır
              </Typography>
            </Box>
          )}
        </Box>

        {/* Öneriler */}
        {shortage > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Öneriler
            </Typography>
            <Stack spacing={1}>
              <Typography variant="body2" color="text.secondary">
                • Sınıf sayısını artırarak daha fazla slot elde edebilirsiniz
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Proje sayısını azaltarak mevcut slotlara sığdırabilirsiniz
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Algoritma optimizasyonu ile daha verimli atama yapılabilir
              </Typography>
            </Stack>
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 3, pt: 1 }}>
        <Button 
          onClick={onClose} 
          variant="outlined"
          sx={{ borderRadius: 2 }}
        >
          İptal
        </Button>
        <Button 
          onClick={onContinue} 
          variant="contained"
          color={shortage > 0 ? "warning" : "primary"}
          sx={{ borderRadius: 2 }}
        >
          {shortage > 0 ? 'Yine de Devam Et' : 'Devam Et'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SlotInsufficiencyDialog;
