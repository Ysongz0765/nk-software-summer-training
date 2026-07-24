export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T | null;
}

export interface TaskItem {
  id: string;
  title: string;
  description?: string | null;
  status: string;
  progress: number;
  start_time?: string | null;
  end_time?: string | null;
  evidence_file_ids: number[];
  confidence: number;
  source: string;
  user_confirmed: boolean;
}

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ReportContent {
  report_type: string;
  title: string;
  date: string;
  summary: string;
  completed_tasks: TaskItem[];
  in_progress_tasks: TaskItem[];
  problems: string[];
  solutions: string[];
  next_plan: string[];
  custom_fields: Record<string, unknown>;
  missing_fields: string[];
  style: string;
}

export interface Report {
  id: number;
  user_id?: number | null;
  project_id?: number | null;
  project?: ProjectReference | null;
  template_id?: number | null;
  report_type: string;
  title: string;
  report_date: string;
  status: string;
  content: ReportContent | Record<string, unknown>;
  source_data: Record<string, unknown>;
}

export interface Template {
  id: number;
  user_id?: number | null;
  project_id?: number | null;
  name: string;
  description?: string | null;
  template_type: string;
  file_id?: number | null;
  field_config: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface TemplatePreview {
  id: number;
  name: string;
  template_type: string;
  source: string;
  preview_mode: string;
  fields: string[];
  raw_placeholders: string[];
  body: string;
  html?: string | null;
  description?: string | null;
}

export interface UploadedFile {
  id: number | string;
  user_id?: number | null;
  original_name: string;
  stored_name: string;
  file_type?: string;
  file_size?: number;
  storage_path?: string;
  status?: string;
  created_at?: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
}

export interface FileUploadResult {
  id?: number;
  record_id?: number;
  file_id: string;
  project_id?: number | null;
  original_name: string;
  stored_name: string;
  file_type?: string;
  file_size?: number;
  storage_path?: string;
}

export interface OCRResult {
  text: string;
  pages: number;
  confidence: number;
  language: string;
}

export interface MissingInformationResult {
  missing_fields: string[];
  questions: string[];
  confidence: number;
}

export interface MissingInformationRequest {
  tasks: TaskItem[];
  project_id?: number | null;
  template_id?: number | null;
  template_fields?: string[];
  source_data?: Record<string, unknown>;
}

export interface TaskExtractionRequest {
  source_text: string;
  report_type: string;
  context?: Record<string, unknown>;
}

export interface ReportGenerationRequest {
  report_type: string;
  title: string;
  report_date: string;
  project_id?: number | null;
  start_date?: string | null;
  end_date?: string | null;
  tasks: TaskItem[];
  file_ids?: number[];
  task_ids?: number[];
  user_notes?: string;
  template_id?: number | null;
  template_fields?: string[];
  style?: string;
  source_data?: Record<string, unknown>;
}

export interface ExportResult {
  export_type: string;
  file_path: string;
  status: string;
  download_url?: string | null;
}

export interface ReportVersion {
  id: number;
  report_id: number;
  version_number: number;
  content?: ReportContent | Record<string, unknown>;
  change_note?: string | null;
  created_at?: string | null;
}

export interface ReportSummary {
  id: number;
  project_id?: number | null;
  report_type: string;
  title: string;
  report_date: string;
  status: string;
  task_count: number;
}

export interface TemplateParseResult {
  template_type: string;
  fields: string[];
  description: string;
  raw_content: Record<string, unknown>;
}

export interface ProjectReference {
  id: number;
  name: string;
  status: string;
  current_stage?: string | null;
}

export interface Project {
  id: number;
  user_id: number;
  name: string;
  description?: string | null;
  project_type?: string | null;
  status: string;
  current_stage?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  tech_stack: string[];
  background_summary?: string | null;
  last_activity_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  file_count?: number;
  report_count?: number;
  task_total?: number;
  task_completed?: number;
}

export interface ProjectTask {
  id: number;
  project_id: number;
  title: string;
  description?: string | null;
  module?: string | null;
  status: string;
  priority?: string | null;
  owner?: string | null;
  start_date?: string | null;
  due_date?: string | null;
  completed_at?: string | null;
  source_type?: string | null;
  confidence?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ProjectMember {
  id: number;
  project_id: number;
  name: string;
  role?: string | null;
  responsibility?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ProjectMemory {
  id: number;
  project_id: number;
  memory_type: string;
  content: string;
  source_ids: number[];
  is_user_confirmed: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ProjectFile {
  id: number;
  user_id?: number | null;
  project_id?: number | null;
  original_name: string;
  stored_name: string;
  file_type: string;
  file_size: number;
  storage_path: string;
  status: string;
  created_at?: string | null;
}

export interface ProjectReport {
  id: number;
  project_id?: number | null;
  report_type: string;
  title: string;
  report_date: string;
  status: string;
  task_count: number;
}

export interface ProjectContext {
  project: Project;
  members: ProjectMember[];
  recent_tasks: ProjectTask[];
  completed_tasks: ProjectTask[];
  in_progress_tasks: ProjectTask[];
  blocked_tasks: ProjectTask[];
  recent_files: ProjectFile[];
  recent_reports: ProjectReport[];
  project_memories: ProjectMemory[];
  background_summary: string;
}

export interface ProjectSummarySuggestion {
  generated_summary: string;
  suggested_current_stage?: string | null;
  suggested_tech_stack: string[];
  suggested_completed_work: string[];
  suggested_current_problems: string[];
}
