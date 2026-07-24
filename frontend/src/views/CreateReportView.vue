<script setup lang="ts">
import { ArrowLeft, ArrowRight, Check, MagicStick, Plus } from '@element-plus/icons-vue';
import { isAxiosError } from 'axios';
import { ElMessage } from 'element-plus';
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import {
  checkMissingInfo,
  createReport,
  createTemplate,
  extractTasks,
  generateReport,
  listTemplates,
  uploadFile,
} from '@/api/reportflow';
import FileUploader from '@/components/FileUploader.vue';
import ReportPreview from '@/components/ReportPreview.vue';
import TaskEditor from '@/components/TaskEditor.vue';
import type {
  FileUploadResult,
  MissingInformationResult,
  OCRResult,
  ReportContent,
  TaskItem,
  Template,
} from '@/types/reportflow';

const route = useRoute();
const router = useRouter();
const step = ref(0);
const reportType = ref((route.query.type as string) || 'daily');
const templateId = ref<number | null>(
  typeof route.query.template_id === 'string' ? Number(route.query.template_id) : null,
);
const templates = ref<Template[]>([]);

const uploadedFiles = ref<FileUploadResult[]>([]);
const ocrTexts = ref<string[]>([]);
const ocrText = computed(() => ocrTexts.value.join('\n'));
const ocrLoading = ref(false);
const manualText = ref('');
const sourceText = computed(() => [ocrText.value, manualText.value].filter(Boolean).join('\n'));
const hasSourceMaterial = computed(() => Boolean(sourceText.value.trim() || uploadedFiles.value.length));

const tasks = ref<TaskItem[]>([]);
const extracting = ref(false);
const missing = ref<MissingInformationResult | null>(null);
const checking = ref(false);
const answers = ref<Record<string, string>>({});
// 证据文件：key 为 missing_field 名，value 为上传结果数组
const evidenceFiles = ref<Record<string, FileUploadResult[]>>({});
const evidenceUploading = ref(false);

function isEvidenceField(field: string): boolean {
  const keywords = ['evidence', 'attachment', 'image', 'photo', 'screenshot',
    'file', 'upload', '证据', '附件', '截图', '图片', '文件', '照片', '凭证', '附件材料'];
  const lower = field.toLowerCase();
  return keywords.some((kw) => lower.includes(kw));
}

async function onEvidenceUpload(field: string, file: File) {
  evidenceUploading.value = true;
  try {
    const result = await uploadFile(file);
    if (result.code === 0 && result.data) {
      const current = evidenceFiles.value[field] || [];
      evidenceFiles.value = { ...evidenceFiles.value, [field]: [...current, result.data] };
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
const reportTitle = ref('');
const reportDate = ref(new Date().toISOString().slice(0, 10));
const style = ref('concise');
const selectedTemplate = computed(
  () => templates.value.find((template) => template.id === templateId.value) || null,
);
const selectedTemplateFields = computed(() => {
  const fields = selectedTemplate.value?.field_config?.fields;
  return Array.isArray(fields)
    ? fields.filter((field): field is string => typeof field === 'string')
    : [];
});

onMounted(async () => {
  await loadTemplateList();
});

async function loadTemplateList() {
  try {
    const response = await listTemplates();
    templates.value = response.data || [];
  } catch (error) {
    ElMessage.warning(error instanceof Error ? error.message : '模板列表加载失败');
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
    const uploadRes = await uploadFile(file);
    if (uploadRes.code !== 0 || !uploadRes.data) {
      ElMessage.error(uploadRes.message || '上传失败');
      return;
    }
    const createRes = await createTemplate({
      name: file.name.replace(/\.[^.]+$/, ''),
      file_path: uploadRes.data.file_id,
      template_type: reportType.value,
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
}

function onUploadCleared() {
  uploadedFiles.value = [];
  ocrTexts.value = [];
}

function onOCRResult(result: OCRResult) {
  ocrTexts.value = [...ocrTexts.value, result.text];
  manualText.value = [manualText.value, result.text].filter(Boolean).join('\n');
}

function onOCRLoading(value: boolean) {
  ocrLoading.value = value;
}

async function doExtract() {
  if (!sourceText.value) return;
  extracting.value = true;
  try {
    const response = await extractTasks({
      source_text: sourceText.value,
      report_type: reportType.value,
      context: {
        uploaded_files: uploadedFiles.value,
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

async function doCheckMissing() {
  checking.value = true;
  try {
    const response = await checkMissingInfo({
      tasks: tasks.value,
      template_id: templateId.value,
      template_fields: selectedTemplateFields.value,
      source_data: {
        answers: answers.value,
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

async function doGenerate() {
  generating.value = true;
  try {
    const response = await generateReport({
      report_type: reportType.value,
      title:
        reportTitle.value ||
        `${reportType.value === 'daily' ? '日报' : '周报'} - ${reportDate.value}`,
      report_date: reportDate.value,
      tasks: tasks.value,
      template_id: templateId.value,
      template_fields: selectedTemplateFields.value,
      style: style.value,
      source_data: {
        answers: answers.value,
        uploaded_files: uploadedFiles.value,
        ocr_text: ocrText.value,
        template_fields: selectedTemplateFields.value,
        evidence_files: evidenceFiles.value,
      },
    });
    report.value = response.data;
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

async function saveAndEdit() {
  if (!report.value) return;
  saving.value = true;
  try {
    const response = await createReport({
      report_type: report.value.report_type,
      title: report.value.title,
      report_date: report.value.date,
      template_id: templateId.value,
      source_data: {
        content: report.value,
        answers: answers.value,
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

    <el-steps :active="step" align-center finish-status="success" style="margin-bottom: 28px">
      <el-step title="上传素材" description="截图或文档" />
      <el-step title="确认任务" description="AI 自动提取" />
      <el-step title="补充信息" description="检查缺失项" />
      <el-step title="生成预览" description="确认并保存" />
    </el-steps>

    <div v-show="step === 0">
      <el-card shadow="never">
        <FileUploader
          @uploaded="onUploaded"
          @cleared="onUploadCleared"
          @ocr-result="onOCRResult"
          @ocr-loading="onOCRLoading"
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
          <el-button type="primary" :icon="ArrowRight" :disabled="!hasSourceMaterial" @click="step = 1">
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
              :disabled="!sourceText"
              @click="doExtract"
            >
              AI 提取任务
            </el-button>
          </div>
        </template>
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
                <div v-if="(evidenceFiles[missing.missing_fields[index]] || []).length" class="evidence-list">
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
            <el-input v-else v-model="answers[missing.missing_fields[index]]" placeholder="请输入..." />
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
                @visible-change="(visible: boolean) => { if (visible) loadTemplateList(); }"
              >
                <el-option
                  v-for="tpl in templates"
                  :key="tpl.id"
                  :label="tpl.name"
                  :value="tpl.id"
                />
              </el-select>
              <el-button
                :icon="Plus"
                :loading="templateUploading"
                @click="pickTemplateFile"
              >
                添加模板
              </el-button>
            </div>
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
            <el-button @click="doGenerate">重新生成</el-button>
            <el-button type="primary" :icon="Check" :loading="saving" @click="saveAndEdit">
              保存并进入在线编辑
            </el-button>
          </div>
        </div>
      </div>
      <el-empty v-else description="报表生成失败，请返回上一步重试。" />
    </div>
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
</style>
