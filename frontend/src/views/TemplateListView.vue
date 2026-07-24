<script setup lang="ts">
import { Delete, Upload, View, UploadFilled } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { UploadFile, UploadRawFile } from 'element-plus';
import { computed, onMounted, reactive, ref } from 'vue';
import { http } from '@/api/http';
import { getTemplate, listTemplates, parseTemplate, uploadFile } from '@/api/reportflow';
import type { Template, TemplateParseResult } from '@/types/reportflow';

const templates = ref<Template[]>([]);
const loading = ref(false);
const uploading = ref(false);

const typeLabel = (t: string) => ({ daily: '日报', weekly: '周报', monthly: '月报', custom: '自定义' }[t] || t);
const typeTag = (t: string) => ({ daily: 'primary', weekly: 'success', monthly: 'warning', custom: 'info' }[t] || 'info');

// ---------- 上传对话框 ----------
const uploadDialogVisible = ref(false);
const uploadFileList = ref<UploadFile[]>([]);
const uploadForm = reactive({
  name: '',
  description: '',
  template_type: 'daily' as string,
});
const ALLOWED_EXTENSIONS = '.docx,.xlsx,.pdf';
const uploadFileName = computed(() => uploadFileList.value[0]?.name || '');

function openUploadDialog() {
  uploadFileList.value = [];
  uploadForm.name = '';
  uploadForm.description = '';
  uploadForm.template_type = 'daily';
  uploadDialogVisible.value = true;
}

function handleFileChange(file: UploadFile) {
  uploadFileList.value = [file];
  if (!uploadForm.name && file.name) {
    uploadForm.name = file.name.replace(/\.[^.]+$/, '');
  }
}

function beforeUpload(raw: UploadRawFile) {
  const suffix = '.' + raw.name.split('.').pop()?.toLowerCase();
  if (!ALLOWED_EXTENSIONS.split(',').includes(suffix)) {
    ElMessage.error('仅支持 .docx / .xlsx / .pdf 格式');
    return false;
  }
  if (raw.size > 20 * 1024 * 1024) {
    ElMessage.error('文件不能超过 20MB');
    return false;
  }
  return true;
}

async function submitUpload() {
  const fileItem = uploadFileList.value[0];
  if (!fileItem?.raw) {
    ElMessage.warning('请先选择模板文件');
    return;
  }
  if (!uploadForm.name.trim()) {
    ElMessage.warning('请输入模板名称');
    return;
  }

  uploading.value = true;
  try {
    const upRes = await uploadFile(fileItem.raw);
    if (upRes.code !== 0 || !upRes.data) {
      ElMessage.error('文件上传失败');
      return;
    }

    await http.post('/templates', {
      name: uploadForm.name.trim(),
      description: uploadForm.description.trim() || null,
      file_path: upRes.data.file_id,
      template_type: uploadForm.template_type,
    });

    uploadDialogVisible.value = false;
    ElMessage.success('模板上传成功');
    await load();
  } catch {
    ElMessage.error('模板上传失败');
  } finally {
    uploading.value = false;
  }
}

// ---------- 查看模板内容 ----------
const drawerVisible = ref(false);
const viewing = ref(false);
const viewingTemplate = ref<Template | null>(null);
const viewingContent = ref<TemplateParseResult | null>(null);
const contentLoading = ref(false);

async function load() {
  loading.value = true;
  try { const r = await listTemplates(); templates.value = r.data || []; }
  catch { templates.value = []; }
  finally { loading.value = false; }
}

async function handleView(row: Template) {
  drawerVisible.value = true;
  viewing.value = true;
  viewingContent.value = null;

  try {
    const res = await getTemplate(row.id);
    viewingTemplate.value = res.data;
  } catch {
    viewingTemplate.value = row;
  }

  // 如果有关联文件，解析模板内容
  const tmpl = viewingTemplate.value;
  if (tmpl?.file_id) {
    contentLoading.value = true;
    try {
      const parsed = await parseTemplate(String(tmpl.file_id));
      viewingContent.value = parsed.data;
    } catch {
      viewingContent.value = null;
    } finally {
      contentLoading.value = false;
    }
  }

  viewing.value = false;
}

async function handleDelete(row: Template) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.name}」？`, '删除确认', { type: 'warning' });
    await load();
    ElMessage.success('模板已删除');
  } catch { /* 取消 */ }
}

function closeDrawer() {
  drawerVisible.value = false;
  viewingTemplate.value = null;
  viewingContent.value = null;
}

onMounted(load);
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h2>模板库</h2>
        <p class="muted">管理 Word / Excel / PDF 报表模板</p>
      </div>
      <el-button type="primary" :icon="Upload" @click="openUploadDialog">
        上传模板
      </el-button>
    </div>

    <!-- ========== 上传模板对话框 ========== -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传模板"
      width="520px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form label-position="top" size="default">
        <el-form-item label="选择模板文件" required>
          <el-upload
            v-model:file-list="uploadFileList"
            class="upload-zone"
            drag
            :auto-upload="false"
            :limit="1"
            :accept="ALLOWED_EXTENSIONS"
            :before-upload="beforeUpload"
            :on-change="handleFileChange"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击选择文件</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 .docx / .xlsx / .pdf 格式，≤ 20MB
              </div>
            </template>
          </el-upload>
          <div v-if="uploadFileName" class="file-selected">
            ✅ 已选择：<strong>{{ uploadFileName }}</strong>
          </div>
        </el-form-item>

        <el-form-item label="模板名称" required>
          <el-input
            v-model="uploadForm.name"
            placeholder="例：项目日报模板"
            maxlength="64"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="模板类型">
          <el-radio-group v-model="uploadForm.template_type">
            <el-radio-button value="daily">日报</el-radio-button>
            <el-radio-button value="weekly">周报</el-radio-button>
            <el-radio-button value="monthly">月报</el-radio-button>
            <el-radio-button value="custom">自定义</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="描述">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="2"
            placeholder="可选：模板用途说明"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">
          {{ uploading ? '上传中...' : '确认上传' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ========== 模板列表 ========== -->
    <el-card shadow="never" v-loading="loading">
      <div v-if="!templates.length && !loading" style="text-align: center; padding: 64px 0">
        <span style="font-size: 48px">📁</span>
        <p class="muted" style="margin: 12px 0">还没有上传模板</p>
        <el-button type="primary" :icon="Upload" @click="openUploadDialog">
          上传第一份模板
        </el-button>
      </div>

      <el-table v-else :data="templates" stripe>
        <el-table-column prop="name" label="模板名称" min-width="180" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="typeTag(row.template_type)" size="small" effect="plain">
              {{ typeLabel(row.template_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="260">
          <template #default="{ row }">
            {{ row.description || '暂无描述' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <div class="action-cell">
              <el-button size="small" text type="primary" :icon="View" @click="handleView(row)">
                查看
              </el-button>
              <el-button size="small" text type="danger" :icon="Delete" @click="handleDelete(row)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ========== 查看模板内容抽屉 ========== -->
    <el-drawer
      v-model="drawerVisible"
      direction="rtl"
      size="520px"
      @close="closeDrawer"
    >
      <template #header>
        <div style="display: flex; align-items: center; gap: 10px">
          <span style="font-size: 18px; font-weight: 600">📄 模板内容</span>
          <el-tag
            v-if="viewingTemplate"
            :type="typeTag(viewingTemplate.template_type)"
            size="small"
            effect="plain"
          >
            {{ typeLabel(viewingTemplate.template_type) }}
          </el-tag>
        </div>
      </template>

      <div v-loading="viewing" style="min-height: 300px">
        <template v-if="viewingTemplate">
          <div v-if="!viewingTemplate.file_id" class="content-empty">
            ⚠️ 该模板未关联文件，无法查看内容
          </div>

          <div v-else-if="contentLoading" v-loading="contentLoading" class="content-loading">
            正在解析模板文件...
          </div>

          <div v-else-if="viewingContent" class="content-body">
            <div class="content-text">
              <pre>{{ viewingContent.description.replace(/\{\{.*?\}\}/g, '______') }}</pre>
            </div>
          </div>

          <div v-else class="content-empty">
            ⚠️ 解析模板内容失败
          </div>
        </template>

        <div v-else-if="!viewing" style="text-align: center; padding: 48px 0">
          <span style="font-size: 40px">📋</span>
          <p class="muted">加载模板信息中...</p>
        </div>
      </div>
    </el-drawer>
  </section>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0 0 4px;
  font-size: 20px;
}
.muted {
  color: #909399;
  font-size: 13px;
  margin: 0;
}
.upload-zone {
  width: 100%;
}
.upload-zone :deep(.el-upload) {
  width: 100%;
}
.upload-zone :deep(.el-upload-dragger) {
  width: 100%;
}
.file-selected {
  margin-top: 8px;
  padding: 6px 10px;
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
  border-radius: 6px;
  font-size: 13px;
}
.action-cell {
  display: flex;
  flex-wrap: nowrap;
  gap: 2px;
}
.content-empty,
.content-loading {
  text-align: center;
  padding: 32px 16px;
  background: #f5f7fb;
  border-radius: 8px;
  font-size: 13px;
  color: #909399;
}
.content-body {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}
.content-body {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}
.content-text {
  padding: 14px;
  max-height: 400px;
  overflow-y: auto;
}
.content-text pre {
  margin: 0;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  color: #303133;
}
</style>
