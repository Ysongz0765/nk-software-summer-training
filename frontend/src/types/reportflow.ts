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
  name: string;
  description?: string | null;
  template_type: string;
  file_id?: number | null;
  field_config: Record<string, unknown>;
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
  file_id: string;
  original_name: string;
  stored_name: string;
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

export interface TaskExtractionRequest {
  source_text: string;
  report_type: string;
  context?: Record<string, unknown>;
}

export interface ReportGenerationRequest {
  report_type: string;
  title: string;
  report_date: string;
  tasks: TaskItem[];
  template_id?: number | null;
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
  report_id: number;
  version_number: number;
  content?: ReportContent | Record<string, unknown>;
  change_note?: string | null;
}

export interface ReportSummary {
  id?: number;
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
