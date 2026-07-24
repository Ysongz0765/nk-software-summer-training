<script setup lang="ts">
import { Delete, Plus } from '@element-plus/icons-vue';
import type { TaskItem } from '@/types/reportflow';

const props = defineProps<{ tasks: TaskItem[]; title?: string }>();
const emit = defineEmits<{ (e: 'update:tasks', tasks: TaskItem[]): void }>();

function add() {
  const t: TaskItem = {
    id: 'task-' + Date.now(),
    title: '',
    status: 'pending',
    progress: 0,
    evidence_file_ids: [],
    confidence: 1,
    source: 'manual',
    user_confirmed: true,
  };
  emit('update:tasks', [...props.tasks, t]);
}
function remove(i: number) {
  const n = [...props.tasks];
  n.splice(i, 1);
  emit('update:tasks', n);
}
function update(i: number, p: Partial<TaskItem>) {
  emit(
    'update:tasks',
    props.tasks.map((t, j) => (j === i ? { ...t, ...p } : t)),
  );
}
</script>

<template>
  <div class="te">
    <div class="te-hd" :class="{ 'te-hd-end': !title }">
      <span v-if="title" class="te-title">{{ title }}</span>
      <el-button size="small" type="primary" text :icon="Plus" @click="add">添加</el-button>
    </div>
    <div v-if="!tasks.length" class="te-empty muted">暂无，点击添加</div>
    <div v-for="(t, i) in tasks" :key="t.id" class="te-row">
      <div class="te-row-top">
        <el-input
          :model-value="t.title"
          size="small"
          placeholder="任务标题"
          style="flex: 1"
          @input="(value: string) => update(i, { title: value })"
        />
        <el-select
          :model-value="t.status"
          size="small"
          style="width: 100px"
          @change="(v: string) => update(i, { status: v })"
        >
          <el-option label="已完成" value="completed" />
          <el-option label="进行中" value="in_progress" />
          <el-option label="未开始" value="pending" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
        <el-input-number
          :model-value="t.progress"
          size="small"
          :min="0"
          :max="100"
          style="width: 110px"
          @change="(v: number | undefined) => update(i, { progress: v ?? 0 })"
        />
        <el-button size="small" type="danger" text :icon="Delete" @click="remove(i)" />
      </div>
      <div class="te-row-sub">
        <el-input
          :model-value="t.description || ''"
          size="small"
          placeholder="描述（可选）"
          @input="(value: string) => update(i, { description: value })"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.te {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.te-hd {
  display: flex;
  align-items: center;
  gap: 12px;
}
.te-hd-end {
  justify-content: flex-end;
}
.te-title {
  font-weight: 600;
}
.te-empty {
  padding: 16px;
  text-align: center;
  background: #f5f7fb;
  border-radius: 6px;
}
.te-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
}
.te-row-top {
  display: flex;
  gap: 8px;
  align-items: center;
}
.te-row-sub {
  padding-left: 4px;
}
</style>
