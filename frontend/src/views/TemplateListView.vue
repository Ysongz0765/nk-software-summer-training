<script setup lang="ts">
import { Delete, Upload, View } from '@element-plus/icons-vue';
import { isAxiosError } from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import {
  createTemplate,
  deleteTemplate,
  listTemplates,
  previewTemplate,
  uploadFile,
} from '@/api/reportflow';
import type { Template, TemplatePreview } from '@/types/reportflow';

const router = useRouter();
const templates = ref<Template[]>([]);
const loading = ref(false);
const uploading = ref(false);
const previewVisible = ref(false);
const previewLoading = ref(false);
const preview = ref<TemplatePreview | null>(null);
const MAX_TEMPLATE_UPLOAD_BYTES = 20 * 1024 * 1024;
const TEMPLATE_UPLOAD_EXTENSIONS = ['.docx', '.xlsx', '.pdf'];

const typeLabel = (type: string) =>
  ({ daily: '日报', weekly: '周报', monthly: '月报', custom: '自定义' })[type] || type;
const typeTag = (type: string) =>
  ({ daily: 'primary', weekly: 'success', monthly: 'warning', custom: 'info' })[type] || 'info';
const previewSegments = computed(() => splitPreviewBody(preview.value?.body || ''));
const sourcePreviewDocument = computed(() => buildSourcePreviewDocument(preview.value?.html));

onMounted(load);

async function load() {
  loading.value = true;
  try {
    const response = await listTemplates();
    templates.value = response.data || [];
  } catch (error) {
    templates.value = [];
    ElMessage.error(error instanceof Error ? error.message : '模板列表加载失败');
  } finally {
    loading.value = false;
  }
}

function handleUpload() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.docx,.xlsx,.pdf';
  input.onchange = () => {
    const file = input.files?.[0];
    if (file) void uploadTemplate(file);
  };
  input.click();
}

async function uploadTemplate(file: File) {
  const validationError = validateTemplateFile(file);
  if (validationError) {
    ElMessage.error(validationError);
    return;
  }

  uploading.value = true;
  try {
    const uploadResponse = await uploadFile(file);
    if (uploadResponse.code !== 0 || !uploadResponse.data) {
      ElMessage.error(uploadResponse.message || '上传失败');
      return;
    }
    await createTemplate({
      name: file.name.replace(/\.[^.]+$/, ''),
      file_path: uploadResponse.data.file_id,
      template_type:
        file.name.includes('周') || file.name.toLowerCase().includes('week') ? 'weekly' : 'daily',
    });
    await load();
    ElMessage.success('模板已上传');
  } catch (error) {
    ElMessage.error(templateUploadErrorMessage(error));
  } finally {
    uploading.value = false;
  }
}

async function handlePreview(row: Template) {
  previewVisible.value = true;
  previewLoading.value = true;
  preview.value = null;
  try {
    const response = await previewTemplate(row.id);
    preview.value = response.data;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '模板预览加载失败');
  } finally {
    previewLoading.value = false;
  }
}

async function handleDelete(row: Template) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.name}」？`, '删除确认', { type: 'warning' });
    await deleteTemplate(row.id);
    await load();
    ElMessage.success('已删除');
  } catch (error) {
    if (error instanceof Error) ElMessage.error(error.message);
  }
}

function useTemplate(row: Pick<Template, 'id' | 'template_type'>) {
  router.push({
    path: '/reports/create',
    query: {
      type: row.template_type,
      template_id: String(row.id),
    },
  });
}

function splitPreviewBody(body: string) {
  const pattern = /(\{\{\s*[^{}\r\n]+?\s*\}\})/g;
  const placeholderPattern = /^\{\{\s*[^{}\r\n]+?\s*\}\}$/;
  return body
    .split(pattern)
    .filter((text) => text.length)
    .map((text) => ({ text, placeholder: placeholderPattern.test(text) }));
}

function previewModeLabel(mode: string) {
  return mode === 'source' ? '源文件样式' : '文本结构';
}

function buildSourcePreviewDocument(content?: string | null) {
  if (!content) return '';
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 24px;
      color: #111827;
      background: #f3f4f6;
      font-family: Arial, "Microsoft YaHei", sans-serif;
    }
    .source-preview {
      width: fit-content;
      min-width: min(100%, 680px);
      margin: 0 auto;
      padding: 34px 42px;
      background: #fff;
      border: 1px solid #d0d5dd;
      box-shadow: 0 12px 32px rgba(15, 23, 42, 0.12);
    }
    .source-preview-docx {
      max-width: 760px;
      min-height: 820px;
    }
    .source-preview-pdf {
      width: 100%;
      min-width: 0;
      max-width: 840px;
      height: 560px;
      padding: 0;
      overflow: hidden;
    }
    .source-preview-pdf object {
      width: 100%;
      height: 100%;
      display: block;
      border: 0;
      background: #fff;
    }
    .source-preview p {
      margin: 0 0 10px;
      min-height: 1.4em;
      line-height: 1.75;
    }
    .source-heading {
      margin-top: 18px;
      font-weight: 700;
    }
    .source-title {
      text-align: center;
      font-size: 20pt;
    }
    .source-sheet + .source-sheet {
      margin-top: 28px;
    }
    .source-sheet h4 {
      margin: 0 0 12px;
      font-size: 14px;
      color: #344054;
    }
    .source-table {
      border-collapse: collapse;
      table-layout: fixed;
    }
    .source-table td {
      min-width: 48px;
      padding: 6px 8px;
      vertical-align: top;
      border: 1px solid #d0d5dd;
      line-height: 1.5;
      overflow-wrap: anywhere;
    }
    .source-preview-docx .source-table {
      width: 100%;
      margin: 12px 0;
    }
    .source-placeholder {
      padding: 1px 5px;
      color: #1d4ed8;
      background: #dbeafe;
      border-radius: 4px;
    }
    .source-note,
    .source-empty {
      color: #667085;
      font-size: 13px;
    }
  </style>
</head>
<body>${content}</body>
</html>`;
}

function validateTemplateFile(file: File) {
  const suffix = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
  if (!TEMPLATE_UPLOAD_EXTENSIONS.includes(suffix)) {
    return '模板库仅支持 DOCX / XLSX / PDF 文件';
  }
  if (file.size > MAX_TEMPLATE_UPLOAD_BYTES) {
    return '模板文件不能超过 20MB';
  }
  return '';
}

function templateUploadErrorMessage(error: unknown) {
  if (isAxiosError(error)) {
    const responseData = error.response?.data;
    if (
      responseData &&
      typeof responseData === 'object' &&
      'message' in responseData &&
      typeof responseData.message === 'string'
    ) {
      return responseData.message;
    }
    if (error.code === 'ECONNABORTED') {
      return '模板上传或解析超时，请换用较小的 PDF 后重试';
    }
    if (error.message === 'Network Error') {
      return '网络请求失败，请确认后端服务已启动，并且 PDF 未超过 20MB';
    }
  }
  return error instanceof Error ? error.message : '模板上传失败';
}
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h2>模板库</h2>
        <p class="muted">管理 Word / Excel / PDF 报表模板</p>
      </div>
      <el-button type="primary" :icon="Upload" :loading="uploading" @click="handleUpload">
        上传模板
      </el-button>
    </div>

    <el-card shadow="never" v-loading="loading">
      <div v-if="!templates.length && !loading" class="empty-block">
        <p class="muted">还没有上传模板</p>
        <el-button type="primary" :icon="Upload" @click="handleUpload">上传第一份模板</el-button>
      </div>
      <el-table v-else :data="templates">
        <el-table-column prop="name" label="模板名称" min-width="180" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="typeTag(row.template_type)" size="small" effect="plain">
              {{ typeLabel(row.template_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }">{{ row.description || '-' }}</template>
        </el-table-column>
        <el-table-column label="字段数" width="80" align="center">
          <template #default="{ row }">
            {{ Array.isArray(row.field_config?.fields) ? row.field_config.fields.length : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button size="small" text :icon="View" @click="handlePreview(row)">预览</el-button>
            <el-button size="small" text type="primary" @click="useTemplate(row)">使用</el-button>
            <el-button
              size="small"
              text
              type="danger"
              :icon="Delete"
              :disabled="!row.file_id"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="previewVisible" width="920px" destroy-on-close>
      <template #header>
        <div class="preview-title">
          <strong>{{ preview?.name || '模板预览' }}</strong>
          <el-tag v-if="preview" :type="typeTag(preview.template_type)" size="small" effect="plain">
            {{ typeLabel(preview.template_type) }}
          </el-tag>
        </div>
      </template>

      <div v-loading="previewLoading" class="preview-dialog">
        <template v-if="preview">
          <div class="preview-meta">
            <span>来源：{{ preview.source.toUpperCase() }}</span>
            <span>预览：{{ previewModeLabel(preview.preview_mode) }}</span>
            <span>字段数：{{ preview.fields.length }}</span>
          </div>
          <iframe
            v-if="preview.html"
            class="source-preview-frame"
            title="模板源文件样式预览"
            :srcdoc="sourcePreviewDocument"
          />
          <div v-else class="preview-paper">
            <template v-for="(segment, index) in previewSegments" :key="index">
              <mark v-if="segment.placeholder">{{ segment.text }}</mark>
              <span v-else>{{ segment.text }}</span>
            </template>
          </div>
          <div v-if="preview.raw_placeholders.length" class="placeholder-list">
            <el-tag
              v-for="placeholder in preview.raw_placeholders"
              :key="placeholder"
              size="small"
              effect="plain"
            >
              {{ placeholder }}
            </el-tag>
          </div>
        </template>
        <el-empty v-else-if="!previewLoading" description="暂无预览内容" />
      </div>

      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button v-if="preview" type="primary" @click="useTemplate(preview)">使用模板</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.empty-block {
  padding: 64px 0;
  text-align: center;
}

.preview-title {
  display: flex;
  gap: 10px;
  align-items: center;
}

.preview-dialog {
  min-height: 560px;
}

.preview-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  color: #667085;
  font-size: 13px;
}

.preview-paper {
  min-height: 260px;
  max-height: 520px;
  padding: 28px 32px;
  overflow: auto;
  color: #1f2937;
  font-size: 14px;
  line-height: 1.9;
  white-space: pre-wrap;
  background: #fff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.source-preview-frame {
  width: 100%;
  height: 620px;
  overflow: hidden;
  background: #f3f4f6;
  border: 1px solid #d0d5dd;
}

.preview-paper mark {
  padding: 1px 5px;
  color: #1d4ed8;
  background: #dbeafe;
  border-radius: 4px;
}

.placeholder-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}
</style>
