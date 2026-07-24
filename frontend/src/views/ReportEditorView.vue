<script setup lang="ts">
import { ArrowLeft, Check, Download, Edit, View } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import {
  createVersion,
  exportReport as exportReportApi,
  getReport,
  listVersions,
  updateReport,
} from '@/api/reportflow';
import ReportPreview from '@/components/ReportPreview.vue';
import TaskEditor from '@/components/TaskEditor.vue';
import type { ReportContent, ReportVersion, TaskItem } from '@/types/reportflow';

const route = useRoute();
const router = useRouter();
const reportId = ref(Number(route.params.id));

const report = ref<ReportContent>({
  report_type: 'daily',
  title: '',
  date: new Date().toISOString().slice(0, 10),
  summary: '',
  completed_tasks: [],
  in_progress_tasks: [],
  problems: [],
  solutions: [],
  next_plan: [],
  custom_fields: {},
  missing_fields: [],
  style: 'concise',
});

const editMode = ref<'form' | 'preview'>('form');
const loading = ref(false);
const saving = ref(false);
const exporting = ref(false);
const versioning = ref(false);
const versions = ref<ReportVersion[]>([]);

const problemsText = ref('');
const solutionsText = ref('');
const nextPlanText = ref('');

onMounted(async () => {
  await loadReport();
  await loadVersions();
});

async function loadReport() {
  if (!reportId.value) return;
  loading.value = true;
  try {
    const response = await getReport(reportId.value);
    if (response.data?.content) {
      report.value = response.data.content as ReportContent;
      syncListToText();
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '报表加载失败');
  } finally {
    loading.value = false;
  }
}

async function loadVersions() {
  if (!reportId.value) return;
  try {
    const response = await listVersions(reportId.value);
    versions.value = response.data || [];
  } catch (error) {
    ElMessage.warning(error instanceof Error ? error.message : '版本列表加载失败');
  }
}

function syncListToText() {
  problemsText.value = (report.value.problems || []).join('\n');
  solutionsText.value = (report.value.solutions || []).join('\n');
  nextPlanText.value = (report.value.next_plan || []).join('\n');
}

function syncTextToList() {
  report.value.problems = problemsText.value.split('\n').filter((item) => item.trim());
  report.value.solutions = solutionsText.value.split('\n').filter((item) => item.trim());
  report.value.next_plan = nextPlanText.value.split('\n').filter((item) => item.trim());
}

function onCompleted(tasks: TaskItem[]) {
  report.value.completed_tasks = tasks.map((task) => ({ ...task, status: 'completed' }));
}

function onInProgress(tasks: TaskItem[]) {
  report.value.in_progress_tasks = tasks.map((task) =>
    task.status === 'completed' ? { ...task, status: 'in_progress' } : task,
  );
}

async function handleSave() {
  if (!reportId.value) return;
  syncTextToList();
  saving.value = true;
  try {
    const response = await updateReport(reportId.value, {
      title: report.value.title,
      status: 'draft',
      content: report.value,
    });
    if (response.data?.content) {
      report.value = response.data.content as ReportContent;
      syncListToText();
    }
    await loadVersions();
    ElMessage.success('已保存');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存失败');
  } finally {
    saving.value = false;
  }
}

async function handleCreateVersion() {
  if (!reportId.value) return;
  syncTextToList();
  versioning.value = true;
  try {
    await createVersion(reportId.value, report.value);
    await loadVersions();
    ElMessage.success('版本已记录');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '版本记录失败');
  } finally {
    versioning.value = false;
  }
}

async function handleExport(type: string) {
  if (!reportId.value) return;
  await handleSave();
  exporting.value = true;
  try {
    const response = await exportReportApi(reportId.value, type);
    if (response.data?.download_url) {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
      const appBaseUrl = apiBaseUrl.replace('/api/v1', '');
      const link = document.createElement('a');
      link.href = `${appBaseUrl}${response.data.download_url}`;
      link.download = '';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '导出失败');
  } finally {
    exporting.value = false;
  }
}
</script>

<template>
  <section v-loading="loading">
    <div class="page-header">
      <div>
        <el-button text :icon="ArrowLeft" @click="router.push('/reports')">返回历史</el-button>
        <h2 style="margin-top: 8px">在线编辑</h2>
      </div>
      <div class="inline-actions">
        <el-button
          size="small"
          :icon="editMode === 'preview' ? View : Edit"
          @click="editMode = editMode === 'form' ? 'preview' : 'form'"
        >
          {{ editMode === 'form' ? '切换预览' : '切换编辑' }}
        </el-button>
        <el-button size="small" :icon="Check" :loading="saving" @click="handleSave">
          保存
        </el-button>
        <el-button size="small" :loading="versioning" @click="handleCreateVersion">
          记录版本
        </el-button>
        <el-dropdown @command="(type: string) => handleExport(type)">
          <el-button size="small" :icon="Download" :loading="exporting">导出</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="docx">Word (.docx)</el-dropdown-item>
              <el-dropdown-item command="pdf">PDF (.pdf)</el-dropdown-item>
              <el-dropdown-item command="xlsx">Excel (.xlsx)</el-dropdown-item>
              <el-dropdown-item command="json">JSON</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div v-show="editMode === 'form'" class="editor-form">
      <el-card shadow="never" class="editor-section">
        <el-row :gutter="16">
          <el-col :span="8">
            <label class="field-label">报表类型</label>
            <el-select v-model="report.report_type" style="width: 100%">
              <el-option label="日报" value="daily" />
              <el-option label="周报" value="weekly" />
            </el-select>
          </el-col>
          <el-col :span="8">
            <label class="field-label">标题</label>
            <el-input v-model="report.title" placeholder="报表标题" />
          </el-col>
          <el-col :span="8">
            <label class="field-label">日期</label>
            <el-date-picker
              v-model="report.date"
              type="date"
              style="width: 100%"
              value-format="YYYY-MM-DD"
            />
          </el-col>
        </el-row>
      </el-card>

      <el-card shadow="never" class="editor-section">
        <template #header><strong>工作总结</strong></template>
        <el-input
          v-model="report.summary"
          type="textarea"
          :rows="3"
          placeholder="概述工作内容和进展..."
        />
      </el-card>
      <el-card shadow="never" class="editor-section">
        <TaskEditor
          :tasks="report.completed_tasks"
          title="已完成任务"
          @update:tasks="onCompleted"
        />
      </el-card>
      <el-card shadow="never" class="editor-section">
        <TaskEditor
          :tasks="report.in_progress_tasks"
          title="进行中任务"
          @update:tasks="onInProgress"
        />
      </el-card>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-card shadow="never" class="editor-section">
            <template #header><strong>问题与风险</strong></template>
            <el-input
              v-model="problemsText"
              type="textarea"
              :rows="4"
              placeholder="每行一个问题..."
            />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never" class="editor-section">
            <template #header><strong>解决方案</strong></template>
            <el-input
              v-model="solutionsText"
              type="textarea"
              :rows="4"
              placeholder="每行一个方案..."
            />
          </el-card>
        </el-col>
      </el-row>
      <el-card shadow="never" class="editor-section">
        <template #header><strong>下一步计划</strong></template>
        <el-input v-model="nextPlanText" type="textarea" :rows="4" placeholder="每行一个计划..." />
      </el-card>

      <el-card shadow="never" class="editor-section">
        <template #header><strong>版本记录</strong></template>
        <el-table :data="versions" empty-text="暂无版本" size="small">
          <el-table-column prop="version_number" label="版本" width="90" />
          <el-table-column prop="change_note" label="说明" min-width="160" />
          <el-table-column prop="created_at" label="创建时间" min-width="180" />
        </el-table>
      </el-card>
    </div>

    <div v-show="editMode === 'preview'">
      <ReportPreview :report="report" />
    </div>
  </section>
</template>

<style scoped>
.inline-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.editor-form {
  display: flex;
  flex-direction: column;
}

.editor-section {
  margin-bottom: 12px;
}

.field-label {
  display: block;
  margin-bottom: 4px;
  color: #374151;
  font-size: 13px;
  font-weight: 500;
}
</style>
