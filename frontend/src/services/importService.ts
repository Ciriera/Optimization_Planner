import { api } from './authService';

export interface ImportRow {
    row_number: number;
    instructor_name: string;
    project_type: string;
    project_type_normalized?: string;
    project_description: string;
    project_title?: string;
    status?: 'new' | 'existing' | 'new_project' | 'duplicate' | 'error' | 'ready';
    instructor_status?: 'new' | 'existing';
    project_status?: 'new' | 'existing';
    instructor_id?: number;
    project_id?: number;
    errors?: string[];
    warnings?: string[];
}

export interface ValidateResponse {
    success: boolean;
    error?: string;
    rows: ImportRow[];
    total_rows: number;
    valid_rows: number;
    invalid_rows: number;
}

export interface ImportStatistics {
    instructors_created: number;
    instructors_existing: number;
    projects_created: number;
    projects_existing: number;
    rows_processed: number;
    rows_skipped: number;
    rows_errors: number;
}

export interface ExecuteResponse {
    success: boolean;
    error?: string;
    statistics: ImportStatistics;
    errors?: string[];
    dry_run: boolean;
    timestamp: string;
}

export const importService = {
    async validateFile(file: File): Promise<ValidateResponse> {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await api.post('/import/validate', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        
        return response.data;
    },

    async executeImport(file: File, dryRun: boolean = false): Promise<ExecuteResponse> {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await api.post(`/import/execute?dry_run=${dryRun}`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        
        return response.data;
    },

    async downloadTemplate(): Promise<void> {
        const response = await api.get('/import/template', {
            responseType: 'blob',
        });
        
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'import_template.xlsx');
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
    },

    async downloadInstructorEmailTemplate(): Promise<void> {
        const response = await api.get('/import/instructor-emails/template', {
            responseType: 'blob',
        });

        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'instructor_email_template.xlsx');
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
    },

    async validateInstructorEmails(file: File): Promise<any> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post('/import/instructor-emails/validate', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    async executeInstructorEmails(file: File, dryRun: boolean = false): Promise<any> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post(`/import/instructor-emails/execute?dry_run=${dryRun}`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },
};













