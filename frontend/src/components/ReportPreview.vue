<script setup lang="ts">
import type { ReportContent, TaskItem } from '@/types/reportflow';

defineProps<{ report: ReportContent }>();

const reportTypeLabel = (t: string) =>
  ({ daily: '日报', weekly: '周报', monthly: '月报', custom: '自定义' })[t] || t;

function taskItems(tasks: TaskItem[]): string[] {
  if (!tasks.length) return ['暂无'];
  return tasks.map((t, i) => {
    const desc = t.description ? `：${t.description}` : '';
    return `${i + 1}. ${t.title}${desc}（进度 ${t.progress}%）`;
  });
}

function listItems(items: string[]): string[] {
  if (!items?.length) return ['暂无'];
  return items.map((item, i) => `${i + 1}. ${item}`);
}
</script>

<template>
  <div class="rp-document">
    <!-- 标题 -->
    <h1 class="rp-title">{{ report.title || '未命名报表' }}</h1>
    <p class="rp-meta">报表类型：{{ reportTypeLabel(report.report_type) }}</p>
    <p class="rp-meta">日期：{{ report.date }}</p>

    <!-- 一、工作总结 -->
    <h3 class="rp-heading">一、工作总结</h3>
    <p class="rp-body">{{ report.summary || '暂无' }}</p>

    <!-- 二、已完成任务 -->
    <h3 class="rp-heading">二、已完成任务</h3>
    <p v-for="(line, i) in taskItems(report.completed_tasks || [])" :key="'c' + i" class="rp-body">
      {{ line }}
    </p>

    <!-- 三、进行中任务 -->
    <h3 class="rp-heading">三、进行中任务</h3>
    <p
      v-for="(line, i) in taskItems(report.in_progress_tasks || [])"
      :key="'p' + i"
      class="rp-body"
    >
      {{ line }}
    </p>

    <!-- 四、问题与风险 -->
    <h3 class="rp-heading">四、问题与风险</h3>
    <p v-for="(line, i) in listItems(report.problems || [])" :key="'b' + i" class="rp-body">
      {{ line }}
    </p>

    <!-- 五、解决方案 -->
    <h3 class="rp-heading">五、解决方案</h3>
    <p v-for="(line, i) in listItems(report.solutions || [])" :key="'s' + i" class="rp-body">
      {{ line }}
    </p>

    <!-- 六、下一步计划 -->
    <h3 class="rp-heading">六、下一步计划</h3>
    <p v-for="(line, i) in listItems(report.next_plan || [])" :key="'n' + i" class="rp-body">
      {{ line }}
    </p>
  </div>
</template>

<style scoped>
.rp-document {
  background: #fff;
  border: 1px solid #d0d5dd;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
  padding: 56px 64px;
  max-width: 760px;
  margin: 0 auto;
  min-height: 600px;
}

.rp-title {
  margin: 0 0 12px;
  font-size: 22px;
  font-weight: 700;
  text-align: center;
  color: #111827;
}

.rp-meta {
  margin: 0 0 4px;
  font-size: 13px;
  color: #667085;
  text-align: center;
}

.rp-heading {
  margin: 24px 0 10px;
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}

.rp-body {
  margin: 0 0 4px;
  font-size: 14px;
  line-height: 1.8;
  color: #374151;
}
</style>
