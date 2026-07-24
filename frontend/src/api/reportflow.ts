import { http } from './http';
import type {
  ApiResponse,
  AuthResponse,
  ExportResult,
  FileTextResult,
  FileUploadResult,
  HealthStatus,
  MissingInformationRequest,
  MissingInformationResult,
  OCRResult,
  Project,
  ProjectContext,
  ProjectFile,
  ProjectMember,
  ProjectSummarySuggestion,
  ProjectTask,
  Report,
  ReportContent,
  ReportGenerationRequest,
  ReportSummary,
  ReportVersion,
  TaskExtractionRequest,
  TaskItem,
  Template,
  TemplateParseResult,
  TemplatePreview,
  User,
} from '@/types/reportflow';

export async function getHealth(): Promise<ApiResponse<HealthStatus>> {
  const response = await http.get<ApiResponse<HealthStatus>>('/health');
  return response.data;
}

export async function register(payload: {
  username: string;
  email: string;
  password: string;
}): Promise<ApiResponse<AuthResponse>> {
  const response = await http.post<ApiResponse<AuthResponse>>('/auth/register', payload);
  return response.data;
}

export async function login(payload: {
  username: string;
  password: string;
}): Promise<ApiResponse<AuthResponse>> {
  const response = await http.post<ApiResponse<AuthResponse>>('/auth/login', payload);
  return response.data;
}

export async function getMe(): Promise<ApiResponse<User>> {
  const response = await http.get<ApiResponse<User>>('/auth/me');
  return response.data;
}

export async function uploadFile(
  file: File,
  projectId?: number | null,
): Promise<ApiResponse<FileUploadResult>> {
  const fd = new FormData();
  fd.append('file', file);
  if (projectId) fd.append('project_id', String(projectId));
  const response = await http.post<ApiResponse<FileUploadResult>>('/files/upload', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  });
  return response.data;
}

export async function getFileInfo(
  fileId: string,
): Promise<ApiResponse<{ file_id: string; path: string }>> {
  const response = await http.get(`/files/${fileId}`);
  return response.data;
}

export async function extractFileText(fileId: string): Promise<ApiResponse<FileTextResult>> {
  const response = await http.get<ApiResponse<FileTextResult>>(`/files/${fileId}/text`);
  return response.data;
}

export async function recognizeFile(filePath: string): Promise<ApiResponse<OCRResult>> {
  const response = await http.post<ApiResponse<OCRResult>>('/ocr/recognize', {
    file_path: filePath,
  });
  return response.data;
}

export async function extractTasks(
  payload: TaskExtractionRequest,
): Promise<ApiResponse<TaskItem[]>> {
  const response = await http.post<ApiResponse<TaskItem[]>>('/ai/extract-tasks', payload);
  return response.data;
}

export async function checkMissingInfo(
  payload: TaskItem[] | MissingInformationRequest,
): Promise<ApiResponse<MissingInformationResult>> {
  const response = await http.post<ApiResponse<MissingInformationResult>>(
    '/ai/check-missing',
    payload,
  );
  return response.data;
}

export async function generateReport(
  payload: ReportGenerationRequest,
): Promise<ApiResponse<ReportContent>> {
  const response = await http.post<ApiResponse<ReportContent>>('/ai/generate-report', payload);
  return response.data;
}

export async function createReport(payload: {
  report_type: string;
  title: string;
  report_date: string;
  project_id?: number | null;
  template_id?: number | null;
  source_data?: Record<string, unknown>;
}): Promise<ApiResponse<Report>> {
  const response = await http.post<ApiResponse<Report>>('/reports', payload);
  return response.data;
}

export async function listReports(
  projectId?: number | null,
): Promise<ApiResponse<ReportSummary[]>> {
  const response = await http.get<ApiResponse<ReportSummary[]>>('/reports', {
    params: projectId ? { project_id: projectId } : undefined,
  });
  return response.data;
}

export async function getReport(reportId: number): Promise<ApiResponse<Report>> {
  const response = await http.get<ApiResponse<Report>>(`/reports/${reportId}`);
  return response.data;
}

export async function updateReport(
  reportId: number,
  payload: { title?: string; status?: string; content?: ReportContent },
): Promise<ApiResponse<Report>> {
  const response = await http.put<ApiResponse<Report>>(`/reports/${reportId}`, payload);
  return response.data;
}

export async function deleteReport(reportId: number): Promise<ApiResponse<{ id: number }>> {
  const response = await http.delete<ApiResponse<{ id: number }>>(`/reports/${reportId}`);
  return response.data;
}

export async function createVersion(
  reportId: number,
  content: ReportContent,
): Promise<ApiResponse<ReportVersion>> {
  const response = await http.post<ApiResponse<ReportVersion>>(
    `/reports/${reportId}/versions`,
    content,
  );
  return response.data;
}

export async function listVersions(reportId: number): Promise<ApiResponse<ReportVersion[]>> {
  const response = await http.get<ApiResponse<ReportVersion[]>>(`/reports/${reportId}/versions`);
  return response.data;
}

export async function exportReport(
  reportId: number,
  exportType: string,
  templatePath?: string,
  templateId?: number | null,
): Promise<ApiResponse<ExportResult>> {
  const response = await http.post<ApiResponse<ExportResult>>(`/reports/${reportId}/export`, {
    export_type: exportType,
    template_path: templatePath || null,
    template_id: templateId || null,
  });
  return response.data;
}

export async function listTemplates(projectId?: number | null): Promise<ApiResponse<Template[]>> {
  const response = await http.get<ApiResponse<Template[]>>('/templates', {
    params: projectId ? { project_id: projectId } : undefined,
  });
  return response.data;
}

export async function getTemplate(templateId: number): Promise<ApiResponse<Template>> {
  const response = await http.get<ApiResponse<Template>>(`/templates/${templateId}`);
  return response.data;
}

export async function previewTemplate(templateId: number): Promise<ApiResponse<TemplatePreview>> {
  const response = await http.get<ApiResponse<TemplatePreview>>(`/templates/${templateId}/preview`);
  return response.data;
}

export async function createTemplate(payload: {
  name: string;
  description?: string | null;
  template_type: string;
  project_id?: number | null;
  file_path?: string | null;
  file_id?: number | null;
  field_config?: Record<string, unknown>;
}): Promise<ApiResponse<Template>> {
  const response = await http.post<ApiResponse<Template>>('/templates', payload, {
    timeout: 60000,
  });
  return response.data;
}

export async function parseTemplate(filePath: string): Promise<ApiResponse<TemplateParseResult>> {
  const response = await http.post<ApiResponse<TemplateParseResult>>('/templates/parse', {
    file_path: filePath,
  });
  return response.data;
}

export async function deleteTemplate(templateId: number): Promise<ApiResponse<{ id: number }>> {
  const response = await http.delete<ApiResponse<{ id: number }>>(`/templates/${templateId}`);
  return response.data;
}

export async function createProject(payload: {
  name: string;
  description?: string | null;
  project_type?: string | null;
  status?: string;
  current_stage?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  tech_stack?: string[];
  background_summary?: string | null;
}): Promise<ApiResponse<Project>> {
  const response = await http.post<ApiResponse<Project>>('/projects', payload);
  return response.data;
}

export async function listProjects(status?: string | null): Promise<ApiResponse<Project[]>> {
  const response = await http.get<ApiResponse<Project[]>>('/projects', {
    params: status ? { status } : undefined,
  });
  return response.data;
}

export async function getProject(projectId: number): Promise<ApiResponse<Project>> {
  const response = await http.get<ApiResponse<Project>>(`/projects/${projectId}`);
  return response.data;
}

export async function updateProject(
  projectId: number,
  payload: Partial<Project>,
): Promise<ApiResponse<Project>> {
  const response = await http.patch<ApiResponse<Project>>(`/projects/${projectId}`, payload);
  return response.data;
}

export async function archiveProject(projectId: number): Promise<ApiResponse<{ id: number }>> {
  const response = await http.delete<ApiResponse<{ id: number }>>(`/projects/${projectId}`);
  return response.data;
}

export async function createProjectTask(
  projectId: number,
  payload: {
    title: string;
    description?: string | null;
    module?: string | null;
    status?: string;
    priority?: string | null;
    owner?: string | null;
    start_date?: string | null;
    due_date?: string | null;
  },
): Promise<ApiResponse<ProjectTask>> {
  const response = await http.post<ApiResponse<ProjectTask>>(
    `/projects/${projectId}/tasks`,
    payload,
  );
  return response.data;
}

export async function listProjectTasks(
  projectId: number,
  params?: { status?: string | null; module?: string | null },
): Promise<ApiResponse<ProjectTask[]>> {
  const response = await http.get<ApiResponse<ProjectTask[]>>(`/projects/${projectId}/tasks`, {
    params,
  });
  return response.data;
}

export async function updateProjectTask(
  projectId: number,
  taskId: number,
  payload: Partial<ProjectTask>,
): Promise<ApiResponse<ProjectTask>> {
  const response = await http.patch<ApiResponse<ProjectTask>>(
    `/projects/${projectId}/tasks/${taskId}`,
    payload,
  );
  return response.data;
}

export async function deleteProjectTask(
  projectId: number,
  taskId: number,
): Promise<ApiResponse<{ id: number }>> {
  const response = await http.delete<ApiResponse<{ id: number }>>(
    `/projects/${projectId}/tasks/${taskId}`,
  );
  return response.data;
}

export async function createProjectMember(
  projectId: number,
  payload: { name: string; role?: string | null; responsibility?: string | null },
): Promise<ApiResponse<ProjectMember>> {
  const response = await http.post<ApiResponse<ProjectMember>>(
    `/projects/${projectId}/members`,
    payload,
  );
  return response.data;
}

export async function listProjectMembers(projectId: number): Promise<ApiResponse<ProjectMember[]>> {
  const response = await http.get<ApiResponse<ProjectMember[]>>(`/projects/${projectId}/members`);
  return response.data;
}

export async function updateProjectMember(
  projectId: number,
  memberId: number,
  payload: Partial<ProjectMember>,
): Promise<ApiResponse<ProjectMember>> {
  const response = await http.patch<ApiResponse<ProjectMember>>(
    `/projects/${projectId}/members/${memberId}`,
    payload,
  );
  return response.data;
}

export async function deleteProjectMember(
  projectId: number,
  memberId: number,
): Promise<ApiResponse<{ id: number }>> {
  const response = await http.delete<ApiResponse<{ id: number }>>(
    `/projects/${projectId}/members/${memberId}`,
  );
  return response.data;
}

export async function listProjectFiles(projectId: number): Promise<ApiResponse<ProjectFile[]>> {
  const response = await http.get<ApiResponse<ProjectFile[]>>(`/projects/${projectId}/files`);
  return response.data;
}

export async function getProjectContext(projectId: number): Promise<ApiResponse<ProjectContext>> {
  const response = await http.get<ApiResponse<ProjectContext>>(`/projects/${projectId}/context`);
  return response.data;
}

export async function generateProjectSummary(
  projectId: number,
): Promise<ApiResponse<ProjectSummarySuggestion>> {
  const response = await http.post<ApiResponse<ProjectSummarySuggestion>>(
    `/projects/${projectId}/generate-summary`,
  );
  return response.data;
}
