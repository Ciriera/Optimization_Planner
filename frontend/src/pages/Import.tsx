import React, { useState, useCallback } from 'react';
import {
    Box,
    Typography,
    Paper,
    Card,
    CardContent,
    Button,
    Chip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Stack,
    Divider,
    Snackbar,
    Alert,
    CircularProgress,
    IconButton,
    Tooltip,
    LinearProgress,
    TextField,
} from '@mui/material';
import {
    CloudUpload,
    CheckCircle,
    Error as ErrorIcon,
    Warning,
    Download,
    PlayArrow,
    Cancel,
    Refresh,
    Info,
    Transform,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { importService, ImportRow, ValidateResponse, ExecuteResponse } from '../services/importService';
import * as XLSX from 'xlsx';

const Import: React.FC = () => {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [validatedData, setValidatedData] = useState<ValidateResponse | null>(null);
    const [importResult, setImportResult] = useState<ExecuteResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [validating, setValidating] = useState(false);
    const [importing, setImporting] = useState(false);
    const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
    const [snack, setSnack] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'warning' | 'info' }>({
        open: false,
        message: '',
        severity: 'success',
    });

    // Notification import (instructor emails)
    const [emailFile, setEmailFile] = useState<File | null>(null);
    const [emailValidation, setEmailValidation] = useState<any>(null);
    const [emailImportResult, setEmailImportResult] = useState<any>(null);
    const [emailValidating, setEmailValidating] = useState(false);
    const [emailImporting, setEmailImporting] = useState(false);

    // Format converter states
    const [converterFile, setConverterFile] = useState<File | null>(null);
    const [converting, setConverting] = useState(false);
    const [conversionPreview, setConversionPreview] = useState<any[]>([]);

    // Format converter function - Hoca/Ara/Bitirme format to InstructorName/ProjectType/ProjectDescription
    const handleConvertFormat = async () => {
        if (!converterFile) {
            showSnack('Lütfen önce bir Excel dosyası seçin', 'warning');
            return;
        }

        setConverting(true);
        try {
            const data = await converterFile.arrayBuffer();
            const workbook = XLSX.read(data, { type: 'array' });
            const sheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[sheetName];
            const jsonData = XLSX.utils.sheet_to_json(worksheet);

            // Convert each row to the new format
            const convertedRows: any[] = [];

            jsonData.forEach((row: any) => {
                // Get instructor name - check various possible column names
                const instructorName = row['Hoca'] || row['hoca'] || row['HOCA'] ||
                    row['İsim'] || row['isim'] || row['Name'] ||
                    row['Öğretim Üyesi'] || '';

                // Get Ara and Bitirme counts
                const araCount = parseInt(row['Ara'] || row['ara'] || row['ARA'] || '0') || 0;
                const bitirmeCount = parseInt(row['Bitirme'] || row['bitirme'] || row['BITIRME'] || '0') || 0;

                if (!instructorName) return;

                // Create Ara projects
                for (let i = 1; i <= araCount; i++) {
                    convertedRows.push({
                        InstructorName: instructorName,
                        ProjectType: 'Ara Proje',
                        ProjectDescription: `Ara Proje ${i} - ${instructorName}`
                    });
                }

                // Create Bitirme projects
                for (let i = 1; i <= bitirmeCount; i++) {
                    convertedRows.push({
                        InstructorName: instructorName,
                        ProjectType: 'Bitirme Projesi',
                        ProjectDescription: `Bitirme Projesi ${i} - ${instructorName}`
                    });
                }
            });

            setConversionPreview(convertedRows);

            if (convertedRows.length > 0) {
                showSnack(`${convertedRows.length} proje satırı oluşturuldu. İndirmek için butona tıklayın.`, 'success');
            } else {
                showSnack('Dönüştürülecek veri bulunamadı. Excel formatınızı kontrol edin.', 'warning');
            }
        } catch (error: any) {
            console.error('Conversion error:', error);
            showSnack('Excel dosyası dönüştürülürken hata oluştu: ' + error.message, 'error');
        } finally {
            setConverting(false);
        }
    };

    // Download converted file
    const handleDownloadConverted = () => {
        if (conversionPreview.length === 0) {
            showSnack('Önce dosyayı dönüştürün', 'warning');
            return;
        }

        const worksheet = XLSX.utils.json_to_sheet(conversionPreview);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Converted');

        // Set column widths
        worksheet['!cols'] = [
            { wch: 30 }, // InstructorName
            { wch: 15 }, // ProjectType
            { wch: 50 }, // ProjectDescription
        ];

        XLSX.writeFile(workbook, 'converted_import_data.xlsx');
        showSnack('Dönüştürülmüş dosya indirildi!', 'success');
    };

    // Import converted data directly
    const handleImportConverted = async () => {
        if (conversionPreview.length === 0) {
            showSnack('Önce dosyayı dönüştürün', 'warning');
            return;
        }

        try {
            // Create Excel file from converted data
            const worksheet = XLSX.utils.json_to_sheet(conversionPreview);
            const workbook = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(workbook, worksheet, 'Import');

            // Convert to array buffer and create File object
            const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
            const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
            const file = new File([blob], 'converted_import_data.xlsx', {
                type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            });

            // Set as selected file and trigger validation
            setSelectedFile(file);
            setValidatedData(null);
            setImportResult(null);

            showSnack('Dönüştürülmüş dosya yüklendi! Şimdi validate butonuna tıklayabilirsiniz.', 'success');

            // Auto-validate after setting file
            setValidating(true);
            try {
                const result = await importService.validateFile(file);
                setValidatedData(result);

                if (result.success) {
                    showSnack(`Dosya doğrulandı! ${result.valid_rows} geçerli satır bulundu. Import için hazır.`, 'success');
                } else {
                    showSnack(`Doğrulama başarısız: ${result.error}`, 'error');
                }
            } catch (error: any) {
                console.error('Error validating file:', error);
                showSnack(error.response?.data?.detail || 'Dosya doğrulanırken hata oluştu', 'error');
            } finally {
                setValidating(false);
            }
        } catch (error: any) {
            console.error('Error importing converted data:', error);
            showSnack('Dönüştürülmüş veri import edilirken hata oluştu: ' + error.message, 'error');
        }
    };

    const showSnack = useCallback((message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
        setSnack({ open: true, message, severity });
    }, []);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            const file = acceptedFiles[0];
            if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
                setSelectedFile(file);
                setValidatedData(null);
                setImportResult(null);
            } else {
                setSnack({ open: true, message: 'Please select a valid Excel file (.xlsx or .xls)', severity: 'error' });
            }
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
            'application/vnd.ms-excel': ['.xls'],
        },
        multiple: false,
    });

    const handleValidate = async () => {
        if (!selectedFile) {
            showSnack('Please select a file first', 'warning');
            return;
        }

        setValidating(true);
        try {
            const result = await importService.validateFile(selectedFile);
            setValidatedData(result);

            if (result.success) {
                showSnack(`File validated successfully. ${result.valid_rows} valid rows found.`, 'success');
            } else {
                showSnack(`Validation failed: ${result.error}`, 'error');
            }
        } catch (error: any) {
            console.error('Error validating file:', error);
            showSnack(error.response?.data?.detail || 'Error validating file', 'error');
        } finally {
            setValidating(false);
        }
    };

    const handleImport = async (dryRun: boolean = false) => {
        if (!selectedFile) {
            showSnack('Please select a file first', 'warning');
            return;
        }

        if (!validatedData || !validatedData.success) {
            showSnack('Please validate the file first', 'warning');
            return;
        }

        setImporting(true);
        try {
            const result = await importService.executeImport(selectedFile, dryRun);
            setImportResult(result);

            if (result.success) {
                const stats = result.statistics;
                showSnack(
                    dryRun
                        ? `Dry run completed: ${stats.projects_created} projects and ${stats.instructors_created} instructors would be created.`
                        : `Import completed successfully! ${stats.projects_created} projects and ${stats.instructors_created} instructors created.`,
                    'success'
                );
            } else {
                showSnack(`Import failed: ${result.error}`, 'error');
            }
        } catch (error: any) {
            console.error('Error executing import:', error);
            showSnack(error.response?.data?.detail || 'Error executing import', 'error');
        } finally {
            setImporting(false);
            setConfirmDialogOpen(false);
        }
    };

    const handleDownloadTemplate = async () => {
        try {
            await importService.downloadTemplate();
            showSnack('Template downloaded successfully', 'success');
        } catch (error: any) {
            console.error('Error downloading template:', error);
            showSnack('Error downloading template', 'error');
        }
    };

    // Notification import (instructor emails)
    const handleEmailFileChange = (file: File | null) => {
        setEmailFile(file);
        setEmailValidation(null);
        setEmailImportResult(null);
    };

    const handleDownloadEmailTemplate = async () => {
        try {
            setLoading(true);
            await importService.downloadInstructorEmailTemplate();
            showSnack('Instructor email template downloaded', 'success');
        } catch (error: any) {
            showSnack(error?.response?.data?.detail || 'Template download failed', 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleValidateEmails = async () => {
        if (!emailFile) {
            showSnack('Please select an email file first', 'warning');
            return;
        }
        setEmailValidating(true);
        try {
            const res = await importService.validateInstructorEmails(emailFile);
            setEmailValidation(res);
            if (res.success) {
                showSnack(`Validation successful. ${res.valid_rows} valid rows.`, 'success');
            } else {
                showSnack(res.error || 'Validation failed', 'error');
            }
        } catch (e: any) {
            showSnack(e?.response?.data?.detail || 'Validation failed', 'error');
        } finally {
            setEmailValidating(false);
        }
    };

    const handleImportEmails = async (dryRun: boolean = false) => {
        if (!emailFile) {
            showSnack('Please select an email file first', 'warning');
            return;
        }
        if (!emailValidation || !emailValidation.success) {
            showSnack('Please validate the email file first', 'warning');
            return;
        }
        setEmailImporting(true);
        try {
            const res = await importService.executeInstructorEmails(emailFile, dryRun);
            setEmailImportResult(res);
            if (res.success) {
                showSnack(
                    dryRun
                        ? `Dry run: ${res.statistics?.valid_rows || 0} rows valid`
                        : `Emails updated: ${res.statistics?.updated || 0}`,
                    'success'
                );
            } else {
                showSnack(res.error || 'Import failed', 'error');
            }
        } catch (e: any) {
            showSnack(e?.response?.data?.detail || 'Import failed', 'error');
        } finally {
            setEmailImporting(false);
        }
    };

    const handleReset = () => {
        setSelectedFile(null);
        setValidatedData(null);
        setImportResult(null);
    };

    const getStatusIcon = (status?: string): React.ReactElement | undefined => {
        switch (status) {
            case 'new':
                return <CheckCircle color="success" fontSize="small" />;
            case 'existing':
                return <Info color="info" fontSize="small" />;
            case 'new_project':
                return <CheckCircle color="success" fontSize="small" />;
            case 'duplicate':
                return <Warning color="warning" fontSize="small" />;
            case 'error':
                return <ErrorIcon color="error" fontSize="small" />;
            default:
                return undefined;
        }
    };

    const getStatusColor = (status?: string): 'success' | 'error' | 'warning' | 'info' | 'default' => {
        switch (status) {
            case 'new':
            case 'new_project':
                return 'success';
            case 'error':
                return 'error';
            case 'duplicate':
                return 'warning';
            case 'existing':
                return 'info';
            default:
                return 'default';
        }
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ mb: 4 }}>
                <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
                    Excel Import – Instructor & Project Loader
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Upload an Excel file to import instructor-project assignments. The file should contain columns: InstructorName, ProjectType, ProjectDescription
                </Typography>
            </Box>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
                {/* Upload Panel */}
                <Card>
                    <CardContent>
                        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                            Upload Excel File
                        </Typography>

                        {/* Dropzone */}
                        <Box
                            {...getRootProps()}
                            sx={{
                                border: '2px dashed',
                                borderColor: isDragActive ? 'primary.main' : 'grey.300',
                                borderRadius: 2,
                                p: 4,
                                textAlign: 'center',
                                cursor: 'pointer',
                                bgcolor: isDragActive ? 'action.hover' : 'background.paper',
                                transition: 'all 0.2s',
                                '&:hover': {
                                    borderColor: 'primary.main',
                                    bgcolor: 'action.hover',
                                },
                            }}
                        >
                            <input {...getInputProps()} />
                            <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                            {selectedFile ? (
                                <Box>
                                    <Typography variant="body1" sx={{ fontWeight: 600, mb: 1 }}>
                                        {selectedFile.name}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {(selectedFile.size / 1024).toFixed(2)} KB
                                    </Typography>
                                </Box>
                            ) : (
                                <Box>
                                    <Typography variant="body1" sx={{ mb: 1 }}>
                                        {isDragActive ? 'Drop the file here' : 'Drag & drop Excel file here'}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        or click to select
                                    </Typography>
                                </Box>
                            )}
                        </Box>

                        <Stack direction="row" spacing={2} sx={{ mt: 3 }}>
                            <Button
                                variant="outlined"
                                startIcon={<Download />}
                                onClick={handleDownloadTemplate}
                            >
                                Download Template
                            </Button>
                            {selectedFile && (
                                <Button
                                    variant="outlined"
                                    color="error"
                                    startIcon={<Cancel />}
                                    onClick={handleReset}
                                >
                                    Clear
                                </Button>
                            )}
                        </Stack>

                        {/* Actions */}
                        <Stack direction="row" spacing={2} sx={{ mt: 3 }}>
                            <Button
                                variant="contained"
                                startIcon={validating ? <CircularProgress size={20} /> : <Refresh />}
                                onClick={handleValidate}
                                disabled={!selectedFile || validating}
                                fullWidth
                            >
                                {validating ? 'Validating...' : 'Validate File'}
                            </Button>
                        </Stack>
                    </CardContent>
                </Card>

                {/* Notification Import: Instructor Emails */}
                <Card>
                    <CardContent>
                        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                            Notification Import (Instructor Emails)
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            1) "Export Instructor Email Template" ile mevcut öğretim görevlilerini ve e-posta alanlarını dışa aktarın.
                            2) Excel'de e-posta sütunlarını doldurun veya güncelleyin.
                            3) Dosyayı seçip doğrulayın, ardından içeri aktarın.
                        </Typography>

                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
                            <Button
                                variant="outlined"
                                startIcon={<Download />}
                                onClick={handleDownloadEmailTemplate}
                                disabled={loading}
                            >
                                Export Instructor Email Template
                            </Button>
                            <Button
                                variant="outlined"
                                color="error"
                                startIcon={<Cancel />}
                                onClick={() => handleEmailFileChange(null)}
                            >
                                Clear Selection
                            </Button>
                        </Stack>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                            <Button variant="contained" component="label" startIcon={<CloudUpload />}>
                                Select Email Excel
                                <input
                                    type="file"
                                    accept=".xlsx,.xls"
                                    hidden
                                    onChange={(e) => handleEmailFileChange(e.target.files?.[0] || null)}
                                />
                            </Button>
                            <Typography variant="body2">
                                {emailFile ? `${emailFile.name} (${(emailFile.size / 1024).toFixed(1)} KB)` : 'No file selected'}
                            </Typography>
                        </Box>

                        <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                            <Button
                                variant="contained"
                                startIcon={emailValidating ? <CircularProgress size={20} /> : <Refresh />}
                                onClick={handleValidateEmails}
                                disabled={!emailFile || emailValidating}
                            >
                                {emailValidating ? 'Validating...' : 'Validate Emails'}
                            </Button>
                            <Button
                                variant="outlined"
                                color="secondary"
                                startIcon={<PlayArrow />}
                                onClick={() => handleImportEmails(true)}
                                disabled={!emailFile || emailImporting}
                            >
                                Dry Run
                            </Button>
                            <Button
                                variant="contained"
                                color="success"
                                startIcon={emailImporting ? <CircularProgress size={20} /> : <CheckCircle />}
                                onClick={() => handleImportEmails(false)}
                                disabled={!emailFile || emailImporting}
                            >
                                {emailImporting ? 'Importing...' : 'Import Emails'}
                            </Button>
                        </Stack>

                        {emailValidation && (
                            <Box sx={{ mt: 2 }}>
                                <Alert severity={emailValidation.success ? 'success' : 'warning'}>
                                    {emailValidation.success
                                        ? `Validation successful. Valid rows: ${emailValidation.valid_rows}, Invalid rows: ${emailValidation.invalid_rows}.`
                                        : emailValidation.error || 'Validation failed.'}
                                </Alert>
                                {emailValidation.rows && emailValidation.rows.length > 0 && (
                                    <TableContainer component={Paper} sx={{ mt: 2, maxHeight: 320 }}>
                                        <Table size="small" stickyHeader>
                                            <TableHead>
                                                <TableRow>
                                                    <TableCell>Row</TableCell>
                                                    <TableCell>Instructor</TableCell>
                                                    <TableCell>Email</TableCell>
                                                    <TableCell>Errors</TableCell>
                                                </TableRow>
                                            </TableHead>
                                            <TableBody>
                                                {emailValidation.rows.map((row: any) => (
                                                    <TableRow key={row.row_number}>
                                                        <TableCell>{row.row_number}</TableCell>
                                                        <TableCell>{row.instructor_name}</TableCell>
                                                        <TableCell>{row.email}</TableCell>
                                                        <TableCell>
                                                            {row.errors && row.errors.length > 0 ? (
                                                                <Stack spacing={0.5}>
                                                                    {row.errors.map((err: string, idx: number) => (
                                                                        <Typography key={idx} variant="caption" color="error">
                                                                            {err}
                                                                        </Typography>
                                                                    ))}
                                                                </Stack>
                                                            ) : (
                                                                <Typography variant="caption" color="success.main">
                                                                    OK
                                                                </Typography>
                                                            )}
                                                        </TableCell>
                                                    </TableRow>
                                                ))}
                                            </TableBody>
                                        </Table>
                                    </TableContainer>
                                )}
                            </Box>
                        )}

                        {emailImportResult && (
                            <Box sx={{ mt: 2 }}>
                                <Alert severity={emailImportResult.success ? 'success' : 'error'}>
                                    {emailImportResult.success
                                        ? `Updated: ${emailImportResult.statistics?.updated || 0}, Valid rows: ${emailImportResult.statistics?.valid_rows || 0}, Invalid: ${emailImportResult.statistics?.invalid_rows || 0}`
                                        : emailImportResult.error || 'Import failed'}
                                </Alert>
                            </Box>
                        )}
                    </CardContent>
                </Card>

                {/* Statistics Panel */}
                <Card>
                    <CardContent>
                        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                            Import Statistics
                        </Typography>

                        {validatedData && (
                            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                                <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                                    <Typography variant="h4" color="primary">
                                        {validatedData.total_rows}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Total Rows
                                    </Typography>
                                </Paper>
                                <Paper sx={{ p: 2, bgcolor: 'success.light', color: 'success.contrastText' }}>
                                    <Typography variant="h4">
                                        {validatedData.valid_rows}
                                    </Typography>
                                    <Typography variant="body2">
                                        Valid Rows
                                    </Typography>
                                </Paper>
                                {validatedData.invalid_rows > 0 && (
                                    <Paper sx={{ p: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
                                        <Typography variant="h4">
                                            {validatedData.invalid_rows}
                                        </Typography>
                                        <Typography variant="body2">
                                            Invalid Rows
                                        </Typography>
                                    </Paper>
                                )}
                            </Box>
                        )}

                        {importResult && (
                            <Box sx={{ mt: 3 }}>
                                <Divider sx={{ my: 2 }} />
                                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                                    Import Results
                                </Typography>
                                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">
                                            Instructors Created
                                        </Typography>
                                        <Typography variant="h6">
                                            {importResult.statistics.instructors_created}
                                        </Typography>
                                    </Box>
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">
                                            Projects Created
                                        </Typography>
                                        <Typography variant="h6">
                                            {importResult.statistics.projects_created}
                                        </Typography>
                                    </Box>
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">
                                            Rows Processed
                                        </Typography>
                                        <Typography variant="h6">
                                            {importResult.statistics.rows_processed}
                                        </Typography>
                                    </Box>
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">
                                            Rows Skipped
                                        </Typography>
                                        <Typography variant="h6">
                                            {importResult.statistics.rows_skipped}
                                        </Typography>
                                    </Box>
                                </Box>
                            </Box>
                        )}

                        {validatedData && validatedData.success && (
                            <Box sx={{ mt: 3 }}>
                                <Button
                                    variant="contained"
                                    color="success"
                                    startIcon={importing ? <CircularProgress size={20} /> : <PlayArrow />}
                                    onClick={() => setConfirmDialogOpen(true)}
                                    disabled={importing}
                                    fullWidth
                                    size="large"
                                >
                                    {importing ? 'Importing...' : 'Import to System'}
                                </Button>
                            </Box>
                        )}
                    </CardContent>
                </Card>

                {/* Excel Format Converter */}
                <Card sx={{ gridColumn: { md: 'span 2' } }}>
                    <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            <Transform sx={{ mr: 1, color: 'secondary.main' }} />
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                                Excel Format Dönüştürücü
                            </Typography>
                        </Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            <strong>Hoca | Ara | Bitirme | Toplam</strong> formatındaki Excel dosyasını sisteme uygun formata dönüştürün.
                            Her öğretim üyesi için Ara ve Bitirme proje sayısı kadar ayrı satır oluşturulur.
                        </Typography>

                        <Alert severity="info" sx={{ mb: 2 }}>
                            <Typography variant="body2">
                                <strong>Beklenen Format:</strong> Excel'de "Hoca", "Ara", "Bitirme" sütunları olmalıdır.
                                Örnek: "Prof. Dr. Ahmet Yılmaz | 3 | 2 | 5" → 3 Ara + 2 Bitirme = 5 proje satırı oluşturulur.
                            </Typography>
                        </Alert>

                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
                            <Button
                                variant="contained"
                                component="label"
                                startIcon={<CloudUpload />}
                                color="secondary"
                            >
                                Excel Dosyası Seç
                                <input
                                    type="file"
                                    accept=".xlsx,.xls"
                                    hidden
                                    onChange={(e) => {
                                        setConverterFile(e.target.files?.[0] || null);
                                        setConversionPreview([]);
                                    }}
                                />
                            </Button>
                            <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
                                {converterFile ? `📄 ${converterFile.name} (${(converterFile.size / 1024).toFixed(1)} KB)` : 'Dosya seçilmedi'}
                            </Typography>
                        </Stack>

                        <Stack direction="row" spacing={2}>
                            <Button
                                variant="contained"
                                color="primary"
                                startIcon={converting ? <CircularProgress size={20} /> : <Transform />}
                                onClick={handleConvertFormat}
                                disabled={!converterFile || converting}
                            >
                                {converting ? 'Dönüştürülüyor...' : 'Dönüştür'}
                            </Button>
                            {conversionPreview.length > 0 && (
                                <>
                                    <Button
                                        variant="contained"
                                        color="success"
                                        startIcon={validating ? <CircularProgress size={20} /> : <PlayArrow />}
                                        onClick={handleImportConverted}
                                        disabled={validating}
                                    >
                                        {validating ? 'Doğrulanıyor...' : 'Doğrudan Import Et'}
                                    </Button>
                                    <Button
                                        variant="outlined"
                                        color="secondary"
                                        startIcon={<Download />}
                                        onClick={handleDownloadConverted}
                                    >
                                        İndir
                                    </Button>
                                </>
                            )}
                            {converterFile && (
                                <Button
                                    variant="outlined"
                                    color="error"
                                    startIcon={<Cancel />}
                                    onClick={() => {
                                        setConverterFile(null);
                                        setConversionPreview([]);
                                    }}
                                >
                                    Temizle
                                </Button>
                            )}
                        </Stack>

                        {/* Conversion Preview Table */}
                        {conversionPreview.length > 0 && (
                            <Box sx={{ mt: 3 }}>
                                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                                    Dönüşüm Önizleme ({conversionPreview.length} satır)
                                </Typography>
                                <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
                                    <Table size="small" stickyHeader>
                                        <TableHead>
                                            <TableRow>
                                                <TableCell>#</TableCell>
                                                <TableCell>InstructorName</TableCell>
                                                <TableCell>ProjectType</TableCell>
                                                <TableCell>ProjectDescription</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {conversionPreview.slice(0, 50).map((row, index) => (
                                                <TableRow key={index} hover>
                                                    <TableCell>{index + 1}</TableCell>
                                                    <TableCell>{row.InstructorName}</TableCell>
                                                    <TableCell>
                                                        <Chip
                                                            label={row.ProjectType}
                                                            size="small"
                                                            color={row.ProjectType === 'Bitirme Projesi' ? 'primary' : 'secondary'}
                                                        />
                                                    </TableCell>
                                                    <TableCell>{row.ProjectDescription}</TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                                {conversionPreview.length > 50 && (
                                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                        ... ve {conversionPreview.length - 50} satır daha (toplam: {conversionPreview.length})
                                    </Typography>
                                )}
                            </Box>
                        )}
                    </CardContent>
                </Card>
            </Box>

            {/* Preview Table */}
            {validatedData && validatedData.rows.length > 0 && (
                <Box sx={{ mt: 3 }}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                                File Preview
                            </Typography>
                            <TableContainer sx={{ maxHeight: 600 }}>
                                <Table stickyHeader>
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>Row</TableCell>
                                            <TableCell>Instructor Name</TableCell>
                                            <TableCell>Project Type</TableCell>
                                            <TableCell>Project Description</TableCell>
                                            <TableCell>Status</TableCell>
                                            <TableCell>Instructor</TableCell>
                                            <TableCell>Project</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {validatedData.rows.map((row: ImportRow) => (
                                            <TableRow key={row.row_number}>
                                                <TableCell>{row.row_number}</TableCell>
                                                <TableCell>{row.instructor_name}</TableCell>
                                                <TableCell>{row.project_type}</TableCell>
                                                <TableCell>{row.project_description}</TableCell>
                                                <TableCell>
                                                    {getStatusIcon(row.status) ? (
                                                        <Chip
                                                            icon={getStatusIcon(row.status)}
                                                            label={row.status || 'unknown'}
                                                            color={getStatusColor(row.status)}
                                                            size="small"
                                                        />
                                                    ) : (
                                                        <Chip
                                                            label={row.status || 'unknown'}
                                                            color={getStatusColor(row.status)}
                                                            size="small"
                                                        />
                                                    )}
                                                </TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={row.instructor_status || 'N/A'}
                                                        color={row.instructor_status === 'new' ? 'success' : 'info'}
                                                        size="small"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={row.project_status || 'N/A'}
                                                        color={row.project_status === 'new' ? 'success' : 'info'}
                                                        size="small"
                                                    />
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </CardContent>
                    </Card>
                </Box>
            )}

            {/* Confirmation Dialog */}
            <Dialog open={confirmDialogOpen} onClose={() => setConfirmDialogOpen(false)}>
                <DialogTitle>Confirm Import</DialogTitle>
                <DialogContent>
                    <Typography>
                        Are you sure you want to import {validatedData?.valid_rows || 0} rows to the database?
                        This will create new instructors and projects.
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setConfirmDialogOpen(false)}>Cancel</Button>
                    <Button
                        variant="contained"
                        onClick={() => handleImport(false)}
                        disabled={importing}
                    >
                        {importing ? 'Importing...' : 'Confirm Import'}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Snackbar */}
            <Snackbar
                open={snack.open}
                autoHideDuration={6000}
                onClose={() => setSnack({ ...snack, open: false })}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            >
                <Alert onClose={() => setSnack({ ...snack, open: false })} severity={snack.severity} sx={{ width: '100%' }}>
                    {snack.message}
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default Import;

