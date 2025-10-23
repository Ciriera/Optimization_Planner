import React, { useEffect, useMemo, useState } from 'react';
import { Box, Grid, Paper, Typography, Chip, Divider, Select, MenuItem, FormControl, InputLabel, Button } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { metricsService, PlanInput } from '../services/metricsService';
import { api } from '../services/authService';

const Card: React.FC<{ title: string; value: string | number; color?: 'success' | 'warning' | 'error' | 'default' }>
  = ({ title, value, color = 'default' }) => {
  const palette = { success: '#2e7d32', warning: '#ed6c02', error: '#d32f2f', default: '#1976d2' };
  return (
    <Paper sx={{ p: 2, borderRadius: 2 }} elevation={2}>
      <Typography variant="body2" sx={{ color: 'text.secondary' }}>{title}</Typography>
      <Typography variant="h5" sx={{ fontWeight: 700, color: palette[color] }}>{value}</Typography>
    </Paper>
  );
};

const statusChip = (ok: boolean, label: string) => (
  <Chip label={label} color={ok ? 'success' : 'error'} size="small" variant={ok ? 'filled' : 'outlined'} />
);

export default function PerformanceDashboard() {
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<PlanInput | null>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [algorithmName, setAlgorithmName] = useState<string>('Current Plan');

  const columns: GridColDef[] = [
    { field: 'metric', headerName: 'Metric', flex: 1 },
    { field: 'score', headerName: 'Score', width: 120 },
  ];

  const rows = useMemo(() => {
    if (!metrics) return [];
    return Object.entries(metrics.perMetric || {}).map(([k, v], i) => ({ id: i, metric: k, score: v as number }));
  }, [metrics]);

  const fetchPlan = async () => {
    // Build a plan from backend schedules + related lookups
    const [schedulesRes, classesRes, slotsRes, peopleRes, projectsRes] = await Promise.all([
      api.get('/schedules/public'),
      api.get('/classrooms/public'),
      api.get('/timeslots/public'),
      api.get('/instructors/public'),
      api.get('/projects/public'),
    ]);
    const assignments = (schedulesRes.data || []).map((s: any) => ({
      project_id: s.project_id,
      project_type: s.project?.type || s.type,
      class_id: s.classroom_id,
      slot_id: s.timeslot_id,
      roles: [
        { person_id: s.project?.responsible_id || s.responsible_id, role: 'SORUMLU' },
      ],
      instructors_used: (s.instructors || []).map((x: any) => x.id),
    }));
    const classes = (classesRes.data || []).map((c: any) => ({ id: c.id, name: c.name }));
    const slots = (slotsRes.data || []).map((t: any) => ({ id: t.id, label: `${t.start_time?.slice(0,5)}-${t.end_time?.slice(0,5)}` }));
    const people = (peopleRes.data || []).map((i: any) => ({ id: i.id, name: i.name, type: i.type?.toUpperCase() === 'INSTRUCTOR' ? 'HOCA' : 'ARASTIRMA_GOREVLISI' }));
    const expected_projects = (projectsRes.data || []).map((p: any) => ({ id: p.id, type: p.type, title: p.title }));
    setPlan({ classes, slots, assignments, people, expected_projects });
  };

  const computeNow = async () => {
    if (!plan) return;
    setLoading(true);
    try {
      const res = await metricsService.compute(plan);
      setMetrics(res);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlan().then(() => undefined);
  }, []);

  const coverageOk = (metrics?.counts?.missing_count ?? 1) === 0 && metrics?.counts?.scheduled_total === metrics?.counts?.expected_total;
  const duplicateOk = (metrics?.counts?.duplicate_count ?? 1) === 0;
  const gapOk = (metrics?.counts?.gap_units ?? 1) === 0;
  const lateOk = (metrics?.counts?.late_assignments ?? 1) === 0;
  const roleOk = (metrics?.counts?.role_violations_count ?? 1) === 0;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>Performance Dashboard</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small">
            <InputLabel>Algorithm</InputLabel>
            <Select value={algorithmName} label="Algorithm" onChange={(e) => setAlgorithmName(String(e.target.value))}>
              <MenuItem value="Current Plan">Current Plan</MenuItem>
            </Select>
          </FormControl>
          <Button variant="contained" onClick={computeNow} disabled={loading || !plan}>Compute</Button>
        </Box>
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(12, 1fr)' }, gap: 2 }}>
        <Box sx={{ gridColumn: { xs: '1 / -1', md: 'span 2' } }}>
          <Card title="Overall Score" value={metrics?.totals?.WeightedTotalScore ?? '-'} color={(metrics?.totals?.WeightedTotalScore ?? 0) >= 90 ? 'success' : (metrics?.totals?.WeightedTotalScore ?? 0) >= 75 ? 'warning' : 'error'} />
        </Box>
        <Box sx={{ gridColumn: { xs: '1 / -1', md: 'span 2' } }}>
          <Card title="Coverage %" value={metrics ? metrics.perMetric?.CoverageScore : '-'} color={coverageOk ? 'success' : 'error'} />
        </Box>
        <Box sx={{ gridColumn: { xs: '1 / -1', md: 'span 2' } }}>
          <Card title="Duplicate Score" value={metrics ? metrics.perMetric?.DuplicateScore : '-'} color={duplicateOk ? 'success' : 'error'} />
        </Box>
        <Box sx={{ gridColumn: { xs: '1 / -1', md: 'span 2' } }}>
          <Card title="Gap Score" value={metrics ? metrics.perMetric?.GapScore : '-'} color={gapOk ? 'success' : 'error'} />
        </Box>
        <Box sx={{ gridColumn: { xs: '1 / -1', md: 'span 2' } }}>
          <Card title="Late Slot Score" value={metrics ? metrics.perMetric?.LateSlotScore : '-'} color={lateOk ? 'success' : 'error'} />
        </Box>

        <Box sx={{ gridColumn: { xs: '1 / -1', md: 'span 4' } }}>
          <Paper sx={{ p: 2, borderRadius: 2 }} elevation={2}>
            <Typography variant="subtitle2" sx={{ color: 'text.secondary', mb: 1 }}>Status</Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {statusChip(coverageOk, 'Coverage')}
              {statusChip(duplicateOk, 'Duplicates')}
              {statusChip(gapOk, 'Gaps')}
              {statusChip(lateOk, 'Late Slots')}
              {statusChip(roleOk, 'Roles')}
            </Box>
          </Paper>
        </Box>
        <Box sx={{ gridColumn: { xs: '1 / -1', md: 'span 8' } }}>
          <Paper sx={{ p: 2, borderRadius: 2, height: 340 }} elevation={2}>
            <Typography variant="subtitle2" sx={{ color: 'text.secondary', mb: 1 }}>Per-Metric Scores</Typography>
            <DataGrid columns={columns} rows={rows} disableRowSelectionOnClick density="compact" hideFooter sx={{ height: 300 }} />
          </Paper>
        </Box>

        <Box sx={{ gridColumn: '1 / -1' }}>
          <Paper sx={{ p: 2, borderRadius: 2 }} elevation={2}>
            <Typography variant="subtitle2" sx={{ color: 'text.secondary' }}>Violations</Typography>
            <Divider sx={{ my: 1 }} />
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
              <Typography variant="body2">Missing: {metrics?.counts?.missing_count ?? '-'}</Typography>
              <Typography variant="body2">Duplicates: {metrics?.counts?.duplicate_count ?? '-'}</Typography>
              <Typography variant="body2">Gap Units: {metrics?.counts?.gap_units ?? '-'}</Typography>
              <Typography variant="body2">Late Assignments: {metrics?.counts?.late_assignments ?? '-'}</Typography>
              <Typography variant="body2">Role Violations: {metrics?.counts?.role_violations_count ?? '-'}</Typography>
            </Box>
          </Paper>
        </Box>
      </Box>
    </Box>
  );
}


