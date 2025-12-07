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
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { importService, ImportRow, ValidateResponse, ExecuteResponse } from '../services/importService';

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

