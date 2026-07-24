<script setup lang="ts">
import { Delete, Upload } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { createTemplate, deleteTemplate, listTemplates, uploadFile } from '@/api/reportflow';
import type { Template } from '@/types/reportflow';

const router = useRouter();
const templates = ref<Template[]>([]);
const loading = ref(false);
const uploading = ref(false);

const typeLabel = (type: string) =>
  ({ daily: '日报', weekly: '周报', monthly: '月报', custom: '自定义' })[type] || type;
const typeTag = (type: string) =>
  ({ daily: 'primary', weekly: 'success', monthly: 'warning', custom: 'info' })[type] || 'info';

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
  input.accept = '.docx,.xlsx';
  input.onchange = () => {
    const file = input.files?.[0];
    if (file) void uploadTemplate(file);
  };
  input.click();
}

async function uploadTemplate(file: File) {
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
    ElMessage.error(error instanceof Error ? error.message : '模板上传失败');
  } finally {
    uploading.value = false;
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

function useTemplate(row: Template) {
  router.push({
    path: '/reports/create',
    query: {
      type: row.template_type,
      template_id: String(row.id),
    },
  });
}
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h2>模板库</h2>
        <p class="muted">管理 Word / Excel 报表模板</p>
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
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
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
  </section>
</template>

<style scoped>
.empty-block {
  padding: 64px 0;
  text-align: center;
}
</style>
