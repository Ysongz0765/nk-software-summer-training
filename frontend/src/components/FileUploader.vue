<script setup lang="ts">
import { UploadFilled } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { ref } from 'vue';

import { http } from '@/api/http';
import type { ApiResponse, FileUploadResult, OCRResult } from '@/types/reportflow';

const emit = defineEmits<{
  (e: 'uploaded', result: FileUploadResult): void;
  (e: 'ocr-result', result: OCRResult): void;
  (e: 'ocr-loading', loading: boolean): void;
}>();

const fileList = ref<any[]>([]);
const uploading = ref(false);
const ocrLoading = ref(false);
const previewUrl = ref<string | null>(null);
const previewType = ref<'image' | 'other' | null>(null);

const ALLOWED = ['.png', '.jpg', '.jpeg', '.pdf', '.docx', '.xlsx', '.txt'];

function getPreviewType(name: string) {
  const ext = name.toLowerCase().split('.').pop() || '';
  return ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'].includes(ext) ? 'image' : 'other';
}

const beforeUpload = (file: File) => {
  const suffix = '.' + file.name.split('.').pop()?.toLowerCase();
  if (!ALLOWED.includes(suffix)) { ElMessage.error('不支持该类型'); return false; }
  if (file.size > 20 * 1024 * 1024) { ElMessage.error('文件过大'); return false; }
  return true;
};

async function handleUpload() {
  const item = fileList.value[0];
  if (!item?.raw) return;
  uploading.value = true;
  try {
    const fd = new FormData();
    fd.append('file', item.raw);
    const res = await http.post<ApiResponse<FileUploadResult>>('/files/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }, timeout: 30000,
    });
    if (res.data.code === 0 && res.data.data) {
      emit('uploaded', res.data.data);
      const pType = getPreviewType(item.name);
      previewType.value = pType;
      if (pType === 'image') previewUrl.value = URL.createObjectURL(item.raw);
      await doOCR(res.data.data.file_id);
    } else ElMessage.error('上传失败');
  } catch { ElMessage.error('上传失败'); }
  finally { uploading.value = false; }
}

async function doOCR(fileId: string) {
  ocrLoading.value = true;
  emit('ocr-loading', true);
  try {
    const res = await http.post<ApiResponse<OCRResult>>('/ocr/recognize', { file_path: fileId });
    if (res.data.code === 0 && res.data.data) emit('ocr-result', res.data.data);
  } catch { /* */ }
  finally { ocrLoading.value = false; emit('ocr-loading', false); }
}

function handleRemove() { previewUrl.value = null; previewType.value = null; }
function clearFiles() { fileList.value = []; previewUrl.value = null; previewType.value = null; }
defineExpose({ clearFiles });
</script>

<template>
  <div class="fu">
    <el-upload
      v-model:file-list="fileList" class="fu-zone" drag
      :auto-upload="false" :before-upload="beforeUpload" :limit="1" :on-remove="handleRemove"
      accept=".png,.jpg,.jpeg,.pdf,.docx,.xlsx,.txt"
    >
      <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
      <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
      <template #tip><div class="el-upload__tip">PNG / JPG / PDF / DOCX / XLSX / TXT，≤20MB</div></template>
    </el-upload>
    <div v-if="fileList.length" style="margin-top:12px;text-align:right">
      <el-button type="primary" :loading="uploading" @click="handleUpload">
        {{ uploading ? '上传中...' : '开始上传' }}
      </el-button>
    </div>
    <div v-if="previewType === 'image' && previewUrl" class="fu-preview">
      <img :src="previewUrl" alt="预览" />
    </div>
    <div v-if="ocrLoading" style="margin-top:8px">
      <el-alert type="info" :closable="false" title="OCR 识别中..." show-icon />
    </div>
  </div>
</template>

<style scoped>
.fu { display:flex; flex-direction:column; gap:12px; }
.fu-preview { text-align:center; }
.fu-preview img { max-width:100%; max-height:360px; border-radius:8px; border:1px solid #e5e7eb; object-fit:contain; }
</style>
