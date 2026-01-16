import React, { useState, useEffect, useRef } from 'react';
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

// Results sayfasından alınan detaylı analiz fonksiyonları
const isSeniorInstructor = (role: string) => {
  if (!role) return false;
  return role.includes('Prof. Dr.') || role.includes('Doç. Dr.') || role.includes('Dr. Öğr. Üyesi');
};

const calculateConflicts = (schedules: any[], instructors?: any[], classrooms?: any[], timeslots?: any[]) => {
  // Map: instructor_id -> timeslot_id -> list of schedules at that timeslot
  const instructorTimeslotMap = new Map<number, Map<number, any[]>>();
  let conflictCount = 0;
  const conflictDetails: Array<{
    instructorId: number;
    instructorName: string;
    timeslotId: number;
    timeslotLabel: string;
    classroomIds: number[];
    classroomNames: string[];
    projectIds: number[];
    projectNames: string[];
  }> = [];

  // Helper to get instructor name
  const getInstructorNameById = (id: number) => {
    if (!instructors || id === -1) return `Hoca ${id}`;
    const inst = instructors.find((i: any) => i.id === id);
    return inst?.name || inst?.full_name || `Hoca ${id}`;
  };

  // Helper to get classroom name
  const getClassroomNameById = (id: number) => {
    if (!classrooms) return `Sınıf ${id}`;
    const cls = classrooms.find((c: any) => c.id === id);
    return cls?.name || `Sınıf ${id}`;
  };

  // Helper to get timeslot label
  const getTimeslotLabel = (id: number) => {
    if (!timeslots) return `Slot ${id}`;
    const ts = timeslots.find((t: any) => t.id === id);
    if (ts?.start_time && ts?.end_time) {
      return `${String(ts.start_time).slice(0, 5)}-${String(ts.end_time).slice(0, 5)}`;
    }
    return `Slot ${id}`;
  };

  schedules.forEach((schedule: any) => {
    if (!schedule.timeslot_id) return;

    // Get all instructors involved (PS + J1)
    const involvedInstructors: number[] = [];

    // Responsible instructor
    let responsibleInstructorId = schedule.project?.responsible_instructor_id ||
      schedule.responsible_instructor_id;

    // From instructors array
    if (schedule.instructors && Array.isArray(schedule.instructors)) {
      schedule.instructors.forEach((inst: any) => {
        if (typeof inst === 'object' && inst?.id && inst.id !== -1) {
          involvedInstructors.push(inst.id);
          // Also get responsible from instructors array
          if (!responsibleInstructorId && inst?.role === 'responsible') {
            responsibleInstructorId = inst.id;
          }
        }
      });
    }

    // Add responsible if found
    if (responsibleInstructorId && responsibleInstructorId !== -1 && !involvedInstructors.includes(responsibleInstructorId)) {
      involvedInstructors.push(responsibleInstructorId);
    }

    // Track each instructor at this timeslot
    involvedInstructors.forEach((instructorId) => {
      if (instructorId === -1) return;

      if (!instructorTimeslotMap.has(instructorId)) {
        instructorTimeslotMap.set(instructorId, new Map());
      }

      const timeslotMap = instructorTimeslotMap.get(instructorId)!;
      if (!timeslotMap.has(schedule.timeslot_id)) {
        timeslotMap.set(schedule.timeslot_id, []);
      }

      timeslotMap.get(schedule.timeslot_id)!.push(schedule);
    });
  });

  // Find conflicts (instructor has multiple schedules at the same timeslot)
  instructorTimeslotMap.forEach((timeslotMap, instructorId) => {
    timeslotMap.forEach((schedulesAtSlot, timeslotId) => {
      if (schedulesAtSlot.length > 1) {
        // Found a conflict - this instructor has multiple duties at the same time
        const classroomIds = schedulesAtSlot.map(s => s.classroom_id).filter(Boolean);
        const uniqueClassroomIds = Array.from(new Set(classroomIds));

        // Only count as conflict if in different classrooms
        if (uniqueClassroomIds.length > 1) {
          conflictCount += schedulesAtSlot.length - 1;

          conflictDetails.push({
            instructorId,
            instructorName: getInstructorNameById(instructorId),
            timeslotId,
            timeslotLabel: getTimeslotLabel(timeslotId),
            classroomIds: uniqueClassroomIds,
            classroomNames: uniqueClassroomIds.map(id => getClassroomNameById(id)),
            projectIds: schedulesAtSlot.map(s => s.project_id).filter(Boolean),
            projectNames: schedulesAtSlot.map(s => s.project?.title || `Proje ${s.project_id}`),
          });
        }
      }
    });
  });

  return {
    totalConflicts: conflictCount,
    instructorsWithConflicts: conflictDetails.length,
    conflictDetails: conflictDetails.sort((a, b) => a.timeslotId - b.timeslotId)
  };
};

// Tüm öğretim görevlilerinin detaylı iş yükünü hesapla (sorumlu + jüri)
const calculateAllInstructorWorkloads = (schedules: any[], instructors: any[]) => {
  const workloadMap = new Map<number, {
    responsibleCount: number;
    juryCount: number;
    totalCount: number;
    instructor: any;
  }>();

  // Önce tüm instructor'ları map'e ekle (Instructor -1 hariç)
  instructors.forEach((instructor: any) => {
    // Instructor -1'i dahil etme
    if (instructor.id === -1 || instructor.id === null || instructor.id === undefined) {
      return;
    }
    workloadMap.set(instructor.id, {
      responsibleCount: 0,
      juryCount: 0,
      totalCount: 0,
      instructor
    });
  });

  // Schedule'ları işle
  schedules.forEach((schedule: any) => {
    const responsibleId = schedule.responsible_instructor_id;

    // Sorumlu instructor'ı say (Instructor -1 hariç)
    if (responsibleId && responsibleId !== -1) {
      const workload = workloadMap.get(responsibleId);
      if (workload) {
        workload.responsibleCount += 1;
        workload.totalCount += 1;
      } else {
        // Eğer instructor bulunamazsa yeni kayıt oluştur (sadece geçerli ID'ler için)
        const instructor = instructors.find((i: any) => i.id === responsibleId && i.id !== -1);
        if (instructor) {
          workloadMap.set(responsibleId, {
            responsibleCount: 1,
            juryCount: 0,
            totalCount: 1,
            instructor: instructor
          });
        }
      }
    }

    // Jüri üyelerini say (Instructor -1 hariç)
    if (schedule.instructors && Array.isArray(schedule.instructors)) {
      schedule.instructors.forEach((inst: any) => {
        // String kontrolü: "[Araştırma Görevlisi]" placeholder'ını atla (iş yüküne dahil edilmez)
        if (typeof inst === 'string' && inst === '[Araştırma Görevlisi]') {
          return; // Placeholder'ı iş yükü hesaplamalarına dahil etme
        }

        // Placeholder kontrolü: is_placeholder veya id: -1
        if (inst?.is_placeholder === true || inst?.id === -1 || inst?.id === null || inst?.id === undefined) {
          return; // Instructor -1'i iş yükü hesaplamalarına dahil etme
        }

        const juryId = typeof inst === 'object' ? inst.id : inst;
        // Sorumlu dışındaki jüri üyelerini say (Instructor -1 hariç)
        if (juryId && juryId !== -1 && juryId !== responsibleId) {
          const workload = workloadMap.get(juryId);
          if (workload) {
            workload.juryCount += 1;
            workload.totalCount += 1;
          } else {
            // Eğer instructor bulunamazsa yeni kayıt oluştur (sadece geçerli ID'ler için)
            const instructor = instructors.find((i: any) => i.id === juryId && i.id !== -1);
            if (instructor) {
              workloadMap.set(juryId, {
                responsibleCount: 0,
                juryCount: 1,
                totalCount: 1,
                instructor: instructor
              });
            }
          }
        }
      });
    }
  });

  // Liste olarak döndür ve sırala (toplam yüküne göre azalan) - Instructor -1'i filtrele
  const workloadList = Array.from(workloadMap.values())
    .filter(item => item.instructor.id !== -1 && item.instructor.id !== null && item.instructor.id !== undefined)
    .map(item => ({
      instructorId: item.instructor.id,
      instructorName: item.instructor.name || item.instructor.full_name || `Instructor ${item.instructor.id}`,
      responsibleCount: item.responsibleCount,
      juryCount: item.juryCount,
      totalCount: item.totalCount
    }))
    .sort((a, b) => b.totalCount - a.totalCount);

  return workloadList;
};

const analyzeWorkloadDistribution = (schedules: any[], instructors: any[]) => {
  // calculateAllInstructorWorkloads kullanarak doğru iş yükünü al
  const allInstructorWorkloads = calculateAllInstructorWorkloads(schedules, instructors);

  // Sadece toplam yükü 0'dan büyük olan ve Instructor -1 olmayan instructor'ları al
  const workloadsWithLoad = allInstructorWorkloads.filter(w =>
    w.totalCount > 0 &&
    w.instructorId !== -1 &&
    w.instructorId !== null &&
    w.instructorId !== undefined
  );

  if (workloadsWithLoad.length === 0) {
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

  const workloadValues = workloadsWithLoad.map(w => w.totalCount);
  const maxWorkload = Math.max(...workloadValues);
  const minWorkload = Math.min(...workloadValues);
  const avgWorkload = workloadValues.reduce((a, b) => a + b, 0) / workloadValues.length;

  // Maksimum yüke sahip instructor(lar)ı bul
  const maxWorkloadInstructors = workloadsWithLoad
    .filter(w => w.totalCount === maxWorkload)
    .map(w => w.instructorName);

  // Minimum yüke sahip instructor(lar)ı bul
  const minWorkloadInstructors = workloadsWithLoad
    .filter(w => w.totalCount === minWorkload)
    .map(w => w.instructorName);

  return {
    maxWorkload,
    minWorkload,
    avgWorkload: Math.round(avgWorkload * 10) / 10,
    maxDifference: maxWorkload - minWorkload,
    totalInstructors: workloadsWithLoad.length,
    maxWorkloadInstructors,
    minWorkloadInstructors
  };
};

const analyzeClassroomChanges = (schedules: any[]) => {
  const instructorClassrooms = new Map<number, Set<number>>();
  let totalChanges = 0;
  let instructorsWithChanges = 0;

  schedules.forEach((schedule: any) => {
    // Responsible instructor'ı bul - schedule'dan veya project'ten
    let responsibleInstructorId = schedule.project?.responsible_instructor_id ||
      schedule.responsible_instructor_id;

    // Eğer schedule.instructors array'i varsa, ilk eleman (role:'responsible') responsible instructor
    if (!responsibleInstructorId && schedule.instructors && Array.isArray(schedule.instructors) && schedule.instructors.length > 0) {
      const firstInstructor = schedule.instructors[0];
      if (firstInstructor?.role === 'responsible' && firstInstructor?.id) {
        responsibleInstructorId = firstInstructor.id;
      }
    }

    // SADECE SORUMLU ÖĞRETİM ÜYESİ için sınıf değişimi kontrolü (Instructor -1 hariç)
    if (responsibleInstructorId && responsibleInstructorId !== -1 && schedule.classroom_id) {
      if (!instructorClassrooms.has(responsibleInstructorId)) {
        instructorClassrooms.set(responsibleInstructorId, new Set());
      }
      instructorClassrooms.get(responsibleInstructorId)!.add(schedule.classroom_id);
    }
  });

  instructorClassrooms.forEach((classrooms) => {
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
  const totalSchedules = data.totalSchedules || 0;

  // Çakışma cezası - Toplam schedule'a göre normalize edilmiş (max 25 puan)
  const totalConflicts = data.conflictAnalysis?.totalConflicts || 0;
  if (totalConflicts > 0 && totalSchedules > 0) {
    const conflictRate = totalConflicts / totalSchedules;
    score -= Math.min(conflictRate * 50, 25);
  }

  // Yük dağılımı cezası - Daha toleranslı (max 20 puan)
  const maxDifference = data.workloadAnalysis?.maxDifference || 0;
  if (maxDifference > 2) {
    const penalty = Math.min((maxDifference - 2) * 3, 20);
    score -= penalty;
  }

  // Sınıf değişimi cezası - Daha düşük (max 15 puan)
  if (data.classroomChangeAnalysis?.instructorsWithChanges > 0 && data.classroomChangeAnalysis?.totalInstructors > 0) {
    const changeRate = data.classroomChangeAnalysis.instructorsWithChanges / data.classroomChangeAnalysis.totalInstructors;
    score -= Math.min(changeRate * 30, 15);
  }

  // Atanmamış proje cezası - Orantılı ama makul (max 30 puan)
  if (data.unassignedProjects > 0 && data.totalProjects > 0) {
    const unassignedRate = data.unassignedProjects / data.totalProjects;
    score -= Math.min(unassignedRate * 40, 30);
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
  // Manuel düzenleme için state'ler
  const [editableResponsibleId, setEditableResponsibleId] = useState<number | ''>('');
  const [editableJuryIds, setEditableJuryIds] = useState<number[]>([]);
  // Drag-and-drop için state
  const [draggedSchedule, setDraggedSchedule] = useState<any>(null);
  const [dragOverCell, setDragOverCell] = useState<string | null>(null);

  // Dialog açıldığında state'leri initialize et
  useEffect(() => {
    if (openDialog && selectedTimeSlot?.project) {
      const sch = schedules.find((s: any) => s.id === selectedTimeSlot.scheduleId);
      const currentJury = sch ? getJuryForSchedule(sch) : [];
      const currentJuryIds = currentJury.map((j: any) => j.id).filter((id: number) => id !== -1);

      setEditableResponsibleId(selectedTimeSlot.project.responsible_instructor_id || '');
      setEditableJuryIds(currentJuryIds);
    } else if (!openDialog) {
      // Dialog kapandığında state'leri temizle
      setEditableResponsibleId('');
      setEditableJuryIds([]);
    }
  }, [openDialog, selectedTimeSlot, schedules]);
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
    let juryFromSchedule: Array<{ id: number, name: string, role: string }> = [];

    try {
      // Schedule'dan project verisini al (sorumlu hocayı kontrol etmek için)
      const proj = schedule?.project || projects.find((p: any) => p.id === schedule?.project_id);

      // SADECE algoritmanın ürettiği gerçek jüri üyelerini kullan (schedule.instructors)
      // Placeholder jürileri (assistant_instructors, advisor_id, co_advisor_id) tamamen kaldır
      if (schedule?.instructors && Array.isArray(schedule.instructors)) {
        // DEBUG: Log schedule data
        console.log('🔍 getJuryForSchedule DEBUG:', JSON.stringify({
          scheduleId: schedule?.id,
          projectId: schedule?.project_id,
          instructors: schedule?.instructors,
          instructorsCount: schedule?.instructors?.length || 0
        }, null, 2));

        // DEBUG: Detailed instructor analysis
        console.log('🔍 Detailed Instructor Analysis:', {
          scheduleId: schedule?.id,
          projectId: schedule?.project_id,
          instructorsArray: schedule?.instructors,
          instructorsLength: schedule?.instructors?.length,
          firstInstructor: schedule?.instructors?.[0],
          secondInstructor: schedule?.instructors?.[1],
          thirdInstructor: schedule?.instructors?.[2]
        });

        // Sadece jüri üyelerini dahil et (sorumlu hariç)
        // ÖNCELİK: Backend'den gelen role field'ını kullan (daha güvenilir)
        // Fallback: Eğer role yoksa, responsibleId ile karşılaştır
        const responsibleId = proj?.responsible_instructor_id;
        schedule.instructors
          .filter((inst: any) => {
            // String kontrolü: "[Araştırma Görevlisi]" placeholder'ı için
            if (typeof inst === 'string' && inst === '[Araştırma Görevlisi]') {
              return true; // J2 placeholder'ı her zaman dahil et
            }

            // Object kontrolü
            if (typeof inst === 'object') {
              // Placeholder kontrolü: is_placeholder veya id: -1 veya name: '[Araştırma Görevlisi]'
              if (inst?.is_placeholder === true ||
                inst?.id === -1 ||
                inst?.name === '[Araştırma Görevlisi]') {
                return true; // J2 placeholder'ı her zaman dahil et
              }

              // Öncelik: role field'ını kontrol et (backend'den geliyor)
              if (inst?.role === 'jury') {
                return true; // Jüri üyesi
              }
              if (inst?.role === 'responsible') {
                return false; // Sorumlu - hariç tut
              }
              // Fallback: role yoksa eski mantık (responsibleId ile karşılaştır)
              return inst.id && inst.id !== responsibleId;
            }

            return false;
          })
          .forEach((inst: any) => {
            // String kontrolü: "[Araştırma Görevlisi]" placeholder'ı
            if (typeof inst === 'string' && inst === '[Araştırma Görevlisi]') {
              juryFromSchedule.push({
                id: -1,
                name: '[Araştırma Görevlisi]',
                role: 'Araştırma Görevlisi'
              });
              return;
            }

            // Object kontrolü
            if (typeof inst === 'object') {
              // Placeholder kontrolü: is_placeholder flag'i veya özel ID'ler
              const isPlaceholder = inst.is_placeholder === true ||
                inst.id === -1 ||
                inst.id === 'RA_PLACEHOLDER' ||
                inst.name === '[Araştırma Görevlisi]';

              // Gerçek öğretim üyeleri için 'Öğretim Üyesi', placeholder'lar için 'Araştırma Görevlisi'
              const displayRole = isPlaceholder ? 'Araştırma Görevlisi' : 'Öğretim Üyesi';

              // id kontrolü: -1 veya gerçek id olabilir
              const juryId = inst.id !== undefined ? inst.id : -1;

              juryFromSchedule.push({
                id: juryId,
                name: inst.full_name || inst.name || '[Araştırma Görevlisi]',
                role: displayRole
              });
            }
          });

        // DEBUG: Log jury result
        console.log('🎯 Jury result:', JSON.stringify({
          scheduleId: schedule?.id,
          juryCount: juryFromSchedule.length,
          juryMembers: juryFromSchedule
        }, null, 2));

        // DEBUG: Step-by-step jury filtering
        console.log('🔍 Step-by-step jury filtering:', {
          scheduleId: schedule?.id,
          allInstructors: schedule?.instructors,
          instructorsWithRoles: schedule?.instructors?.map((inst: any) => ({
            id: inst.id,
            role: inst.role,
            name: inst.name || inst.full_name
          })),
          responsibleId: proj?.responsible_instructor_id,
          filteredJuryByRole: schedule.instructors.filter((inst: any) => {
            if (inst?.role === 'jury') return true;
            if (inst?.role === 'responsible') return false;
            return inst.id && inst.id !== proj?.responsible_instructor_id;
          }),
          finalJuryCount: juryFromSchedule.length,
          finalJuryMembers: juryFromSchedule.map(j => ({ id: j.id, name: j.name }))
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

  // --- Export to Excel (backend-generated .xlsx) ---
  const handleExportProgram = async () => {
    try {
      if (!schedules || schedules.length === 0) {
        setSnack({
          open: true,
          message: 'Henüz hiç program oluşturulmamış!',
          severity: 'warning',
        });
        return;
      }

      // Map for timeslot string → id
      const slotToId = new Map<string, number>();
      (timeslots || []).forEach((t: any) => {
        const key = `${String(t.start_time).slice(0, 5)}-${String(t.end_time).slice(0, 5)}`;
        if (t?.id) slotToId.set(key, t.id);
      });

      // Ensure deterministic order - use timeslots directly
      const orderedSlots: string[] =
        timeslots && timeslots.length > 0
          ? timeslots.map((t: any) => {
            const startTime = String(t.start_time).slice(0, 5);
            const endTime = String(t.end_time).slice(0, 5);
            return `${startTime}-${endTime}`;
          })
          : [
            '09:00-09:30',
            '09:30-10:00',
            '10:00-10:30',
            '10:30-11:00',
            '11:00-11:30',
            '11:30-12:00',
            '13:00-13:30',
            '13:30-14:00',
            '14:00-14:30',
            '14:30-15:00',
            '15:00-15:30',
            '15:30-16:00',
            '16:00-16:30',
            '16:30-17:00',
            '17:00-17:30',
            '17:30-18:00',
          ];

      // Respect selected classroom count, then sort by name
      const baseRooms = (classrooms || []).slice(0, selectedClassroomCount);
      const orderedRooms = baseRooms
        .slice()
        .sort((a: any, b: any) => String(a.name).localeCompare(String(b.name)));

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
        if (type === 'interim' || type === 'ara') return '#dc004e'; // Magenta
        return '#00796b'; // Teal
      };

      const findSchedule = (room: any, slotStr: string) => {
        const tsId = slotToId.get(slotStr);
        return (schedules || []).find((s: any) => {
          if (s.classroom_id !== room.id) return false;
          if (tsId && (s.timeslot_id === tsId || s?.timeslot?.id === tsId)) return true;
          if (s?.timeslot?.start_time && s?.timeslot?.end_time) {
            const key = `${String(s.timeslot.start_time).slice(0, 5)}-${String(
              s.timeslot.end_time,
            ).slice(0, 5)}`;
            return key === slotStr;
          }
          return false;
        });
      };

      // --- Build plannerData payload for backend ---
      const timeSlots = orderedSlots.map((slot) => slot.split('-')[0]); // "09:00-09:30" -> "09:00"
      const classesNames = orderedRooms.map((room) => String(room.name));

      const projectsPayload: any[] = [];

      for (const slotStr of orderedSlots) {
        const timeCode = slotStr.split('-')[0];
        for (const room of orderedRooms) {
          const sch = findSchedule(room, slotStr);
          if (!sch) continue;

          const projId = sch?.project_id || sch?.project?.id;
          const proj = projId ? (projects || []).find((p: any) => p.id === projId) : undefined;
          if (!proj) continue;

          const jury = getJuryForSchedule(sch) || [];
          const responsibleId = proj?.responsible_instructor_id || proj?.responsible_id;
          const responsibleName = responsibleId ? getInstructorName(responsibleId) : '';
          const projectTitle = proj.title || `Proje ${proj.id}`;

          // Use full names instead of codes
          const juryNames = jury.map((j: any) => j.name || '').filter(Boolean);

          const typeLabel = getTypeLabelExcel(proj);
          const colorCode = getProjectColorCode(proj);

          projectsPayload.push({
            class: String(room.name),
            time: timeCode,
            projectTitle: projectTitle, // Full project title
            type: typeLabel,
            responsible: responsibleName, // Full responsible name
            jury: juryNames, // Full jury member names
            color: colorCode,
          });
        }
      }

      // Build load distributions (Hoca / Arş Gör.) - using full names
      const allInstructorWorkloads = calculateAllInstructorWorkloads(schedules, instructors);
      const hocaLoad: Record<string, number> = {};
      const arsGorLoad: Record<string, number> = {};

      allInstructorWorkloads.forEach((item: any) => {
        const inst = (instructors || []).find((i: any) => i.id === item.instructorId);
        const isAssistant = (inst?.type || '').toString().toLowerCase() === 'assistant';
        const fullName = item.instructorName || '';
        if (!fullName) return;
        if (isAssistant) {
          arsGorLoad[fullName] = item.totalCount;
        } else {
          hocaLoad[fullName] = item.totalCount;
        }
      });

      const plannerData = {
        classes: classesNames,
        timeSlots,
        projects: projectsPayload,
        hocaLoad,
        arsGorLoad,
        title: 'BİLGİSAYAR ve BİTİRME Projesi Jüri Programı',
        date: new Date()
          .toLocaleDateString('tr-TR', { day: '2-digit', month: 'long', year: 'numeric' })
          .toUpperCase(),
      };

      const response = await api.post('/reports/export-planner-excel', plannerData, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      const disposition = (response.headers as any)?.['content-disposition'] as
        | string
        | undefined;
      let fileName = `juri_programi_${new Date().toISOString().slice(0, 10)}.xlsx`;
      if (disposition) {
        const match = /filename="?([^"]+)"?/i.exec(disposition);
        if (match && match[1]) {
          fileName = match[1];
        }
      }

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setSnack({ open: true, message: 'Excel çıktısı oluşturuldu', severity: 'success' });
    } catch (e: any) {
      console.error('Export error:', e);
      setSnack({
        open: true,
        message: e?.response?.data?.detail || 'Excel dışa aktarma sırasında hata oluştu',
        severity: 'error',
      });
    }
  };

  // Animated session card with Collapse effect
  const SessionCard: React.FC<{
    proj: any;
    jury: any[];
    color: string;
    onClick: () => void;
    delay?: number;
    scheduleId?: number;
    onDragStart?: (schedule: any) => void;
  }> = ({ proj, jury, color, onClick, delay = 0, scheduleId, onDragStart }) => {
    // Jüri sayısına göre dinamik boyut
    const hasJury = jury && jury.length > 0;
    const juryCount = hasJury ? jury.length : 0;
    const cardHeight = hasJury ? Math.max(120, 96 + (juryCount * 20)) : 96; // Jüri sayısına göre yükseklik

    const dragStartedRef = useRef(false);

    const handleDragStart = (e: React.DragEvent) => {
      if (!scheduleId || !proj) {
        e.preventDefault();
        return;
      }

      dragStartedRef.current = true;
      const schedule = schedules.find((s: any) => s.id === scheduleId);
      if (schedule && onDragStart) {
        console.log('🚀 Drag started:', { scheduleId: schedule.id, projectId: proj.id });
        onDragStart(schedule);
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.dropEffect = 'move';
        e.dataTransfer.setData('text/plain', JSON.stringify({
          scheduleId: schedule.id,
          projectId: proj.id
        }));
      }
    };

    const handleClick = (e: React.MouseEvent) => {
      // Drag işlemi sırasında onClick'i engelle
      if (!dragStartedRef.current) {
        onClick();
      }
      dragStartedRef.current = false;
    };

    return (
      <Box
        sx={{
          width: 220,
          minHeight: cardHeight,
          cursor: proj && scheduleId ? 'grab' : 'pointer',
          position: 'relative',
          m: 1,
          opacity: draggedSchedule?.id === scheduleId ? 0.5 : 1,
          transition: 'opacity 0.2s',
          userSelect: 'none',
          pointerEvents: 'auto' // Drag event'lerinin çalışması için
        }}
        onClick={handleClick}
        draggable={!!proj && !!scheduleId}
        onDragStart={handleDragStart}
        onDrag={(e: React.DragEvent) => {
          // Drag sırasında event'i durdurma - cell'e ulaşması için
        }}
        onDragEnd={() => {
          dragStartedRef.current = false;
          setDraggedSchedule(null);
          setDragOverCell(null);
        }}
      >
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
                pointerEvents: 'auto'
              }}
              onDragStart={(e) => {
                // Child element'lerin drag'ini engelle - sadece parent Box drag edilebilir
                if (e.target !== e.currentTarget && (e.target as HTMLElement).closest('button, [role="button"]')) {
                  e.preventDefault();
                  e.stopPropagation();
                }
              }}
            >
              {proj ? (
                <>
                  {/* Üst kısım: Proje bilgileri */}
                  <Box
                    sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, width: '100%' }}
                    draggable={false}
                    onDragStart={(e) => e.preventDefault()}
                  >
                    <Box
                      sx={{ width: 6, height: 48, bgcolor: color, borderRadius: 1, mt: 0.3, flexShrink: 0 }}
                      draggable={false}
                      onDragStart={(e) => e.preventDefault()}
                    />
                    <Box
                      sx={{ flex: 1, minWidth: 0 }}
                      draggable={false}
                      onDragStart={(e) => e.preventDefault()}
                    >
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
                    <Box
                      sx={{ display: 'flex', gap: 0.5 }}
                      draggable={false}
                      onDragStart={(e) => e.preventDefault()}
                      onMouseDown={(e) => e.stopPropagation()} // IconButton'lara tıklamayı engelleme
                    >
                      <Tooltip title="Projeyi görüntüle" arrow>
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            onClick();
                          }}
                          aria-label="Projeyi görüntüle"
                          onMouseDown={(e) => e.stopPropagation()}
                          draggable={false}
                          onDragStart={(e) => e.preventDefault()}
                        >
                          <Info fontSize="inherit" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Projeyi düzenle" arrow>
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            onClick();
                          }}
                          aria-label="Projeyi düzenle"
                          onMouseDown={(e) => e.stopPropagation()}
                          draggable={false}
                          onDragStart={(e) => e.preventDefault()}
                        >
                          <Edit fontSize="inherit" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>

                  {/* Alt kısım: Jüri üyeleri */}
                  {hasJury && (
                    <Box
                      sx={{ mt: 0.5, pt: 0.5, borderTop: '1px solid', borderColor: 'divider' }}
                      draggable={false}
                      onDragStart={(e) => e.preventDefault()}
                    >
                      <Typography variant="caption" sx={{ fontSize: '0.7rem', color: 'text.secondary', fontWeight: 600, mb: 0.5, display: 'block' }}>
                        🎯 Jüri Üyeleri:
                      </Typography>
                      <Box
                        sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}
                        draggable={false}
                        onDragStart={(e) => e.preventDefault()}
                      >
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
                              draggable={false}
                              onDragStart={(e) => e.preventDefault()}
                            >
                              • {juryMember.name}
                            </Typography>
                          </Tooltip>
                        ))}
                        {jury.length > 3 && (
                          <Typography
                            variant="caption"
                            sx={{ fontSize: '0.65rem', color: 'text.disabled', fontStyle: 'italic' }}
                            draggable={false}
                            onDragStart={(e) => e.preventDefault()}
                          >
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
    } catch { }
  }, []);

  // Load classroom count from localStorage
  useEffect(() => {
    try {
      const savedClassroomCount = localStorage.getItem('selected_classroom_count');
      if (savedClassroomCount) {
        setSelectedClassroomCount(Number(savedClassroomCount));
      }
    } catch { }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem('planner_overlays', JSON.stringify(calendarOverlays));
    } catch { }
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
    } catch (e) { }
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
      } catch { }
    }

    // 3) Yine bulunamazsa, standart slotları seed et ve tekrar dene (superuser için)
    if (!found) {
      try {
        await api.post('/timeslots/seed-standard');
        const res2 = await api.get('/timeslots/');
        source = res2.data || [];
        setTimeslots(source);
        found = matchFrom(source);
      } catch { }
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
      } catch { }
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
          } catch (e) { }
          finally { localStorage.removeItem('planner_refresh'); }
        })();
      }
    } catch { }
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

            const toKey = (t: any) => `${String(t.start_time).slice(0, 5)}-${String(t.end_time).slice(0, 5)}`;
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
              try { localStorage.setItem('planner_overlays', JSON.stringify(overlaysTemp)); } catch { }
            }
          }
        } catch { }
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
    <Paper sx={{ p: 3, overflow: 'hidden' }}>
      <Box sx={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', mb: 3, width: '100%', flexWrap: 'wrap', gap: 2 }}>
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
                    .sort(([, a], [, b]) => (b as number) - (a as number))
                    .slice(0, 5);

                  // Detaylı analizler
                  const conflictAnalysis = calculateConflicts(schedules, instructors, classrooms, timeslots);
                  const workloadAnalysis = analyzeWorkloadDistribution(schedules, instructors);
                  const classroomChangeAnalysis = analyzeClassroomChanges(schedules);
                  const allInstructorWorkloads = calculateAllInstructorWorkloads(schedules, instructors);

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
                    programDistribution: uniqueProjects > 0 ? (totalSchedules / uniqueProjects).toFixed(2) : '0.00',
                    classroomUsage: uniqueClassrooms > 0 ? (totalSchedules / uniqueClassrooms).toFixed(2) : '0.00',
                    // Yeni detaylı analizler
                    conflictAnalysis,
                    workloadAnalysis,
                    classroomChangeAnalysis,
                    allInstructorWorkloads, // Tüm öğretim görevlilerinin detaylı iş yükü
                    satisfactionScore,
                    totalProjects: projects.length,
                    assignedProjects: uniqueProjects, // Benzersiz atanmış proje sayısı
                    unassignedProjects: projects.length - uniqueProjects, // Toplam - atanmış
                    utilizationRate: projects.length > 0 ? Math.round((uniqueProjects / projects.length) * 100 * 10) / 10 : 0
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
              for (const s of all) { try { await api.delete(`/schedules/${s.id}`); } catch { } }
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
      <Box sx={{ width: '100%', pb: 2, overflowX: 'auto' }}>
        <Box sx={{
          display: 'grid',
          gridTemplateColumns: `100px repeat(${filteredClassrooms.length}, minmax(220px, 1fr))`,
          gridAutoRows: 'minmax(96px, auto)',
          gap: 1,
          minWidth: `${100 + (filteredClassrooms.length * 220)}px`,
        }}>
          {/* Header row */}
          <Box sx={{ position: 'sticky', top: 0, zIndex: 5, bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', p: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>Zaman</Typography>
          </Box>
          {filteredClassrooms.map((room) => (
            <Box key={`hdr-${room.id}`} sx={{ position: 'sticky', top: 0, zIndex: 5, bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, p: 1 }}>
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
                const ts = timeslots.find((t: any) => `${String(t.start_time).slice(0, 5)}-${String(t.end_time).slice(0, 5)}` === slot);
                const existing = (schedules || []).find((s: any) => {
                  if (s.classroom_id !== room.id) return false;
                  if (ts?.id) return s.timeslot_id === ts.id || s.timeslot?.id === ts.id;
                  if (s?.timeslot?.start_time && s?.timeslot?.end_time) {
                    const key = `${String(s.timeslot.start_time).slice(0, 5)}-${String(s.timeslot.end_time).slice(0, 5)}`;
                    return key === slot;
                  }
                  return false;
                });

                // Debug: Log when we find a match
                if (existing) {
                  console.log('🎯 Found schedule match:', JSON.stringify({ room: room.name, slot, existing }, null, 2));
                }
                const [startTime, endTime] = slot.split('-');
                const ov = calendarOverlays.find((o: any) => o.classroom === room.name && o.startTime === startTime && o.endTime === endTime);
                const proj = existing ? (projects.find((p: any) => p.id === existing.project_id) || (existing as any).project) : ov?.project;
                const jury = existing ? getJuryForSchedule(existing) : [];
                const color = getProjectColor(proj);
                const delay = roomIndex * 100; // Her sınıf için 100ms gecikme
                const cellKey = `${room.id}-${slot}`;
                const isDragOver = dragOverCell === cellKey;

                const handleDragEnter = (e: React.DragEvent) => {
                  e.preventDefault();
                  e.stopPropagation();
                  if (!existing && draggedSchedule) {
                    console.log('📥 Drag enter:', cellKey, { room: room.name, slot });
                    setDragOverCell(cellKey);
                  }
                };

                const handleDragOver = (e: React.DragEvent) => {
                  e.preventDefault();
                  e.stopPropagation();

                  if (!existing && draggedSchedule) {
                    // Sadece boş cell'lere drop edilebilir
                    e.dataTransfer.dropEffect = 'move';
                    if (dragOverCell !== cellKey) {
                      setDragOverCell(cellKey);
                    }
                  } else {
                    e.dataTransfer.dropEffect = 'none';
                  }
                };

                const handleDragLeave = (e: React.DragEvent) => {
                  // Sadece gerçekten cell'den çıkıldığında tetikle
                  // (child element'lere geçildiğinde tetiklenmemesi için)
                  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
                  const x = e.clientX;
                  const y = e.clientY;

                  // Eğer hala cell içindeyse, dragLeave'i yok say
                  if (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom) {
                    return;
                  }

                  if (dragOverCell === cellKey) {
                    console.log('📤 Drag leave:', cellKey);
                    setDragOverCell(null);
                  }
                };

                const handleDrop = async (e: React.DragEvent) => {
                  e.preventDefault();
                  e.stopPropagation();
                  console.log('🎯 Drop event:', cellKey, { draggedSchedule, existing, room: room.name, slot });
                  setDragOverCell(null);

                  if (!draggedSchedule) {
                    console.log('❌ No dragged schedule');
                    return;
                  }

                  if (existing) {
                    console.log('❌ Cell already has a project');
                    return; // Zaten bir proje varsa drop edilemez
                  }

                  try {
                    console.log('🔄 Starting drop operation...');
                    // Zaman dilimini database'den bul
                    const ts = await resolveDbTimeslot(startTime, endTime);
                    if (!ts?.id || !room?.id) {
                      console.error('❌ Timeslot or room not found:', { ts, room });
                      setSnack({ open: true, message: 'Zaman veya sınıf bulunamadı', severity: 'error' });
                      return;
                    }

                    console.log('✅ Found timeslot and room:', { timeslotId: ts.id, roomId: room.id });

                    // Schedule'ı güncelle
                    const updatePayload = {
                      classroom_id: room.id,
                      timeslot_id: ts.id
                    };

                    console.log('📤 Updating schedule:', { scheduleId: draggedSchedule.id, payload: updatePayload });
                    await api.put(`/schedules/${draggedSchedule.id}`, updatePayload);

                    // Verileri yenile
                    const refreshed = await api.get('/schedules/');
                    setSchedules(refreshed.data || []);

                    console.log('✅ Schedule updated successfully');
                    setSnack({ open: true, message: 'Proje taşındı', severity: 'success' });
                    setDraggedSchedule(null);
                  } catch (e: any) {
                    console.error('❌ Drop error:', e);
                    setSnack({ open: true, message: e?.response?.data?.detail || 'Taşıma başarısız', severity: 'error' });
                    setDraggedSchedule(null);
                  }
                };

                return (
                  <Box
                    key={cellKey}
                    sx={{
                      position: 'relative',
                      border: '2px dashed',
                      borderColor: isDragOver ? 'primary.main' : 'divider',
                      borderRadius: 2,
                      minHeight: 96,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      bgcolor: isDragOver ? 'primary.light' : 'transparent',
                      transition: 'all 0.2s',
                      pointerEvents: 'auto' // Drop event'lerinin çalışması için
                    }}
                    onDragEnter={handleDragEnter}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    {proj ? (
                      <SessionCard
                        proj={proj}
                        jury={jury}
                        color={color}
                        onClick={() => handleTimeSlotClick(slot, room.name, proj, (existing as any)?.id)}
                        delay={delay}
                        scheduleId={(existing as any)?.id}
                        onDragStart={setDraggedSchedule}
                      />
                    ) : (
                      // Boş cell için drop zone göster
                      <Box
                        sx={{
                          width: '100%',
                          height: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          minHeight: 96,
                          pointerEvents: 'none' // Text'in drag event'lerini engelle
                        }}
                      >
                        <Typography variant="caption" sx={{ color: isDragOver ? 'primary.main' : 'text.secondary', fontWeight: isDragOver ? 600 : 400 }}>
                          {isDragOver ? 'Bırakın' : 'Boş'}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                );
              })}
            </React.Fragment>
          ))}
        </Box>
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
                acc[`${String(ts?.start_time).slice(0, 5)}-${String(ts?.end_time).slice(0, 5)}`] = s;
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
    <Box sx={{ width: '100%', overflow: 'hidden' }}>



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

                  {/* Sorumlu Öğretim Üyesi - Editable */}
                  <TextField
                    select
                    label="Sorumlu Öğretim Üyesi"
                    fullWidth
                    value={editableResponsibleId || selectedTimeSlot.project.responsible_instructor_id || ''}
                    onChange={(e) => setEditableResponsibleId(Number(e.target.value) || '')}
                    helperText="Sorumlu öğretim üyesini değiştirebilirsiniz"
                  >
                    {instructors.filter((i: any) => i.type === 'instructor').map((inst: any) => (
                      <MenuItem key={inst.id} value={inst.id}>
                        {inst.name}
                      </MenuItem>
                    ))}
                  </TextField>

                  {/* Jüri Üyeleri - Editable (Multi-select) */}
                  <TextField
                    select
                    label="Jüri Üyeleri"
                    fullWidth
                    SelectProps={{
                      multiple: true,
                      value: editableJuryIds.length > 0 ? editableJuryIds : (() => {
                        const sch = schedules.find((s: any) => s.id === selectedTimeSlot.scheduleId);
                        if (sch && sch.instructors) {
                          const juryFromSchedule = getJuryForSchedule(sch);
                          return juryFromSchedule.map((j: any) => j.id).filter((id: number) => id !== -1);
                        }
                        return [];
                      })(),
                      onChange: (e: any) => setEditableJuryIds(e.target.value),
                      renderValue: (selected: any) => {
                        if (!selected || selected.length === 0) return 'Jüri üyesi seçin';
                        return selected.map((id: number) => {
                          const inst = instructors.find((i: any) => i.id === id);
                          return inst ? inst.name : `ID: ${id}`;
                        }).join(', ');
                      }
                    }}
                    helperText="Jüri üyelerini seçebilirsiniz (Çoklu seçim)"
                  >
                    {instructors.filter((i: any) => i.type === 'instructor' && i.id !== (editableResponsibleId || selectedTimeSlot.project.responsible_instructor_id)).map((inst: any) => (
                      <MenuItem key={inst.id} value={inst.id}>
                        {inst.name}
                      </MenuItem>
                    ))}
                  </TextField>
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
                    {projects.filter((p: any) => p.id !== selectedTimeSlot.project.id).map((p: any) => (
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
          <Button onClick={() => {
            setOpenDialog(false);
            setEditableResponsibleId('');
            setEditableJuryIds([]);
          }}>
            İptal
          </Button>
          {selectedTimeSlot?.project ? (
            <>
              {/* Kaydet Butonu - Manuel Düzenleme */}
              <Button
                variant="contained"
                color="primary"
                onClick={async () => {
                  try {
                    if (!selectedTimeSlot?.scheduleId) {
                      setSnack({ open: true, message: 'Schedule ID bulunamadı', severity: 'error' });
                      return;
                    }

                    const updatePayload: any = {};

                    // Sorumlu öğretim üyesi değiştiyse
                    if (editableResponsibleId && editableResponsibleId !== selectedTimeSlot.project.responsible_instructor_id) {
                      updatePayload.responsible_instructor_id = editableResponsibleId;
                    }

                    // Jüri üyeleri değiştiyse
                    const sch = schedules.find((s: any) => s.id === selectedTimeSlot.scheduleId);
                    const currentJury = sch ? getJuryForSchedule(sch) : [];
                    const currentJuryIds = currentJury.map((j: any) => j.id).filter((id: number) => id !== -1);

                    if (JSON.stringify(editableJuryIds.sort()) !== JSON.stringify(currentJuryIds.sort())) {
                      // Jüri üyelerini formatla: [responsible_id, jury1_id, jury2_id, ...]
                      // Responsible'ı ilk sıraya ekle
                      const responsibleId = editableResponsibleId || selectedTimeSlot.project.responsible_instructor_id;
                      const formattedInstructors = [
                        { id: responsibleId, role: 'responsible' },
                        ...editableJuryIds.map((id: number) => ({ id, role: 'jury' }))
                      ];
                      updatePayload.instructors = formattedInstructors;
                    }

                    // Eğer değişiklik varsa güncelle
                    if (Object.keys(updatePayload).length > 0) {
                      await api.put(`/schedules/${selectedTimeSlot.scheduleId}`, updatePayload);

                      // Verileri yenile
                      const refreshed = await api.get('/schedules/');
                      setSchedules(refreshed.data || []);

                      // Projects'i de yenile (responsible_id değişmiş olabilir)
                      const projectsRefreshed = await api.get('/projects/');
                      setProjects(projectsRefreshed.data || []);

                      setSnack({ open: true, message: 'Değişiklikler kaydedildi', severity: 'success' });
                      setOpenDialog(false);
                      setEditableResponsibleId('');
                      setEditableJuryIds([]);
                    } else {
                      setSnack({ open: true, message: 'Değişiklik yapılmadı', severity: 'warning' });
                    }
                  } catch (e: any) {
                    setSnack({ open: true, message: e?.response?.data?.detail || 'Güncelleme yapılamadı', severity: 'error' });
                  }
                }}
              >
                Kaydet
              </Button>
              <Button color="error" onClick={async () => {
                try {
                  // mevcut programı kaldır
                  if (selectedTimeSlot?.scheduleId) {
                    await api.delete(`/schedules/${selectedTimeSlot.scheduleId}`);
                  }
                  const refreshed = await api.get('/schedules/');
                  setSchedules(refreshed.data || []);
                  setSnack({ open: true, message: 'Program kaldırıldı', severity: 'success' });
                  setOpenDialog(false);
                } catch (e: any) {
                  setSnack({ open: true, message: e?.response?.data?.detail || 'Program kaldırılamadı', severity: 'error' });
                }
              }}>Takvimden Kaldır</Button>
              <Button variant="contained" disabled={!selectedProjectId} onClick={async () => {
                try {
                  if (!selectedProjectId) return;
                  // Zaman dilimini backend'de bul
                  const ts = await resolveDbTimeslot(selectedTimeSlot.startTime, selectedTimeSlot.endTime);
                  const clsSan = (s: string) => (s || '').toLowerCase().replace(/\s|-/g, '');
                  const classroom = classrooms.find((c: any) => clsSan(c.name) === clsSan(selectedTimeSlot.classroom));
                  if (!ts?.id || !classroom?.id) { setSnack({ open: true, message: 'Zaman veya sınıf bulunamadı', severity: 'error' }); return; }
                  const payload: any = { project_id: selectedProjectId, classroom_id: classroom.id, timeslot_id: ts.id };
                  await api.post('/schedules/', { schedule_in: payload, instructor_ids: [] });
                  // eski programı kaldır
                  if (selectedTimeSlot?.scheduleId) {
                    try { await api.delete(`/schedules/${selectedTimeSlot.scheduleId}`); } catch { }
                  }
                  const refreshed = await api.get('/schedules/');
                  setSchedules(refreshed.data || []);
                  setSnack({ open: true, message: 'Proje değiştirildi', severity: 'success' });
                  setOpenDialog(false);
                  setSelectedProjectId('');
                } catch (e: any) {
                  setSnack({ open: true, message: e?.response?.data?.detail || 'Değişiklik yapılamadı', severity: 'error' });
                }
              }}>Bu seansa taşı</Button>
            </>
          ) : (
            <Button variant="contained" onClick={async () => {
              try {
                if (!selectedProjectId) return;
                // Zaman dilimini database'den bul
                const ts = await resolveDbTimeslot(selectedTimeSlot.startTime, selectedTimeSlot.endTime);
                const clsSan = (s: string) => (s || '').toLowerCase().replace(/\s|-/g, '');
                const classroom = classrooms.find((c: any) => clsSan(c.name) === clsSan(selectedTimeSlot.classroom));
                if (!selectedProjectId) { window.alert('Lütfen bir proje seçin'); return; }
                if (!ts?.id) { window.alert('Seçilen zaman dilimi sistemde bulunamadı'); return; }
                if (!classroom?.id) { window.alert('Seçilen sınıf sistemde bulunamadı'); return; }
                const payload: any = {
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
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 2, mb: performanceData.conflictAnalysis.totalConflicts > 0 ? 2 : 0 }}>
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
                      Çakışan Öğretim Üyesi
                    </Typography>
                  </Box>
                </Box>

                {/* Çakışma Detayları - Sadece çakışma varsa göster */}
                {performanceData.conflictAnalysis.totalConflicts > 0 &&
                  performanceData.conflictAnalysis.conflictDetails &&
                  performanceData.conflictAnalysis.conflictDetails.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" sx={{ mb: 1.5, color: 'error.main', fontWeight: 'bold' }}>
                        🚨 Çakışma Detayları:
                      </Typography>
                      <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 300 }}>
                        <Table size="small" stickyHeader>
                          <TableHead>
                            <TableRow>
                              <TableCell sx={{ fontWeight: 'bold', bgcolor: 'error.lighter' }}>Saat</TableCell>
                              <TableCell sx={{ fontWeight: 'bold', bgcolor: 'error.lighter' }}>Öğretim Üyesi</TableCell>
                              <TableCell sx={{ fontWeight: 'bold', bgcolor: 'error.lighter' }}>Çakışan Sınıflar</TableCell>
                              <TableCell sx={{ fontWeight: 'bold', bgcolor: 'error.lighter' }}>Projeler</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {performanceData.conflictAnalysis.conflictDetails.map((conflict: any, index: number) => (
                              <TableRow key={index} sx={{ '&:nth-of-type(odd)': { bgcolor: 'grey.50' } }}>
                                <TableCell>
                                  <Chip
                                    label={conflict.timeslotLabel}
                                    size="small"
                                    color="error"
                                    variant="outlined"
                                    sx={{ fontWeight: 'bold' }}
                                  />
                                </TableCell>
                                <TableCell>
                                  <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                                    {conflict.instructorName}
                                  </Typography>
                                </TableCell>
                                <TableCell>
                                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                    {conflict.classroomNames.map((name: string, idx: number) => (
                                      <Chip
                                        key={idx}
                                        label={name}
                                        size="small"
                                        variant="outlined"
                                        color="warning"
                                        sx={{ fontSize: '0.75rem' }}
                                      />
                                    ))}
                                  </Box>
                                </TableCell>
                                <TableCell>
                                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                                    {conflict.projectNames.slice(0, 2).join(', ')}
                                    {conflict.projectNames.length > 2 && ` +${conflict.projectNames.length - 2}`}
                                  </Typography>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Box>
                  )}

                {/* Çakışma yoksa başarı mesajı */}
                {performanceData.conflictAnalysis.totalConflicts === 0 && (
                  <Box sx={{
                    mt: 2,
                    p: 2,
                    bgcolor: 'success.lighter',
                    borderRadius: 1,
                    border: '1px solid',
                    borderColor: 'success.light',
                    textAlign: 'center'
                  }}>
                    <Typography variant="body1" color="success.main" sx={{ fontWeight: 'medium' }}>
                      ✅ Hiçbir öğretim üyesinin aynı anda birden fazla sınıfta görevi yok!
                    </Typography>
                  </Box>
                )}
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

              {/* Öğretim Görevlileri İş Yükü */}
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
                  👥 Öğretim Görevlileri İş Yükü
                </Typography>
                {performanceData.allInstructorWorkloads && performanceData.allInstructorWorkloads.length > 0 ? (
                  <TableContainer sx={{ bgcolor: 'white', borderRadius: 1, maxHeight: 400, overflow: 'auto' }}>
                    <Table size="small" stickyHeader>
                      <TableHead>
                        <TableRow>
                          <TableCell sx={{ fontWeight: 'bold', bgcolor: 'grey.100' }}>Öğretim Görevlisi</TableCell>
                          <TableCell align="center" sx={{ fontWeight: 'bold', bgcolor: 'grey.100' }}>Sorumlu</TableCell>
                          <TableCell align="center" sx={{ fontWeight: 'bold', bgcolor: 'grey.100' }}>Jüri</TableCell>
                          <TableCell align="center" sx={{ fontWeight: 'bold', bgcolor: 'grey.100' }}>Toplam</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {performanceData.allInstructorWorkloads
                          .filter((workload: any) => workload.instructorId !== -1 && workload.instructorId !== null && workload.instructorId !== undefined)
                          .map((workload: any, index: number) => {
                            // Renk belirleme: Ortalama yükün üstünde ise uyarı rengi
                            const avgWorkload = performanceData.workloadAnalysis.avgWorkload || 0;
                            const isAboveAverage = workload.totalCount > avgWorkload;
                            const isBelowAverage = workload.totalCount < avgWorkload && workload.totalCount > 0;

                            return (
                              <TableRow
                                key={workload.instructorId}
                                sx={{
                                  '&:nth-of-type(odd)': { bgcolor: 'grey.50' },
                                  '&:hover': { bgcolor: 'action.hover' }
                                }}
                              >
                                <TableCell sx={{ fontWeight: 500 }}>
                                  {workload.instructorName}
                                </TableCell>
                                <TableCell align="center">
                                  <Chip
                                    label={workload.responsibleCount}
                                    size="small"
                                    sx={{
                                      bgcolor: 'primary.lighter',
                                      color: 'primary.main',
                                      fontWeight: 'bold'
                                    }}
                                  />
                                </TableCell>
                                <TableCell align="center">
                                  <Chip
                                    label={workload.juryCount}
                                    size="small"
                                    sx={{
                                      bgcolor: 'secondary.lighter',
                                      color: 'secondary.main',
                                      fontWeight: 'bold'
                                    }}
                                  />
                                </TableCell>
                                <TableCell align="center">
                                  <Chip
                                    label={workload.totalCount}
                                    size="small"
                                    color={isAboveAverage ? 'warning' : isBelowAverage ? 'info' : 'success'}
                                    sx={{ fontWeight: 'bold' }}
                                  />
                                </TableCell>
                              </TableRow>
                            );
                          })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                    İş yükü bilgisi bulunamadı
                  </Typography>
                )}
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