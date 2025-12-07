import { api } from './authService';

export interface InstructorAssignment {
    date: string;
    time: string;
    room: string;
    project: string;
    role: string;
    otherInstructors: string[];
    projectType?: string;
}

export interface InstructorPreview {
    instructor: {
        id: number;
        name: string;
        email: string;
    };
    assignments: InstructorAssignment[];
    hasAssignments: boolean;
    assignmentCount: number;
}

export interface GlobalPlannerPreview {
    planner_data: {
        classes: string[];
        timeSlots: string[];
        projects: Array<{
            class: string;
            time: string;
            projectTitle: string;
            type: string;
            responsible: string;
            jury: string[];
            color: string;
        }>;
        title: string;
        date: string;
    };
    metadata: {
        total_schedules: number;
        total_instructors: number;
        total_classrooms: number;
        generated_at: string;
    };
}

export interface NotificationLog {
    id: number;
    instructor_id: number;
    instructor_email: string;
    instructor_name: string;
    planner_timestamp: string | null;
    subject: string | null;
    status: 'pending' | 'success' | 'error' | 'failed';
    error_message: string | null;
    sent_at: string | null;
    attempt_count: number;
    metadata: any;
    created_at: string;
    updated_at: string;
}

export interface SendAllResult {
    success: boolean;
    results: {
        total: number;
        success: number;
        failed: number;
        errors: Array<{
            instructor_id: number;
            instructor_email: string;
            error: string;
        }>;
    };
}

export const notificationService = {
    /**
     * Get global planner preview
     */
    async getGlobalPreview(): Promise<GlobalPlannerPreview> {
        const response = await api.get<GlobalPlannerPreview>('/notification/preview/global');
        return response.data;
    },

    /**
     * Get instructor-specific preview
     */
    async getInstructorPreview(instructorId: number): Promise<InstructorPreview> {
        const response = await api.get<InstructorPreview>(`/notification/preview/instructor/${instructorId}`);
        return response.data;
    },

    /**
     * Send notifications to all instructors
     */
    async sendToAll(dryRun: boolean = false): Promise<SendAllResult> {
        const response = await api.post<SendAllResult>('/notification/send/all', null, {
            params: { dry_run: dryRun },
        });
        return response.data;
    },

    /**
     * Send notification to a specific instructor
     */
    async sendToInstructor(instructorId: number, dryRun: boolean = false): Promise<any> {
        const response = await api.post(`/notification/send/${instructorId}`, null, {
            params: { dry_run: dryRun },
        });
        return response.data;
    },

    /**
     * Send test email to admin
     */
    async sendTestEmail(adminEmail: string = 'cavuldak-eren@hotmail.com'): Promise<any> {
        const response = await api.post('/notification/send/test', null, {
            params: { admin_email: adminEmail },
        });
        return response.data;
    },

    /**
     * Send notification to custom email address (e.g., TEST_ADMIN)
     */
    async sendToCustomEmail(email: string, recipientName: string = 'TEST_ADMIN', dryRun: boolean = false): Promise<any> {
        const response = await api.post('/notification/send/custom-email', {
            email,
            recipient_name: recipientName,
        }, {
            params: { dry_run: dryRun },
        });
        return response.data;
    },

    /**
     * Get notification logs
     */
    async getLogs(
        limit: number = 100,
        offset: number = 0,
        status?: 'pending' | 'success' | 'error' | 'failed'
    ): Promise<{
        success: boolean;
        logs: NotificationLog[];
        total: number;
        limit: number;
        offset: number;
        error?: string;
    }> {
        const params: any = { limit, offset };
        if (status) {
            params.status = status;
        }
        const response = await api.get('/notification/logs', { params });
        return response.data;
    },
};

