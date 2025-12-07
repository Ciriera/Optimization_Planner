import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  LinearProgress,
  Alert,
  IconButton,
  Menu,
  MenuItem,
  Divider,
  Avatar,
  Stack,
  CircularProgress,
  CardHeader,
  Tooltip,
} from '@mui/material';
import {
  Assessment,
  PictureAsPdf,
  FileDownload,
  TableChart,
  BarChart,
  PieChart,
  TrendingUp,
  Person,
  Assignment,
  CheckCircle,
  Warning,
  Error,
  Info,
  Visibility,
  Print,
  Share,
  Refresh,
  Work,
  Timeline,
  School,
  People,
  Schedule,
  Speed,
  Analytics,
} from '@mui/icons-material';
import { api } from '../services/authService';

const Results: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<any[]>([]);
  const [schedules, setSchedules] = useState<any[]>([]);
  const [instructors, setInstructors] = useState<any[]>([]);
  const [workloads, setWorkloads] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [error, setError] = useState<string>('');

  // Proje türü fonksiyonları - Planner.tsx'teki gibi
  const getProjectTypeLabel = (project: any) => {
    // Önce project_type alanını kontrol et, sonra type alanını
    const type = (project?.project_type || project?.type || '').toString().toLowerCase();
    if (type === 'final' || type === 'bitirme') return 'Bitirme';
    if (type === 'interim' || type === 'ara') return 'Ara';
    return 'Proje';
  };

  const getProjectTypeColor = (project: any) => {
    // Önce project_type alanını kontrol et, sonra type alanını
    const type = (project?.project_type || project?.type || '').toString().toLowerCase();
    if (type === 'final' || type === 'bitirme') return 'primary';
    if (type === 'interim' || type === 'ara') return 'secondary';
    return 'default';
  };

  const getInstructorName = (instructorId: number) => {
    if (!instructorId) return '';
    const instructor = instructors.find((i: any) => i.id === instructorId);
    return instructor?.full_name || instructor?.name || `Hoca ${instructorId}`;
  };

  // Proje türü sayma fonksiyonları
  const getBitirmeCount = () => {
    return projects.filter(p => {
      const type = (p?.project_type || p?.type || '').toString().toLowerCase();
      return type === 'final' || type === 'bitirme';
    }).length;
  };

  const getAraCount = () => {
    return projects.filter(p => {
      const type = (p?.project_type || p?.type || '').toString().toLowerCase();
      return type === 'interim' || type === 'ara';
    }).length;
  };

  // Performance data hesaplama fonksiyonu
  const calculatePerformanceData = (schedules: any[], projects: any[], instructors: any[], timeslots: any[], classrooms: any[]) => {
    console.log('Performance Debug: calculatePerformanceData called with:', {
      schedules: schedules.length,
      projects: projects.length,
      instructors: instructors.length,
      timeslots: timeslots.length,
      classrooms: classrooms.length
    });

    // Zaman analizi - Gerçek hesaplama
    const timeSlotUsage = new Map();
    schedules.forEach((schedule: any) => {
      if (schedule.timeslot_id) {
        const timeslot = timeslots.find((t: any) => t.id === schedule.timeslot_id);
        if (timeslot) {
          const timeKey = `${timeslot.start_time}-${timeslot.end_time}`;
          timeSlotUsage.set(timeKey, (timeSlotUsage.get(timeKey) || 0) + 1);
        }
      }
    });

    const activeTimeSlots = timeSlotUsage.size;
    const totalTimeSlots = timeslots.length > 0 ? timeslots.length : 16;
    const usageRate = totalTimeSlots > 0 ? Math.round((activeTimeSlots / totalTimeSlots) * 100) : 0;
    
    // Slot başına ortalama yük - aktif slot sayısı 0 ise 0, değilse toplam program / aktif slot
    const avgLoadPerSlot = activeTimeSlots > 0 ? Math.round((schedules.length / activeTimeSlots) * 10) / 10 : 0;
    
    console.log('Performance Debug - Slot Başına Ortalama Yük:', {
      schedulesLength: schedules.length,
      activeTimeSlots,
      totalTimeSlots,
      avgLoadPerSlot,
      timeSlotUsageEntries: Array.from(timeSlotUsage.entries())
    });

    // En yoğun zaman slotları
    const topTimeSlots = Array.from(timeSlotUsage.entries())
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5);

    // En yoğun zaman slotu
    const mostUsedTimeslot = topTimeSlots.length > 0 ? {
      time: topTimeSlots[0][0],
      count: topTimeSlots[0][1]
    } : null;

    // Sınıf kullanım analizi
    const classroomUsage = new Map();
    schedules.forEach((schedule: any) => {
      if (schedule.classroom_id) {
        const classroom = classrooms.find(c => c.id === schedule.classroom_id);
        const classroomName = classroom?.name || `Sınıf ${schedule.classroom_id}`;
        const count = classroomUsage.get(classroomName) || 0;
        classroomUsage.set(classroomName, count + 1);
      }
    });

    // En yoğun sınıf
    const mostUsedClassroom = classroomUsage.size > 0 ? 
      Array.from(classroomUsage.entries())
        .sort(([,a], [,b]) => b - a)[0] : null;

    const timeAnalysis = {
      activeTimeSlots,
      totalTimeSlots,
      usageRate,
      avgLoadPerSlot
    };

    // Proje türü analizi
    const projectTypeAnalysis = projects.reduce((acc: any, project: any) => {
      const projectType = (project?.project_type || project?.type || '').toString().toLowerCase();
      let type = 'Ara'; // Default
      
      if (projectType === 'final' || projectType === 'bitirme') {
        type = 'Bitirme';
      } else if (projectType === 'interim' || projectType === 'ara') {
        type = 'Ara';
      }
      
      if (!acc[type]) {
        acc[type] = 0;
      }
      acc[type]++;
      return acc;
    }, {});

    // Kalite metrikleri - Gerçek hesaplama
    const programProjectRatio = projects.length > 0 ? Math.round((schedules.length / projects.length) * 100) / 100 : 0;
    const programClassroomRatio = classrooms.length > 0 ? Math.round((schedules.length / classrooms.length) * 100) / 100 : 0;
    const utilizationRate = projects.length > 0 ? Math.round((schedules.length / projects.length) * 100) : 0;

    const qualityMetrics = {
      programProjectRatio,
      programClassroomRatio,
      utilizationRate
    };

    // Çakışma analizi - Schedule verilerinden direkt hesaplama (Planner ile aynı mantık)
    const conflictAnalysis = calculateConflictsDetailed(schedules);
    const conflictCount = conflictAnalysis.totalConflicts;

    // Yük dağılımı analizi - Planner'daki mantıkla hesaplama
    const workloadAnalysis = analyzeWorkloadDistributionDetailed(schedules, instructors);
    
    // En yoğun ve en az yoğun öğretim üyesini bul
    const workloadMap = new Map<number, number>();
    schedules.forEach((schedule: any) => {
      if (schedule.instructors && Array.isArray(schedule.instructors)) {
        schedule.instructors.forEach((instructor: any) => {
          if (instructor && !instructor.is_placeholder && instructor.id && instructor.id !== -1) {
            const count = workloadMap.get(instructor.id) || 0;
            workloadMap.set(instructor.id, count + 1);
          }
        });
      }
    });
    
    const mostBusyInstructor = workloadMap.size > 0 ? 
      Array.from(workloadMap.entries()).sort(([,a], [,b]) => b - a)[0] : null;
    const minWorkloadInstructor = workloadMap.size > 0 ? 
      Array.from(workloadMap.entries()).sort(([,a], [,b]) => a - b)[0] : null;

    // Sınıf değişimi analizi - Planner'daki mantıkla hesaplama
    const classroomChangeAnalysis = analyzeClassroomChangesDetailed(schedules);

    // Atama durumu
    const assignmentStatus = {
      totalProjects: projects.length,
      assignedProjects: schedules.length,
      unassignedProjects: projects.length - schedules.length
    };

    // Memnuniyet skoru - Planner'daki mantıkla hesaplama
    const satisfactionScore = calculateSatisfactionScoreDetailed({
      totalSchedules: schedules.length,
      conflictAnalysis,
      workloadAnalysis,
      classroomChangeAnalysis,
      unassignedProjects: assignmentStatus.unassignedProjects,
      totalProjects: assignmentStatus.totalProjects
    });

    console.log('Performance Debug: Calculated data:', {
      timeAnalysis,
      qualityMetrics,
      conflictAnalysis,
      workloadAnalysis,
      classroomChangeAnalysis,
      assignmentStatus,
      satisfactionScore
    });
    

    return {
      totalSchedules: schedules.length,
      uniqueProjects: new Set(schedules.map(s => s.project_id)).size,
      uniqueInstructors: instructors.length,
      uniqueClassrooms: new Set(schedules.map(s => s.classroom_id)).size,
      // Zaman analizi - renderPerformanceTab için uyumlu alanlar
      timeSlots: timeAnalysis.activeTimeSlots,
      totalTimeSlots: timeAnalysis.totalTimeSlots,
      avgLoadPerSlot: timeAnalysis.avgLoadPerSlot,
      usageRate: timeAnalysis.usageRate,
      topTimeSlots: topTimeSlots,
      mostUsedTimeslot: mostUsedTimeslot,
      mostUsedClassroom: mostUsedClassroom ? {
        name: mostUsedClassroom[0],
        count: mostUsedClassroom[1]
      } : null,
      mostBusyInstructor: mostBusyInstructor ? {
        name: instructors.find(i => i.id === mostBusyInstructor[0])?.full_name || 
              instructors.find(i => i.id === mostBusyInstructor[0])?.name || 
              `Hoca ${mostBusyInstructor[0]}`,
        count: mostBusyInstructor[1]
      } : null,
      minWorkloadInstructor: minWorkloadInstructor ? {
        name: instructors.find(i => i.id === minWorkloadInstructor[0])?.full_name || 
              instructors.find(i => i.id === minWorkloadInstructor[0])?.name || 
              `Hoca ${minWorkloadInstructor[0]}`,
        count: minWorkloadInstructor[1]
      } : null,
      // Kalite metrikleri - renderPerformanceTab için uyumlu alanlar
      programDistribution: qualityMetrics.programProjectRatio,
      classroomUsage: qualityMetrics.programClassroomRatio,
      utilizationRate: qualityMetrics.utilizationRate,
      // Atama durumu - renderPerformanceTab için uyumlu alanlar
      totalProjects: assignmentStatus.totalProjects,
      assignedProjects: assignmentStatus.assignedProjects,
      unassignedProjects: assignmentStatus.unassignedProjects,
      // Detaylı analizler
      timeAnalysis,
      qualityMetrics,
      conflictAnalysis,
      workloadAnalysis,
      classroomChangeAnalysis,
      assignmentStatus,
      satisfactionScore,
      projectTypeAnalysis
    };
  };

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      // Gerçek verileri çek
      const [projectsRes, schedulesRes, instructorsRes, algorithmsRes] = await Promise.all([
        api.get('/projects/'),
        api.get('/schedules/'),
        api.get('/instructors/'),
        api.get('/algorithms/list'),
      ]);
      
      const projectsData = projectsRes.data || [];
      const schedulesData = schedulesRes.data || [];
      const instructorsData = instructorsRes.data || [];
      const algorithmsData = algorithmsRes.data || [];
      
      // Son çalıştırılan algoritma run'ını al
      let lastAlgorithmRun = null;
      try {
        const algorithmRunsRes = await api.get('/algorithms/runs');
        const algorithmRuns = algorithmRunsRes.data || [];
        if (algorithmRuns.length > 0) {
          // En son completed olan run'ı al
          lastAlgorithmRun = algorithmRuns
            .filter((run: any) => run.status === 'completed')
            .sort((a: any, b: any) => new Date(b.completed_at || b.started_at).getTime() - new Date(a.completed_at || a.started_at).getTime())[0];
        }
      } catch (err) {
        console.log('Algorithm runs fetch failed:', err);
      }
      
      setProjects(projectsData);
      setSchedules(schedulesData);
      setInstructors(instructorsData);
      
      // Projeleri schedules ile birleştir ve jüri bilgilerini ekle
      const projectsWithDetails = projectsData.map((project: any) => {
        const schedule = schedulesData.find((s: any) => s.project_id === project.id);
        const responsibleInstructor = instructorsData.find((i: any) => i.id === project.responsible_instructor_id);
        const assistantInstructors = project.assistant_instructors || [];
        
        // Jüri üyelerini birleştir - schedule.instructors'dan al (jury refinement sonucu)
        let juryMembers = [];
        
        if (schedule?.instructors && Array.isArray(schedule.instructors)) {
          // DEBUG: Log jury refinement data
          console.log('🔍 Results Jury DEBUG:', {
            projectId: project.id,
            projectTitle: project.title,
            scheduleInstructors: schedule.instructors,
            instructorsCount: schedule.instructors.length
          });
          
          // Backend'den gelen schedule.instructors array'i formatı:
          // [responsible (role:'responsible'), jury1 (role:'jury'), jury2_placeholder, ...]
          // Sadece jüri üyelerini (role:'jury') ve placeholder'ları dahil et
          const responsibleId = project.responsible_instructor_id;
          juryMembers = schedule.instructors
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
                // Backend'de role:'responsible' olan ilk instructor'ı hariç tut
                // Ayrıca responsibleId ile eşleşen instructor'ı da hariç tut (güvenlik için)
                if (inst?.role === 'responsible') {
                  return false; // Responsible instructor'ı dahil etme
                }
                // Jüri üyelerini dahil et (role:'jury' veya role belirtilmemiş)
                return inst.id && inst.id !== responsibleId;
              }
              return false;
            })
            .map((inst: any) => {
              // String kontrolü: "[Araştırma Görevlisi]" placeholder'ı
              if (typeof inst === 'string' && inst === '[Araştırma Görevlisi]') {
                return {
                  id: -1,
                  name: '[Araştırma Görevlisi]',
                  role: 'Araştırma Görevlisi',
                  isSenior: false
                };
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
                
                return {
                  id: juryId,
                  name: inst.full_name || inst.name || '[Araştırma Görevlisi]',
                  role: displayRole,
                  isSenior: isSeniorInstructor(inst.role || inst.type)
                };
              }
              
              return null;
            })
            .filter((m: any) => m !== null); // null değerleri temizle
          
          // DEBUG: Log final jury result
          console.log('🎯 Results Jury Result:', {
            projectId: project.id,
            juryCount: juryMembers.length,
            juryMembers: juryMembers
          });
        } else {
          // Fallback: eski yöntem (sorumlu + assistant)
          juryMembers = [
            { 
              id: responsibleInstructor?.id,
              name: responsibleInstructor?.name || 'Bilinmiyor', 
              role: 'Sorumlu Öğretim Üyesi',
              isSenior: isSeniorInstructor(responsibleInstructor?.role)
            },
            ...assistantInstructors.map((ai: any) => ({ 
              id: ai.id,
              name: ai.name, 
              role: ai.role === 'hoca' ? 'Öğretim Üyesi' : 'Araştırma Görevlisi',
              isSenior: isSeniorInstructor(ai.role)
            }))
          ];
        }
        
        return {
          id: project.id,
          title: project.title,
          type: project.type,
          responsibleInstructor: responsibleInstructor,
          assistantInstructors: assistantInstructors,
          juryMembers: juryMembers,
          juryCount: juryMembers.length,
          classroom: schedule?.classroom?.name || 'Atanmamış',
          classroomId: schedule?.classroom_id,
          timeSlot: schedule?.timeslot ? 
            `${schedule.timeslot.start_time}-${schedule.timeslot.end_time}` : 'Atanmamış',
          timeslotId: schedule?.timeslot_id,
          status: schedule ? 'assigned' : 'pending'
        };
      });
      
      // Projelerin type'larını kontrol et
      console.log('PROJECT TYPES DEBUG:', projectsData.map((p: any) => ({ id: p.id, type: p.type, title: p.title })));
      
      // Workload verilerini hesapla
      const workloadData = instructorsData.map((instructor: any) => {
        // Sorumlu olduğu projeler
        const responsibleProjects = projectsData.filter((p: any) => p.responsible_instructor_id === instructor.id);
        
        // Jüri üyesi olduğu projeler (schedule.instructors'dan)
        // Backend'den gelen array'de responsible instructor da var, sadece role:'jury' olanları say
        const juryProjects = projectsData.filter((p: any) => {
          const schedule = schedulesData.find((s: any) => s.project_id === p.id);
          if (schedule?.instructors && Array.isArray(schedule.instructors)) {
            return schedule.instructors.some((inst: any) => {
              // Placeholder'ları hariç tut
              if (inst?.is_placeholder === true || inst?.id === -1) {
                return false;
              }
              // Sadece jüri üyesi olanları dahil et (role:'jury' veya role belirtilmemiş ama responsible değil)
              if (inst?.role === 'responsible') {
                return false; // Responsible instructor'ı dahil etme
              }
              return inst.id === instructor.id;
            });
          }
          return false;
        });
        
        // Bitirme projelerinde jüri üyeliği (hem sorumlu hem assistant)
        const bitirmeCount = [
          ...responsibleProjects.filter((p: any) => {
            const type = (p?.project_type || p?.type || '').toString().toLowerCase();
            return type === 'final' || type === 'bitirme';
          }),
          ...juryProjects.filter((p: any) => {
            const type = (p?.project_type || p?.type || '').toString().toLowerCase();
            return type === 'final' || type === 'bitirme';
          })
        ].length;
        
        // Ara projelerde jüri üyeliği (hem sorumlu hem assistant)
        const araCount = [
          ...responsibleProjects.filter((p: any) => {
            const type = (p?.project_type || p?.type || '').toString().toLowerCase();
            return type === 'interim' || type === 'ara';
          }),
          ...juryProjects.filter((p: any) => {
            const type = (p?.project_type || p?.type || '').toString().toLowerCase();
            return type === 'interim' || type === 'ara';
          })
        ].length;
        
        // DEBUG: Log workload calculation
        console.log(`🔍 Workload DEBUG ${instructor.name}:`, {
          responsibleProjects: responsibleProjects.length,
          juryProjects: juryProjects.length,
          totalJuryCount: juryProjects.length,
          juryProjectDetails: juryProjects.map((p: any) => ({
            id: p.id,
            title: p.title,
            scheduleInstructors: schedulesData.find((s: any) => s.project_id === p.id)?.instructors?.length || 0
          }))
        });
        const totalJuryCount = juryProjects.length; // Sadece jüri üyesi olarak çalışılan projeler
        
        return {
          id: instructor.id,
          name: instructor.full_name || instructor.name || `Hoca ${instructor.id}`,
          role: instructor.role,
          isSenior: isSeniorInstructor(instructor.role),
          finalCount: bitirmeCount,
          interimCount: araCount,
          totalJuryCount: totalJuryCount,
          responsibleCount: responsibleProjects.length,
          assistantJuryCount: juryProjects.length
        };
      });
      
      setWorkloads(workloadData);
      
      // Metrikleri hesapla
      const totalProjects = projectsData.length;
      const assignedProjects = schedulesData.length;
      
      // Çakışma sayısını hesapla - schedule verilerinden direkt (Planner ile aynı mantık)
      const conflictAnalysis = calculateConflictsDetailed(schedulesData);
      const conflictCount = conflictAnalysis.totalConflicts;
      
      // Yük dağılımı analizi - Planner.tsx'teki mantıkla
      const allInstructorWorkloads = calculateAllInstructorWorkloads(schedulesData, instructorsData);
      const loadAnalysis = analyzeLoadDistribution(allInstructorWorkloads, instructorsData);
      
      // DEBUG: Log workload analysis
      console.log('🔍 Load Analysis DEBUG:', {
        allInstructorWorkloads: allInstructorWorkloads.map((w: any) => ({ 
          name: w.instructorName, 
          totalCount: w.totalCount,
          responsibleCount: w.responsibleCount,
          juryCount: w.juryCount
        })),
        loadAnalysis
      });
      
      // Sınıf değişimi analizi - Planner.tsx'teki mantıkla
      const classroomChanges = analyzeClassroomChanges(schedulesData);
      
      // DEBUG: Log classroom changes
      console.log('🔍 Classroom Changes DEBUG:', {
        classroomChanges
      });
      
      // Skor hesaplama
      const satisfactionScore = calculateSatisfactionScore({
        conflictCount,
        loadAnalysis,
        classroomChanges,
        totalProjects,
        assignedProjects
      });
      
      // DEBUG: Log jury metrics
      const totalJuryMembers = projectsWithDetails.reduce((sum: number, p: any) => sum + p.juryCount, 0);
      const averageJuryPerProject = Math.round((totalJuryMembers / totalProjects) * 10) / 10;
      
      console.log('🔍 Results Analytics DEBUG:', {
        totalProjects,
        assignedProjects,
        totalJuryMembers,
        averageJuryPerProject,
        projectsWithJury: projectsWithDetails.filter((p: any) => p.juryCount > 0).length,
        juryCounts: projectsWithDetails.map((p: any) => ({ id: p.id, title: p.title, juryCount: p.juryCount }))
      });
      
      setMetrics({
        totalProjects: totalProjects,
        assignedProjects: assignedProjects,
        unassignedProjects: totalProjects - assignedProjects,
        conflictCount: conflictCount,
        satisfactionScore: satisfactionScore,
        algorithmUsed: lastAlgorithmRun ? getAlgorithmDisplayName(lastAlgorithmRun.algorithm_name) : 'Fallback Algorithm',
        executionTime: lastAlgorithmRun ? (lastAlgorithmRun.execution_time || 0) : 0,
        utilizationRate: Math.round((assignedProjects / totalProjects) * 100 * 10) / 10,
        totalJuryMembers: totalJuryMembers,
        averageJuryPerProject: averageJuryPerProject,
        loadAnalysis: loadAnalysis,
        classroomChanges: classroomChanges
      });

      // Timeslot ve classroom verilerini de al
      const timeslotsResponse = await api.get('/timeslots/');
      const classroomsResponse = await api.get('/classrooms/');
      const timeslotsData = timeslotsResponse.data || [];
      const classroomsData = classroomsResponse.data || [];
      
      // Performance data hesapla - timeslot ve classroom verilerini de geç
      const performanceMetrics = calculatePerformanceData(schedulesData, projectsData, instructorsData, timeslotsData, classroomsData);
      setPerformanceData(performanceMetrics);
      
    } catch (err: any) {
      console.error('Error fetching data:', err);
      setError(err?.response?.data?.detail || 'Veri yüklenirken hata oluştu');
      
      // Fallback data
      setProjects([]);
      setSchedules([]);
      setInstructors([]);
      setWorkloads([]);
      setMetrics({
        totalProjects: 0,
        assignedProjects: 0,
        unassignedProjects: 0,
        conflictCount: 0,
        satisfactionScore: 0,
        algorithmUsed: 'N/A',
        executionTime: 0,
        utilizationRate: 0,
        totalJuryMembers: 0,
        averageJuryPerProject: 0,
        loadAnalysis: { seniorMaxDiff: 0, assistantMaxDiff: 0 },
        classroomChanges: { totalChanges: 0, instructorsWithChanges: 0 }
      });
    } finally {
      setLoading(false);
    }
  };

  // Yardımcı fonksiyonlar
  const isSeniorInstructor = (role: string) => {
    if (!role) return false;
    return role.includes('Prof. Dr.') || role.includes('Doç. Dr.') || role.includes('Dr. Öğr. Üyesi');
  };

  const getAlgorithmDisplayName = (algorithmName: string) => {
    const algorithmNames: { [key: string]: string } = {
      'simplex': 'Simplex Method',
      'genetic': 'Genetic Algorithm',
      'simulated_annealing': 'Simulated Annealing',
      'ant_colony': 'Ant Colony Optimization',
      'nsga_ii': 'NSGA-II',
      'greedy': 'Greedy Algorithm',
      'tabu_search': 'Tabu Search',
      'pso': 'Particle Swarm Optimization (PSO)',
      'harmony_search': 'Harmony Search',
      'firefly': 'Firefly Algorithm',
      'grey_wolf': 'Grey Wolf Optimizer',
      'cp_sat': 'Constraint Programming (CP-SAT)',
      'deep_search': 'Deep Search'
    };
    return algorithmNames[algorithmName] || algorithmName;
  };

  const calculateConflicts = (projects: any[], schedules: any[]) => {
    const instructorTimeslots = new Map<number, Array<{timeslot_id: number, classroom_id: number}>>();
    let conflictCount = 0;

    projects.forEach((project: any) => {
      if (!project.timeslotId || !project.classroomId) return;

      // Tüm jüri üyelerini kontrol et
      project.juryMembers.forEach((member: any) => {
        if (!member.id) return;

        if (!instructorTimeslots.has(member.id)) {
          instructorTimeslots.set(member.id, []);
        }

        const existingSlots = instructorTimeslots.get(member.id)!;
        const conflict = existingSlots.some((slot: any) => 
          slot.timeslot_id === project.timeslotId && slot.classroom_id !== project.classroomId
        );

        if (conflict) {
          conflictCount++;
        }

        existingSlots.push({ 
          timeslot_id: project.timeslotId, 
          classroom_id: project.classroomId 
        });
      });
    });

    return conflictCount;
  };

  // Planner.tsx'teki gibi tüm öğretim görevlilerinin detaylı iş yükünü hesapla (sorumlu + jüri)
  const calculateAllInstructorWorkloads = (schedules: any[], instructors: any[]) => {
    const workloadMap = new Map<number, {
      responsibleCount: number;
      juryCount: number;
      totalCount: number;
      instructor: any;
    }>();

    // Önce tüm instructor'ları map'e ekle
    instructors.forEach((instructor: any) => {
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
      
      // Sorumlu instructor'ı say
      if (responsibleId) {
        const workload = workloadMap.get(responsibleId);
        if (workload) {
          workload.responsibleCount += 1;
          workload.totalCount += 1;
        } else {
          // Eğer instructor bulunamazsa yeni kayıt oluştur
          const instructor = instructors.find((i: any) => i.id === responsibleId);
          workloadMap.set(responsibleId, {
            responsibleCount: 1,
            juryCount: 0,
            totalCount: 1,
            instructor: instructor || { id: responsibleId, name: `Instructor ${responsibleId}` }
          });
        }
      }

      // Jüri üyelerini say
      if (schedule.instructors && Array.isArray(schedule.instructors)) {
        schedule.instructors.forEach((inst: any) => {
          // String kontrolü: "[Araştırma Görevlisi]" placeholder'ını atla (iş yüküne dahil edilmez)
          if (typeof inst === 'string' && inst === '[Araştırma Görevlisi]') {
            return; // Placeholder'ı iş yükü hesaplamalarına dahil etme
          }
          
          // Placeholder kontrolü
          if (inst?.is_placeholder === true || inst?.id === -1 || inst?.name === '[Araştırma Görevlisi]') {
            return; // Placeholder'ı iş yükü hesaplamalarına dahil etme
          }
          
          const juryId = typeof inst === 'object' ? inst.id : inst;
          // Sorumlu dışındaki jüri üyelerini say
          if (juryId && juryId !== responsibleId) {
            const workload = workloadMap.get(juryId);
            if (workload) {
              workload.juryCount += 1;
              workload.totalCount += 1;
            } else {
              // Eğer instructor bulunamazsa yeni kayıt oluştur
              const instructor = instructors.find((i: any) => i.id === juryId);
              workloadMap.set(juryId, {
                responsibleCount: 0,
                juryCount: 1,
                totalCount: 1,
                instructor: instructor || { id: juryId, name: `Instructor ${juryId}` }
              });
            }
          }
        });
      }
    });

    // Liste olarak döndür ve sırala (toplam yüküne göre azalan)
    const workloadList = Array.from(workloadMap.values())
      .map(item => ({
        instructorId: item.instructor.id,
        instructorName: item.instructor.name || item.instructor.full_name || `Instructor ${item.instructor.id}`,
        responsibleCount: item.responsibleCount,
        juryCount: item.juryCount,
        totalCount: item.totalCount,
        instructor: item.instructor
      }))
      .sort((a, b) => b.totalCount - a.totalCount);

    return workloadList;
  };

  const analyzeLoadDistribution = (allInstructorWorkloads: any[], instructors: any[]) => {
    // Instructor type/role mapping oluştur
    const instructorTypeMap = new Map<number, { isSenior: boolean; type: string }>();
    instructors.forEach((inst: any) => {
      if (inst.id) {
        const role = inst.role || '';
        const type = (inst.type || '').toString().toLowerCase();
        const isSenior = isSeniorInstructor(role) || type === 'instructor';
        instructorTypeMap.set(inst.id, { isSenior, type });
      }
    });

    // Senior ve assistant'ları ayır
    const seniors = allInstructorWorkloads.filter(w => {
      const typeInfo = instructorTypeMap.get(w.instructorId);
      return typeInfo?.isSenior === true;
    });
    const assistants = allInstructorWorkloads.filter(w => {
      const typeInfo = instructorTypeMap.get(w.instructorId);
      return typeInfo?.isSenior === false;
    });

    // Sadece yükü olan instructor'ları al (totalCount > 0)
    const seniorLoads = seniors.filter(s => s.totalCount > 0).map(s => s.totalCount);
    const assistantLoads = assistants.filter(a => a.totalCount > 0).map(a => a.totalCount);

    const seniorMaxDiff = seniorLoads.length > 0 ? Math.max(...seniorLoads) - Math.min(...seniorLoads) : 0;
    const assistantMaxDiff = assistantLoads.length > 0 ? Math.max(...assistantLoads) - Math.min(...assistantLoads) : 0;

    return {
      seniorMaxDiff,
      assistantMaxDiff,
      seniorLoads,
      assistantLoads
    };
  };

  const analyzeClassroomChanges = (schedules: any[]) => {
    // Planner.tsx'teki implementasyon ile BİREBİR AYNI
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
    const totalSchedules = data.assignedProjects || 0;
    
    // Çakışma cezası - Toplam schedule'a göre normalize edilmiş (max 25 puan)
    if (data.conflictCount > 0 && totalSchedules > 0) {
      const conflictRate = data.conflictCount / totalSchedules;
      score -= Math.min(conflictRate * 50, 25);
    }
    
    // Yük dağılımı cezası - Daha toleranslı (max 20 puan)
    if (data.loadAnalysis.seniorMaxDiff > 2) {
      const penalty = Math.min((data.loadAnalysis.seniorMaxDiff - 2) * 3, 10);
      score -= penalty;
    }
    if (data.loadAnalysis.assistantMaxDiff > 2) {
      const penalty = Math.min((data.loadAnalysis.assistantMaxDiff - 2) * 3, 10);
      score -= penalty;
    }
    
    // Sınıf değişimi cezası - Daha düşük (max 15 puan)
    if (data.classroomChanges.instructorsWithChanges > 0 && data.classroomChanges.totalInstructors > 0) {
      const changeRate = data.classroomChanges.instructorsWithChanges / data.classroomChanges.totalInstructors;
      score -= Math.min(changeRate * 30, 15);
    }
    
    // Atanmamış proje cezası - Orantılı ama makul (max 30 puan)
    if (data.unassignedProjects > 0 && data.totalProjects > 0) {
      const unassignedRate = data.unassignedProjects / data.totalProjects;
      score -= Math.min(unassignedRate * 40, 30);
    }
    
    return Math.max(0, Math.round(score));
  };

  // Planner.tsx'teki detaylı analiz fonksiyonları
  const calculateConflictsDetailed = (schedules: any[]) => {
    const instructorTimeslots = new Map<number, Set<number>>();
    let conflictCount = 0;

    schedules.forEach((schedule: any) => {
      if (!schedule.timeslot_id || !schedule.classroom_id) return;

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

      if (!responsibleInstructorId) return;

      if (!instructorTimeslots.has(responsibleInstructorId)) {
        instructorTimeslots.set(responsibleInstructorId, new Set());
      }

      const existingTimeslots = instructorTimeslots.get(responsibleInstructorId)!;
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

  const analyzeWorkloadDistributionDetailed = (schedules: any[], instructors: any[]) => {
    const workloadMap = new Map<number, number>();
    
    // Instructor type mapping - backend ile uyumlu
    // Backend'de sadece "hoca" (type="instructor") öğretim üyeleri için yük dengesi hesaplanıyor
    const instructorTypeMap = new Map<number, string>();
    instructors.forEach((inst: any) => {
      if (inst.id) {
        // Type kontrolü: type, role veya instructor_type alanlarından biri olabilir
        const type = (inst.type || inst.role || inst.instructor_type || '').toString().toLowerCase();
        instructorTypeMap.set(inst.id, type);
      }
    });
    
    // Her schedule için hem sorumlu hem de jüri üyelerini hesapla
    // Backend'den gelen schedule.instructors array'i formatı:
    // [responsible (role:'responsible'), jury1 (role:'jury'), jury2_placeholder, ...]
    schedules.forEach((schedule: any) => {
      // Tüm instructors array'ini kullanarak workload hesapla
      // Responsible instructor zaten array'in ilk elemanı, tekrar eklemeye gerek yok
      if (schedule.instructors && Array.isArray(schedule.instructors)) {
        schedule.instructors.forEach((instructor: any) => {
          // Placeholder'ları (J2) dahil etme - sadece gerçek instructor'ları say
          if (instructor && !instructor.is_placeholder && instructor.id && instructor.id !== -1) {
            // Backend ile uyumlu: sadece "hoca" (instructor) tipindeki öğretim üyelerini dahil et
            const instructorType = instructorTypeMap.get(instructor.id) || '';
            // Type kontrolü: "instructor", "hoca" veya boş (varsayılan olarak instructor kabul et)
            if (!instructorType || instructorType === 'instructor' || instructorType === 'hoca' || instructorType.includes('instructor')) {
              const count = workloadMap.get(instructor.id) || 0;
              workloadMap.set(instructor.id, count + 1);
            }
          }
        });
      } else {
        // Fallback: Eğer instructors array yoksa, responsible_instructor_id'yi kullan
        const responsibleId = schedule.responsible_instructor_id || schedule.project?.responsible_instructor_id;
        if (responsibleId) {
          const instructorType = instructorTypeMap.get(responsibleId) || '';
          // Sadece "instructor" tipindeki öğretim üyelerini dahil et
          if (!instructorType || instructorType === 'instructor' || instructorType === 'hoca' || instructorType.includes('instructor')) {
            const count = workloadMap.get(responsibleId) || 0;
            workloadMap.set(responsibleId, count + 1);
          }
        }
      }
    });

    const workloads = Array.from(workloadMap.values());
    
    if (workloads.length === 0) {
      return {
        maxWorkload: 0,
        minWorkload: 0,
        avgWorkload: 0,
        maxDifference: 0,
        stdDeviation: 0,
        variance: 0,
        loadBalanceScore: 0,
        totalInstructors: 0
      };
    }

    const maxWorkload = Math.max(...workloads);
    const minWorkload = Math.min(...workloads);
    const avgWorkload = workloads.reduce((a, b) => a + b, 0) / workloads.length;
    
    // Standart sapma hesaplama (backend performans metrikleri ile uyumlu)
    const variance = workloads.reduce((sum, load) => sum + Math.pow(load - avgWorkload, 2), 0) / workloads.length;
    const stdDeviation = Math.sqrt(variance);
    
    // Load Balance Score hesaplama (backend ile uyumlu)
    // Backend'de: std <= 0.5 -> 100, std >= 2.0 -> 0 (threshold=0.5, span=1.5)
    const loadStdThreshold = 0.5;
    const loadStdSpan = 1.5;
    let loadBalanceScore = 100.0;
    if (stdDeviation > loadStdThreshold) {
      const over = Math.min(1.0, (stdDeviation - loadStdThreshold) / Math.max(1e-6, loadStdSpan));
      loadBalanceScore = Math.max(0, Math.min(100, 100.0 * (1.0 - over)));
    }

    return {
      maxWorkload,
      minWorkload,
      avgWorkload: Math.round(avgWorkload * 10) / 10,
      maxDifference: maxWorkload - minWorkload,
      stdDeviation: Math.round(stdDeviation * 100) / 100,
      variance: Math.round(variance * 100) / 100,
      loadBalanceScore: Math.round(loadBalanceScore * 10) / 10,
      totalInstructors: workloadMap.size
    };
  };

  const analyzeClassroomChangesDetailed = (schedules: any[]) => {
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

      // SADECE SORUMLU ÖĞRETİM ÜYESİ için sınıf değişimi kontrolü
      // Assistant jüri üyeleri sınıf değiştirebilir, bu yüzden onları dahil etmiyoruz
      if (responsibleInstructorId && schedule.classroom_id) {
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

  const calculateSatisfactionScoreDetailed = (data: any) => {
    let score = 100;
    const totalSchedules = data.totalSchedules || data.conflictAnalysis?.totalSchedules || 0;
    
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


  useEffect(() => {
    fetchData();
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'assigned': return 'success';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'assigned': return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'pending': return <Warning sx={{ color: 'warning.main' }} />;
      default: return <Info />;
    }
  };

  const getWorkloadColor = (count: number, maxCount: number) => {
    const ratio = maxCount > 0 ? count / maxCount : 0;
    if (ratio < 0.6) return 'success';
    if (ratio <= 0.8) return 'warning';
    return 'error';
  };

  const handleExport = (format: 'pdf' | 'excel') => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      console.log(`Exporting as ${format.toUpperCase()}`);
      alert(`${format.toUpperCase()} formatında rapor indiriliyor...`);
    }, 2000);
  };

  const renderOverviewTab = () => (
    <Box>
      {/* Ana Metrikler - Algorithms sayfası ile aynı grid tasarımı */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(4, 1fr)' }, gap: 3, mb: 4 }}>
        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
            <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Assignment sx={{ fontSize: 40, color: 'primary.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                    Toplam Proje
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main', mb: 0.5 }}>
                    {metrics?.totalProjects || 0}
                  </Typography>
                <Typography variant="body2" color="text.secondary">
                    Sistemdeki toplam proje sayısı
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
            <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <CheckCircle sx={{ fontSize: 40, color: 'success.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                    Atanmış Proje
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main', mb: 0.5 }}>
                    {metrics?.assignedProjects || 0}
                  </Typography>
                <Typography variant="body2" color="text.secondary">
                    Başarıyla atanan projeler
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
            <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              {metrics?.conflictCount > 0 ? 
                <Error sx={{ fontSize: 40, color: 'error.main' }} /> :
                <CheckCircle sx={{ fontSize: 40, color: 'success.main' }} />
              }
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                    Çakışma Sayısı
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: metrics?.conflictCount > 0 ? 'error.main' : 'success.main', mb: 0.5 }}>
                    {metrics?.conflictCount || 0}
                  </Typography>
                <Typography variant="body2" color="text.secondary">
                    {metrics?.conflictCount > 0 ? 'Çakışma tespit edildi' : 'Çakışma yok'}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
            <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <TrendingUp sx={{ fontSize: 40, color: metrics?.satisfactionScore >= 80 ? 'success.main' : metrics?.satisfactionScore >= 60 ? 'warning.main' : 'error.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                    Optimizasyon Skoru
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: metrics?.satisfactionScore >= 80 ? 'success.main' : metrics?.satisfactionScore >= 60 ? 'warning.main' : 'error.main', mb: 0.5 }}>
                    {metrics?.satisfactionScore || 0}
                  </Typography>
                <Typography variant="body2" color="text.secondary">
                    {metrics?.satisfactionScore >= 80 ? 'Mükemmel' : metrics?.satisfactionScore >= 60 ? 'İyi' : 'Düşük'}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
      </Box>

      {/* Detaylı Analiz - Algorithms sayfası ile aynı grid tasarımı */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(2, 1fr)' }, gap: 3, mb: 4 }}>
        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
            <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Assessment sx={{ fontSize: 40, color: 'primary.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  Algoritma Bilgileri
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Kullanılan Algoritma:</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{metrics?.algorithmUsed}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Çalışma Süresi:</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{metrics?.executionTime}s</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Atama Oranı:</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>%{metrics?.utilizationRate}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Toplam Jüri Üyesi:</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{metrics?.totalJuryMembers}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Proje Başına Ortalama Jüri:</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{metrics?.averageJuryPerProject}</Typography>
                </Box>
                </Box>
              </Box>
            </Box>
            </CardContent>
          </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
            <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Work sx={{ fontSize: 40, color: 'secondary.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  Yük Dağılımı Analizi
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Hocalar Arası Maksimum Fark:</Typography>
                  <Chip 
                    label={metrics?.loadAnalysis?.seniorMaxDiff || 0}
                    color={metrics?.loadAnalysis?.seniorMaxDiff <= 2 ? 'success' : 'error'}
                    size="small"
                  />
                </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Asistanlar Arası Maksimum Fark:</Typography>
                  <Chip 
                    label={metrics?.loadAnalysis?.assistantMaxDiff || 0}
                    color={metrics?.loadAnalysis?.assistantMaxDiff <= 2 ? 'success' : 'error'}
                    size="small"
                  />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Sınıf Değiştiren Öğretim Üyesi:</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {metrics?.classroomChanges?.instructorsWithChanges || 0}/{metrics?.classroomChanges?.totalInstructors || 0}
                  </Typography>
                </Box>
                </Box>
              </Box>
            </Box>
            </CardContent>
          </Card>
        </Box>
    </Box>
  );

  const renderAssignmentsTab = () => (
    <Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Proje ID</TableCell>
              <TableCell>Proje Başlığı</TableCell>
              <TableCell>Tür</TableCell>
              <TableCell>Sorumlu Öğretim Üyesi</TableCell>
              <TableCell>Sınıf</TableCell>
              <TableCell>Zaman Dilimi</TableCell>
              <TableCell>Jüri Üyeleri</TableCell>
              <TableCell>Durum</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {projects.map((project: any) => {
              const schedule = schedules.find((s: any) => s.project_id === project.id);
              // SADECE algoritmanın ürettiği gerçek jüri üyelerini kullan (schedule.instructors)
              // Placeholder jürileri (assistant_instructors) tamamen kaldır
              // Sadece jüri üyelerini dahil et (sorumlu hariç)
              // İlk instructor sorumlu, geri kalanlar jüri
              // Backend'den gelen schedule.instructors array'i formatı:
              // [responsible (role:'responsible'), jury1 (role:'jury'), jury2_placeholder, ...]
              // Sadece jüri üyelerini (role:'jury') ve placeholder'ları göster
              const juryMembers = schedule?.instructors && Array.isArray(schedule.instructors) 
                ? schedule.instructors
                    .filter((inst: any) => {
                      // Placeholder'ları dahil et
                      if (inst?.is_placeholder === true || inst?.id === -1 || inst?.name === '[Araştırma Görevlisi]') {
                        return true;
                      }
                      // Responsible instructor'ı hariç tut (role:'responsible' veya ilk eleman)
                      if (inst?.role === 'responsible') {
                        return false;
                      }
                      // Jüri üyelerini dahil et (role:'jury' veya role belirtilmemiş)
                      return inst.id && inst.id !== project.responsible_instructor_id;
                    })
                    .map((inst: any) => {
                      // Placeholder için özel işleme
                      if (inst?.is_placeholder === true || inst?.id === -1 || inst?.name === '[Araştırma Görevlisi]') {
                        return {
                          name: '[Araştırma Görevlisi]',
                          role: 'Araştırma Görevlisi'
                        };
                      }
                      return {
                        name: inst.full_name || inst.name || `Hoca ${inst.id}`,
                        role: inst.type === 'instructor' || inst.role === 'jury' ? 'Öğretim Üyesi' : 'Araştırma Görevlisi'
                      };
                    })
                : [];
              
              return (
                <TableRow key={project.id}>
                  <TableCell>{project.id}</TableCell>
                  <TableCell>{project.title}</TableCell>
                  <TableCell>
                    <Chip 
                      label={getProjectTypeLabel(project)} 
                      color={getProjectTypeColor(project)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{getInstructorName(project.responsible_instructor_id) || 'Atanmamış'}</TableCell>
                  <TableCell>{schedule?.classroom?.name || 'Atanmamış'}</TableCell>
                  <TableCell>
                    {schedule?.timeslot ? 
                      `${schedule.timeslot.start_time}-${schedule.timeslot.end_time}` : 
                      'Atanmamış'
                    }
                  </TableCell>
                  <TableCell>
                    <Box>
                      {juryMembers.map((member: any, index: number) => (
                        <Chip
                          key={index}
                          label={`${member.name} (${member.role})`}
                          size="small"
                          variant="outlined"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={schedule ? 'Atanmış' : 'Beklemede'}
                      color={schedule ? 'success' : 'warning'}
                      icon={getStatusIcon(schedule ? 'assigned' : 'pending')}
                      size="small"
                    />
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  const renderWorkloadTab = () => (
    <Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Öğretim Üyesi</TableCell>
              <TableCell>Bitirme Projesi</TableCell>
              <TableCell>Ara Proje</TableCell>
              <TableCell>Toplam Jüri Üyeliği</TableCell>
              <TableCell>Sorumlu Proje</TableCell>
              <TableCell>Toplam İş Yükü</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {workloads.map((workload: any) => {
              const maxLoad = Math.max(...workloads.map(w => w.totalJuryCount));
              
              return (
                <TableRow key={workload.id}>
                  <TableCell>{workload.name}</TableCell>
                  <TableCell>{workload.finalCount}</TableCell>
                  <TableCell>{workload.interimCount}</TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="bold">
                      {workload.totalJuryCount}
                    </Typography>
                  </TableCell>
                  <TableCell>{workload.responsibleCount}</TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="bold" color="primary.main">
                      {workload.totalJuryCount + workload.responsibleCount}
                    </Typography>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  const renderAnalyticsTab = () => (
    <Box>
      {/* Analytics Grid - Algorithms sayfası ile aynı tasarım */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(2, 1fr)' }, gap: 3, mb: 4 }}>
        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
            <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <PieChart sx={{ fontSize: 40, color: 'primary.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  Proje Türü Dağılımı
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Bitirme Projesi:</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={(getBitirmeCount() / projects.length) * 100}
                      sx={{ width: 100, height: 8 }}
                      color="primary"
                    />
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {getBitirmeCount()} ({Math.round((getBitirmeCount() / projects.length) * 100)}%)
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Ara Proje:</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={(getAraCount() / projects.length) * 100}
                      sx={{ width: 100, height: 8 }}
                      color="secondary"
                    />
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {getAraCount()} ({Math.round((getAraCount() / projects.length) * 100)}%)
                    </Typography>
                  </Box>
                </Box>
                </Box>
              </Box>
            </Box>
            </CardContent>
          </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
            <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <People sx={{ fontSize: 40, color: 'secondary.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  Öğretim Üyesi Yük Dağılımı
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {/* Toplam İş Yükü Analizi */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Toplam Öğretim Üyesi:</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{instructors.length}</Typography>
        </Box>

                  {/* Maksimum Yük */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Maksimum Yük:</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: 'error.main' }}>
                      {workloads.length > 0 ? Math.max(...workloads.map(w => w.totalJuryCount + w.responsibleCount)) : 0}
                    </Typography>
                  </Box>
                  
                  {/* Minimum Yük */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Minimum Yük:</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.main' }}>
                      {workloads.length > 0 ? Math.min(...workloads.map(w => w.totalJuryCount + w.responsibleCount)) : 0}
                    </Typography>
                  </Box>
                  
                  {/* Ortalama Yük */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Ortalama Yük:</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main' }}>
                      {workloads.length > 0 ? Math.round((workloads.reduce((sum, w) => sum + w.totalJuryCount + w.responsibleCount, 0) / workloads.length) * 10) / 10 : 0}
                    </Typography>
                  </Box>
                  
                  {/* Yük Dağılımı Progress Bar */}
                  {workloads.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        Yük Dağılımı:
                      </Typography>
                      {workloads.slice(0, 5).map((workload: any, index: number) => {
                        const totalWorkload = workload.totalJuryCount + workload.responsibleCount;
                        const maxWorkload = Math.max(...workloads.map(w => w.totalJuryCount + w.responsibleCount));
                        const percentage = maxWorkload > 0 ? (totalWorkload / maxWorkload) * 100 : 0;
                        
                        return (
                          <Box key={workload.id} sx={{ mb: 1 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                              <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>
                                {workload.name}
                              </Typography>
                              <Typography variant="caption" sx={{ fontSize: '0.75rem', fontWeight: 600 }}>
                                {totalWorkload}
                              </Typography>
                            </Box>
                            <LinearProgress
                              variant="determinate"
                              value={percentage}
                              sx={{ 
                                height: 6, 
                                borderRadius: 3,
                                bgcolor: 'grey.200',
                                '& .MuiLinearProgress-bar': {
                                  bgcolor: index < 3 ? 'error.main' : index < 5 ? 'warning.main' : 'success.main'
                                }
                              }}
                            />
                          </Box>
                        );
                      })}
                    </Box>
                  )}
                </Box>
              </Box>
            </Box>
            </CardContent>
          </Card>
        </Box>

      {/* Optimizasyon Skoru Detayı - Full width card */}
      <Card
        sx={{
          transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: 4,
          },
        }}
      >
            <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
            <TrendingUp sx={{ fontSize: 40, color: 'success.main' }} />
            <Box sx={{ ml: 2, flexGrow: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Optimizasyon Skoru Detayı
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* Ana Skor Kartı */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
                  <Box sx={{ textAlign: 'center', minWidth: '200px' }}>
                    <Typography variant="h2" sx={{ fontWeight: 600, color: performanceData?.satisfactionScore >= 80 ? 'success.main' : performanceData?.satisfactionScore >= 60 ? 'warning.main' : 'error.main' }}>
                      {performanceData?.satisfactionScore || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Genel Memnuniyet Skoru
                    </Typography>
                </Box>
                  
                  {/* Detaylı Metrikler */}
                  <Box sx={{ flex: 1, minWidth: '300px' }}>
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                      {/* Çakışma Analizi */}
                      <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2, border: '1px solid', borderColor: performanceData?.conflictAnalysis?.totalConflicts === 0 ? 'success.main' : 'error.main' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          {performanceData?.conflictAnalysis?.totalConflicts === 0 ? 
                            <CheckCircle sx={{ fontSize: 20, color: 'success.main' }} /> : 
                            <Error sx={{ fontSize: 20, color: 'error.main' }} />
                          }
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Çakışma Analizi
                          </Typography>
                        </Box>
                        <Typography variant="h6" sx={{ fontWeight: 600, color: performanceData?.conflictAnalysis?.totalConflicts === 0 ? 'success.main' : 'error.main' }}>
                          {performanceData?.conflictAnalysis?.totalConflicts || 0}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {performanceData?.conflictAnalysis?.totalConflicts === 0 ? 'Çakışma Yok' : 'Toplam Çakışma'}
                        </Typography>
                      </Box>

                      {/* Yük Dağılımı Analizi */}
                      <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2, border: '1px solid', borderColor: performanceData?.workloadAnalysis?.stdDeviation <= 0.5 ? 'success.main' : performanceData?.workloadAnalysis?.stdDeviation <= 2.0 ? 'warning.main' : 'error.main' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          {performanceData?.workloadAnalysis?.stdDeviation <= 0.5 ? 
                            <CheckCircle sx={{ fontSize: 20, color: 'success.main' }} /> : 
                            performanceData?.workloadAnalysis?.stdDeviation <= 2.0 ?
                            <Warning sx={{ fontSize: 20, color: 'warning.main' }} /> :
                            <Error sx={{ fontSize: 20, color: 'error.main' }} />
                          }
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Yük Dağılımı
                          </Typography>
                        </Box>
                        <Typography variant="h6" sx={{ fontWeight: 600, color: performanceData?.workloadAnalysis?.stdDeviation <= 0.5 ? 'success.main' : performanceData?.workloadAnalysis?.stdDeviation <= 2.0 ? 'warning.main' : 'error.main' }}>
                          {performanceData?.workloadAnalysis?.loadBalanceScore !== undefined 
                            ? `${performanceData.workloadAnalysis.loadBalanceScore}` 
                            : performanceData?.workloadAnalysis?.stdDeviation !== undefined 
                            ? `${performanceData.workloadAnalysis.stdDeviation.toFixed(2)} σ`
                            : '0'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                          {performanceData?.workloadAnalysis?.stdDeviation <= 0.5 ? 'Mükemmel Denge' : 
                           performanceData?.workloadAnalysis?.stdDeviation <= 2.0 ? 'Kabul Edilebilir' : 
                           'Dengesiz'}
                        </Typography>
                        {performanceData?.workloadAnalysis && (
                          <Box sx={{ mt: 1.5, pt: 1.5, borderTop: '1px solid', borderColor: 'grey.300' }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="caption" color="text.secondary">Maks:</Typography>
                              <Typography variant="caption" sx={{ fontWeight: 600 }}>{performanceData.workloadAnalysis.maxWorkload || 0}</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="caption" color="text.secondary">Min:</Typography>
                              <Typography variant="caption" sx={{ fontWeight: 600 }}>{performanceData.workloadAnalysis.minWorkload || 0}</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="caption" color="text.secondary">Ortalama:</Typography>
                              <Typography variant="caption" sx={{ fontWeight: 600 }}>{performanceData.workloadAnalysis.avgWorkload || 0}</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="caption" color="text.secondary">Fark:</Typography>
                              <Typography variant="caption" sx={{ fontWeight: 600 }}>{performanceData.workloadAnalysis.maxDifference || 0}</Typography>
                            </Box>
                          </Box>
                        )}
                      </Box>

                      {/* Sınıf Değişimi Analizi */}
                      <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2, border: '1px solid', borderColor: performanceData?.classroomChangeAnalysis?.totalChanges <= 5 ? 'success.main' : 'warning.main' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          {performanceData?.classroomChangeAnalysis?.totalChanges <= 5 ? 
                            <CheckCircle sx={{ fontSize: 20, color: 'success.main' }} /> : 
                            <Warning sx={{ fontSize: 20, color: 'warning.main' }} />
                          }
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Sınıf Değişimi
                          </Typography>
                        </Box>
                        <Typography variant="h6" sx={{ fontWeight: 600, color: performanceData?.classroomChangeAnalysis?.totalChanges <= 5 ? 'success.main' : 'warning.main' }}>
                          {performanceData?.classroomChangeAnalysis?.totalChanges || 0}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {performanceData?.classroomChangeAnalysis?.totalChanges <= 5 ? 'Minimum' : 'Fazla Değişim'}
                        </Typography>
                      </Box>

                      {/* Atama Durumu Analizi */}
                      <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2, border: '1px solid', borderColor: performanceData?.assignmentStatus?.unassignedProjects === 0 ? 'success.main' : 'error.main' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          {performanceData?.assignmentStatus?.unassignedProjects === 0 ? 
                            <CheckCircle sx={{ fontSize: 20, color: 'success.main' }} /> : 
                            <Error sx={{ fontSize: 20, color: 'error.main' }} />
                          }
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            Atama Durumu
                          </Typography>
                        </Box>
                        <Typography variant="h6" sx={{ fontWeight: 600, color: performanceData?.assignmentStatus?.unassignedProjects === 0 ? 'success.main' : 'error.main' }}>
                          {performanceData?.assignmentStatus?.assignedProjects || 0}/{performanceData?.assignmentStatus?.totalProjects || 0}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {performanceData?.assignmentStatus?.unassignedProjects === 0 ? 'Tam Atama' : 'Eksik Atama'}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                </Box>

              </Box>
            </Box>
          </Box>
            </CardContent>
          </Card>
        </Box>
  );

  const renderPerformanceTab = () => (
    <Box>
      {/* Genel İstatistikler - Planner.tsx'teki gibi */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(4, 1fr)' }, gap: 3, mb: 4 }}>
        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Schedule sx={{ fontSize: 40, color: 'primary.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Toplam Program
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main', mb: 0.5 }}>
                  {performanceData?.totalSchedules || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Oluşturulan toplam program sayısı
                  </Typography>
                </Box>
            </Box>
            </CardContent>
          </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Assignment sx={{ fontSize: 40, color: 'secondary.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Benzersiz Proje
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'secondary.main', mb: 0.5 }}>
                  {performanceData?.uniqueProjects || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Programda yer alan benzersiz proje sayısı
                </Typography>
        </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
            <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <People sx={{ fontSize: 40, color: 'success.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Öğretim Üyesi
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main', mb: 0.5 }}>
                  {performanceData?.uniqueInstructors || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                  Programda görev alan öğretim üyesi sayısı
                    </Typography>
                  </Box>
                </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <School sx={{ fontSize: 40, color: 'info.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Kullanılan Sınıf
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'info.main', mb: 0.5 }}>
                  {performanceData?.uniqueClassrooms || 0}
                </Typography>
                      <Typography variant="body2" color="text.secondary">
                  Programda kullanılan sınıf sayısı
                      </Typography>
                    </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Zaman Analizi - Planner.tsx'teki gibi */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(3, 1fr)' }, gap: 3, mb: 4 }}>
        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Schedule sx={{ fontSize: 40, color: 'info.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Toplam Zaman Slotu
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'info.main', mb: 0.5 }}>
                  {performanceData?.totalTimeSlots || 0}
                </Typography>
                      <Typography variant="body2" color="text.secondary">
                  Sistemdeki toplam zaman slotu
                      </Typography>
                    </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Speed sx={{ fontSize: 40, color: 'secondary.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Slot Başına Ortalama Yük
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'secondary.main', mb: 0.5 }}>
                  {performanceData?.avgLoadPerSlot?.toFixed(1) || 0}
                </Typography>
                      <Typography variant="body2" color="text.secondary">
                  Zaman slotu başına ortalama program sayısı
                      </Typography>
                    </Box>
                </Box>
            </CardContent>
          </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <TrendingUp sx={{ fontSize: 40, color: 'success.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Kullanım Oranı
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main', mb: 0.5 }}>
                  {performanceData?.usageRate || 0}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Zaman slotu kullanım oranı
                </Typography>
        </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Jüri Metrikleri */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(3, 1fr)' }, gap: 3, mb: 4 }}>
        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <People sx={{ fontSize: 40, color: 'primary.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Toplam Jüri Üyesi
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main', mb: 0.5 }}>
                  {metrics?.totalJuryMembers || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Tüm projelerdeki toplam jüri üyesi sayısı
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Assignment sx={{ fontSize: 40, color: 'secondary.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Ortalama Jüri/Proje
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'secondary.main', mb: 0.5 }}>
                  {metrics?.averageJuryPerProject?.toFixed(1) || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Proje başına ortalama jüri üyesi sayısı
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <TrendingUp sx={{ fontSize: 40, color: 'success.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Jüri Atama Oranı
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main', mb: 0.5 }}>
                  {metrics?.totalJuryMembers > 0 ? Math.round((metrics.totalJuryMembers / (metrics.totalProjects * 2)) * 100) : 0}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Hedef jüri sayısına göre atama oranı
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Kalite Metrikleri - Planner.tsx'teki gibi */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(4, 1fr)' }, gap: 3, mb: 4 }}>
        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <TrendingUp sx={{ fontSize: 40, color: 'success.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Program/Proje Oranı
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main', mb: 0.5 }}>
                  {performanceData?.programDistribution || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Program başına proje oranı
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <School sx={{ fontSize: 40, color: 'info.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Program/Sınıf Oranı
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'info.main', mb: 0.5 }}>
                  {performanceData?.classroomUsage || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sınıf başına program oranı
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Speed sx={{ fontSize: 40, color: 'primary.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Kullanım Oranı
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main', mb: 0.5 }}>
                  {performanceData?.utilizationRate || 0}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Genel kullanım oranı
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Analytics sx={{ fontSize: 40, color: performanceData?.satisfactionScore >= 80 ? 'success.main' : performanceData?.satisfactionScore >= 60 ? 'warning.main' : 'error.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Memnuniyet Skoru
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: performanceData?.satisfactionScore >= 80 ? 'success.main' : performanceData?.satisfactionScore >= 60 ? 'warning.main' : 'error.main', mb: 0.5 }}>
                  {performanceData?.satisfactionScore || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Genel memnuniyet skoru
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Çakışma ve Öğretim Üyesi Analizi */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(2, 1fr)' }, gap: 3, mb: 4 }}>
        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Error sx={{ fontSize: 40, color: performanceData?.conflictAnalysis?.totalConflicts === 0 ? 'success.main' : 'error.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Toplam Çakışma
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: performanceData?.conflictAnalysis?.totalConflicts === 0 ? 'success.main' : 'error.main', mb: 0.5 }}>
                  {performanceData?.conflictAnalysis?.totalConflicts || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sistemdeki toplam çakışma sayısı
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Person sx={{ fontSize: 40, color: 'info.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                  En Az Yoğun Öğretim Üyesi
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'info.main', mb: 0.5 }}>
                  {performanceData?.minWorkloadInstructor?.name || 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {performanceData?.minWorkloadInstructor?.count || 0} görev
                </Typography>
                {performanceData?.workloadAnalysis?.minWorkloadInstructors && 
                 performanceData.workloadAnalysis.minWorkloadInstructors.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    {performanceData.workloadAnalysis.minWorkloadInstructors.map((name: string, index: number) => (
                      <Chip
                        key={index}
                        label={name}
                        size="small"
                        sx={{ 
                          fontSize: '0.75rem',
                          height: '24px',
                          mb: 0.5,
                          mr: 0.5,
                          bgcolor: 'info.lighter',
                          color: 'info.main'
                        }}
                      />
                    ))}
                  </Box>
                )}
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Yük Dağılımı Analizi - Planner.tsx'teki gibi */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(4, 1fr)' }, gap: 3, mb: 4 }}>
        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <TrendingUp sx={{ fontSize: 40, color: 'info.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Maksimum Yük
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'info.main', mb: 0.5 }}>
                  {performanceData?.workloadAnalysis?.maxWorkload || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  En yüksek öğretim üyesi yükü
                </Typography>
                {performanceData?.workloadAnalysis?.maxWorkloadInstructors && 
                 performanceData.workloadAnalysis.maxWorkloadInstructors.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    {performanceData.workloadAnalysis.maxWorkloadInstructors.map((name: string, index: number) => (
                      <Chip
                        key={index}
                        label={name}
                        size="small"
                        sx={{ 
                          fontSize: '0.75rem',
                          height: '24px',
                          mb: 0.5,
                          mr: 0.5,
                          bgcolor: 'info.lighter',
                          color: 'info.main'
                        }}
                      />
                    ))}
                  </Box>
                )}
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Speed sx={{ fontSize: 40, color: 'success.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Minimum Yük
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main', mb: 0.5 }}>
                  {performanceData?.workloadAnalysis?.minWorkload || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  En düşük öğretim üyesi yükü
                </Typography>
                {performanceData?.workloadAnalysis?.minWorkloadInstructors && 
                 performanceData.workloadAnalysis.minWorkloadInstructors.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    {performanceData.workloadAnalysis.minWorkloadInstructors.map((name: string, index: number) => (
                      <Chip
                        key={index}
                        label={name}
                        size="small"
                        sx={{ 
                          fontSize: '0.75rem',
                          height: '24px',
                          mb: 0.5,
                          mr: 0.5,
                          bgcolor: 'success.lighter',
                          color: 'success.main'
                        }}
                      />
                    ))}
                  </Box>
                )}
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Analytics sx={{ fontSize: 40, color: 'primary.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Ortalama Yük
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main', mb: 0.5 }}>
                  {performanceData?.workloadAnalysis?.avgWorkload || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Ortalama öğretim üyesi yükü
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Warning sx={{ fontSize: 40, color: performanceData?.workloadAnalysis?.maxDifference <= 2 ? 'success.main' : 'warning.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Yük Farkı
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: performanceData?.workloadAnalysis?.maxDifference <= 2 ? 'success.main' : 'warning.main', mb: 0.5 }}>
                  {performanceData?.workloadAnalysis?.maxDifference || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Maksimum ve minimum yük arasındaki fark
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Sınıf Değişimi Analizi - Planner.tsx'teki gibi */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(2, 1fr)' }, gap: 3, mb: 4 }}>
        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <School sx={{ fontSize: 40, color: performanceData?.classroomChangeAnalysis?.totalChanges === 0 ? 'success.main' : 'warning.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Toplam Sınıf Değişimi
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: performanceData?.classroomChangeAnalysis?.totalChanges === 0 ? 'success.main' : 'warning.main', mb: 0.5 }}>
                  {performanceData?.classroomChangeAnalysis?.totalChanges || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sistemdeki toplam sınıf değişimi sayısı
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <People sx={{ fontSize: 40, color: performanceData?.classroomChangeAnalysis?.instructorsWithChanges === 0 ? 'success.main' : 'info.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Sınıf Değiştiren Öğretim Üyesi
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: performanceData?.classroomChangeAnalysis?.instructorsWithChanges === 0 ? 'success.main' : 'info.main', mb: 0.5 }}>
                  {performanceData?.classroomChangeAnalysis?.instructorsWithChanges || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sınıf değiştiren öğretim üyesi sayısı
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Proje Atama Durumu - Planner.tsx'teki gibi */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(3, 1fr)' }, gap: 3, mb: 4 }}>
        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Assignment sx={{ fontSize: 40, color: 'primary.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Toplam Proje
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main', mb: 0.5 }}>
                  {performanceData?.totalProjects || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sistemdeki toplam proje sayısı
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <CheckCircle sx={{ fontSize: 40, color: 'success.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Atanmış Proje
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main', mb: 0.5 }}>
                  {performanceData?.assignedProjects || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Başarıyla atanan proje sayısı
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Warning sx={{ fontSize: 40, color: performanceData?.unassignedProjects === 0 ? 'success.main' : 'warning.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Atanmamış Proje
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: performanceData?.unassignedProjects === 0 ? 'success.main' : 'warning.main', mb: 0.5 }}>
                  {performanceData?.unassignedProjects || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Henüz atanmamış proje sayısı
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* En Yoğun Kullanımlar */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(2, 1fr)' }, gap: 3, mb: 4 }}>
        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <School sx={{ fontSize: 40, color: 'primary.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                  En Yoğun Sınıf
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main', mb: 0.5 }}>
                  {performanceData?.mostUsedClassroom?.name || 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {performanceData?.mostUsedClassroom?.count || 0} kullanım
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          sx={{
            height: '100%',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <Person sx={{ fontSize: 40, color: 'success.main' }} />
              <Box sx={{ ml: 2, flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                  En Yoğun Öğretim Üyesi
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main', mb: 0.5 }}>
                  {performanceData?.mostBusyInstructor?.name || 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {performanceData?.mostBusyInstructor?.count || 0} görev
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Proje Türü Dağılımı */}
      <Card
        sx={{
          transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: 4,
          },
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
            <PieChart sx={{ fontSize: 40, color: 'info.main' }} />
            <Box sx={{ ml: 2, flexGrow: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Proje Türü Dağılımı
              </Typography>
              <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                {Object.entries(performanceData?.projectTypeAnalysis || {}).map(([type, count]: [string, any]) => (
                  <Box key={type} sx={{ textAlign: 'center', minWidth: '120px' }}>
                    <Typography variant="h4" sx={{ fontWeight: 600, color: type === 'Bitirme' ? 'primary.main' : 'secondary.main' }}>
                      {count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {type} Projesi
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={fetchData} startIcon={<Refresh />}>
          Tekrar Dene
        </Button>
      </Box>
    );
  }

  return (
          <Box>
      {/* Header - Algorithms sayfası ile aynı stil */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Algorithm Results Center
            </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="contained"
            startIcon={<FileDownload />}
            sx={{ borderRadius: 2 }}
            onClick={(e) => setAnchorEl(e.currentTarget)}
          >
            Export Results
          </Button>
          <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
            <MenuItem onClick={() => { handleExport('pdf'); setAnchorEl(null); }}>
              <PictureAsPdf sx={{ mr: 1 }} />
              PDF İndir
            </MenuItem>
            <MenuItem onClick={() => { handleExport('excel'); setAnchorEl(null); }}>
              <TableChart sx={{ mr: 1 }} />
              Excel İndir
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      {/* Results Categories Tabs - Algorithms sayfası ile aynı stil */}
      <Paper sx={{ mb: 4 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Genel Bakış" icon={<Assessment />} />
          <Tab label="Atamalar" icon={<Assignment />} />
          <Tab label="İş Yükü" icon={<Work />} />
          <Tab label="Analizler" icon={<BarChart />} />
            <Tab label="Performans" icon={<Speed />} />
        </Tabs>
        </Box>
      </Paper>

        {/* Tab Content */}
        <Box>
          {tabValue === 0 && renderOverviewTab()}
          {tabValue === 1 && renderAssignmentsTab()}
          {tabValue === 2 && renderWorkloadTab()}
          {tabValue === 3 && renderAnalyticsTab()}
        {tabValue === 4 && renderPerformanceTab()}
        </Box>
    </Box>
  );
};

export default Results;