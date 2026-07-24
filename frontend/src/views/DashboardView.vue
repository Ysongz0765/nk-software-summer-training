<script setup lang="ts">
import { Document, Files, Plus, TrendCharts, Upload } from '@element-plus/icons-vue';
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { listReports, listTemplates } from '@/api/reportflow';
import type { ReportSummary } from '@/types/reportflow';

const router = useRouter();
const reports = ref<ReportSummary[]>([]);
const templateCount = ref(0);
const reportsLoading = ref(false);

onMounted(async () => {
  reportsLoading.value = true;
  try {
    const [reportResponse, templateResponse] = await Promise.all([listReports(), listTemplates()]);
    reports.value = (reportResponse.data || []).slice(0, 5);
    templateCount.value = templateResponse.data?.length || 0;
  } catch {
    reports.value = [];
    templateCount.value = 0;
  } finally {
    reportsLoading.value = false;
  }
});

const statusTag = (s: string) =>
  ({ draft: 'info', published: 'success', archived: 'warning' })[s] || 'info';
const statusLabel = (s: string) =>
  ({ draft: '草稿', published: '已发布', archived: '已归档' })[s] || s;

const statCards = computed(() => [
  {
    icon: Document,
    color: '#409eff',
    label: '报表总数',
    value: reports.value.length,
    suffix: '份',
  },
  {
    icon: TrendCharts,
    color: '#67c23a',
    label: '本月新建',
    value: reports.value.length,
    suffix: '份',
  },
  { icon: Files, color: '#e6a23c', label: '模板数量', value: templateCount.value, suffix: '个' },
  { icon: Upload, color: '#909399', label: '本月导出', value: 0, suffix: '次' },
]);

const quickActions = [
  {
    icon: '📝',
    title: '创建日报',
    desc: '快速生成本日工作报表',
    path: '/reports/create',
    query: { type: 'daily' },
  },
  {
    icon: '📊',
    title: '创建周报',
    desc: '汇总本周工作内容',
    path: '/reports/create',
    query: { type: 'weekly' },
  },
  { icon: '📋', title: '查看历史', desc: '浏览和管理历史报表', path: '/reports' },
  { icon: '📁', title: '管理模板', desc: '上传和维护报表模板', path: '/templates' },
];
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h2>工作台</h2>
        <p class="muted">欢迎使用 ReportFlow AI 智能报表平台</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="router.push('/reports/create')"
        >创建报表</el-button
      >
    </div>

    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col v-for="a in quickActions" :key="a.title" :span="6">
        <el-card
          shadow="hover"
          class="quick-card"
          @click="router.push({ path: a.path, query: a.query })"
        >
          <span class="qc-icon">{{ a.icon }}</span>
          <div>
            <strong>{{ a.title }}</strong>
            <p class="muted" style="margin: 2px 0 0; font-size: 12px">{{ a.desc }}</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col v-for="card in statCards" :key="card.label" :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-row">
            <div class="stat-icon" :style="{ background: card.color + '18', color: card.color }">
              <el-icon :size="22"><component :is="card.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <span class="stat-num"
                >{{ card.value }}<small>{{ card.suffix }}</small></span
              >
              <span class="stat-label muted">{{ card.label }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" v-loading="reportsLoading">
      <template #header>
        <div class="card-hd">
          <strong>最近报表</strong
          ><el-button size="small" text type="primary" @click="router.push('/reports')"
            >查看全部</el-button
          >
        </div>
      </template>
      <div v-if="!reports.length && !reportsLoading" class="empty-block">
        <div style="font-size: 40px; margin-bottom: 8px">📋</div>
        <p class="muted">还没有创建任何报表</p>
        <el-button
          size="small"
          type="primary"
          style="margin-top: 8px"
          @click="router.push('/reports/create')"
          >创建第一份报表</el-button
        >
      </div>
      <div v-else class="report-list">
        <div
          v-for="r in reports"
          :key="r.id"
          class="report-row"
          @click="router.push(`/reports/${r.id}/edit`)"
        >
          <div>
            <span class="r-title">{{ r.title }}</span
            ><span class="muted r-date">{{ r.report_date }}</span>
          </div>
          <div class="r-meta">
            <el-tag :type="statusTag(r.status)" size="small">{{ statusLabel(r.status) }}</el-tag>
            <span class="muted">{{ r.task_count }} 项任务</span>
          </div>
        </div>
      </div>
    </el-card>
  </section>
</template>

<style scoped>
.quick-card {
  cursor: pointer;
  transition: transform 0.15s;
}
.quick-card:hover {
  transform: translateY(-2px);
}
.quick-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
}
.qc-icon {
  font-size: 28px;
}
.stat-card {
  border-radius: 10px;
}
.stat-row {
  display: flex;
  align-items: center;
  gap: 14px;
}
.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stat-info {
  display: flex;
  flex-direction: column;
}
.stat-num {
  font-size: 22px;
  font-weight: 700;
}
.stat-num small {
  font-size: 13px;
  font-weight: 400;
  margin-left: 2px;
}
.stat-label {
  font-size: 13px;
}
.card-hd {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.empty-block {
  text-align: center;
  padding: 48px 0;
}
.report-list {
  display: flex;
  flex-direction: column;
}
.report-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}
.report-row:hover {
  background: #f5f7fb;
}
.r-title {
  font-weight: 500;
}
.r-date {
  margin-left: 10px;
  font-size: 12px;
}
.r-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
}
</style>
