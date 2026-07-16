import { http } from './http';
import type { ApiResponse, HealthStatus, ReportContent, TaskItem } from '@/types/reportflow';

export async function getHealth(): Promise<ApiResponse<HealthStatus>> {
  const response = await http.get<ApiResponse<HealthStatus>>('/health');
  return response.data;
}

export async function extractTasks(sourceText: string): Promise<ApiResponse<TaskItem[]>> {
  const response = await http.post<ApiResponse<TaskItem[]>>('/ai/extract-tasks', {
    source_text: sourceText,
    report_type: 'daily',
  });
  return response.data;
}

export async function generateReport(payload: {
  report_type: string;
  title: string;
  report_date: string;
  tasks: TaskItem[];
}): Promise<ApiResponse<ReportContent>> {
  const response = await http.post<ApiResponse<ReportContent>>('/ai/generate-report', payload);
  return response.data;
}
