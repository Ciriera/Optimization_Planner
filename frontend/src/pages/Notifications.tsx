import React, { useState, useEffect } from 'react';
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
    TextField,
    Autocomplete,
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
    ToggleButton,
    ToggleButtonGroup,
    CircularProgress,
    IconButton,
    Tooltip,
    Grid,
    LinearProgress,
} from '@mui/material';
import {
    Email,
    Send,
    Preview,
    Refresh,
    CheckCircle,
    Error as ErrorIcon,
    Schedule,
    People,
    Visibility,
    VisibilityOff,
    Room,
} from '@mui/icons-material';
import { api } from '../services/authService';
import { notificationService, InstructorPreview, GlobalPlannerPreview, NotificationLog } from '../services/notificationService';

const Notifications: React.FC = () => {
    const [previewMode, setPreviewMode] = useState<'global' | 'personal'>('global');
    const [selectedInstructorId, setSelectedInstructorId] = useState<number | null>(null);
    const [instructors, setInstructors] = useState<any[]>([]);
    const [isTestAdmin, setIsTestAdmin] = useState(false);
    const [customEmail, setCustomEmail] = useState('');
    const [globalPreview, setGlobalPreview] = useState<GlobalPlannerPreview | null>(null);
    const [instructorPreview, setInstructorPreview] = useState<InstructorPreview | null>(null);
    const [logs, setLogs] = useState<NotificationLog[]>([]);
    const [logsTotal, setLogsTotal] = useState(0);
    const [logsStatusFilter, setLogsStatusFilter] = useState<'all' | 'pending' | 'success' | 'error' | 'failed'>('all');
    const [loading, setLoading] = useState(false);
    const [sending, setSending] = useState(false);
    const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
    const [confirmAction, setConfirmAction] = useState<(() => void) | null>(null);
    const [snack, setSnack] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'warning' | 'info' }>({
        open: false,
        message: '',
        severity: 'success',
    });

    // Load instructors list
    useEffect(() => {
        const loadInstructors = async () => {
            try {
                const response = await api.get('/instructors/');
                setInstructors(response.data || []);
            } catch (error: any) {
                console.error('Error loading instructors:', error);
            }
        };
        loadInstructors();
    }, []);

    // Load global preview on mount
    useEffect(() => {
        loadGlobalPreview();
    }, []);

    // Load logs
    useEffect(() => {
        loadLogs();
        // Auto-refresh logs every 30 seconds
        const interval = setInterval(loadLogs, 30000);
        return () => clearInterval(interval);
    }, [logsStatusFilter]);

    const missingEmails = instructors.filter((i: any) => !i.email);

    // Load instructor preview when selected
    useEffect(() => {
        if (selectedInstructorId && previewMode === 'personal') {
            loadInstructorPreview(selectedInstructorId);
        }
    }, [selectedInstructorId, previewMode]);

    const loadGlobalPreview = async () => {
        setLoading(true);
        try {
            const data = await notificationService.getGlobalPreview();
            setGlobalPreview(data);
        } catch (error: any) {
            setSnack({
                open: true,
                message: 'Planner verisi yüklenemedi: ' + (error?.response?.data?.detail || error.message),
                severity: 'error',
            });
        } finally {
            setLoading(false);
        }
    };

    const loadInstructorPreview = async (instructorId: number) => {
        setLoading(true);
        try {
            const data = await notificationService.getInstructorPreview(instructorId);
            setInstructorPreview(data);
        } catch (error: any) {
            setSnack({
                open: true,
                message: 'Öğretim görevlisi önizlemesi yüklenemedi: ' + (error?.response?.data?.detail || error.message),
                severity: 'error',
            });
        } finally {
            setLoading(false);
        }
    };

    const loadLogs = async () => {
        try {
            const data = await notificationService.getLogs(
                100,
                0,
                logsStatusFilter === 'all' ? undefined : logsStatusFilter
            );
            if (data.success) {
                setLogs(data.logs || []);
                setLogsTotal(data.total || 0);
            } else {
                console.error('Error loading logs:', data.error);
                setSnack({
                    open: true,
                    message: 'Loglar yüklenemedi: ' + (data.error || 'Bilinmeyen hata'),
                    severity: 'error',
                });
            }
        } catch (error: any) {
            console.error('Error loading logs:', error);
            setSnack({
                open: true,
                message: 'Loglar yüklenemedi: ' + (error?.response?.data?.detail || error.message || 'Bilinmeyen hata'),
                severity: 'error',
            });
        }
    };

    const handleSendToAll = () => {
        setConfirmAction(() => async () => {
            setSending(true);
            try {
                const result = await notificationService.sendToAll(false);
                setSnack({
                    open: true,
                    message: `Bildirimler gönderildi: ${result.results.success} başarılı, ${result.results.failed} başarısız`,
                    severity: result.results.failed === 0 ? 'success' : 'warning',
                });
                loadLogs();
            } catch (error: any) {
                setSnack({
                    open: true,
                    message: 'Bildirimler gönderilemedi: ' + (error?.response?.data?.detail || error.message),
                    severity: 'error',
                });
            } finally {
                setSending(false);
                setConfirmDialogOpen(false);
            }
        });
        setConfirmDialogOpen(true);
    };

    const handleSendTestEmail = async () => {
        setSending(true);
        try {
            await notificationService.sendTestEmail();
            setSnack({
                open: true,
                message: 'Test emaili gönderildi (cavuldak-eren@hotmail.com)',
                severity: 'success',
            });
        } catch (error: any) {
            setSnack({
                open: true,
                message: 'Test emaili gönderilemedi: ' + (error?.response?.data?.detail || error.message),
                severity: 'error',
            });
        } finally {
            setSending(false);
        }
    };

    const handleSendToSelected = () => {
        if (isTestAdmin) {
            if (!customEmail || !customEmail.trim()) {
                setSnack({
                    open: true,
                    message: 'Lütfen email adresini girin',
                    severity: 'warning',
                });
                return;
            }

            setConfirmAction(() => async () => {
                setSending(true);
                try {
                    await notificationService.sendToCustomEmail(customEmail, 'TEST_ADMIN', false);
                    setSnack({
                        open: true,
                        message: `Bildirim ${customEmail} adresine gönderildi`,
                        severity: 'success',
                    });
                    loadLogs();
                } catch (error: any) {
                    setSnack({
                        open: true,
                        message: 'Bildirim gönderilemedi: ' + (error?.response?.data?.detail || error.message),
                        severity: 'error',
                    });
                } finally {
                    setSending(false);
                    setConfirmDialogOpen(false);
                }
            });
            setConfirmDialogOpen(true);
            return;
        }

        if (!selectedInstructorId) {
            setSnack({
                open: true,
                message: 'Lütfen bir öğretim görevlisi seçin',
                severity: 'warning',
            });
            return;
        }

        setConfirmAction(() => async () => {
            setSending(true);
            try {
                await notificationService.sendToInstructor(selectedInstructorId, false);
                setSnack({
                    open: true,
                    message: 'Bildirim gönderildi',
                    severity: 'success',
                });
                loadLogs();
                if (previewMode === 'personal') {
                    loadInstructorPreview(selectedInstructorId);
                }
            } catch (error: any) {
                setSnack({
                    open: true,
                    message: 'Bildirim gönderilemedi: ' + (error?.response?.data?.detail || error.message),
                    severity: 'error',
                });
            } finally {
                setSending(false);
                setConfirmDialogOpen(false);
            }
        });
        setConfirmDialogOpen(true);
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'success':
                return 'success';
            case 'error':
            case 'failed':
                return 'error';
            case 'pending':
                return 'warning';
            default:
                return 'default';
        }
    };

    const getStatusIcon = (status: string): React.ReactElement | undefined => {
        switch (status) {
            case 'success':
                return <CheckCircle fontSize="small" />;
            case 'error':
            case 'failed':
                return <ErrorIcon fontSize="small" />;
            default:
                return undefined;
        }
    };

    return (
        <Box sx={{ p: 3, width: '100%' }}>
            {/* Header */}
            <Box sx={{ mb: 4 }}>
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                    Send Exam Planner Notifications to Instructors
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    Send the finalized calendar + personalized duty summaries by email to all instructors.
                </Typography>
            </Box>

            {/* Instructor email status */}
            <Paper sx={{ p: 2, mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>Instructor Emails</Typography>
                    <Chip
                        label={
                            missingEmails.length > 0
                                ? `${missingEmails.length} missing email${missingEmails.length > 1 ? 's' : ''}`
                                : 'All emails present'
                        }
                        color={missingEmails.length > 0 ? 'warning' : 'success'}
                        size="small"
                    />
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Eksik e-posta adreslerini Import sayfasındaki "Notification Import (Instructor Emails)" bölümünden Excel ile içeri aktarabilirsiniz.
                </Typography>
                <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 320 }}>
                    <Table size="small" stickyHeader>
                        <TableHead>
                            <TableRow>
                                <TableCell>Name</TableCell>
                                <TableCell>Email</TableCell>
                                <TableCell>Type</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {instructors.map((inst) => (
                                <TableRow key={inst.id} sx={{ bgcolor: inst.email ? undefined : 'warning.light' }}>
                                    <TableCell>{inst.name}</TableCell>
                                    <TableCell>
                                        {inst.email ? (
                                            inst.email
                                        ) : (
                                            <Typography variant="caption" color="warning.main">
                                                Missing email
                                            </Typography>
                                        )}
                                    </TableCell>
                                    <TableCell>{inst.type}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Paper>

            {/* Top Controls */}
            <Card sx={{ mb: 3, p: 3 }}>
                <Stack spacing={2}>
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
                        <Button
                            variant="contained"
                            color="primary"
                            size="large"
                            startIcon={<Send />}
                            onClick={handleSendToAll}
                            disabled={sending || loading}
                            sx={{ borderRadius: 2 }}
                        >
                            {sending ? 'Gönderiliyor...' : 'Send Notifications to All Instructors'}
                        </Button>

                        <Button
                            variant="outlined"
                            color="primary"
                            startIcon={<Email />}
                            onClick={handleSendTestEmail}
                            disabled={sending || loading}
                            sx={{ borderRadius: 2 }}
                        >
                            Send Test Email (Admin)
                        </Button>

                        <Autocomplete
                            options={[
                                { id: 'TEST_ADMIN', name: 'TEST_ADMIN', email: '', isTestAdmin: true },
                                ...instructors.map(i => ({ ...i, isTestAdmin: false }))
                            ]}
                            getOptionLabel={(option) => {
                                if (option.isTestAdmin) {
                                    return 'TEST_ADMIN';
                                }
                                return `${option.name || ''} ${option.email ? `(${option.email})` : ''}`;
                            }}
                            value={
                                isTestAdmin
                                    ? { id: 'TEST_ADMIN', name: 'TEST_ADMIN', email: '', isTestAdmin: true }
                                    : instructors.find((i) => i.id === selectedInstructorId) || null
                            }
                            onChange={(_, newValue) => {
                                if (newValue && newValue.isTestAdmin) {
                                    setIsTestAdmin(true);
                                    setSelectedInstructorId(null);
                                } else {
                                    setIsTestAdmin(false);
                                    setSelectedInstructorId(newValue?.id || null);
                                }
                            }}
                            sx={{ minWidth: 300 }}
                            renderInput={(params) => (
                                <TextField {...params} label="Select Instructor" variant="outlined" />
                            )}
                        />

                        {isTestAdmin && (
                            <TextField
                                label="Custom Email Address"
                                type="email"
                                value={customEmail}
                                onChange={(e) => setCustomEmail(e.target.value)}
                                placeholder="Enter email address"
                                variant="outlined"
                                sx={{ minWidth: 300 }}
                            />
                        )}

                        <Button
                            variant="outlined"
                            color="secondary"
                            startIcon={<Send />}
                            onClick={handleSendToSelected}
                            disabled={(isTestAdmin ? !customEmail || !customEmail.trim() : !selectedInstructorId) || sending || loading}
                            sx={{ borderRadius: 2 }}
                        >
                            Send to Selected Instructor
                        </Button>
                    </Box>

                    <Divider />

                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                            Preview Mode:
                        </Typography>
                        <ToggleButtonGroup
                            value={previewMode}
                            exclusive
                            onChange={(_, value) => value && setPreviewMode(value)}
                            size="small"
                        >
                            <ToggleButton value="global">Global Calendar</ToggleButton>
                            <ToggleButton value="personal">Personal Duties</ToggleButton>
                        </ToggleButtonGroup>

                        <Button
                            variant="text"
                            size="small"
                            startIcon={<Refresh />}
                            onClick={loadGlobalPreview}
                            disabled={loading}
                        >
                            Refresh Preview
                        </Button>
                    </Box>
                </Stack>
            </Card>

            {/* Preview Section */}
            <Card sx={{ mb: 3, p: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                    Preview
                </Typography>

                {loading && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                        <CircularProgress />
                    </Box>
                )}

                {!loading && previewMode === 'global' && globalPreview && (
                    <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            Global Planner Preview ({globalPreview.metadata.total_schedules} schedules,{' '}
                            {globalPreview.metadata.total_instructors} instructors)
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 2, maxHeight: 600, overflow: 'auto' }}>
                            {globalPreview.planner_data && globalPreview.planner_data.classes && globalPreview.planner_data.classes.length > 0 ? (
                                <Box sx={{ display: 'grid', gridTemplateColumns: `120px repeat(${globalPreview.planner_data.classes.length}, minmax(200px, 1fr))`, gap: 1 }}>
                                    {/* Header row */}
                                    <Box sx={{ p: 1.5, bgcolor: 'primary.main', color: 'white', borderRadius: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, position: 'sticky', top: 0, zIndex: 10 }}>
                                        <Typography variant="body2" sx={{ fontWeight: 700 }}>Zaman</Typography>
                                    </Box>
                                    {globalPreview.planner_data.classes.map((cls: string) => (
                                        <Box key={`hdr-${cls}`} sx={{ p: 1.5, bgcolor: 'primary.main', color: 'white', borderRadius: 1, display: 'flex', alignItems: 'center', gap: 1, fontWeight: 600, position: 'sticky', top: 0, zIndex: 10 }}>
                                            <Room sx={{ fontSize: 18 }} />
                                            <Typography variant="body2" sx={{ fontWeight: 700 }}>{cls}</Typography>
                                        </Box>
                                    ))}

                                    {/* Time slot rows */}
                                    {globalPreview.planner_data.timeSlots && globalPreview.planner_data.timeSlots.map((timeSlot: string, idx: number) => (
                                        <React.Fragment key={`row-${timeSlot}`}>
                                            {/* Time cell */}
                                            <Box sx={{ p: 1.5, bgcolor: idx % 2 === 0 ? 'grey.50' : 'white', border: '1px solid', borderColor: 'divider', borderRadius: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, minHeight: 80 }}>
                                                <Typography variant="body2" sx={{ fontWeight: 700 }}>{timeSlot}</Typography>
                                            </Box>

                                            {/* Project cells for each class */}
                                            {globalPreview.planner_data.classes.map((cls: string) => {
                                                const projectsForSlot = globalPreview.planner_data.projects.filter(
                                                    (p: any) => p.class === cls && p.time === timeSlot
                                                );

                                                return (
                                                    <Box
                                                        key={`cell-${cls}-${timeSlot}`}
                                                        sx={{
                                                            p: 1,
                                                            bgcolor: idx % 2 === 0 ? 'grey.50' : 'white',
                                                            border: '1px solid',
                                                            borderColor: 'divider',
                                                            borderRadius: 1,
                                                            minHeight: 80,
                                                            display: 'flex',
                                                            flexDirection: 'column',
                                                            gap: 0.5,
                                                        }}
                                                    >
                                                        {projectsForSlot.length > 0 ? (
                                                            projectsForSlot.map((proj: any, projIdx: number) => (
                                                                <Box
                                                                    key={`proj-${projIdx}`}
                                                                    sx={{
                                                                        p: 1.2,
                                                                        bgcolor: proj.color || 'grey.200',
                                                                        borderRadius: 0.5,
                                                                        borderLeft: `3px solid ${proj.color || 'grey.400'}`,
                                                                    }}
                                                                >
                                                                    <Typography
                                                                        variant="caption"
                                                                        sx={{
                                                                            fontWeight: 700,
                                                                            display: 'block',
                                                                            mb: 0.8,
                                                                            fontSize: '0.75rem',
                                                                            color: 'text.primary',
                                                                            lineHeight: 1.3
                                                                        }}
                                                                    >
                                                                        {proj.projectTitle || 'N/A'}
                                                                    </Typography>
                                                                    <Typography
                                                                        variant="caption"
                                                                        sx={{
                                                                            fontSize: '0.72rem',
                                                                            display: 'block',
                                                                            color: 'text.primary',
                                                                            fontWeight: 600,
                                                                            mb: 0.3
                                                                        }}
                                                                    >
                                                                        <Box component="span" sx={{ fontWeight: 700 }}>Sorumlu:</Box> {proj.responsible || 'N/A'}
                                                                    </Typography>
                                                                    <Box sx={{ mt: 0.6 }}>
                                                                        {/* Always show Jüri 1 and Jüri 2, use placeholder if missing */}
                                                                        {[0, 1].map((juryIdx: number) => {
                                                                            const juryMember = proj.jury && proj.jury[juryIdx];
                                                                            const displayText = juryMember || '[Araştırma Görevlisi]';
                                                                            const isPlaceholder = !juryMember;

                                                                            return (
                                                                                <Typography
                                                                                    key={`jury-${juryIdx}`}
                                                                                    variant="caption"
                                                                                    sx={{
                                                                                        fontSize: '0.72rem',
                                                                                        display: 'block',
                                                                                        color: isPlaceholder ? 'text.secondary' : 'text.primary',
                                                                                        fontStyle: 'normal',
                                                                                        fontWeight: isPlaceholder ? 600 : 600,
                                                                                        mb: 0.2
                                                                                    }}
                                                                                >
                                                                                    <Box component="span" sx={{ fontWeight: 700 }}>Jüri {juryIdx + 1}:</Box> {displayText}
                                                                                </Typography>
                                                                            );
                                                                        })}
                                                                    </Box>
                                                                    <Chip
                                                                        label={proj.type || 'N/A'}
                                                                        size="small"
                                                                        sx={{
                                                                            mt: 0.8,
                                                                            height: 20,
                                                                            fontSize: '0.7rem',
                                                                            fontWeight: 600
                                                                        }}
                                                                        color={proj.type === 'Bitirme' ? 'primary' : 'secondary'}
                                                                    />
                                                                </Box>
                                                            ))
                                                        ) : (
                                                            <Typography variant="caption" color="text.disabled" sx={{ textAlign: 'center', mt: 2 }}>
                                                                -
                                                            </Typography>
                                                        )}
                                                    </Box>
                                                );
                                            })}
                                        </React.Fragment>
                                    ))}
                                </Box>
                            ) : (
                                <Alert severity="info">
                                    Henüz planlanmış program yok. Planner sayfasından program oluşturun.
                                </Alert>
                            )}
                        </Paper>
                    </Box>
                )}

                {!loading && previewMode === 'personal' && instructorPreview && (
                    <Box>
                        {instructorPreview.hasAssignments ? (
                            <>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                    Personal Duties for {instructorPreview.instructor.name} ({instructorPreview.assignmentCount} assignments)
                                </Typography>
                                <TableContainer component={Paper} variant="outlined">
                                    <Table>
                                        <TableHead>
                                            <TableRow>
                                                <TableCell sx={{ fontWeight: 600 }}>Date</TableCell>
                                                <TableCell sx={{ fontWeight: 600 }}>Time</TableCell>
                                                <TableCell sx={{ fontWeight: 600 }}>Room</TableCell>
                                                <TableCell sx={{ fontWeight: 600 }}>Project</TableCell>
                                                <TableCell sx={{ fontWeight: 600 }}>Role</TableCell>
                                                <TableCell sx={{ fontWeight: 600 }}>Colleagues</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {instructorPreview.assignments.map((assignment, idx) => (
                                                <TableRow key={idx}>
                                                    <TableCell>{assignment.date}</TableCell>
                                                    <TableCell>{assignment.time}</TableCell>
                                                    <TableCell>{assignment.room}</TableCell>
                                                    <TableCell>{assignment.project}</TableCell>
                                                    <TableCell>
                                                        <Chip
                                                            label={assignment.role}
                                                            size="small"
                                                            color={assignment.role === 'Project Responsible' ? 'primary' : 'secondary'}
                                                        />
                                                    </TableCell>
                                                    <TableCell>
                                                        {assignment.otherInstructors.length > 0
                                                            ? assignment.otherInstructors.join(', ')
                                                            : '-'}
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            </>
                        ) : (
                            <Alert severity="info">
                                {instructorPreview.instructor.name} has no assignments in the current planner.
                            </Alert>
                        )}
                    </Box>
                )}

                {!loading && previewMode === 'personal' && !instructorPreview && selectedInstructorId && (
                    <Alert severity="warning">Select an instructor to preview their duties.</Alert>
                )}
            </Card>

            {/* Logs Section */}
            <Card sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        Notification Logs
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                        <Chip
                            label={`Total: ${logsTotal}`}
                            size="small"
                            color="primary"
                            variant="outlined"
                        />
                        <ToggleButtonGroup
                            value={logsStatusFilter}
                            exclusive
                            onChange={(_, value) => value && setLogsStatusFilter(value)}
                            size="small"
                        >
                            <ToggleButton value="all">All</ToggleButton>
                            <ToggleButton value="success">Success</ToggleButton>
                            <ToggleButton value="error">Error</ToggleButton>
                            <ToggleButton value="pending">Pending</ToggleButton>
                        </ToggleButtonGroup>
                        <IconButton size="small" onClick={loadLogs}>
                            <Refresh />
                        </IconButton>
                    </Box>
                </Box>

                <TableContainer component={Paper} variant="outlined">
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell sx={{ fontWeight: 600 }}>Instructor</TableCell>
                                <TableCell sx={{ fontWeight: 600 }}>Email</TableCell>
                                <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                                <TableCell sx={{ fontWeight: 600 }}>Sent At</TableCell>
                                <TableCell sx={{ fontWeight: 600 }}>Attempts</TableCell>
                                <TableCell sx={{ fontWeight: 600 }}>Error</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {logs.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                                        <Typography color="text.secondary">No logs found</Typography>
                                    </TableCell>
                                </TableRow>
                            ) : (
                                logs.map((log) => (
                                    <TableRow key={log.id}>
                                        <TableCell>{log.instructor_name || 'N/A'}</TableCell>
                                        <TableCell>{log.instructor_email}</TableCell>
                                        <TableCell>
                                            <Chip
                                                icon={getStatusIcon(log.status)}
                                                label={log.status}
                                                size="small"
                                                color={getStatusColor(log.status) as any}
                                            />
                                        </TableCell>
                                        <TableCell>
                                            {log.sent_at
                                                ? new Date(log.sent_at).toLocaleString('tr-TR')
                                                : '-'}
                                        </TableCell>
                                        <TableCell>{log.attempt_count}</TableCell>
                                        <TableCell>
                                            {log.error_message ? (
                                                <Tooltip title={log.error_message}>
                                                    <Typography
                                                        variant="body2"
                                                        color="error"
                                                        sx={{
                                                            maxWidth: 200,
                                                            overflow: 'hidden',
                                                            textOverflow: 'ellipsis',
                                                            whiteSpace: 'nowrap',
                                                        }}
                                                    >
                                                        {log.error_message}
                                                    </Typography>
                                                </Tooltip>
                                            ) : (
                                                '-'
                                            )}
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Card>

            {/* Confirmation Dialog */}
            <Dialog open={confirmDialogOpen} onClose={() => setConfirmDialogOpen(false)}>
                <DialogTitle>Confirm Notification Dispatch</DialogTitle>
                <DialogContent>
                    <Typography>
                        This will send notification emails to instructors with the latest planner data. Continue?
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setConfirmDialogOpen(false)}>Cancel</Button>
                    <Button
                        onClick={() => {
                            if (confirmAction) {
                                confirmAction();
                            }
                        }}
                        variant="contained"
                        color="primary"
                    >
                        Confirm
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

export default Notifications;

