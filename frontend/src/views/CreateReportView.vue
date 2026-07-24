<script setup lang="ts">
import { ArrowLeft, ArrowRight, Check, MagicStick, Plus } from '@element-plus/icons-vue';
import { isAxiosError } from 'axios';
import { ElMessage } from 'element-plus';
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import {
  checkMissingInfo,
  createReport,
  createTemplate,
  extractFileText,
  extractTasks,
  generateReport,
  getProjectContext,
  listTemplates,
  recognizeFile,
  uploadFile,
} from '@/api/reportflow';
import FileUploader from '@/components/FileUploader.vue';
import ReportPreview from '@/components/ReportPreview.vue';
import TaskEditor from '@/components/TaskEditor.vue';
import { useAppStore } from '@/stores/app';
import type {
  FileUploadResult,
  MissingInformationResult,
  ProjectContext,
  ReportContent,
  TaskItem,
  Template,
} from '@/types/reportflow';

const route = useRoute();
const router = useRouter();
const appStore = useAppStore();
const step = ref(0);
const reportType = ref((route.query.type as string) || 'daily');
const projectId = ref<number | null>(
  typeof route.query.project_id === 'string' ? Number(route.query.project_id) : null,
);
const templateId = ref<number | null>(
  typeof route.query.template_id === 'string' ? Number(route.query.template_id) : null,
);
const templates = ref<Template[]>([]);
const projectContext = ref<ProjectContext | null>(null);
const contextLoading = ref(false);
const selectedFileIds = ref<number[]>([]);
const selectedTaskIds = ref<number[]>([]);

const uploadedFiles = ref<FileUploadResult[]>([]);
const ocrTexts = ref<string[]>([]);
const ocrText = computed(() => ocrTexts.value.join('\n'));
const ocrLoading = ref(false);
const manualText = ref('');
const sourceText = computed(() => [ocrText.value, manualText.value].filter(Boolean).join('\n'));
const hasSourceMaterial = computed(() =>
  Boolean(sourceText.value.trim() || uploadedFiles.value.length),
);

const tasks = ref<TaskItem[]>([]);
const extracting = ref(false);
const missing = ref<MissingInformationResult | null>(null);
const checking = ref(false);
const answers = ref<Record<string, string>>({});
// 证据文件：key 为 missing_field 名，value 为上传结果数组
const evidenceFiles = ref<Record<string, FileUploadResult[]>>({});
const evidenceUploading = ref(false);

function isEvidenceField(field: string): boolean {
  const keywords = [
    'evidence',
    'attachment',
    'image',
    'photo',
    'screenshot',
    'file',
    'upload',
    '证据',
    '附件',
    '截图',
    '图片',
    '文件',
    '照片',
    '凭证',
    '附件材料',
  ];
  const lower = field.toLowerCase();
  return keywords.some((kw) => lower.includes(kw));
}

async function onEvidenceUpload(field: string, file: File) {
  evidenceUploading.value = true;
  try {
    const result = await uploadFile(file, projectId.value);
    if (result.code === 0 && result.data) {
      const current = evidenceFiles.value[field] || [];
      evidenceFiles.value = { ...evidenceFiles.value, [field]: [...current, result.data] };
      if (result.data.record_id && !selectedFileIds.value.includes(result.data.record_id)) {
        selectedFileIds.value = [...selectedFileIds.value, result.data.record_id];
      }
    }
  } catch {
    ElMessage.error(`${file.name} 上传失败`);
  } finally {
    evidenceUploading.value = false;
  }
}

function pickEvidenceFile(field: string) {
  const input = document.createElement('input');
  input.type = 'file';
  input.multiple = true;
  input.accept = '.png,.jpg,.jpeg,.pdf,.docx,.xlsx,.txt';
  input.onchange = () => {
    if (input.files) {
      for (const file of input.files) void onEvidenceUpload(field, file);
    }
  };
  input.click();
}

function removeEvidenceFile(field: string, index: number) {
  const current = evidenceFiles.value[field] || [];
  evidenceFiles.value = {
    ...evidenceFiles.value,
    [field]: current.filter((_, i) => i !== index),
  };
}

const report = ref<ReportContent | null>(null);
const generating = ref(false);
const saving = ref(false);
const regenerateDialogVisible = ref(false);
const regenerationInstruction = ref('');
const regenerationCount = ref(0);
const reportTitle = ref('');
const reportDate = ref(new Date().toISOString().slice(0, 10));
const style = ref('concise');
const selectedTemplate = computed(
  () => templates.value.find((template) => template.id === templateId.value) || null,
);
const currentProject = computed(
  () => appStore.projects.find((project) => project.id === projectId.value) || null,
);
const selectedTemplateFields = computed(() => {
  const fields = selectedTemplate.value?.field_config?.fields;
  return Array.isArray(fields)
    ? fields.filter((field): field is string => typeof field === 'string')
    : [];
});
const contextSummary = computed(() => {
  if (!projectContext.value) return null;
  return {
    files: selectedFileIds.value.length || projectContext.value.recent_files.length,
    tasks: selectedTaskIds.value.length || projectContext.value.recent_tasks.length,
    reports: projectContext.value.recent_reports.length,
    blocked: projectContext.value.blocked_tasks.length,
  };
});

interface UploadedSourceText {
  file_id: string;
  original_name: string;
  file_type: string;
  source: 'text' | 'ocr';
  text: string;
  pages?: number;
  confidence?: number;
}

const TEXT_READ_FILE_TYPES = new Set(['txt', 'docx', 'xlsx']);
const OCR_FILE_TYPES = new Set(['png', 'jpg', 'jpeg']);

onMounted(async () => {
  await appStore.refreshProjects();
  if (!projectId.value) projectId.value = appStore.currentProjectId;
  await loadTemplateAndContext();
});

watch(projectId, async (value) => {
  appStore.setCurrentProject(value || null);
  templateId.value = null;
  selectedFileIds.value = [];
  selectedTaskIds.value = [];
  await loadTemplateAndContext();
});

async function loadTemplateAndContext() {
  await Promise.all([loadTemplateList(), loadProjectContext()]);
}

async function loadTemplateList() {
  try {
    const response = await listTemplates(projectId.value);
    templates.value = response.data || [];
  } catch (error) {
    ElMessage.warning(error instanceof Error ? error.message : '模板列表加载失败');
  }
}

async function loadProjectContext() {
  projectContext.value = null;
  if (!projectId.value) return;
  contextLoading.value = true;
  try {
    const response = await getProjectContext(projectId.value);
    projectContext.value = response.data;
  } catch (error) {
    ElMessage.warning(error instanceof Error ? error.message : '项目上下文加载失败');
  } finally {
    contextLoading.value = false;
  }
}

/* ---------- 模板上传 ---------- */
const MAX_TEMPLATE_BYTES = 20 * 1024 * 1024;
const TEMPLATE_EXTENSIONS = ['.docx', '.xlsx', '.pdf'];
const templateUploading = ref(false);

function pickTemplateFile() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.docx,.xlsx,.pdf';
  input.onchange = () => {
    const file = input.files?.[0];
    if (file) void handleTemplateUpload(file);
  };
  input.click();
}

async function handleTemplateUpload(file: File) {
  const suffix = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
  if (!TEMPLATE_EXTENSIONS.includes(suffix)) {
    ElMessage.error('模板仅支持 DOCX / XLSX / PDF');
    return;
  }
  if (file.size > MAX_TEMPLATE_BYTES) {
    ElMessage.error('模板文件不能超过 20MB');
    return;
  }

  templateUploading.value = true;
  try {
    const uploadRes = await uploadFile(file, projectId.value);
    if (uploadRes.code !== 0 || !uploadRes.data) {
      ElMessage.error(uploadRes.message || '上传失败');
      return;
    }
    const createRes = await createTemplate({
      name: file.name.replace(/\.[^.]+$/, ''),
      file_path: uploadRes.data.file_id,
      template_type: reportType.value,
      project_id: projectId.value,
    });
    await loadTemplateList();
    // 自动选中新上传的模板
    templateId.value = createRes.data?.id ?? null;
    ElMessage.success(`模板「${createRes.data?.name || file.name}」已添加并选中`);
  } catch (error) {
    const msg = isAxiosError(error)
      ? (error.response?.data as { message?: string })?.message || error.message
      : error instanceof Error
        ? error.message
        : '模板上传失败';
    ElMessage.error(msg);
  } finally {
    templateUploading.value = false;
  }
}

function onUploaded(file: FileUploadResult) {
  uploadedFiles.value = [...uploadedFiles.value, file];
  if (file.record_id && !selectedFileIds.value.includes(file.record_id)) {
    selectedFileIds.value = [...selectedFileIds.value, file.record_id];
  }
  void loadProjectContext();
}

function onUploadCleared() {
  const uploadedRecordIds = new Set(
    uploadedFiles.value
      .map((file) => file.record_id)
      .filter((id): id is number => typeof id === 'number'),
  );
  selectedFileIds.value = selectedFileIds.value.filter((id) => !uploadedRecordIds.has(id));
  uploadedFiles.value = [];
  ocrTexts.value = [];
  void loadProjectContext();
}

async function doExtract() {
  if (!hasSourceMaterial.value) return;
  extracting.value = true;
  try {
    const uploadedSourceTexts = await readUploadedFileTexts();
    const sourceForExtraction = [
      ...uploadedSourceTexts.map((result) => result.text),
      manualText.value,
    ]
      .filter((text) => text.trim())
      .join('\n');

    if (!sourceForExtraction.trim()) {
      tasks.value = [];
      ElMessage.warning('未识别到可用于任务提取的文本，可以手动补充工作内容');
      return;
    }

    const response = await extractTasks({
      source_text: sourceForExtraction,
      report_type: reportType.value,
      context: {
        project_id: projectId.value,
        project_context: projectContext.value,
        uploaded_files: uploadedFiles.value,
        source_texts: uploadedSourceTexts,
        evidence_files: evidenceFiles.value,
        template_id: templateId.value,
        template_fields: selectedTemplateFields.value,
      },
    });
    tasks.value = (response.data || []).map((task) => ({ ...task, user_confirmed: false }));
    if (!tasks.value.length) ElMessage.warning('没有识别到任务，可以手动添加');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '任务提取失败');
  } finally {
    extracting.value = false;
  }
}

async function readUploadedFileTexts(): Promise<UploadedSourceText[]> {
  if (!uploadedFiles.value.length) {
    ocrTexts.value = [];
    return [];
  }

  ocrLoading.value = true;
  try {
    const results = await Promise.all(
      uploadedFiles.value.map((file) => readUploadedFileText(file)),
    );
    const readableResults = results.filter((result): result is UploadedSourceText =>
      Boolean(result?.text.trim()),
    );
    ocrTexts.value = readableResults.map((result) => result.text);
    return readableResults;
  } finally {
    ocrLoading.value = false;
  }
}

async function readUploadedFileText(file: FileUploadResult): Promise<UploadedSourceText | null> {
  const fileType = normalizeFileType(file);
  if (TEXT_READ_FILE_TYPES.has(fileType)) {
    return extractUploadedFileText(file);
  }
  if (fileType === 'pdf') {
    const textResult = await extractUploadedFileText(file, false);
    if (textResult?.text.trim()) return textResult;
    return recognizeUploadedFile(file);
  }
  if (OCR_FILE_TYPES.has(fileType)) {
    return recognizeUploadedFile(file);
  }

  ElMessage.warning((file.original_name || file.file_id) + ' is not supported for automatic reading yet, skipped');
  return null;
}

async function extractUploadedFileText(
  file: FileUploadResult,
  warnOnFailure = true,
): Promise<UploadedSourceText | null> {
  try {
    const response = await extractFileText(file.file_id);
    const data = response.data;
    if (!data?.text.trim()) return null;
    return {
      file_id: data.file_id,
      original_name: data.original_name,
      file_type: data.file_type,
      source: 'text',
      text: data.text,
    };
  } catch {
    if (warnOnFailure) {
      ElMessage.warning((file.original_name || file.file_id) + ' text extraction failed, skipped');
    }
    return null;
  }
}

async function recognizeUploadedFile(file: FileUploadResult): Promise<UploadedSourceText | null> {
  try {
    const response = await recognizeFile(file.file_id);
    const data = response.data;
    if (!data?.text.trim()) return null;
    return {
      file_id: file.file_id,
      original_name: file.original_name || file.file_id,
      file_type: normalizeFileType(file),
      source: 'ocr',
      text: data.text,
      pages: data.pages,
      confidence: data.confidence,
    };
  } catch {
    ElMessage.warning((file.original_name || file.file_id) + ' OCR failed, skipped');
    return null;
  }
}

function normalizeFileType(file: FileUploadResult): string {
  const fromType = file.file_type?.trim().toLowerCase();
  if (fromType) return fromType;
  const name = file.original_name || file.file_id;
  return name.includes('.') ? name.split('.').pop()?.toLowerCase() || '' : '';
}async function doCheckMissing() {
  checking.value = true;
  try {
    const response = await checkMissingInfo({
      tasks: tasks.value,
      project_id: projectId.value,
      template_id: templateId.value,
      template_fields: selectedTemplateFields.value,
      source_data: {
        answers: answers.value,
        project_context: projectContext.value,
        uploaded_files: uploadedFiles.value,
        evidence_files: evidenceFiles.value,
      },
    });
    missing.value = response.data;
  } catch (error) {
    missing.value = null;
    ElMessage.error(error instanceof Error ? error.message : '缺失信息检查失败');
  } finally {
    checking.value = false;
  }
}

async function goMissingStep() {
  await doCheckMissing();
  step.value = 2;
}

async function doGenerate(revisionInstruction = '') {
  generating.value = true;
  const revisionInstructionText = revisionInstruction.trim();
  const nextRegenerationIndex = revisionInstructionText
    ? regenerationCount.value + 1
    : regenerationCount.value;
  try {
    const response = await generateReport({
      report_type: reportType.value,
      title:
        reportTitle.value ||
        `${reportType.value === 'daily' ? '日报' : '周报'} - ${reportDate.value}`,
      report_date: reportDate.value,
      project_id: projectId.value,
      start_date: reportDate.value,
      end_date: reportDate.value,
      tasks: tasks.value,
      file_ids: selectedFileIds.value,
      task_ids: selectedTaskIds.value,
      user_notes: manualText.value,
      template_id: templateId.value,
      template_fields: selectedTemplateFields.value,
      style: style.value,
      source_data: {
        answers: answers.value,
        project_context: projectContext.value,
        uploaded_files: uploadedFiles.value,
        ocr_text: ocrText.value,
        template_fields: selectedTemplateFields.value,
        evidence_files: evidenceFiles.value,
        previous_report: revisionInstructionText ? report.value : null,
        revision_instruction: revisionInstructionText,
        regeneration_index: nextRegenerationIndex,
      },
    });
    report.value = response.data;
    if (revisionInstructionText) {
      regenerationCount.value = nextRegenerationIndex;
      regenerationInstruction.value = '';
    }
  } catch (error) {
    report.value = null;
    ElMessage.error(error instanceof Error ? error.message : '报表生成失败');
  } finally {
    generating.value = false;
  }
}

async function goPreviewStep() {
  step.value = 3;
  await doGenerate();
}

function openRegenerateDialog() {
  regenerationInstruction.value = '';
  regenerateDialogVisible.value = true;
}

async function confirmRegenerate() {
  if (!regenerationInstruction.value.trim()) {
    ElMessage.warning('请先输入修改意见');
    return;
  }
  regenerateDialogVisible.value = false;
  await doGenerate(regenerationInstruction.value);
}

async function saveAndEdit() {
  if (!report.value) return;
  saving.value = true;
  try {
    const response = await createReport({
      report_type: report.value.report_type,
      title: report.value.title,
      report_date: report.value.date,
      project_id: projectId.value,
      template_id: templateId.value,
      source_data: {
        content: report.value,
        answers: answers.value,
        project_context: projectContext.value,
        uploaded_files: uploadedFiles.value,
        evidence_files: evidenceFiles.value,
        template_fields: selectedTemplateFields.value,
      },
    });
    if (!response.data?.id) {
      ElMessage.error('报表保存失败');
      return;
    }
    await router.push(`/reports/${response.data.id}/edit`);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '报表保存失败');
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h2>创建报表</h2>
        <p class="muted">{{ reportType === 'daily' ? '日报' : '周报' }} · 四步生成</p>
      </div>
    </div>

    <el-card shadow="never" class="project-context-card" v-loading="contextLoading">
      <el-row :gutter="16">
        <el-col :span="8">
          <label class="field-label">项目</label>
          <el-select v-model="projectId" clearable filterable style="width: 100%">
            <el-option
              v-for="project in appStore.projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-col>
        <el-col :span="8">
          <label class="field-label">报表类型</label>
          <el-select v-model="reportType" style="width: 100%">
            <el-option label="日报" value="daily" />
            <el-option label="周报" value="weekly" />
            <el-option label="阶段总结" value="stage_summary" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <label class="field-label">时间</label>
          <el-date-picker
            v-model="reportDate"
            type="date"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-col>
      </el-row>
      <div v-if="currentProject && contextSummary" class="context-summary">
        <span>当前项目：{{ currentProject.name }}</span>
        <span>项目阶段：{{ currentProject.current_stage || '未设置' }}</span>
        <span>已选择文件：{{ selectedFileIds.length }} 个</span>
        <span>可读取任务：{{ contextSummary.tasks }} 项</span>
        <span>历史报表：{{ contextSummary.reports }} 份</span>
        <span>当前问题：{{ contextSummary.blocked }} 项</span>
      </div>
      <el-alert
        v-else
        type="info"
        :closable="false"
        title="未选择项目时将按旧流程生成无项目报表。"
      />
    </el-card>

    <el-steps :active="step" align-center finish-status="success" style="margin-bottom: 28px">
      <el-step title="上传素材" description="截图或文档" />
      <el-step title="确认任务" description="AI 自动提取" />
      <el-step title="补充信息" description="检查缺失项" />
      <el-step title="生成预览" description="确认并保存" />
    </el-steps>

    <div v-show="step === 0">
      <el-card shadow="never">
        <FileUploader
          :project-id="projectId"
          @uploaded="onUploaded"
          @cleared="onUploadCleared"
        />
        <el-divider>或直接输入文本</el-divider>
        <el-input
          v-model="manualText"
          type="textarea"
          :rows="6"
          placeholder="输入或粘贴工作内容，每行一项任务..."
          :disabled="ocrLoading"
        />
        <div class="step-actions end">
          <el-button
            type="primary"
            :icon="ArrowRight"
            :disabled="!hasSourceMaterial"
            @click="step = 1"
          >
            下一步
          </el-button>
        </div>
      </el-card>
    </div>

    <div v-show="step === 1">
      <el-card shadow="never">
        <template #header>
          <div class="card-hd">
            <strong>任务列表</strong>
            <el-button
              size="small"
              type="primary"
              :loading="extracting"
              :icon="MagicStick"
              :disabled="!hasSourceMaterial"
              @click="doExtract"
            >
              AI 提取任务
            </el-button>
          </div>
        </template>
        <div v-if="!tasks.length" class="step-empty">
          <p>点击“AI 提取任务”从素材中自动识别，或手动添加。</p>
        </div>
        <TaskEditor v-model:tasks="tasks" title="任务列表" />
        <div class="step-actions between">
          <el-button :icon="ArrowLeft" @click="step = 0">上一步</el-button>
          <el-button
            type="primary"
            :icon="ArrowRight"
            :disabled="!tasks.length"
            @click="goMissingStep"
          >
            下一步
          </el-button>
        </div>
      </el-card>
    </div>

    <div v-show="step === 2">
      <el-card shadow="never">
        <template #header>
          <div class="card-hd">
            <strong>信息补充</strong>
            <el-button size="small" :loading="checking" @click="doCheckMissing">
              重新检查
            </el-button>
          </div>
        </template>

        <div v-if="!missing" class="step-empty">
          <p>正在等待缺失信息检查结果。</p>
        </div>
        <div v-else-if="!missing.missing_fields.length">
          <el-result icon="success" title="信息完整" sub-title="可以直接生成报表" />
        </div>
        <div v-else>
          <el-alert
            type="warning"
            :closable="false"
            :title="`以下 ${missing.questions.length} 项建议补充：`"
            style="margin-bottom: 16px"
          />
          <div v-for="(question, index) in missing.questions" :key="question" class="field-row">
            <label class="field-label">{{ index + 1 }}. {{ question }}</label>
            <!-- 证据类字段 → 上传按钮 -->
            <template v-if="isEvidenceField(missing.missing_fields[index])">
              <div class="evidence-area">
                <el-button
                  :icon="Plus"
                  :loading="evidenceUploading"
                  @click="pickEvidenceFile(missing.missing_fields[index])"
                >
                  添加证据文件
                </el-button>
                <div
                  v-if="(evidenceFiles[missing.missing_fields[index]] || []).length"
                  class="evidence-list"
                >
                  <el-tag
                    v-for="(ef, ei) in evidenceFiles[missing.missing_fields[index]]"
                    :key="ef.file_id"
                    closable
                    type="success"
                    @close="removeEvidenceFile(missing.missing_fields[index], ei)"
                  >
                    {{ ef.original_name }}
                  </el-tag>
                </div>
              </div>
            </template>
            <!-- 普通字段 → 输入框 -->
            <el-input
              v-else
              v-model="answers[missing.missing_fields[index]]"
              placeholder="请输入..."
            />
          </div>
        </div>

        <el-divider />
        <el-row :gutter="16">
          <el-col :span="6">
            <label class="field-label">报表标题</label>
            <el-input v-model="reportTitle" placeholder="例：项目日报" />
          </el-col>
          <el-col :span="6">
            <label class="field-label">日期</label>
            <el-date-picker
              v-model="reportDate"
              type="date"
              style="width: 100%"
              value-format="YYYY-MM-DD"
            />
          </el-col>
          <el-col :span="6">
            <label class="field-label">语言风格</label>
            <el-select v-model="style" style="width: 100%">
              <el-option label="简洁专业" value="concise" />
              <el-option label="正式详尽" value="formal" />
              <el-option label="积极汇报" value="positive" />
            </el-select>
          </el-col>
          <el-col :span="6">
            <label class="field-label">模板</label>
            <div class="template-picker">
              <el-select
                v-model="templateId"
                clearable
                placeholder="选择已有模板"
                style="flex: 1"
                @visible-change="
                  (visible: boolean) => {
                    if (visible) loadTemplateList();
                  }
                "
              >
                <el-option
                  v-for="tpl in templates"
                  :key="tpl.id"
                  :label="tpl.name"
                  :value="tpl.id"
                />
              </el-select>
              <el-button :icon="Plus" :loading="templateUploading" @click="pickTemplateFile">
                添加模板
              </el-button>
            </div>
          </el-col>
        </el-row>
        <el-row :gutter="16" style="margin-top: 14px">
          <el-col :span="12">
            <label class="field-label">相关文件</label>
            <el-select
              v-model="selectedFileIds"
              multiple
              clearable
              collapse-tags
              style="width: 100%"
              placeholder="选择本次报表使用的项目文件"
            >
              <el-option
                v-for="file in projectContext?.recent_files || []"
                :key="file.id"
                :label="file.original_name"
                :value="file.id"
              />
            </el-select>
          </el-col>
          <el-col :span="12">
            <label class="field-label">相关任务</label>
            <el-select
              v-model="selectedTaskIds"
              multiple
              clearable
              collapse-tags
              style="width: 100%"
              placeholder="选择本次报表重点任务"
            >
              <el-option
                v-for="task in projectContext?.recent_tasks || []"
                :key="task.id"
                :label="task.title"
                :value="task.id"
              />
            </el-select>
          </el-col>
        </el-row>
        <div class="step-actions between">
          <el-button :icon="ArrowLeft" @click="step = 1">上一步</el-button>
          <el-button type="primary" :icon="ArrowRight" @click="goPreviewStep">
            生成报表预览
          </el-button>
        </div>
      </el-card>
    </div>

    <div v-show="step === 3">
      <el-card v-if="generating" shadow="never" class="generating-card">
        <p>AI 正在生成报表...</p>
      </el-card>
      <div v-else-if="report">
        <ReportPreview :report="report" />
        <div class="step-actions between">
          <el-button :icon="ArrowLeft" @click="step = 2">上一步</el-button>
          <div class="inline-actions">
            <el-button @click="openRegenerateDialog">重新生成</el-button>
            <el-button type="primary" :icon="Check" :loading="saving" @click="saveAndEdit">
              保存并进入在线编辑
            </el-button>
          </div>
        </div>
      </div>
      <el-empty v-else description="报表生成失败，请返回上一步重试。" />
    </div>

    <el-dialog
      v-model="regenerateDialogVisible"
      title="填写修改意见"
      width="560px"
      :close-on-click-modal="!generating"
    >
      <el-input
        v-model="regenerationInstruction"
        type="textarea"
        :rows="5"
        maxlength="800"
        show-word-limit
        placeholder="例如：把总结写得更正式，问题与风险补充到两条，下一步计划改成按时间顺序。"
      />
      <template #footer>
        <el-button @click="regenerateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="confirmRegenerate">
          根据意见重新生成
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.card-hd,
.step-actions {
  display: flex;
  align-items: center;
}

.card-hd {
  justify-content: space-between;
}

.step-actions {
  margin-top: 18px;
}

.between {
  justify-content: space-between;
}

.end {
  justify-content: flex-end;
}

.step-empty,
.generating-card {
  padding: 48px 0;
  color: #667085;
  text-align: center;
}

.field-row {
  margin-bottom: 12px;
}

.field-label {
  display: block;
  margin-bottom: 4px;
  color: #374151;
  font-size: 13px;
  font-weight: 500;
}

.inline-actions {
  display: flex;
  gap: 8px;
}

.template-picker {
  display: flex;
  gap: 8px;
}

.evidence-area {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.evidence-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.project-context-card {
  margin-bottom: 18px;
}

.context-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
  margin-top: 14px;
  color: #475467;
  font-size: 13px;
}
</style>
