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
  MenuItem,
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
  AlertTitle,
  ToggleButton,
  ToggleButtonGroup,
  Fade,
  Collapse,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  Room,
  Add,
  ColorLens,
  Event,
  ViewList,
  People,
  Edit,
  Info,
  FileDownload,
  Analytics,
} from '@mui/icons-material';
import { api } from '../services/authService';
import SlotInsufficiencyDialog from '../components/SlotInsufficiencyDialog';
// import { algorithmService } from '../services/algorithmService';
// Lazy import to avoid type-resolution issues in CRA TS envs
// eslint-disable-next-line @typescript-eslint/no-var-requires
const XLSX: any = require('xlsx');

// Results sayfasından alınan detaylı analiz fonksiyonları
const isSeniorInstructor = (role: string) => {
  if (!role) return false;
  return role.includes('Prof. Dr.') || role.includes('Doç. Dr.') || role.includes('Dr. Öğr. Üyesi');
};

const calculateConflicts = (schedules: any[]) => {
  const instructorTimeslots = new Map<number, Set<number>>();
  let conflictCount = 0;

  schedules.forEach((schedule: any) => {
    if (!schedule.timeslot_id || !schedule.classroom_id || !schedule.responsible_instructor_id) return;

    const instructorId = schedule.responsible_instructor_id;
    if (!instructorTimeslots.has(instructorId)) {
      instructorTimeslots.set(instructorId, new Set());
    }

    const existingTimeslots = instructorTimeslots.get(instructorId)!;
    if (existingTimeslots.has(schedule.timeslot_id)) {
      conflictCount++;
    } else {
      existingTimeslots.add(schedule.timeslot_id);
    }
  });

  return {
    totalConflicts: conflictCount,
    instructorsWithConflicts: Array.from(instructorTimeslots.entries())
      .filter(([, timeslots]) => timeslots.size > 1).length
  };
};

const analyzeWorkloadDistribution = (schedules: any[], instructors: any[]) => {
  const workloadMap = new Map<number, number>();
  
  schedules.forEach((schedule: any) => {
    if (schedule.responsible_instructor_id) {
      const count = workloadMap.get(schedule.responsible_instructor_id) || 0;
      workloadMap.set(schedule.responsible_instructor_id, count + 1);
    }
  });

  const workloads = Array.from(workloadMap.values());
  
  if (workloads.length === 0) {
    return {
      maxWorkload: 0,
      minWorkload: 0,
      avgWorkload: 0,
      maxDifference: 0,
      totalInstructors: 0,
      maxWorkloadInstructors: [],
      minWorkloadInstructors: []
    };
  }

  const maxWorkload = Math.max(...workloads);
  const minWorkload = Math.min(...workloads);
  const avgWorkload = workloads.reduce((a, b) => a + b, 0) / workloads.length;

  // Maksimum yüke sahip instructor(lar)ı bul
  const maxWorkloadInstructorIds = Array.from(workloadMap.entries())
    .filter(([_, workload]) => workload === maxWorkload)
    .map(([instructorId, _]) => instructorId);
  
  const maxWorkloadInstructors = maxWorkloadInstructorIds.map(id => {
    const instructor = instructors.find(i => i.id === id);
    return instructor ? instructor.name : `Instructor ${id}`;
  });

  // Minimum yüke sahip instructor(lar)ı bul
  const minWorkloadInstructorIds = Array.from(workloadMap.entries())
    .filter(([_, workload]) => workload === minWorkload)
    .map(([instructorId, _]) => instructorId);
  
  const minWorkloadInstructors = minWorkloadInstructorIds.map(id => {
    const instructor = instructors.find(i => i.id === id);
    return instructor ? instructor.name : `Instructor ${id}`;
  });

  return {
    maxWorkload,
    minWorkload,
    avgWorkload: Math.round(avgWorkload * 10) / 10,
    maxDifference: maxWorkload - minWorkload,
    totalInstructors: workloadMap.size,
    maxWorkloadInstructors,
    minWorkloadInstructors
  };
};

const analyzeClassroomChanges = (schedules: any[]) => {
  const instructorClassrooms = new Map<number, Set<number>>();
  let totalChanges = 0;
  let instructorsWithChanges = 0;

  schedules.forEach((schedule: any) => {
    if (schedule.responsible_instructor_id && schedule.classroom_id) {
      if (!instructorClassrooms.has(schedule.responsible_instructor_id)) {
        instructorClassrooms.set(schedule.responsible_instructor_id, new Set());
      }
      instructorClassrooms.get(schedule.responsible_instructor_id)!.add(schedule.classroom_id);
    }
  });

  instructorClassrooms.forEach((classrooms, instructorId) => {
    if (classrooms.size > 1) {
      instructorsWithChanges++;
      totalChanges += classrooms.size - 1;
    }
  });

  return {
    totalChanges,
    instructorsWithChanges,
    totalInstructors: instructorClassrooms.size
  };
};

const calculateSatisfactionScore = (data: any) => {
  let score = 100;
  
  // Çakışma cezası
  score -= data.conflictAnalysis.totalConflicts * 10;
  
  // Yük dağılımı cezası
  if (data.workloadAnalysis.maxDifference > 2) {
    score -= (data.workloadAnalysis.maxDifference - 2) * 5;
  }
  
  // Sınıf değişimi cezası
  if (data.classroomChangeAnalysis.instructorsWithChanges > 0) {
    const changeRate = data.classroomChangeAnalysis.instructorsWithChanges / data.classroomChangeAnalysis.totalInstructors;
    score -= changeRate * 20;
  }
  
  // Atanmamış proje cezası
  if (data.unassignedProjects > 0) {
    const unassignedRate = data.unassignedProjects / data.totalProjects;
    score -= unassignedRate * 30;
  }
  
  return Math.max(0, Math.round(score));
};

const Planner: React.FC = () => {
  const [currentWeek, setCurrentWeek] = useState(new Date());
  const [schedules, setSchedules] = useState<any[]>([]);
  const [classrooms, setClassrooms] = useState<any[]>([]);
  const [timeslots, setTimeslots] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [instructors, setInstructors] = useState<any[]>([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedTimeSlot, setSelectedTimeSlot] = useState<any>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<number | ''>('');
  // const [algorithmResults, setAlgorithmResults] = useState<any[]>([]);
  const [snack, setSnack] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'warning' }>({ open: false, message: '', severity: 'success' });
  const [lastAlgorithmResult, setLastAlgorithmResult] = useState<any>(null);
  // Performance dialog state
  const [showPerformanceDialog, setShowPerformanceDialog] = useState(false);
  const [performanceData, setPerformanceData] = useState<any>(null);
  // Frontend overlay: Gün bazlı gösterim için (backend'de day yok)
  const [calendarOverlays, setCalendarOverlays] = useState<any[]>([]);
  // View toggle: 'classroom' or 'jury'
  const [viewMode, setViewMode] = useState<'classroom' | 'jury'>('classroom');
  
  // Classroom count from localStorage (set by Algorithms page)
  const [selectedClassroomCount, setSelectedClassroomCount] = useState<number>(7);
  
  // Slot insufficiency dialog state
  const [showSlotDialog, setShowSlotDialog] = useState(false);
  const [slotDialogData, setSlotDialogData] = useState({
    classroomCount: 7,
    projectCount: 0,
    availableSlots: 0,
    requiredSlots: 0,
  });

  // Accessible palette (WCAG AA): blue for bitirme, magenta for ara, teal for özel
  const getProjectColor = (project: any) => {
    // Önce project_type alanını kontrol et, sonra type alanını
    const type = (project?.project_type || project?.type || '').toString().toLowerCase();
    if (type === 'final' || type === 'bitirme') return '#1976d2'; // Blue - WCAG AA compliant
    if (type === 'interim' || type === 'ara') return '#dc004e';   // Magenta - WCAG AA compliant
    return '#00796b'; // Teal - WCAG AA compliant
  };

  const getProjectTypeIcon = (project: any) => {
    // Önce project_type alanını kontrol et, sonra type alanını
    const type = (project?.project_type || project?.type || '').toString().toLowerCase();
    if (type === 'final' || type === 'bitirme') return '🎓';
    if (type === 'interim' || type === 'ara') return '📋';
    return '📄';
  };

  const getTypeLabel = (project: any) => {
    // Önce project_type alanını kontrol et, sonra type alanını
    const type = (project?.project_type || project?.type || '').toString().toLowerCase();
    if (type === 'final' || type === 'bitirme') return 'Bitirme';
    if (type === 'interim' || type === 'ara') return 'Ara';
    return 'Proje';
  };

  const getInstructorName = (instructorId: number) => {
    if (!instructorId) return '';
    const instructor = instructors.find((i: any) => i.id === instructorId);
    return instructor?.full_name || instructor?.name || `Hoca ${instructorId}`;
  };

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

  const getJuryForSchedule = (schedule: any) => {
    let juryFromSchedule: Array<{id: number, name: string, role: string}> = [];
    
    try {
      // Schedule'dan project verisini al (sorumlu hocayı kontrol etmek için)
      const proj = schedule?.project || projects.find((p: any) => p.id === schedule?.project_id);
      
      // SADECE algoritmanın ürettiği gerçek jüri üyelerini kullan (schedule.instructors)
      // Placeholder jürileri (assistant_instructors, advisor_id, co_advisor_id) tamamen kaldır
      if (schedule?.instructors && Array.isArray(schedule.instructors)) {
        schedule.instructors.forEach((inst: any) => {
          // Sorumlu hocayı jüri listesine ekleme
          if (inst?.id && inst.id !== proj?.responsible_instructor_id) {
            juryFromSchedule.push({
              id: inst.id,
              name: inst.full_name || inst.name || `Hoca ${inst.id}`,
              role: inst.role === 'hoca' ? 'Öğretim Üyesi' : 'Araştırma Görevlisi'
            });
          }
        });
      }
      
    } catch (error) {
      console.error('Error getting jury for schedule:', error);
    }

    // Deduplicate by id (final guard)
    const unique: any[] = [];
    const seenIds = new Set<number>();
    for (const mem of juryFromSchedule) {
      if (mem?.id && !seenIds.has(mem.id)) { unique.push(mem); seenIds.add(mem.id); }
    }
    return unique;
  };

  const getJuryNamesForDialog = (selected: any) => {
    if (!selected) return '';
    const sch = schedules.find((s: any) => s.id === selected.scheduleId);
    let list = sch ? getJuryForSchedule(sch) : [];
    
    // Sorumlu hocayı jüri listesine ekleme - sadece yardımcıları göster
    // Eğer yardımcı yoksa "Atanmamış" döndür
    if (!list || list.length === 0) {
      return 'Atanmamış';
    }
    
    return list.map((j: any) => j.name).join(', ');
  };

  const getProjectComplianceStatus = (project: any, juryList: any[]) => {
    if (!project) return { isCompliant: true, message: '', severity: 'success' };
    
    const juryCount = juryList.length;
    const isBitirme = project.type === 'bitirme';
    const requiredMinJury = isBitirme ? 2 : 1; // Bitirme: en az 2 hoca, Ara: en az 1 hoca
    
    if (juryCount < requiredMinJury) {
      const message = isBitirme 
        ? `Bitirme projesi için en az 2 hoca gerekli (şu anda ${juryCount})`
        : `Ara proje için en az 1 hoca gerekli (şu anda ${juryCount})`;
      return { isCompliant: false, message, severity: 'error' };
    }
    
    if (juryCount === requiredMinJury) {
      const message = isBitirme 
        ? `Bitirme projesi için minimum jüri sayısı sağlanmış (${juryCount} hoca)`
        : `Ara proje için jüri ataması tamamlanmış (${juryCount} hoca)`;
      return { isCompliant: true, message, severity: 'warning' };
    }
    
    return { isCompliant: true, message: `Jüri ataması tamamlanmış (${juryCount} hoca)`, severity: 'success' };
  };

  // --- Export to Excel ---
  const handleExportProgram = () => {
    try {
      // Map for timeslot string → id
      const slotToId = new Map<string, number>();
      (timeslots || []).forEach((t: any) => {
        const key = `${String(t.start_time).slice(0, 5)}-${String(t.end_time).slice(0, 5)}`;
        if (t?.id) slotToId.set(key, t.id);
      });

      // Ensure deterministic order - use timeslots directly
      const orderedSlots: string[] = timeslots && timeslots.length > 0 
        ? timeslots.map((t: any) => {
            const startTime = String(t.start_time).slice(0, 5);
            const endTime = String(t.end_time).slice(0, 5);
            return `${startTime}-${endTime}`;
          })
        : [
            '09:00-09:30', '09:30-10:00', '10:00-10:30', '10:30-11:00', '11:00-11:30', '11:30-12:00',
            '13:00-13:30', '13:30-14:00', '14:00-14:30', '14:30-15:00', '15:00-15:30', '15:30-16:00',
            '16:00-16:30', '16:30-17:00', '17:00-17:30', '17:30-18:00'
          ];
      const orderedRooms = (classrooms || []).slice().sort((a: any, b: any) => String(a.name).localeCompare(String(b.name)));

      const getTypeLabelExcel = (project: any) => {
        // Önce project_type alanını kontrol et, sonra type alanını
        const type = (project?.project_type || project?.type || '').toString().toLowerCase();
        if (type === 'final' || type === 'bitirme') return 'Bitirme';
        if (type === 'interim' || type === 'ara') return 'Ara';
        return 'Özel';
      };

      const getProjectColorCode = (project: any) => {
        // Önce project_type alanını kontrol et, sonra type alanını
        const type = (project?.project_type || project?.type || '').toString().toLowerCase();
        if (type === 'final' || type === 'bitirme') return '#1976d2'; // Blue
        if (type === 'interim' || type === 'ara') return '#dc004e';   // Magenta
        return '#2e7d32'; // Teal
      };

      const findSchedule = (room: any, slotStr: string) => {
        const tsId = slotToId.get(slotStr);
        return (schedules || []).find((s: any) => {
          if (s.classroom_id !== room.id) return false;
          if (tsId && (s.timeslot_id === tsId || s?.timeslot?.id === tsId)) return true;
          if (s?.timeslot?.start_time && s?.timeslot?.end_time) {
            const key = `${String(s.timeslot.start_time).slice(0, 5)}-${String(s.timeslot.end_time).slice(0, 5)}`;
            return key === slotStr;
          }
          return false;
        });
      };

      // Create workbook
      const wb = XLSX.utils.book_new();
      
      // Create main schedule sheet
      const scheduleData: any[] = [];
      
      // Title row
      scheduleData.push(['BİLGİSAYAR ve BİTİRME Projesi Jüri Programı - ' + new Date().toLocaleDateString('tr-TR', { 
        day: '2-digit', 
        month: 'long', 
        year: 'numeric' 
      }).toUpperCase()]);
      scheduleData.push([]); // Empty row
      
      // Header row with classrooms
      const headerRow = ['ZAMAN'];
      orderedRooms.forEach(room => {
        headerRow.push(`Otr-${orderedRooms.indexOf(room) + 1}: ${room.name}`);
      });
      scheduleData.push(headerRow);
      
      // Data rows
      for (const slotStr of orderedSlots) {
        const slotLabel = slotStr.replace('-', '–');
        const row = [slotLabel];
        
        for (const room of orderedRooms) {
          const sch = findSchedule(room, slotStr);
          const projId = sch?.project_id || sch?.project?.id;
          const proj = projId ? (projects || []).find((p: any) => p.id === projId) : undefined;
          const jury = sch ? getJuryForSchedule(sch) : [];
          const responsibleId = proj?.responsible_instructor_id || proj?.responsible_id;
          const responsibleName = responsibleId ? getInstructorName(responsibleId) : '';
          
          if (proj) {
            
            // Create meaningful instructor/jury acronyms
            const responsibleAcronym = responsibleName ? responsibleName.split(' ').map((n: string) => n.charAt(0)).join('').toUpperCase() : 'XX';
            const juryAcronyms = jury.slice(0, 2).map((j: any) => 
              j.name ? j.name.split(' ').map((n: string) => n.charAt(0)).join('').toUpperCase() : 'XX'
            ).join('');
            
            // Create project title with type and instructor codes
            const projectType = getTypeLabelExcel(proj);
            const projectNumber = proj.id ? String(proj.id).padStart(2, '0') : '01';
            const projectTitle = proj.title || 'Proje Başlığı';
            const instructorCodes = `${responsibleAcronym}${juryAcronyms}`;
            
            // Format: "Bitirme 02: Kısa Başlık" (simplified version without instructor codes)
            const shortTitle = projectTitle.length > 20 ? projectTitle.substring(0, 20) + '...' : projectTitle;
            const cellContent = `${projectType} ${projectNumber}: ${shortTitle}`;
            row.push(cellContent);
          } else {
            row.push(''); // Empty cell
          }
        }
        scheduleData.push(row);
      }
      
      // Create worksheet
      const ws = XLSX.utils.aoa_to_sheet(scheduleData);
      
      // Merge title cell
      ws['!merges'] = [
        { s: { r: 0, c: 0 }, e: { r: 0, c: orderedRooms.length } }
      ];
      
      // Set column widths
      const colWidths = [{ wch: 15 }]; // Time column
      for (let i = 0; i < orderedRooms.length; i++) {
        colWidths.push({ wch: 50 }); // Classroom columns - wider for project titles
      }
      ws['!cols'] = colWidths;
      
      // Style the worksheet
      const range = XLSX.utils.decode_range(ws['!ref'] || 'A1');
      
      // Style title row
      for (let col = range.s.c; col <= range.e.c; col++) {
        const cellRef = XLSX.utils.encode_cell({ r: 0, c: col });
        if (!ws[cellRef]) ws[cellRef] = { v: '' };
        ws[cellRef].s = {
          font: { bold: true, size: 16, color: { rgb: "000000" } },
          alignment: { horizontal: "center", vertical: "center" },
          fill: { fgColor: { rgb: "E6F3FF" } }
        };
      }
      
      // Style header row
      for (let col = range.s.c; col <= range.e.c; col++) {
        const cellRef = XLSX.utils.encode_cell({ r: 2, c: col });
        if (!ws[cellRef]) ws[cellRef] = { v: '' };
        ws[cellRef].s = {
          font: { bold: true, size: 12 },
          alignment: { horizontal: "center", vertical: "center" },
          fill: { fgColor: { rgb: "D9E1F2" } },
          border: {
            top: { style: "thin", color: { rgb: "000000" } },
            bottom: { style: "thin", color: { rgb: "000000" } },
            left: { style: "thin", color: { rgb: "000000" } },
            right: { style: "thin", color: { rgb: "000000" } }
          }
        };
      }
      
      // Style data cells with colors based on project type
      for (let row = 3; row <= range.e.r; row++) {
        for (let col = 1; col <= range.e.c; col++) {
          const cellRef = XLSX.utils.encode_cell({ r: row, c: col });
          if (!ws[cellRef]) ws[cellRef] = { v: '' };
          
          // Find project for this cell
          const slotStr = orderedSlots[row - 3];
          const room = orderedRooms[col - 1];
          const sch = findSchedule(room, slotStr);
          const projId = sch?.project_id || sch?.project?.id;
          const proj = projId ? (projects || []).find((p: any) => p.id === projId) : undefined;
          
          let cellStyle: any = {
            alignment: { horizontal: "center", vertical: "center" },
            border: {
              top: { style: "thin", color: { rgb: "000000" } },
              bottom: { style: "thin", color: { rgb: "000000" } },
              left: { style: "thin", color: { rgb: "000000" } },
              right: { style: "thin", color: { rgb: "000000" } }
            }
          };
          
          if (proj) {
            const colorCode = getProjectColorCode(proj);
            // Convert hex to RGB
            const hex = colorCode.replace('#', '');
            const r = parseInt(hex.substr(0, 2), 16);
            const g = parseInt(hex.substr(2, 2), 16);
            const b = parseInt(hex.substr(4, 2), 16);
            
            const rgbValue = r.toString(16).padStart(2, '0') + g.toString(16).padStart(2, '0') + b.toString(16).padStart(2, '0');
            cellStyle.fill = { fgColor: { rgb: rgbValue } };
            cellStyle.font = { bold: true, color: { rgb: "FFFFFF" } };
          } else {
            cellStyle.fill = { fgColor: { rgb: "FFFFFF" } };
          }
          
          ws[cellRef].s = cellStyle;
        }
      }
      
      // Style time column
      for (let row = 3; row <= range.e.r; row++) {
        const cellRef = XLSX.utils.encode_cell({ r: row, c: 0 });
        if (!ws[cellRef]) ws[cellRef] = { v: '' };
        ws[cellRef].s = {
          font: { bold: true },
          alignment: { horizontal: "center", vertical: "center" },
          fill: { fgColor: { rgb: "F2F2F2" } },
          border: {
            top: { style: "thin", color: { rgb: "000000" } },
            bottom: { style: "thin", color: { rgb: "000000" } },
            left: { style: "thin", color: { rgb: "000000" } },
            right: { style: "thin", color: { rgb: "000000" } }
          }
        };
      }
      
      XLSX.utils.book_append_sheet(wb, ws, 'Jüri Programı');
      
      // Create detailed data sheet
      const detailedData: any[] = [];
      detailedData.push([
        'Zaman', 'Sınıf', 'Proje Başlığı', 'Proje Türü',
        'Sorumlu Öğretim Üyesi', 'Jüri Üyesi 1', 'Jüri Üyesi 2', 'Proje Rengi'
      ]);
      
      for (const slotStr of orderedSlots) {
        const slotLabel = slotStr.replace('-', '–');
        for (const room of orderedRooms) {
          const sch = findSchedule(room, slotStr);
          const projId = sch?.project_id || sch?.project?.id;
          const proj = projId ? (projects || []).find((p: any) => p.id === projId) : undefined;
          const jury = sch ? getJuryForSchedule(sch) : [];
          const responsibleId = proj?.responsible_instructor_id || proj?.responsible_id;
          const responsibleName = responsibleId ? getInstructorName(responsibleId) : '';
          const typeLabel = proj ? getTypeLabelExcel(proj) : '';
          
          detailedData.push([
            slotLabel,
            room?.name ?? '',
            proj ? (proj.title || `Proje ${proj.id}`) : 'Boş',
            proj ? typeLabel : '',
            proj ? responsibleName : '',
            jury?.[0]?.name || '',
            jury?.[1]?.name || '',
            proj ? typeLabel : ''
          ]);
        }
      }
      
      const ws2 = XLSX.utils.aoa_to_sheet(detailedData);
      ws2['!cols'] = [
        { wch: 12 }, { wch: 10 }, { wch: 42 }, { wch: 10 },
        { wch: 28 }, { wch: 24 }, { wch: 24 }, { wch: 24 }
      ];
      XLSX.utils.book_append_sheet(wb, ws2, 'Detaylı Veri');
      
      const fileName = `juri_programi_${new Date().toISOString().slice(0,10)}.xlsx`;
      XLSX.writeFile(wb, fileName);
      setSnack({ open: true, message: 'Excel çıktısı oluşturuldu', severity: 'success' });
    } catch (e: any) {
      console.error('Export error:', e);
      setSnack({ open: true, message: 'Excel dışa aktarma sırasında hata oluştu', severity: 'error' });
    }
  };

  // Animated session card with Collapse effect
  const SessionCard: React.FC<{ proj: any; jury: any[]; color: string; onClick: () => void; delay?: number }> = ({ proj, jury, color, onClick, delay = 0 }) => {
    // Jüri sayısına göre dinamik boyut
    const hasJury = jury && jury.length > 0;
    const juryCount = hasJury ? jury.length : 0;
    const cardHeight = hasJury ? Math.max(120, 96 + (juryCount * 20)) : 96; // Jüri sayısına göre yükseklik
    
    return (
      <Box sx={{ width: 220, minHeight: cardHeight, cursor: 'pointer', position: 'relative', m: 1 }} onClick={onClick}>
        {viewMode === 'classroom' ? (
          /* Classroom View - slides from left */
          <Collapse in={true} orientation="horizontal" collapsedSize={0} sx={{ transitionDelay: `${delay}ms` }}>
            <Box
              sx={{
                width: 220,
                minHeight: cardHeight,
                borderRadius: 2,
                border: '1px solid',
                borderColor: proj ? color : 'grey.300',
                bgcolor: proj ? `${color}12` : 'grey.50',
                display: 'flex',
                flexDirection: 'column',
                p: 1.25,
                overflow: 'hidden',
                gap: 0.75,
              }}
            >
              {proj ? (
                <>
                  {/* Üst kısım: Proje bilgileri */}
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, width: '100%' }}>
                    <Box sx={{ width: 6, height: 48, bgcolor: color, borderRadius: 1, mt: 0.3, flexShrink: 0 }} />
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Tooltip title={proj.title} placement="top" arrow>
                        <Typography variant="body2" sx={{ fontWeight: 700, lineHeight: 1.25, fontSize: 15, color: 'text.primary' }}>
                          {proj.title || `Proje ${proj.id}`}
                        </Typography>
                      </Tooltip>
                      <Typography variant="caption" sx={{ display: 'block', mb: 0.5, color: 'text.secondary' }}>
                        {getProjectTypeIcon(proj)} {getTypeLabel(proj)}
                      </Typography>
                      <Tooltip title={getInstructorName(proj.responsible_instructor_id) || ''} placement="bottom" arrow>
                        <Typography variant="caption" sx={{ display: 'block', color: '#1976d2', fontWeight: 600, fontSize: '0.75rem' }}>
                          👤 {getInstructorName(proj.responsible_instructor_id) || '-'}
                        </Typography>
                      </Tooltip>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Tooltip title="Projeyi görüntüle" arrow>
                        <IconButton size="small" onClick={onClick} aria-label="Projeyi görüntüle"><Info fontSize="inherit" /></IconButton>
                      </Tooltip>
                      <Tooltip title="Projeyi düzenle" arrow>
                        <IconButton size="small" onClick={onClick} aria-label="Projeyi düzenle"><Edit fontSize="inherit" /></IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                  
                  {/* Alt kısım: Jüri üyeleri */}
                  {hasJury && (
                    <Box sx={{ mt: 0.5, pt: 0.5, borderTop: '1px solid', borderColor: 'divider' }}>
                      <Typography variant="caption" sx={{ fontSize: '0.7rem', color: 'text.secondary', fontWeight: 600, mb: 0.5, display: 'block' }}>
                        🎯 Jüri Üyeleri:
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
                        {jury.slice(0, 3).map((juryMember, index) => (
                          <Tooltip key={index} title={juryMember.name} placement="bottom" arrow>
                            <Typography 
                              variant="caption" 
                              sx={{ 
                                fontSize: '0.7rem', 
                                color: 'text.secondary',
                                fontWeight: 500,
                                lineHeight: 1.3,
                                display: 'block',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap'
                              }}
                            >
                              • {juryMember.name}
                            </Typography>
                          </Tooltip>
                        ))}
                        {jury.length > 3 && (
                          <Typography variant="caption" sx={{ fontSize: '0.65rem', color: 'text.disabled', fontStyle: 'italic' }}>
                            +{jury.length - 3} daha...
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  )}
                </>
              ) : (
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
                  <Button size="small" startIcon={<Add />} onClick={onClick}>Proje Ekle</Button>
                </Box>
              )}
            </Box>
          </Collapse>
        ) : (
          /* Jury View - slides from right */
          <Collapse in={true} orientation="horizontal" collapsedSize={0} sx={{ transitionDelay: `${delay}ms` }}>
            <Box
              sx={{
                width: 220,
                minHeight: cardHeight,
                borderRadius: 2,
                border: '1px solid',
                borderColor: proj ? color : 'grey.300',
                bgcolor: proj ? `${color}12` : 'grey.50',
                display: 'flex',
                flexDirection: 'column',
                p: 1.25,
                overflow: 'hidden',
                gap: 0.75,
              }}
            >
              {proj ? (
                <>
                  {/* Proje başlığı */}
                  <Box sx={{ mb: 0.5 }}>
                    <Tooltip title={proj.title} placement="top" arrow>
                      <Typography variant="body2" sx={{ fontWeight: 700, color: 'text.primary', fontSize: 15 }} noWrap>
                        {proj.title}
                      </Typography>
                    </Tooltip>
                  </Box>
                  
                  {/* Sorumlu öğretim üyesi */}
                  <Box sx={{ mb: 0.5 }}>
                    <Tooltip title={getInstructorName(proj.responsible_instructor_id) || ''} placement="bottom" arrow>
                      <Typography variant="caption" sx={{ fontSize: '0.75rem', color: '#1976d2', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        👤 {getInstructorName(proj.responsible_instructor_id) || 'Atanmamış'}
                      </Typography>
                    </Tooltip>
                  </Box>
                  
                  {/* Jüri üyeleri */}
                  {hasJury && (
                    <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 0.25 }}>
                      <Typography variant="caption" sx={{ fontSize: '0.7rem', color: 'text.secondary', fontWeight: 600, mb: 0.25 }}>
                        🎯 Jüri:
                      </Typography>
                      {jury.slice(0, 4).map((juryMember, index) => (
                        <Tooltip key={index} title={juryMember.name} placement="bottom" arrow>
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              fontSize: '0.7rem', 
                              color: 'text.secondary',
                              fontWeight: 500,
                              lineHeight: 1.3,
                              display: 'block',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            • {juryMember.name}
                          </Typography>
                        </Tooltip>
                      ))}
                      {jury.length > 4 && (
                        <Typography variant="caption" sx={{ fontSize: '0.65rem', color: 'text.disabled', fontStyle: 'italic' }}>
                          +{jury.length - 4} daha...
                        </Typography>
                      )}
                    </Box>
                  )}
                </>
              ) : (
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
                  <Button size="small" startIcon={<Add />} onClick={onClick}>Proje Ekle</Button>
                </Box>
              )}
            </Box>
          </Collapse>
        )}
      </Box>
    );
  };

  const getOverlaysForDayTime = (day: string, timeSlot: string) => {
    return (calendarOverlays || []).filter((o: any) => `${o.startTime}-${o.endTime}` === timeSlot && o.day === day);
  };

  // Persisted overlays (day-specific placements)
  useEffect(() => {
    try {
      const saved = localStorage.getItem('planner_overlays');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) setCalendarOverlays(parsed);
      }
    } catch {}
  }, []);
  
  // Load classroom count from localStorage
  useEffect(() => {
    try {
      const savedClassroomCount = localStorage.getItem('selected_classroom_count');
      if (savedClassroomCount) {
        setSelectedClassroomCount(Number(savedClassroomCount));
      }
    } catch {}
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem('planner_overlays', JSON.stringify(calendarOverlays));
    } catch {}
  }, [calendarOverlays]);
  
  // Takvime henüz eklenmemiş projeleri hesapla
  const scheduledProjectIds = React.useMemo(() => {
    const ids = new Set<number>();
    try {
      (schedules || []).forEach((s: any) => {
        if (s?.project_id) ids.add(Number(s.project_id));
        if (s?.project?.id) ids.add(Number(s.project.id));
        if (Array.isArray(s?.timeSlots)) {
          s.timeSlots.forEach((ts: any) => {
            if (ts?.project_id) ids.add(Number(ts.project_id));
            if (ts?.project?.id) ids.add(Number(ts.project.id));
          });
        }
      });
    } catch (e) {}
    return ids;
  }, [schedules]);

  const availableProjects = React.useMemo(() => {
    // Eğer projects yoksa boş array döndür
    if (!projects || projects.length === 0) {
      return [];
    }
    // Eğer henüz hiçbir program yoksa tüm projeleri göster
    if (!scheduledProjectIds || scheduledProjectIds.size === 0) {
      return projects;
    }
    // Zaten programlanmış projeleri filtrele
    return projects.filter((p: any) => !scheduledProjectIds.has(Number(p.id)));
  }, [projects, scheduledProjectIds]);

  // DB timeslot eşleştirme yardımcıları
  const formatHHMM = (value: any) => (typeof value === 'string' ? value.slice(0, 5) : String(value).slice(0, 5));
  const toHHMMSS = (s: string) => (s.length === 5 ? `${s}:00` : s);
  const normalizeSlot = (s: string) => s.replace(/\s/g, '');
  const resolveDbTimeslot = async (start: string, end: string) => {
    const keyHM = normalizeSlot(`${String(start).trim()}-${String(end).trim()}`);
    const keyHMS = normalizeSlot(`${toHHMMSS(String(start).trim())}-${toHHMMSS(String(end).trim())}`);

    // 1) Yereldeki timeslots ile dene
    let source = timeslots as any[];
    const matchFrom = (arr: any[]) => arr.find((t: any) => {
      const a = normalizeSlot(`${formatHHMM(t.start_time)}-${formatHHMM(t.end_time)}`);
      const b = normalizeSlot(`${String(t.start_time)}-${String(t.end_time)}`);
      return a === keyHM || b === keyHMS;
    });
    let found = Array.isArray(source) ? matchFrom(source) : undefined;

    // 2) Bulunamazsa tazele ve tekrar dene
    if (!found) {
      try {
        const res = await api.get('/timeslots/');
        source = res.data || [];
        setTimeslots(source);
        found = matchFrom(source);
      } catch {}
    }

    // 3) Yine bulunamazsa, standart slotları seed et ve tekrar dene (superuser için)
    if (!found) {
      try {
        await api.post('/timeslots/seed-standard');
        const res2 = await api.get('/timeslots/');
        source = res2.data || [];
        setTimeslots(source);
        found = matchFrom(source);
      } catch {}
    }

    // 4) Hala bulunamadıysa, slotı oluşturmayı dene (superuser için)
    if (!found) {
      try {
        const payload = { start_time: toHHMMSS(start), end_time: toHHMMSS(end), period: Number(start.split(':')[0]) < 12 ? 'morning' : 'afternoon' } as any;
        const created = await api.post('/timeslots/', payload);
        found = created.data;
        // listeyi yenile
        const res3 = await api.get('/timeslots/');
        setTimeslots(res3.data || []);
      } catch {}
    }

    return found;
  };

  // Algoritma sonuçlarını çek - artık gerekli değil çünkü direkt apply-fallback kullanıyoruz
  const fetchAlgorithmResults = async () => {
    // Bu fonksiyon artık kullanılmıyor
  };

  useEffect(() => {
    try {
      const refresh = localStorage.getItem('planner_refresh');
      if (refresh === '1') {
        (async () => {
          try {
            // Force cache busting by adding timestamp
            const timestamp = Date.now();
            const [schedulesRes, classroomsRes, timeslotsRes, projectsRes, instructorsRes] = await Promise.all([
              api.get(`/schedules/?_t=${timestamp}`),
              api.get(`/classrooms/?_t=${timestamp}`),
              api.get(`/timeslots/?_t=${timestamp}`),
              api.get(`/projects/?_t=${timestamp}`),
              api.get(`/instructors/?_t=${timestamp}`),
            ]);
            setSchedules(schedulesRes.data || []);
            setClassrooms(classroomsRes.data || []);
            setTimeslots(timeslotsRes.data || []);
            setProjects(projectsRes.data || []);
            setInstructors(instructorsRes.data || []);
            setSnack({ open: true, message: 'Algoritma atamaları yüklendi', severity: 'success' });
          } catch (e) {}
          finally { localStorage.removeItem('planner_refresh'); }
        })();
      }
    } catch {}
  }, []);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const results = await Promise.allSettled([
          api.get('/schedules/'),
          api.get('/classrooms/'),
          api.get('/timeslots/'),
          api.get('/projects/'),
          api.get('/instructors/'),
        ]);

        const [schedulesRes, classroomsRes, timeslotsRes, projectsRes, instructorsRes] = results as any[];

        if (schedulesRes?.status === 'fulfilled') {
          const schedulesData = schedulesRes.value?.data || schedulesRes.value || [];
          console.log('📅 Schedules loaded:', schedulesData.length, schedulesData);
          setSchedules(schedulesData);
        }
        if (classroomsRes?.status === 'fulfilled') {
          const classroomsData = classroomsRes.value?.data || classroomsRes.value || [];
          console.log('🏫 Classrooms loaded:', classroomsData.length, classroomsData);
          setClassrooms(classroomsData);
        }
        if (timeslotsRes?.status === 'fulfilled') {
          const timeslotsData = timeslotsRes.value?.data || timeslotsRes.value || [];
          console.log('⏰ Timeslots loaded:', timeslotsData.length, timeslotsData);
          const generatedTimeSlots = timeslotsData.map((t: any) => {
            const startTime = String(t.start_time).slice(0, 5);
            const endTime = String(t.end_time).slice(0, 5);
            return `${startTime}-${endTime}`;
          });
          console.log('⏰ Generated timeSlots:', generatedTimeSlots);
          setTimeslots(timeslotsData);
        }
        if (projectsRes?.status === 'fulfilled') {
          const projectsData = projectsRes.value?.data || projectsRes.value || [];
          console.log('📚 Projects loaded:', projectsData.length, projectsData);
          setProjects(projectsData);
        }
        if (instructorsRes?.status === 'fulfilled') {
          const instructorsData = instructorsRes.value?.data || instructorsRes.value || [];
          console.log('👥 Instructors loaded:', instructorsData.length, instructorsData);
          setInstructors(instructorsData);
        }

        // Minimal safe fallbacks without wiping successful data
        if (classroomsRes?.status !== 'fulfilled') {
          setClassrooms([
            { id: 1, name: 'D-106', capacity: 30, location: 'D Blok 1. Kat' },
            { id: 2, name: 'D-107', capacity: 25, location: 'D Blok 1. Kat' },
            { id: 3, name: 'D-108', capacity: 35, location: 'D Blok 1. Kat' },
          ]);
        }

        if (projectsRes?.status !== 'fulfilled') {
          setProjects([
            { id: 1, title: 'Yapay Zeka Destekli Öğrenme Sistemi', type: 'bitirme', instructor: 'Dr. Ahmet Yılmaz', color: '#1976d2' },
            { id: 2, title: 'Mobil Uygulama Geliştirme', type: 'ara', instructor: 'Dr. Fatma Demir', color: '#dc004e' },
            { id: 3, title: 'Veri Analizi Projesi', type: 'bitirme', instructor: 'Dr. Mehmet Kaya', color: '#2e7d32' },
          ]);
        }

        // If schedules are empty but we have data, auto-fill overlays as a non-destructive UI fallback
        try {
          const sOk = schedulesRes?.status === 'fulfilled';
          const fetchedSchedules = sOk ? (schedulesRes.value?.data || []) : [];
          const haveNoDbSchedules = !fetchedSchedules || fetchedSchedules.length === 0;
          const haveDataForOverlay =
            (classroomsRes?.status === 'fulfilled' && (classroomsRes.value?.data || []).length > 0) &&
            (timeslotsRes?.status === 'fulfilled' && (timeslotsRes.value?.data || []).length > 0) &&
            (projectsRes?.status === 'fulfilled' && (projectsRes.value?.data || []).length > 0);

          if (haveNoDbSchedules && haveDataForOverlay) {
            // Build a temporary grid using overlays only; do not touch DB
            const cls = (classroomsRes.value?.data || []) as any[];
            const tsList = (timeslotsRes.value?.data || []) as any[];
            const projs = (projectsRes.value?.data || []) as any[];

            const toKey = (t: any) => `${String(t.start_time).slice(0,5)}-${String(t.end_time).slice(0,5)}`;
            const tsKeys = new Set(tsList.map(toKey));
            const gridSlots = timeSlots.filter((s) => tsKeys.has(s));

            const overlaysTemp: any[] = [];
            let pIdx = 0;
            for (const slot of gridSlots) {
              const [st, en] = slot.split('-');
              for (const c of cls) {
                if (pIdx >= projs.length) break;
                overlaysTemp.push({ day: 'Gün', startTime: st, endTime: en, classroom: c.name, project: projs[pIdx] });
                pIdx += 1;
              }
              if (pIdx >= projs.length) break;
            }
            if (overlaysTemp.length > 0) {
              setCalendarOverlays(overlaysTemp);
              try { localStorage.setItem('planner_overlays', JSON.stringify(overlaysTemp)); } catch {}
            }
          }
        } catch {}
      } catch (err) {
        console.error('Failed to fetch planner data:', err);
      } finally {
        // Algoritma sonuçlarını çek (no-op, geriye uyumluluk)
        fetchAlgorithmResults();
      }
    };

    fetchAll();
  }, []);

  // Check slot sufficiency when classroom count changes
  useEffect(() => {
    if (selectedClassroomCount) {
      checkSlotSufficiency();
    }
  }, [selectedClassroomCount]);

  // Generate timeSlots from API data or fallback to hardcoded
  const timeSlots = timeslots && timeslots.length > 0 
    ? timeslots.map((t: any) => {
        // Format time properly: "09:00:00.000000" -> "09:00"
        const startTime = String(t.start_time).slice(0, 5);
        const endTime = String(t.end_time).slice(0, 5);
        return `${startTime}-${endTime}`;
      })
    : [
        // Fallback: Sabah: 09:00, 09:30, 10:00, 10:30, 11:00, 11:30
        '09:00-09:30',
        '09:30-10:00',
        '10:00-10:30',
        '10:30-11:00',
        '11:00-11:30',
        '11:30-12:00',
        // Öğleden sonra: 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30
        '13:00-13:30',
        '13:30-14:00',
        '14:00-14:30',
        '14:30-15:00',
        '15:00-15:30',
        '15:30-16:00',
        '16:00-16:30',
        '16:30-17:00',
        // Akşam: 17:00, 17:30
        '17:00-17:30',
        '17:30-18:00'
      ];

  // Filter classrooms based on selected count
  const filteredClassrooms = React.useMemo(() => {
    if (!classrooms || classrooms.length === 0) return [];
    return classrooms.slice(0, selectedClassroomCount);
  }, [classrooms, selectedClassroomCount]);

  const getWeekDates = (date: Date) => {
    const week = [];
    const startOfWeek = new Date(date);
    const day = startOfWeek.getDay();
    const diff = startOfWeek.getDate() - day + (day === 0 ? -6 : 1); // Monday as first day
    startOfWeek.setDate(diff);

    for (let i = 0; i < 7; i++) {
      const currentDate = new Date(startOfWeek);
      currentDate.setDate(startOfWeek.getDate() + i);
      week.push(currentDate);
    }
    return week;
  };

  const navigateWeek = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentWeek);
    newDate.setDate(currentWeek.getDate() + (direction === 'next' ? 7 : -7));
    setCurrentWeek(newDate);
  };

  const getScheduleForDayAndTime = (day: string, timeSlot: string) => {
    // Haftalık takvim gün görünümünde sadece o güne ait overlay kayıtlarını göster
    const overlay = calendarOverlays.find((o: any) => o.day === day && `${o.startTime}-${o.endTime}` === timeSlot);
    return overlay || null;
  };

  const handleTimeSlotClick = (timeSlot: string, classroom?: string, project?: any, scheduleId?: number) => {
    const [startTime, endTime] = timeSlot.split('-');
    setSelectedTimeSlot({
      id: Date.now(),
      day: 'Gün',
      startTime,
      endTime,
      classroom: classroom || 'D-106',
      project: project || undefined,
      scheduleId: scheduleId || undefined,
    } as any);
    setSelectedProjectId(''); // Form'u temizle
    // Projeleri tazele (liste anlık güncel olsun)
    try { (async () => { const projRes = await api.get('/projects/'); setProjects(projRes.data || []); })(); } catch { }
    setOpenDialog(true);
  };

  /* const renderCalendarView = () => {
    const weekDates = getWeekDates(currentWeek);
    
    return (
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Haftalık Program
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<FileDownload />}
              onClick={handleExportProgram}
            >
              PROGRAMI DIŞA AKTAR
            </Button>
            <Button onClick={() => navigateWeek('prev')}>
              <ChevronLeft />
            </Button>
            <Typography variant="body1" sx={{ minWidth: 200, textAlign: 'center' }}>
              {weekDates[0].toLocaleDateString()} - {weekDates[6].toLocaleDateString()}
            </Typography>
            <Button onClick={() => navigateWeek('next')}>
              <ChevronRight />
            </Button>
          </Box>
        </Box>

        <TableContainer>
          <Table sx={{ minWidth: 800 }}>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600, minWidth: 100, bgcolor: 'grey.50' }}>
                  <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                    Saat
                  </Typography>
                </TableCell>
                {daysOfWeek.map((day, index) => (
                  <TableCell key={day} align="center" sx={{ fontWeight: 600, minWidth: 150 }}>
                    <Box>
                      <Typography variant="body2">{day}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {weekDates[index + 1]?.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit' })}
                      </Typography>
                    </Box>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {timeSlots.map((timeSlot) => (
                <TableRow key={timeSlot}>
                  <TableCell sx={{ fontWeight: 500, bgcolor: 'grey.50', fontSize: '0.75rem', p: 1 }}>
                    {timeSlot}
                  </TableCell>
                  {daysOfWeek.map((day) => {
                    const overlays = getOverlaysForDayTime(day, timeSlot);
                    return (
                      <TableCell
                        key={`${day}-${timeSlot}`}
                        align="center"
                        sx={{ 
                          p: 0.5,
                          cursor: 'pointer',
                          '&:hover': { bgcolor: 'grey.100' },
                          height: 50,
                          minHeight: 50
                        }}
                        onClick={() => handleTimeSlotClick(day, timeSlot)}
                      >
                        {overlays.length > 0 ? (
                          <Box sx={{ display: 'grid', gridTemplateColumns: `repeat(${overlays.length}, 1fr)`, gap: 0.5 }}>
                            {overlays.map((ov: any, idx: number) => (
                              <Card key={idx} sx={{ minHeight: 40, maxHeight: 40, border: `1px solid ${getProjectColor(ov.project)}`, bgcolor: `${getProjectColor(ov.project)}20` }}>
                                <CardContent sx={{ p: 0.5 }}>
                                  <Typography variant="caption" sx={{ fontWeight: 600, display: 'block', fontSize: '0.65rem', lineHeight: 1 }}>
                                    {(ov.project?.title || '').length > 15 ? (ov.project?.title || '').substring(0, 15) + '...' : (ov.project?.title || '')}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
                                    {ov.classroom}
                                  </Typography>
                                </CardContent>
                              </Card>
                            ))}
                          </Box>
                        ) : (
                          <Box
                            sx={{
                              minHeight: 40,
                              maxHeight: 40,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              border: '1px dashed #ccc',
                              borderRadius: 1,
                              '&:hover': { borderColor: 'primary.main' }
                            }}
                          >
                            <Add sx={{ color: 'text.disabled', fontSize: 16 }} />
                          </Box>
                        )}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    );
  }; */

  const renderClassroomView = () => (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', mb: 3, width: '100%' }}>
        {/* Left Side - Toggle Buttons */}
        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={(_, newMode) => {
            if (newMode && newMode !== viewMode) {
              setViewMode(newMode);
            }
          }}
          aria-label="view mode"
          sx={{ 
            '& .MuiToggleButton-root': { 
              borderRadius: 2,
              px: 3,
              py: 1,
              fontWeight: 600,
              transition: 'all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
              transform: 'translateY(0)',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
              },
              '&.Mui-selected': {
                transform: 'translateY(-1px)',
                boxShadow: '0 6px 20px rgba(25, 118, 210, 0.3)'
              }
            }
          }}
        >
          <ToggleButton value="classroom" aria-label="classroom view">
            <ViewList sx={{ mr: 1 }} />
            Sınıf Görünümü
          </ToggleButton>
          <ToggleButton value="jury" aria-label="jury view">
            <People sx={{ mr: 1 }} />
            Jüri Görünümü
          </ToggleButton>
        </ToggleButtonGroup>

        {/* Center - Color Coding Info */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, ml: '36px' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Box
              sx={{
                width: 16,
                height: 16,
                bgcolor: '#1976d2',
                borderRadius: 1,
                mr: 1
              }}
            />
            <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>Bitirme</Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Box
              sx={{
                width: 16,
                height: 16,
                bgcolor: '#dc004e',
                borderRadius: 1,
                mr: 1
              }}
            />
            <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>Ara</Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Box
              sx={{
                width: 16,
                height: 16,
                bgcolor: '#2e7d32',
                borderRadius: 1,
                mr: 1
              }}
            />
            <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>Özel</Typography>
          </Box>
        </Box>

        {/* Right Side - Export, Refresh and Reset Buttons */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, ml: 'auto' }}>
          <Button
            variant="outlined"
            color="secondary"
            startIcon={<Analytics />}
            onClick={async () => {
              try {
                // Mevcut schedule'ları al ve performans analizi yap
                const schedulesResponse = await api.get('/schedules/');
                const schedules = schedulesResponse.data || [];
                
                 if (schedules.length > 0) {
                   // Projeleri ve instructor'ları al
                   const projectsResponse = await api.get('/projects/');
                   const instructorsResponse = await api.get('/instructors/');
                   const projects = projectsResponse.data || [];
                   const instructors = instructorsResponse.data || [];
                   
                   // Detaylı performans analizi
                   const totalSchedules = schedules.length;
                   
                   // Doğru alanları kullanarak benzersiz değerleri hesapla
                   const uniqueProjects = new Set(schedules.map((s: any) => s.project_id).filter((id: any) => id != null)).size;
                   
                   // Öğretim üyesi sayısını hesapla - hem responsible_instructor_id hem de instructors array'inden
                   const instructorIds = new Set<number>();
                   schedules.forEach((s: any) => {
                     if (s.responsible_instructor_id) {
                       instructorIds.add(s.responsible_instructor_id);
                     }
                     if (s.instructors && Array.isArray(s.instructors)) {
                       s.instructors.forEach((inst: any) => {
                         if (inst.id) {
                           instructorIds.add(inst.id);
                         }
                       });
                     }
                   });
                   const uniqueInstructors = instructorIds.size;
                   
                   const uniqueClassrooms = new Set(schedules.map((s: any) => s.classroom_id).filter((id: any) => id != null)).size;
                   
                   // Zaman dağılımı analizi
                   const timeDistribution = schedules.reduce((acc: any, s: any) => {
                     const startTime = s.start_time || 'Bilinmeyen';
                     const sessionType = s.session_type || 'Bilinmeyen';
                     const timeKey = `${sessionType}-${startTime}`;
                     acc[timeKey] = (acc[timeKey] || 0) + 1;
                     return acc;
                   }, {});
                   
                   // Aktif zaman slotu sayısı - kullanılan zaman slotları
                   const activeTimeSlots = Object.keys(timeDistribution).filter(key => 
                     !key.includes('undefined') && !key.includes('Bilinmeyen')
                   ).length;
                   
                   // Toplam zaman slotu sayısı (16 slot)
                   const totalTimeSlots = 16;
                   
                   const avgLoadPerSlot = activeTimeSlots > 0 ? totalSchedules / activeTimeSlots : 0;
                   
                   // En yoğun zaman slotları
                   const topTimeSlots = Object.entries(timeDistribution)
                     .filter(([timeSlot]) => !timeSlot.includes('undefined') && !timeSlot.includes('Bilinmeyen'))
                     .sort(([,a], [,b]) => (b as number) - (a as number))
                     .slice(0, 5);
                   
                   // Detaylı analizler
                   const conflictAnalysis = calculateConflicts(schedules);
                   const workloadAnalysis = analyzeWorkloadDistribution(schedules, instructors);
                   const classroomChangeAnalysis = analyzeClassroomChanges(schedules);
                   
                   // Memnuniyet skoru için geçici veri objesi
                   const tempData = {
                     totalSchedules,
                     uniqueProjects,
                     conflictAnalysis,
                     workloadAnalysis,
                     classroomChangeAnalysis,
                     totalProjects: projects.length,
                     unassignedProjects: projects.length - totalSchedules
                   };
                   const satisfactionScore = calculateSatisfactionScore(tempData);
                   
                   // Performans verilerini state'e kaydet ve dialog'u aç
                   setPerformanceData({
                     totalSchedules,
                     uniqueProjects,
                     uniqueInstructors,
                     uniqueClassrooms,
                     timeSlots: activeTimeSlots, // Aktif zaman slotu sayısı
                     totalTimeSlots, // Toplam zaman slotu sayısı (16)
                     avgLoadPerSlot,
                     topTimeSlots,
                     programDistribution: (totalSchedules / uniqueProjects).toFixed(2),
                     classroomUsage: (totalSchedules / uniqueClassrooms).toFixed(2),
                     // Yeni detaylı analizler
                     conflictAnalysis,
                     workloadAnalysis,
                     classroomChangeAnalysis,
                     satisfactionScore,
                     totalProjects: projects.length,
                     assignedProjects: totalSchedules,
                     unassignedProjects: projects.length - totalSchedules,
                     utilizationRate: Math.round((totalSchedules / projects.length) * 100 * 10) / 10
                   });
                  setShowPerformanceDialog(true);
                } else {
                  setSnack({ 
                    open: true, 
                    message: 'Henüz hiç program oluşturulmamış!', 
                    severity: 'warning' 
                  });
                }
              } catch (error: any) {
                setSnack({ 
                  open: true, 
                  message: 'Performans verileri alınamadı: ' + (error?.response?.data?.detail || error.message), 
                  severity: 'error' 
                });
              }
            }}
            sx={{ borderRadius: 2 }}
          >
            Performansı Görüntüle
          </Button>
          
          <Button
            variant="outlined"
            color="primary"
            startIcon={<People />}
            onClick={async () => {
              try {
                // Projeleri yeniden yükle
                const projectsResponse = await api.get('/projects/');
                setProjects(projectsResponse.data || []);
                // Schedules'ları yeniden yükle
                const schedulesResponse = await api.get('/schedules/');
                setSchedules(schedulesResponse.data || []);
                // Instructor'ları yeniden yükle
                const instructorsResponse = await api.get('/instructors/');
                setInstructors(instructorsResponse.data || []);
                setSnack({ open: true, message: 'Veriler yenilendi', severity: 'success' });
              } catch (e: any) {
                setSnack({ open: true, message: e?.response?.data?.detail || 'Veri yenileme başarısız', severity: 'error' });
              }
            }}
            sx={{ borderRadius: 2 }}
          >
            Verileri Yenile
          </Button>
          
          <Button
            variant="contained"
            startIcon={<Event />}
            onClick={handleExportProgram}
            sx={{ borderRadius: 2 }}
          >
            Programı Dışa Aktar
          </Button>
          
          <Button variant="outlined" color="error" onClick={async () => {
            try {
              const res = await api.get('/schedules/');
              const all = res.data || [];
              for (const s of all) { try { await api.delete(`/schedules/${s.id}`); } catch {} }
              setCalendarOverlays([]);
              localStorage.removeItem('planner_overlays');
              const refreshed = await api.get('/schedules/');
              setSchedules(refreshed.data || []);
              setSnack({ open: true, message: 'Takvim sıfırlandı', severity: 'success' });
            } catch (e: any) {
              setSnack({ open: true, message: e?.response?.data?.detail || 'Sıfırlama başarısız', severity: 'error' });
            }
          }}>Sıfırla</Button>
        </Box>
      </Box>

       {/* Grid with sticky headers/left column for accessibility */}
       <Box sx={{ display: 'grid', gridTemplateColumns: `160px repeat(${filteredClassrooms.length}, 236px)`, gridAutoRows: 'minmax(96px, auto)', gap: 2, pr: 1, maxHeight: 'none', overflow: 'visible' }}>
         {/* Header row */}
         <Box sx={{ position: 'sticky', top: 0, zIndex: 5, bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', p: 1 }}>
           <Typography variant="body2" sx={{ fontWeight: 700 }}>Zaman</Typography>
         </Box>
         {filteredClassrooms.map((room) => (
           <Box key={`hdr-${room.id}`} sx={{ position: 'sticky', top: 0, zIndex: 5, bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 2, display: 'flex', alignItems: 'center', gap: 1, p: 1 }}>
             <Room sx={{ color: 'primary.main' }} />
             <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>{room.name}</Typography>
           </Box>
         ))}

        {/* Rows per timeslot */}
        {timeSlots.map((slot) => (
          <React.Fragment key={`row-${slot}`}>
             {/* Left time cell - sticky */}
             <Box sx={{ position: 'sticky', left: 0, zIndex: 4, p: 1, bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 96 }}>
               <Typography variant="body2" sx={{ fontWeight: 700 }}>{slot}</Typography>
             </Box>
            {/* One cell per classroom */}
            {filteredClassrooms.map((room, roomIndex) => {
              const ts = timeslots.find((t: any) => `${String(t.start_time).slice(0,5)}-${String(t.end_time).slice(0,5)}` === slot);
              const existing = (schedules || []).find((s: any) => {
                if (s.classroom_id !== room.id) return false;
                if (ts?.id) return s.timeslot_id === ts.id || s.timeslot?.id === ts.id;
                if (s?.timeslot?.start_time && s?.timeslot?.end_time) {
                  const key = `${String(s.timeslot.start_time).slice(0,5)}-${String(s.timeslot.end_time).slice(0,5)}`;
                  return key === slot;
                }
                return false;
              });
              
              // Debug: Log when we find a match
              if (existing) {
                console.log('🎯 Found schedule match:', { room: room.name, slot, existing });
              }
              const [startTime, endTime] = slot.split('-');
              const ov = calendarOverlays.find((o: any) => o.classroom === room.name && o.startTime === startTime && o.endTime === endTime);
              const proj = existing ? (projects.find((p: any) => p.id === existing.project_id) || (existing as any).project) : ov?.project;
              const jury = existing ? getJuryForSchedule(existing) : [];
              const color = getProjectColor(proj);
              const delay = roomIndex * 100; // Her sınıf için 100ms gecikme
              return (
                 <Box key={`cell-${room.id}-${slot}`} sx={{ position: 'relative', border: '1px dashed', borderColor: 'divider', borderRadius: 2, minHeight: 96, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <SessionCard 
                    proj={proj} 
                    jury={jury} 
                    color={color} 
                    onClick={() => handleTimeSlotClick(slot, room.name, proj, (existing as any)?.id)}
                    delay={delay}
                  />
                </Box>
              );
            })}
          </React.Fragment>
        ))}
      </Box>
    </Paper>
  );

  const renderJuryView = () => (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Jüri Atamaları
        </Typography>
      </Box>
      
      {/* Time slots on the left sidebar */}
      <Box sx={{ display: 'flex', gap: 2 }}>
        {/* Left sidebar with time slots */}
        <Box sx={{ minWidth: 120, borderRight: 1, borderColor: 'grey.200', pr: 2 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2, color: 'text.secondary' }}>
            Zaman Dilimleri
          </Typography>
          <Stack spacing={1}>
            {timeSlots.map((slot) => (
              <Box
                key={slot}
                sx={{
                  p: 1.5,
                  borderRadius: 1,
                  bgcolor: 'grey.50',
                  textAlign: 'center',
                  border: '1px solid',
                  borderColor: 'grey.200'
                }}
              >
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {slot}
                </Typography>
              </Box>
            ))}
          </Stack>
        </Box>

        {/* Main content area with classrooms and jury */}
        <Box sx={{ flex: 1, display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, gap: 3 }}>
          {filteredClassrooms.map((room) => {
            const roomSessions = (schedules || [])
              .filter((s: any) => s.classroom_id === room.id)
              .reduce((acc: any, s: any) => {
                const ts = timeslots.find((t: any) => t.id === s.timeslot_id);
                acc[`${String(ts?.start_time).slice(0,5)}-${String(ts?.end_time).slice(0,5)}`] = s;
                return acc;
              }, {} as Record<string, any>);

            return (
              <Card key={room.id} sx={{ borderRadius: 2, boxShadow: 2 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Room sx={{ mr: 1, color: 'primary.main' }} />
                      <Typography variant="h6" sx={{ fontWeight: 700 }}>
                        {room.name}
                      </Typography>
                    </Box>
                    <Chip label={`${room.capacity ?? 30} koltuk`} size="small" color="primary" variant="outlined" />
                  </Box>

                  <Divider sx={{ my: 2 }} />
                  <Stack spacing={1.2}>
                    {timeSlots.map((slot) => {
                      const existing = roomSessions[slot];
                      const [startTime, endTime] = slot.split('-');
                      const ov = calendarOverlays.find((o: any) => o.classroom === room.name && o.startTime === startTime && o.endTime === endTime);
                      const proj = existing ? projects.find((p: any) => p.id === existing.project_id) : ov?.project;
                      const jury = existing ? getJuryForSchedule(existing) : [];
                      const color = getProjectColor(proj);
                      
                      return (
                        <Box
                          key={slot}
                          sx={{
                            p: 1.5,
                            borderRadius: 1.5,
                            border: '1px solid',
                            borderColor: proj ? color : 'grey.300',
                            bgcolor: proj ? `${color}15` : 'grey.50',
                            transition: 'all .15s ease',
                            '&:hover': { boxShadow: 1, bgcolor: proj ? `${color}22` : 'grey.100' }
                          }}
                        >
                          {proj ? (
                            <Box>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                <Box sx={{ width: 6, height: 20, bgcolor: color, borderRadius: 1 }} />
                                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                  {proj.title || `Proje ${proj.id}`}
                                </Typography>
                              </Box>
                              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 1 }}>
                                {getTypeLabel(proj)}
                              </Typography>
                              
                              {/* Jury members */}
                              {jury.length > 0 && (
                                <Box sx={{ mt: 1 }}>
                                  <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary' }}>
                                    Jüri Üyeleri:
                                  </Typography>
                                  <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                                    {jury.map((member: any, idx: number) => (
                                      <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                        <People sx={{ fontSize: 12, color: 'text.secondary' }} />
                                        <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                                          {member.name}
                                        </Typography>
                                      </Box>
                                    ))}
                                  </Stack>
                                </Box>
                              )}
                            </Box>
                          ) : (
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 40 }}>
                              <Add sx={{ color: 'text.disabled', fontSize: 16 }} />
                            </Box>
                          )}
                        </Box>
                      );
                    })}
                  </Stack>
                </CardContent>
              </Card>
            );
          })}
        </Box>
      </Box>
    </Paper>
  );

  const renderColorCoding = () => (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, display: 'flex', alignItems: 'center' }}>
        <ColorLens sx={{ mr: 1 }} />
        Renk Kodlaması
      </Typography>
      
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box
            sx={{
              width: 20,
              height: 20,
              bgcolor: '#1976d2',
              borderRadius: 1,
              mr: 1
            }}
          />
          <Typography variant="body2">Bitirme Projeleri</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box
            sx={{
              width: 20,
              height: 20,
              bgcolor: '#dc004e',
              borderRadius: 1,
              mr: 1
            }}
          />
          <Typography variant="body2">Ara Projeler</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box
            sx={{
              width: 20,
              height: 20,
              bgcolor: '#2e7d32',
              borderRadius: 1,
              mr: 1
            }}
          />
          <Typography variant="body2">Özel Projeler</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box
            sx={{
              width: 20,
              height: 20,
              border: '2px dashed #ccc',
              borderRadius: 1,
              mr: 1
            }}
          />
          <Typography variant="body2">Boş Zaman Dilimi</Typography>
        </Box>
      </Box>
    </Paper>
  );

  return (
    <Box>



      {/* Tek düzen: içerik flip ile değişir */}
      <Box 
        sx={{ 
          position: 'relative', 
          minHeight: 'auto',
          transition: 'opacity 0.3s ease-in-out',
          opacity: 1
        }}
      >
        {renderClassroomView()}
      </Box>

      {/* Schedule Detail Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedTimeSlot?.project ? 'Proje Bilgileri' : 'Yeni Program Ekle'}
        </DialogTitle>
        <DialogContent>
          {selectedTimeSlot && (
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  label="Sınıf"
                  value={selectedTimeSlot.classroom}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
                <TextField
                  label="Zaman"
                  value={`${selectedTimeSlot.startTime} - ${selectedTimeSlot.endTime}`}
                  fullWidth
                  InputProps={{ readOnly: true }}
                />
              </Box>
              
              {selectedTimeSlot.project ? (
                <>
                  <TextField label="Proje Başlığı" value={selectedTimeSlot.project.title} fullWidth InputProps={{ readOnly: true }} />
                  <TextField label="Proje Türü" value={selectedTimeSlot.project.type === 'bitirme' ? 'Bitirme' : 'Ara'} fullWidth InputProps={{ readOnly: true }} />
                  <TextField label="Sorumlu Öğretim Üyesi" value={getInstructorName(selectedTimeSlot.project.responsible_instructor_id) || selectedTimeSlot.project.responsible_instructor || selectedTimeSlot.project.instructor || ''} fullWidth InputProps={{ readOnly: true }} />
                  <TextField label="Jüri Üyeleri" value={getJuryNamesForDialog(selectedTimeSlot)} fullWidth InputProps={{ readOnly: true }} />
                  {/* Katılımcı Detayları */}
                  <Paper variant="outlined" sx={{ p: 1.5 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>Katılımcılar</Typography>
                    <Typography variant="caption" sx={{ display: 'block', color: 'text.secondary' }}>Sorumlu</Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      {getInstructorName(selectedTimeSlot.project.responsible_instructor_id) || '-'}
                    </Typography>
                    <Typography variant="caption" sx={{ display: 'block', color: 'text.secondary' }}>Yardımcılar / Jüri</Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      {getJuryNamesForDialog(selectedTimeSlot) || 'Atanmamış'}
                    </Typography>
                    
                    {/* Uyumluluk Durumu */}
                    {(() => {
                      const sch = schedules.find((s: any) => s.id === selectedTimeSlot.scheduleId);
                      const juryList = sch ? getJuryForSchedule(sch) : [];
                      const compliance = getProjectComplianceStatus(selectedTimeSlot.project, juryList);
                      
                      if (!compliance.isCompliant) {
                        return (
                          <Alert severity="error" sx={{ mt: 1 }}>
                            <AlertTitle>Eksik Atama</AlertTitle>
                            {compliance.message}
                          </Alert>
                        );
                      } else if (compliance.severity === 'warning') {
                        return (
                          <Alert severity="warning" sx={{ mt: 1 }}>
                            <AlertTitle>Minimum Atama</AlertTitle>
                            {compliance.message}
                          </Alert>
                        );
                      } else {
                        return (
                          <Alert severity="success" sx={{ mt: 1 }}>
                            <AlertTitle>Atama Tamamlandı</AlertTitle>
                            {compliance.message}
                          </Alert>
                        );
                      }
                    })()}
                  </Paper>
                  <TextField select label="Bu seansa farklı proje yerleştir" fullWidth value={selectedProjectId}
                    onChange={(e) => setSelectedProjectId(Number((e.target as any).value) || '')}>
                    <MenuItem value="">Proje seçin...</MenuItem>
                    {projects.filter((p:any)=> p.id !== selectedTimeSlot.project.id).map((p:any)=> (
                      <MenuItem key={p.id} value={p.id}>{p.title}</MenuItem>
                    ))}
                  </TextField>
                </>
              ) : (
                <>
                  <TextField
                    select
                    label="Proje"
                    fullWidth
                    helperText={availableProjects.length === 0 ? 'Tüm projeler takvime eklenmiş görünüyor' : ''}
                    value={selectedProjectId}
                    onChange={(e) => setSelectedProjectId(Number((e.target as any).value) || '')}
                  >
                    <MenuItem value="">Proje seçin...</MenuItem>
                    {availableProjects.map((p: any) => (
                      <MenuItem key={p.id} value={p.id}>
                        {p.title}
                      </MenuItem>
                    ))}
                  </TextField>
                </>
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>
            İptal
          </Button>
          {selectedTimeSlot?.project ? (
            <>
              <Button color="error" onClick={async ()=>{
                try {
                  // mevcut programı kaldır
                  if (selectedTimeSlot?.scheduleId) {
                    await api.delete(`/schedules/${selectedTimeSlot.scheduleId}`);
                  }
                  const refreshed = await api.get('/schedules/');
                  setSchedules(refreshed.data || []);
                  setSnack({ open: true, message: 'Program kaldırıldı', severity: 'success' });
                  setOpenDialog(false);
                } catch (e:any) {
                  setSnack({ open: true, message: e?.response?.data?.detail || 'Program kaldırılamadı', severity: 'error' });
                }
              }}>Takvimden Kaldır</Button>
              <Button variant="contained" disabled={!selectedProjectId} onClick={async ()=>{
                try {
                  if (!selectedProjectId) return;
                  // Zaman dilimini backend'de bul
                  const ts = await resolveDbTimeslot(selectedTimeSlot.startTime, selectedTimeSlot.endTime);
                  const clsSan = (s:string) => (s || '').toLowerCase().replace(/\s|-/g,'');
                  const classroom = classrooms.find((c:any)=> clsSan(c.name)===clsSan(selectedTimeSlot.classroom));
                  if (!ts?.id || !classroom?.id) { setSnack({open:true, message:'Zaman veya sınıf bulunamadı', severity:'error'}); return; }
                  const payload:any = { project_id: selectedProjectId, classroom_id: classroom.id, timeslot_id: ts.id };
                  await api.post('/schedules/', { schedule_in: payload, instructor_ids: [] });
                  // eski programı kaldır
                  if (selectedTimeSlot?.scheduleId) { try { await api.delete(`/schedules/${selectedTimeSlot.scheduleId}`); } catch {}
                  }
                  const refreshed = await api.get('/schedules/');
                  setSchedules(refreshed.data || []);
                  setSnack({ open: true, message: 'Proje değiştirildi', severity: 'success' });
                  setOpenDialog(false);
                  setSelectedProjectId('');
                } catch (e:any) {
                  setSnack({ open: true, message: e?.response?.data?.detail || 'Değişiklik yapılamadı', severity:'error' });
                }
              }}>Bu seansa taşı</Button>
            </>
          ) : (
            <Button variant="contained" onClick={async () => {
              try {
                if (!selectedProjectId) return;
                // Zaman dilimini database'den bul
                const ts = await resolveDbTimeslot(selectedTimeSlot.startTime, selectedTimeSlot.endTime);
                const clsSan = (s:string) => (s || '').toLowerCase().replace(/\s|-/g,'');
                const classroom = classrooms.find((c:any)=> clsSan(c.name)===clsSan(selectedTimeSlot.classroom));
                if (!selectedProjectId) { window.alert('Lütfen bir proje seçin'); return; }
                if (!ts?.id) { window.alert('Seçilen zaman dilimi sistemde bulunamadı'); return; }
                if (!classroom?.id) { window.alert('Seçilen sınıf sistemde bulunamadı'); return; }
                const payload:any = {
                  project_id: selectedProjectId,
                  classroom_id: classroom?.id,
                  timeslot_id: ts?.id
                };
                await api.post('/schedules/', { schedule_in: payload, instructor_ids: [] });
                const refreshed = await api.get('/schedules/');
                setSchedules(refreshed.data || []);
                // Overlay'e ekle (gün bazlı görünüm için)
                const proj = projects.find((p: any) => p.id === selectedProjectId);
                const updatedOverlays = [
                  ...calendarOverlays,
                  {
                    day: selectedTimeSlot.day,
                    startTime: selectedTimeSlot.startTime,
                    endTime: selectedTimeSlot.endTime,
                    classroom: classroom.name,
                    project: proj,
                  },
                ];
                setCalendarOverlays(updatedOverlays);
                setSnack({ open: true, message: 'Program kaydedildi', severity: 'success' });
                setOpenDialog(false);
                setSelectedProjectId(''); // Form'u temizle
              } catch (e: any) {
                setSnack({ open: true, message: e?.response?.data?.detail || 'Program kaydedilemedi', severity: 'error' });
              }
            }}>
              Programı Kaydet
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar open={snack.open} autoHideDuration={3000} onClose={() => setSnack((s) => ({ ...s, open: false }))}>
        <Alert severity={snack.severity} sx={{ width: '100%' }}>
          {snack.message}
        </Alert>
      </Snackbar>

      {/* Performance Analysis Dialog */}
      <Dialog 
        open={showPerformanceDialog} 
        onClose={() => setShowPerformanceDialog(false)} 
        maxWidth="md" 
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: '0 8px 32px rgba(0,0,0,0.12)'
          }
        }}
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 1,
          pb: 1,
          borderBottom: '1px solid',
          borderColor: 'divider'
        }}>
          <Analytics color="primary" />
          <Typography variant="h6" component="div">
            Program Performans Analizi
          </Typography>
        </DialogTitle>
        
        <DialogContent sx={{ pt: 3 }}>
          {performanceData && (
            <Stack spacing={3}>
              {/* Genel İstatistikler */}
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                  📊 Genel İstatistikler
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
                  <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                    <Typography variant="h4" color="primary.main" sx={{ fontWeight: 'bold' }}>
                      {performanceData.totalSchedules}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Toplam Program
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                    <Typography variant="h4" color="secondary.main" sx={{ fontWeight: 'bold' }}>
                      {performanceData.uniqueProjects}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Benzersiz Proje
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                    <Typography variant="h4" color="success.main" sx={{ fontWeight: 'bold' }}>
                      {performanceData.uniqueInstructors}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Öğretim Üyesi
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                    <Typography variant="h4" color="info.main" sx={{ fontWeight: 'bold' }}>
                      {performanceData.uniqueClassrooms}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Kullanılan Sınıf
                    </Typography>
                  </Box>
                </Box>
              </Paper>

              {/* Zaman Analizi */}
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                  ⏰ Zaman Analizi
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 2 }}>
                  <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                    <Typography variant="h5" color="primary.main" sx={{ fontWeight: 'bold' }}>
                      {performanceData.timeSlots}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Aktif Zaman Slotu
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                    <Typography variant="h5" color="info.main" sx={{ fontWeight: 'bold' }}>
                      {performanceData.totalTimeSlots}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Toplam Zaman Slotu
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                    <Typography variant="h5" color="secondary.main" sx={{ fontWeight: 'bold' }}>
                      {performanceData.avgLoadPerSlot.toFixed(1)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Slot Başına Ortalama Yük
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                    <Typography variant="h5" color="success.main" sx={{ fontWeight: 'bold' }}>
                      {Math.round((performanceData.timeSlots / performanceData.totalTimeSlots) * 100)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Zaman Slotu Kullanım Oranı
                    </Typography>
                  </Box>
                </Box>
              </Paper>

              {/* En Yoğun Zaman Slotları */}
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                  🔥 En Yoğun Zaman Slotları
                </Typography>
                <Stack spacing={1}>
                  {performanceData.topTimeSlots.length > 0 ? (
                    performanceData.topTimeSlots.map(([timeSlot, count]: [string, number], index: number) => {
                      // Zaman slotunu daha okunabilir formata çevir
                      const [sessionType, time] = timeSlot.split('-');
                      const sessionTypeText = sessionType === 'morning' ? 'Sabah' : 
                                           sessionType === 'afternoon' ? 'Öğleden Sonra' : 
                                           sessionType === 'break' ? 'Öğle Arası' : sessionType;
                      const formattedTimeSlot = `${sessionTypeText} - ${time}`;
                      
                      return (
                        <Box key={timeSlot} sx={{ 
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          alignItems: 'center',
                          p: 1.5,
                          bgcolor: 'white',
                          borderRadius: 1,
                          border: '1px solid',
                          borderColor: 'grey.200'
                        }}>
                          <Typography variant="body1" sx={{ fontWeight: 500 }}>
                            {formattedTimeSlot}
                          </Typography>
                          <Chip 
                            label={`${count} program`} 
                            color={index < 2 ? 'error' : index < 3 ? 'warning' : 'default'}
                            size="small"
                          />
                        </Box>
                      );
                    })
                  ) : (
                    <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                      Zaman slotu bilgisi bulunamadı
                    </Typography>
                  )}
                </Stack>
              </Paper>

               {/* Kalite Metrikleri */}
               <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                 <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                   🎯 Kalite Metrikleri
                 </Typography>
                 <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color="success.main" sx={{ fontWeight: 'bold' }}>
                       {performanceData.programDistribution}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Program/Proje Oranı
                     </Typography>
                   </Box>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color="info.main" sx={{ fontWeight: 'bold' }}>
                       {performanceData.classroomUsage}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Program/Sınıf Oranı
                     </Typography>
                   </Box>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color="primary.main" sx={{ fontWeight: 'bold' }}>
                       {performanceData.utilizationRate}%
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Kullanım Oranı
                     </Typography>
                   </Box>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color={performanceData.satisfactionScore >= 80 ? 'success.main' : performanceData.satisfactionScore >= 60 ? 'warning.main' : 'error.main'} sx={{ fontWeight: 'bold' }}>
                       {performanceData.satisfactionScore}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Memnuniyet Skoru
                     </Typography>
                   </Box>
                 </Box>
               </Paper>

               {/* Çakışma Analizi */}
               <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                 <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                   ⚠️ Çakışma Analizi
                 </Typography>
                 <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 2 }}>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color={performanceData.conflictAnalysis.totalConflicts === 0 ? 'success.main' : 'error.main'} sx={{ fontWeight: 'bold' }}>
                       {performanceData.conflictAnalysis.totalConflicts}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Toplam Çakışma
                     </Typography>
                   </Box>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color={performanceData.conflictAnalysis.instructorsWithConflicts === 0 ? 'success.main' : 'warning.main'} sx={{ fontWeight: 'bold' }}>
                       {performanceData.conflictAnalysis.instructorsWithConflicts}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Çakışmalı Öğretim Üyesi
                     </Typography>
                   </Box>
                 </Box>
               </Paper>

               {/* Yük Dağılımı Analizi */}
               <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                 <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                   ⚖️ Yük Dağılımı Analizi
                 </Typography>
                 <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 2 }}>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color="info.main" sx={{ fontWeight: 'bold' }}>
                       {performanceData.workloadAnalysis.maxWorkload}
                     </Typography>
                     <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                       Maksimum Yük
                     </Typography>
                     {performanceData.workloadAnalysis.maxWorkloadInstructors && 
                      performanceData.workloadAnalysis.maxWorkloadInstructors.length > 0 && (
                       <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 0.5 }}>
                         {performanceData.workloadAnalysis.maxWorkloadInstructors.map((name: string, index: number) => (
                           <Chip
                             key={index}
                             label={name}
                             size="small"
                             sx={{ 
                               fontSize: '0.7rem',
                               height: '22px',
                               bgcolor: 'info.lighter',
                               color: 'info.main'
                             }}
                           />
                         ))}
                       </Box>
                     )}
                   </Box>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color="success.main" sx={{ fontWeight: 'bold' }}>
                       {performanceData.workloadAnalysis.minWorkload}
                     </Typography>
                     <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                       Minimum Yük
                     </Typography>
                     {performanceData.workloadAnalysis.minWorkloadInstructors && 
                      performanceData.workloadAnalysis.minWorkloadInstructors.length > 0 && (
                       <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 0.5 }}>
                         {performanceData.workloadAnalysis.minWorkloadInstructors.map((name: string, index: number) => (
                           <Chip
                             key={index}
                             label={name}
                             size="small"
                             sx={{ 
                               fontSize: '0.7rem',
                               height: '22px',
                               bgcolor: 'success.lighter',
                               color: 'success.main'
                             }}
                           />
                         ))}
                       </Box>
                     )}
                   </Box>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color="primary.main" sx={{ fontWeight: 'bold' }}>
                       {performanceData.workloadAnalysis.avgWorkload}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Ortalama Yük
                     </Typography>
                   </Box>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color={performanceData.workloadAnalysis.maxDifference <= 2 ? 'success.main' : 'warning.main'} sx={{ fontWeight: 'bold' }}>
                       {performanceData.workloadAnalysis.maxDifference}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Yük Farkı
                     </Typography>
                   </Box>
                 </Box>
               </Paper>

               {/* Sınıf Değişimi Analizi */}
               <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                 <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                   🏫 Sınıf Değişimi Analizi
                 </Typography>
                 <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 2 }}>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color={performanceData.classroomChangeAnalysis.totalChanges === 0 ? 'success.main' : 'warning.main'} sx={{ fontWeight: 'bold' }}>
                       {performanceData.classroomChangeAnalysis.totalChanges}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Toplam Sınıf Değişimi
                     </Typography>
                   </Box>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color={performanceData.classroomChangeAnalysis.instructorsWithChanges === 0 ? 'success.main' : 'info.main'} sx={{ fontWeight: 'bold' }}>
                       {performanceData.classroomChangeAnalysis.instructorsWithChanges}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Sınıf Değiştiren Öğretim Üyesi
                     </Typography>
                   </Box>
                 </Box>
               </Paper>

               {/* Proje Atama Durumu */}
               <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                 <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                   📋 Proje Atama Durumu
                 </Typography>
                 <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 2 }}>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color="primary.main" sx={{ fontWeight: 'bold' }}>
                       {performanceData.totalProjects}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Toplam Proje
                     </Typography>
                   </Box>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color="success.main" sx={{ fontWeight: 'bold' }}>
                       {performanceData.assignedProjects}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Atanmış Proje
                     </Typography>
                   </Box>
                   <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid', borderColor: 'grey.200' }}>
                     <Typography variant="h5" color={performanceData.unassignedProjects === 0 ? 'success.main' : 'warning.main'} sx={{ fontWeight: 'bold' }}>
                       {performanceData.unassignedProjects}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Atanmamış Proje
                     </Typography>
                   </Box>
                 </Box>
               </Paper>
            </Stack>
          )}
        </DialogContent>
        
        <DialogActions sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
          <Button 
            onClick={() => setShowPerformanceDialog(false)}
            variant="outlined"
            sx={{ borderRadius: 2 }}
          >
            Kapat
          </Button>
        </DialogActions>
      </Dialog>

      {/* Slot Insufficiency Dialog */}
      <SlotInsufficiencyDialog
        open={showSlotDialog}
        onClose={() => setShowSlotDialog(false)}
        onContinue={() => setShowSlotDialog(false)}
        classroomCount={slotDialogData.classroomCount}
        projectCount={slotDialogData.projectCount}
        availableSlots={slotDialogData.availableSlots}
        requiredSlots={slotDialogData.requiredSlots}
      />
    </Box>
  );
};

export default Planner;