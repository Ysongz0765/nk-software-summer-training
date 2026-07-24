<script setup lang="ts">
import { UploadFilled } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import type { UploadFile, UploadRawFile } from 'element-plus';
import { ref } from 'vue';

import { http } from '@/api/http';
import type { ApiResponse, FileUploadResult, OCRResult } from '@/types/reportflow';

const emit = defineEmits<{
  (e: 'uploaded', result: FileUploadResult): void;
  (e: 'ocr-result', result: OCRResult): void;
  (e: 'ocr-loading', loading: boolean): void;
}>();

const fileList = ref<UploadFile[]>([]);
const uploading = ref(false);
const ocrLoading = ref(false);
const previewUrls = ref<string[]>([]);

const ALLOWED = ['.png', '.jpg', '.jpeg', '.pdf', '.docx', '.xlsx', '.txt'];

function getPreviewType(name: string) {
  const ext = name.toLowerCase().split('.').pop() || '';
  return ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'].includes(ext) ? 'image' : 'other';
}

const beforeUpload = (file: UploadRawFile) => {
  const suffix = '.' + file.name.split('.').pop()?.toLowerCase();
  if (!ALLOWED.includes(suffix)) { ElMessage.error('不支持该类型'); return false; }
  if (file.size > 20 * 1024 * 1024) { ElMessage.error('文件过大（≤20MB）'); return false; }
  return true;
};

async function handleUpload() {
  if (!fileList.value.length) return;
  uploading.value = true;
  ocrLoading.value = true;
  emit('ocr-loading', true);
  previewUrls.value = [];

  for (const item of fileList.value) {
    if (!item.raw) continue;
    try {
      const fd = new FormData();
      fd.append('file', item.raw);
      const res = await http.post<ApiResponse<FileUploadResult>>('/files/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' }, timeout: 30000,
      });
      if (res.data.code === 0 && res.data.data) {
        emit('uploaded', res.data.data);

        // 图片预览
        if (getPreviewType(item.name) === 'image') {
          previewUrls.value.push(URL.createObjectURL(item.raw));
        }

        // OCR识别
        try {
          const ocrRes = await http.post<ApiResponse<OCRResult>>('/ocr/recognize', { file_path: res.data.data.file_id });
          if (ocrRes.data.code === 0 && ocrRes.data.data) {
            emit('ocr-result', ocrRes.data.data);
          }
        } catch { /* OCR失败不阻塞 */ }
      }
    } catch { ElMessage.error(`「${item.name}」上传失败`); }
  }

  ocrLoading.value = false;
  emit('ocr-loading', false);
  uploading.value = false;
}

// ---------- 剪贴板粘贴 ----------
function buildFileFromBlob(blob: Blob, name: string): File {
  return new File([blob], name, { type: blob.type });
}

async function handlePaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items;
  if (!items) return;

  for (const item of items) {
    if (item.type.startsWith('image/')) {
      e.preventDefault();
      const blob = item.getAsFile();
      if (!blob) continue;

      const ext = item.type.replace('image/', '').replace('jpeg', 'jpg');
      const name = `paste-${Date.now()}.${ext}`;
      const file = buildFileFromBlob(blob, name);

      const suffix = '.' + name.split('.').pop()?.toLowerCase();
      if (!ALLOWED.includes(suffix)) { ElMessage.error('不支持的图片格式'); continue; }
      if (file.size > 20 * 1024 * 1024) { ElMessage.error('图片过大（≤20MB）'); continue; }

      fileList.value.push({
        name: file.name,
        size: file.size,
        status: 'ready',
        uid: Date.now(),
        raw: file as UploadRawFile,
      } as UploadFile);

      await handleUpload();
      return;
    }
  }
}

function handleRemove(file: UploadFile) {
  const idx = fileList.value.findIndex(f => f.uid === file.uid);
  if (idx >= 0 && idx < previewUrls.value.length) {
    previewUrls.value.splice(idx, 1);
  }
}
function clearFiles() { fileList.value = []; previewUrls.value = []; }
defineExpose({ clearFiles });
</script>

<template>
  <div class="fu" @paste="handlePaste">
    <el-upload
      v-model:file-list="fileList" class="fu-zone" drag
      :auto-upload="false" :before-upload="beforeUpload" :on-remove="handleRemove"
      accept=".png,.jpg,.jpeg,.pdf,.docx,.xlsx,.txt"
      multiple
    >
      <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
      <div class="el-upload__text">
        将文件拖到此处，或<em>点击上传</em>
      </div>
      <div class="el-upload__text" style="font-size:12px;color:#909399;margin-top:4px">
        支持多文件，也可 <kbd>Ctrl+V</kbd> 粘贴截图
      </div>
      <template #tip><div class="el-upload__tip">PNG / JPG / PDF / DOCX / XLSX / TXT，单文件≤20MB</div></template>
    </el-upload>
    <div v-if="fileList.length" style="margin-top:12px;display:flex;justify-content:space-between;align-items:center">
      <span class="muted">已选 {{ fileList.length }} 个文件</span>
      <el-button type="primary" :loading="uploading" @click="handleUpload">
        {{ uploading ? '上传中...' : '全部上传' }}
      </el-button>
    </div>
    <div v-if="previewUrls.length" class="fu-preview-list">
      <img v-for="(url, i) in previewUrls" :key="i" :src="url" alt="预览" />
    </div>
    <div v-if="ocrLoading" style="margin-top:8px">
      <el-alert type="info" :closable="false" title="OCR 识别中..." show-icon />
    </div>
  </div>
</template>

<style scoped>
.fu { display:flex; flex-direction:column; gap:12px; }
.muted { color: #909399; font-size: 13px; }
.fu-preview-list { display: flex; flex-wrap: wrap; gap: 8px; }
.fu-preview-list img { max-width:160px; max-height:160px; border-radius:8px; border:1px solid #e5e7eb; object-fit:contain; }
kbd {
  padding: 1px 5px; font-size: 12px; color: #606266;
  background: #f0f2f5; border: 1px solid #d3d6db; border-radius: 4px;
}
</style>
