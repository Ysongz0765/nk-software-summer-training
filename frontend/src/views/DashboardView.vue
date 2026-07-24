<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { listReports } from '@/api/reportflow';
import type { ReportSummary } from '@/types/reportflow';

const router = useRouter();
const reports = ref<ReportSummary[]>([]);
const reportsLoading = ref(false);

onMounted(async () => {
  reportsLoading.value = true;
  try { const res = await listReports(); reports.value = (res.data || []).slice(0, 5); }
  catch { reports.value = []; }
  finally { reportsLoading.value = false; }
});

const statusTag = (s: string) => ({ draft: 'info', published: 'success', archived: 'warning' }[s] || 'info');
const statusLabel = (s: string) => ({ draft: '草稿', published: '已发布', archived: '已归档' }[s] || s);

const stats = computed(() => [
  { value: reports.value.length, label: '报表总数' },
  { value: 12, label: '本月新建' },
  { value: 3, label: '模板数量' },
  { value: 8, label: '本月导出' },
]);

const quickActions = [
  { icon: '📝', title: '创建日报', desc: '快速生成本日工作报表', path: '/reports/create', query: { type: 'daily' }, bg: '#eff6ff', ring: '#93c5fd' },
  { icon: '📊', title: '创建周报', desc: '汇总本周工作内容', path: '/reports/create', query: { type: 'weekly' }, bg: '#f0fdf4', ring: '#86efac' },
  { icon: '📋', title: '历史报表', desc: '浏览和管理历史报表', path: '/reports', bg: '#fefce8', ring: '#fde047' },
  { icon: '📁', title: '模板管理', desc: '上传和维护报表模板', path: '/templates', bg: '#f5f3ff', ring: '#c4b5fd' },
];
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h2>工作台</h2>
        <p class="muted">欢迎使用 ReportFlow AI 智能报表平台</p>
      </div>
    </div>

    <!-- ====== 快捷操作 ====== -->
    <div class="actions-grid">
      <div
        v-for="a in quickActions"
        :key="a.title"
        class="action-card"
        :style="{ '--card-bg': a.bg, '--card-ring': a.ring }"
        @click="router.push({ path: a.path, query: a.query })"
      >
        <span class="action-icon">{{ a.icon }}</span>
        <div class="action-body">
          <span class="action-title">{{ a.title }}</span>
          <span class="action-desc">{{ a.desc }}</span>
        </div>
      </div>
    </div>

    <!-- ====== 数据统计 ====== -->
    <div class="stats-bar">
      <div class="stats-items">
        <div v-for="s in stats" :key="s.label" class="stats-item">
          <span class="stats-num">{{ s.value }}</span>
          <span class="stats-text">{{ s.label }}</span>
        </div>
      </div>
    </div>

    <!-- ====== 最近报表 ====== -->
    <el-card shadow="never" v-loading="reportsLoading">
      <template #header>
        <div class="card-hd">
          <strong>最近报表</strong>
          <el-button size="small" text type="primary" @click="router.push('/reports')">查看全部</el-button>
        </div>
      </template>
      <div v-if="!reports.length && !reportsLoading" class="empty-block">
        <div style="font-size: 40px; margin-bottom: 8px">📋</div>
        <p class="muted">还没有创建任何报表</p>
        <el-button size="small" type="primary" style="margin-top: 8px" @click="router.push('/reports/create')">创建第一份报表</el-button>
      </div>
      <div v-else class="report-list">
        <div v-for="r in reports" :key="r.id || r.title" class="report-row" @click="router.push('/reports/1/edit')">
          <div>
            <span class="r-title">{{ r.title }}</span>
            <span class="muted r-date">{{ r.report_date }}</span>
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
.page-header { margin-bottom: 24px; }
.page-header h2 { margin: 0 0 4px; font-size: 22px; letter-spacing: -0.3px; }
.muted { color: #94a3b8; font-size: 14px; margin: 0; }

/* 快捷操作 */
.actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 28px;
}
.action-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 22px;
  border-radius: 16px;
  cursor: pointer;
  background: var(--card-bg);
  border: 1px solid var(--card-ring);
  transition: all 0.25s cubic-bezier(.4,0,.2,1);
  position: relative;
  overflow: hidden;
}
.action-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,.6) 0%, transparent 60%);
  pointer-events: none;
}
.action-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,.06), 0 0 0 1px var(--card-ring);
  border-color: var(--card-ring);
}
.action-icon {
  font-size: 30px;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,.04);
}
.action-body { display: flex; flex-direction: column; }
.action-title { font-size: 15px; font-weight: 600; color: #1e293b; }
.action-desc { font-size: 13px; color: #94a3b8; margin-top: 3px; }

/* 数据统计 */
.stats-bar { margin-bottom: 28px; }
.stats-items {
  display: flex;
  background: #fff;
  border-radius: 14px;
  padding: 18px 0;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
  border: 1px solid #f1f5f9;
}
.stats-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  border-right: 1px solid #f1f5f9;
}
.stats-item:last-child { border-right: none; }
.stats-num {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.5px;
}
.stats-text { font-size: 13px; color: #94a3b8; font-weight: 500; }

/* 最近报表 */
.card-hd { display: flex; justify-content: space-between; align-items: center; }
.empty-block { text-align: center; padding: 48px 0; }
.report-list { display: flex; flex-direction: column; }
.report-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 12px; border-radius: 6px; cursor: pointer; transition: background .15s;
}
.report-row:hover { background: #f8fafc; }
.r-title { font-weight: 500; }
.r-date { margin-left: 10px; font-size: 12px; }
.r-meta { display: flex; align-items: center; gap: 10px; font-size: 12px; }
</style>
