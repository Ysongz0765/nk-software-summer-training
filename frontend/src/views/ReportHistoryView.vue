<script setup lang="ts">
import { Delete, Download, Edit, Plus, View } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { deleteReport, exportReport, listReports } from '@/api/reportflow';
import type { ReportSummary } from '@/types/reportflow';

const router = useRouter();
const reports = ref<ReportSummary[]>([]);
const loading = ref(false);
const exportingId = ref<number | null>(null);

const typeLabel = (type: string) =>
  ({ daily: '日报', weekly: '周报', monthly: '月报' })[type] || type;
const statusTag = (status: string) =>
  ({ draft: 'info', published: 'success', archived: 'warning' })[status] || 'info';
const statusLabel = (status: string) =>
  ({ draft: '草稿', published: '已发布', archived: '已归档' })[status] || status;

onMounted(load);

async function load() {
  loading.value = true;
  try {
    const response = await listReports();
    reports.value = response.data || [];
  } catch (error) {
    reports.value = [];
    ElMessage.error(error instanceof Error ? error.message : '历史报表加载失败');
  } finally {
    loading.value = false;
  }
}

async function handleExport(id: number, type: string) {
  exportingId.value = id;
  try {
    const response = await exportReport(id, type);
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
    exportingId.value = null;
  }
}

async function handleDelete(row: ReportSummary) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.title}」？`, '删除确认', { type: 'warning' });
    await deleteReport(row.id);
    await load();
    ElMessage.success('已删除');
  } catch (error) {
    if (error instanceof Error) ElMessage.error(error.message);
  }
}
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h2>历史报表</h2>
        <p class="muted">管理已创建的所有报表</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="router.push('/reports/create')">
        创建新报表
      </el-button>
    </div>

    <el-card shadow="never" v-loading="loading">
      <el-table :data="reports" empty-text="暂无报表">
        <el-table-column prop="title" label="标题" min-width="180">
          <template #default="{ row }">
            <el-link type="primary" @click="router.push(`/reports/${row.id}/edit`)">
              {{ row.title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="80">
          <template #default="{ row }">{{ typeLabel(row.report_type) }}</template>
        </el-table-column>
        <el-table-column prop="report_date" label="日期" width="120" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small">{{
              statusLabel(row.status)
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="task_count" label="任务数" width="80" align="center" />
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              text
              :icon="View"
              @click="router.push(`/reports/${row.id}/edit`)"
            >
              查看
            </el-button>
            <el-button
              size="small"
              text
              :icon="Edit"
              @click="router.push(`/reports/${row.id}/edit`)"
            >
              编辑
            </el-button>
            <el-dropdown @command="(type: string) => handleExport(row.id, type)">
              <el-button size="small" text :icon="Download" :loading="exportingId === row.id">
                导出
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="docx">Word</el-dropdown-item>
                  <el-dropdown-item command="pdf">PDF</el-dropdown-item>
                  <el-dropdown-item command="xlsx">Excel</el-dropdown-item>
                  <el-dropdown-item command="json">JSON</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button size="small" text :icon="Delete" type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!reports.length && !loading" class="empty-block">
        <p class="muted">还没有创建任何报表</p>
        <el-button type="primary" :icon="Plus" @click="router.push('/reports/create')">
          创建第一份报表
        </el-button>
      </div>
    </el-card>
  </section>
</template>

<style scoped>
.empty-block {
  padding: 60px 0;
  text-align: center;
}
</style>
