/**
 * Penalty Calculation Service
 * Implements the correct penalty function based on constraints and objectives
 */

export interface InstructorSchedule {
  instructorId: number;
  instructorName: string;
  schedule: Array<{
    timeslot: number; // timeslot ID
    timeslotTime: number; // time as decimal (e.g., 9.0, 9.5, 10.0)
    classroomId: number;
    classroomName: string;
    projectId: number;
    role: 'SORUMLU' | 'JURI'; // responsible or jury member
  }>;
}

export interface PenaltyCalculationResult {
  totalPenalty: number;
  timePenalty: number;
  classroomPenalty: number;
  instructorPenalties: Array<{
    instructorId: number;
    instructorName: string;
    timePenalty: number;
    classroomPenalty: number;
    totalPenalty: number;
    violations: Array<{
      type: 'TIME_GAP' | 'CLASSROOM_CHANGE';
      fromTimeslot: number;
      toTimeslot: number;
      fromClassroom: number;
      toClassroom: number;
      penalty: number;
    }>;
  }>;
  constraints: {
    allProjectsAssigned: boolean;
    noGapsInTimeslots: boolean;
    correctClassroomCount: boolean;
    noSelfJury: boolean;
    oneTaskPerTimeslot: boolean;
  };
  constraintViolations: Array<{
    type: string;
    description: string;
    severity: 'HIGH' | 'MEDIUM' | 'LOW';
  }>;
}

export class PenaltyCalculationService {
  private slotLength: number = 0.5; // 30 minutes = 0.5 hours
  private tolerance: number = 0.001; // floating point tolerance
  private alpha: number = 1.0; // time penalty weight
  private beta: number = 1.0; // classroom change penalty weight

  constructor(
    slotLength: number = 0.5,
    tolerance: number = 0.001,
    alpha: number = 1.0,
    beta: number = 1.0
  ) {
    this.slotLength = slotLength;
    this.tolerance = tolerance;
    this.alpha = alpha;
    this.beta = beta;
  }

  /**
   * Calculate penalties for all instructors based on the penalty function
   */
  calculatePenalties(
    instructorSchedules: InstructorSchedule[],
    expectedClassroomCount: number,
    allProjects: any[],
    schedules: any[]
  ): PenaltyCalculationResult {
    let totalTimePenalty = 0;
    let totalClassroomPenalty = 0;
    const instructorPenalties: any[] = [];

    // Calculate penalties for each instructor
    for (const instructor of instructorSchedules) {
      const penalty = this.calculateInstructorPenalty(instructor);
      instructorPenalties.push(penalty);
      totalTimePenalty += penalty.timePenalty;
      totalClassroomPenalty += penalty.classroomPenalty;
    }

    // Check constraints
    const constraints = this.checkConstraints(
      instructorSchedules,
      expectedClassroomCount,
      allProjects,
      schedules
    );

    return {
      totalPenalty: totalTimePenalty + totalClassroomPenalty,
      timePenalty: totalTimePenalty,
      classroomPenalty: totalClassroomPenalty,
      instructorPenalties,
      constraints: constraints.satisfied,
      constraintViolations: constraints.violations
    };
  }

  /**
   * Calculate penalty for a single instructor
   */
  private calculateInstructorPenalty(instructor: InstructorSchedule): any {
    const schedule = instructor.schedule;
    if (schedule.length <= 1) {
      return {
        instructorId: instructor.instructorId,
        instructorName: instructor.instructorName,
        timePenalty: 0,
        classroomPenalty: 0,
        totalPenalty: 0,
        violations: []
      };
    }

    // Sort schedule by timeslot time
    const sortedSchedule = [...schedule].sort((a, b) => a.timeslotTime - b.timeslotTime);
    
    let timePenalty = 0;
    let classroomPenalty = 0;
    const violations: any[] = [];

    // Check consecutive pairs
    for (let i = 0; i < sortedSchedule.length - 1; i++) {
      const current = sortedSchedule[i];
      const next = sortedSchedule[i + 1];

      // Time penalty (consecutive check)
      const expectedTime = current.timeslotTime + this.slotLength;
      const timeDiff = Math.abs(next.timeslotTime - expectedTime);
      
      if (timeDiff > this.tolerance) {
        // Calculate gap penalty (proportional to gap size)
        const gapSize = Math.max(0, Math.round((next.timeslotTime - current.timeslotTime) / this.slotLength) - 1);
        const penalty = gapSize;
        timePenalty += penalty;
        
        violations.push({
          type: 'TIME_GAP',
          fromTimeslot: current.timeslot,
          toTimeslot: next.timeslot,
          fromClassroom: current.classroomId,
          toClassroom: next.classroomId,
          penalty: penalty
        });
      }

      // Classroom penalty (classroom change check)
      if (current.classroomId !== next.classroomId) {
        classroomPenalty += 1;
        
        violations.push({
          type: 'CLASSROOM_CHANGE',
          fromTimeslot: current.timeslot,
          toTimeslot: next.timeslot,
          fromClassroom: current.classroomId,
          toClassroom: next.classroomId,
          penalty: 1
        });
      }
    }

    return {
      instructorId: instructor.instructorId,
      instructorName: instructor.instructorName,
      timePenalty: timePenalty * this.alpha,
      classroomPenalty: classroomPenalty * this.beta,
      totalPenalty: (timePenalty * this.alpha) + (classroomPenalty * this.beta),
      violations
    };
  }

  /**
   * Check all constraints
   */
  private checkConstraints(
    instructorSchedules: InstructorSchedule[],
    expectedClassroomCount: number,
    allProjects: any[],
    schedules: any[]
  ): { satisfied: any; violations: any[] } {
    const violations: any[] = [];
    
    // 1. All projects must be assigned
    const assignedProjectIds = new Set(schedules.map(s => s.project_id));
    const unassignedProjects = allProjects.filter(p => !assignedProjectIds.has(p.id));
    if (unassignedProjects.length > 0) {
      violations.push({
        type: 'UNASSIGNED_PROJECTS',
        description: `${unassignedProjects.length} proje atanmamış`,
        severity: 'HIGH' as const
      });
    }

    // 2. No gaps in timeslots (projects must be consecutive from first timeslot)
    const usedTimeslots = new Set(schedules.map(s => s.timeslot_id));
    const allTimeslots = Array.from({ length: 16 }, (_, i) => i + 1); // Assuming 16 timeslots
    const firstUsedTimeslot = Math.min(...Array.from(usedTimeslots));
    const lastUsedTimeslot = Math.max(...Array.from(usedTimeslots));
    
    for (let i = firstUsedTimeslot; i <= lastUsedTimeslot; i++) {
      if (!usedTimeslots.has(i)) {
        violations.push({
          type: 'TIMESLOT_GAP',
          description: `Timeslot ${i} boş - projeler arasında boşluk var`,
          severity: 'HIGH' as const
        });
        break; // Only report first gap
      }
    }

    // 3. Correct classroom count
    const usedClassrooms = new Set(schedules.map(s => s.classroom_id));
    if (usedClassrooms.size !== expectedClassroomCount) {
      violations.push({
        type: 'WRONG_CLASSROOM_COUNT',
        description: `Beklenen ${expectedClassroomCount} sınıf, kullanılan ${usedClassrooms.size} sınıf`,
        severity: 'HIGH' as const
      });
    }

    // 4. No self-jury (instructor cannot be jury of their own project)
    for (const schedule of schedules) {
      const project = allProjects.find(p => p.id === schedule.project_id);
      if (project && schedule.instructors) {
        const responsibleId = project.responsible_instructor_id;
        const juryIds = schedule.instructors.map((inst: any) => inst.id);
        if (juryIds.includes(responsibleId)) {
          violations.push({
            type: 'SELF_JURY',
            description: `Proje ${project.id} - sorumlu öğretim üyesi kendi projesinin jürisi olamaz`,
            severity: 'HIGH' as const
          });
        }
      }
    }

    // 5. One task per timeslot per instructor
    const instructorTimeslotMap = new Map<number, Set<number>>();
    for (const schedule of schedules) {
      if (schedule.instructors) {
        for (const instructor of schedule.instructors) {
          const key = instructor.id;
          if (!instructorTimeslotMap.has(key)) {
            instructorTimeslotMap.set(key, new Set());
          }
          if (instructorTimeslotMap.get(key)!.has(schedule.timeslot_id)) {
            violations.push({
              type: 'MULTIPLE_TASKS_PER_TIMESLOT',
              description: `Öğretim üyesi ${instructor.id} aynı timeslot'ta birden fazla görev`,
              severity: 'HIGH' as const
            });
          }
          instructorTimeslotMap.get(key)!.add(schedule.timeslot_id);
        }
      }
    }

    return {
      satisfied: {
        allProjectsAssigned: unassignedProjects.length === 0,
        noGapsInTimeslots: violations.filter(v => v.type === 'TIMESLOT_GAP').length === 0,
        correctClassroomCount: usedClassrooms.size === expectedClassroomCount,
        noSelfJury: violations.filter(v => v.type === 'SELF_JURY').length === 0,
        oneTaskPerTimeslot: violations.filter(v => v.type === 'MULTIPLE_TASKS_PER_TIMESLOT').length === 0
      },
      violations
    };
  }

  /**
   * Calculate satisfaction score (0-100)
   */
  calculateSatisfactionScore(result: PenaltyCalculationResult): number {
    let score = 100;

    // Constraint violations (high penalty)
    const highSeverityViolations = result.constraintViolations.filter(v => v.severity === 'HIGH');
    score -= highSeverityViolations.length * 20;

    const mediumSeverityViolations = result.constraintViolations.filter(v => v.severity === 'MEDIUM');
    score -= mediumSeverityViolations.length * 10;

    const lowSeverityViolations = result.constraintViolations.filter(v => v.severity === 'LOW');
    score -= lowSeverityViolations.length * 5;

    // Penalty-based deductions
    const totalPenalty = result.totalPenalty;
    if (totalPenalty > 0) {
      score -= Math.min(totalPenalty * 2, 30); // Max 30 points for penalties
    }

    return Math.max(0, Math.round(score));
  }

  /**
   * Get penalty explanation
   */
  getPenaltyExplanation(result: PenaltyCalculationResult): string {
    const explanations: string[] = [];

    if (result.timePenalty > 0) {
      explanations.push(`Zaman cezası: ${result.timePenalty.toFixed(2)} (öğretim üyelerinin projeleri arasında boşluk)`);
    }

    if (result.classroomPenalty > 0) {
      explanations.push(`Sınıf değişimi cezası: ${result.classroomPenalty.toFixed(2)} (öğretim üyelerinin sınıf değiştirmesi)`);
    }

    if (result.constraintViolations.length > 0) {
      explanations.push(`Kısıt ihlalleri: ${result.constraintViolations.length} adet`);
    }

    return explanations.join('; ');
  }
}

export default PenaltyCalculationService;
