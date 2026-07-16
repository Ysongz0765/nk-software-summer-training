<script setup lang="ts">
import { onMounted } from 'vue';

import { useAppStore } from '@/stores/app';

const appStore = useAppStore();

onMounted(() => {
  void appStore.refreshHealth();
});
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h2>工作台</h2>
        <p class="muted">查看系统状态和后续联调入口。</p>
      </div>
      <el-button :loading="appStore.loading" @click="appStore.refreshHealth"
        >刷新健康检查</el-button
      >
    </div>

    <el-card shadow="never">
      <el-descriptions title="后端健康检查" :column="1" border>
        <el-descriptions-item label="状态">
          {{ appStore.health?.status ?? '未连接' }}
        </el-descriptions-item>
        <el-descriptions-item label="服务">
          {{ appStore.health?.service ?? '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="版本">
          {{ appStore.health?.version ?? '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </section>
</template>
