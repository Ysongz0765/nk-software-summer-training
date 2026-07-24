<script setup lang="ts">
import { computed } from 'vue';

import type { ReportContent } from '@/types/reportflow';

const props = defineProps<{ report: ReportContent }>();

const statusLabel = (s: string) =>
  ({ completed: '已完成', in_progress: '进行中', pending: '未开始', cancelled: '已取消' })[s] || s;
const internalCustomFields = new Set([
  'generated_by',
  'model',
  'style',
  'rendered_template',
  'template_fields',
  'template_id',
  'template_name',
]);

const renderedTemplate = computed(() => {
  const value = props.report.custom_fields?.rendered_template;
  return typeof value === 'string' && value.trim() ? value : '';
});

const customFieldRows = computed(() =>
  Object.entries(props.report.custom_fields || {})
    .filter(([key, value]) => !internalCustomFields.has(key) && hasDisplayValue(value))
    .map(([key, value]) => ({ key, value: formatCustomValue(value) })),
);

function hasDisplayValue(value: unknown) {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') return Boolean(value.trim());
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === 'object') return Object.keys(value).length > 0;
  return true;
}

function formatCustomValue(value: unknown) {
  if (Array.isArray(value)) return value.join('\n');
  if (value && typeof value === 'object') {
    return Object.entries(value)
      .map(([key, item]) => `${key}: ${String(item)}`)
      .join('\n');
  }
  return String(value);
}
</script>

<template>
  <div class="rp">
    <div class="rp-header">
      <h2>{{ report.title || '未命名报表' }}</h2>
      <div class="rp-meta">
        <el-tag>{{
          report.report_type === 'daily'
            ? '日报'
            : report.report_type === 'weekly'
              ? '周报'
              : report.report_type
        }}</el-tag>
        <span class="muted">{{ report.date }}</span>
      </div>
    </div>

    <el-card shadow="never" v-if="renderedTemplate" class="template-body">
      <p>{{ renderedTemplate }}</p>
    </el-card>

    <el-card shadow="never" v-if="!renderedTemplate"
      ><template #header><strong>工作总结</strong></template>
      <p>{{ report.summary || '暂无' }}</p>
    </el-card>

    <el-card
      shadow="never"
      v-if="!renderedTemplate && (report.completed_tasks.length || report.in_progress_tasks.length)"
    >
      <template #header><strong>任务列表</strong></template>
      <el-table
        :data="[
          ...report.completed_tasks.map((t) => ({ ...t, _g: '已完成' })),
          ...report.in_progress_tasks.map((t) => ({ ...t, _g: '进行中' })),
        ]"
        size="small"
      >
        <el-table-column prop="title" label="任务" min-width="180" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="
                row.status === 'completed'
                  ? 'success'
                  : row.status === 'in_progress'
                    ? 'warning'
                    : 'info'
              "
              size="small"
            >
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="90">
          <template #default="{ row }"
            ><el-progress :percentage="row.progress" :stroke-width="6"
          /></template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="120" />
      </el-table>
    </el-card>

    <el-card shadow="never" v-if="!renderedTemplate && report.problems?.length"
      ><template #header><strong>问题与风险</strong></template>
      <ul>
        <li v-for="(p, i) in report.problems" :key="i">{{ p }}</li>
      </ul>
    </el-card>
    <el-card shadow="never" v-if="!renderedTemplate && report.solutions?.length"
      ><template #header><strong>解决方案</strong></template>
      <ul>
        <li v-for="(s, i) in report.solutions" :key="i">{{ s }}</li>
      </ul>
    </el-card>
    <el-card shadow="never" v-if="!renderedTemplate && report.next_plan?.length"
      ><template #header><strong>下一步计划</strong></template>
      <ul>
        <li v-for="(n, i) in report.next_plan" :key="i">{{ n }}</li>
      </ul>
    </el-card>
    <el-card shadow="never" v-if="customFieldRows.length">
      <template #header><strong>模板字段</strong></template>
      <div class="custom-field" v-for="field in customFieldRows" :key="field.key">
        <span>{{ field.key }}</span>
        <p>{{ field.value }}</p>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.rp {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.rp-header h2 {
  margin: 0 0 8px;
}
.rp-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}
ul {
  margin: 0;
  padding-left: 20px;
}
li {
  line-height: 1.8;
}
p {
  margin: 0;
  line-height: 1.8;
}
.custom-field {
  display: grid;
  grid-template-columns: minmax(120px, 180px) 1fr;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #eef2f7;
}
.custom-field:last-child {
  border-bottom: 0;
}
.custom-field span {
  color: #667085;
  font-size: 13px;
  font-weight: 600;
}
.custom-field p {
  white-space: pre-line;
}
.template-body p {
  white-space: pre-line;
}
</style>
