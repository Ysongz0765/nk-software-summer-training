<script setup lang="ts">
import { UploadFilled } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import type { UploadUserFile } from 'element-plus';
import { computed, ref } from 'vue';

import { http } from '@/api/http';
import type { ApiResponse, FileUploadResult, OCRResult } from '@/types/reportflow';

const emit = defineEmits<{
  (e: 'uploaded', result: FileUploadResult): void;
  (e: 'ocr-result', result: OCRResult): void;
  (e: 'ocr-loading', loading: boolean): void;
  (e: 'all-uploaded', results: FileUploadResult[]): void;
}>();

const fileList = ref<UploadUserFile[]>([]);
const uploading = ref(false);
const ocrLoading = ref(false);
const uploadedResults = ref<FileUploadResult[]>([]);
const uploadProgress = ref({ current: 0, total: 0 });

const ALLOWED = ['.png', '.jpg', '.jpeg', '.pdf', '.docx', '.xlsx', '.txt'];

function getPreviewType(name: string) {
  const ext = name.toLowerCase().split('.').pop() || '';
  return ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'].includes(ext) ? 'image' : 'other';
}

const beforeUpload = (file: File) => {
  const suffix = '.' + file.name.split('.').pop()?.toLowerCase();
  if (!ALLOWED.includes(suffix)) {
    ElMessage.error(`不支持该类型: ${file.name}`);
    return false;
  }
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.error(`文件过大 (≤20MB): ${file.name}`);
    return false;
  }
  return true;
};

async function handleUpload() {
  if (!fileList.value.length) return;
  uploading.value = true;
  uploadedResults.value = [];
  uploadProgress.value = { current: 0, total: fileList.value.length };

  for (const item of fileList.value) {
    if (!item?.raw) continue;
    try {
      const fd = new FormData();
      fd.append('file', item.raw);
      const res = await http.post<ApiResponse<FileUploadResult>>('/files/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000,
      });
      if (res.data.code === 0 && res.data.data) {
        uploadedResults.value.push(res.data.data);
        emit('uploaded', res.data.data);
        await doOCR(res.data.data.file_id);
      } else {
        ElMessage.error(`${item.name} 上传失败`);
      }
    } catch {
      ElMessage.error(`${item.name} 上传失败`);
    } finally {
      uploadProgress.value.current++;
    }
  }

  uploading.value = false;
  emit('all-uploaded', uploadedResults.value);
  ElMessage.success(`成功上传 ${uploadedResults.value.length}/${fileList.value.length} 个文件`);
}

async function doOCR(fileId: string) {
  ocrLoading.value = true;
  emit('ocr-loading', true);
  try {
    const res = await http.post<ApiResponse<OCRResult>>('/ocr/recognize', { file_path: fileId });
    if (res.data.code === 0 && res.data.data) emit('ocr-result', res.data.data);
  } catch {
    /* OCR 识别失败不阻塞流程 */
  } finally {
    ocrLoading.value = false;
    emit('ocr-loading', false);
  }
}

function handleRemove(_file: UploadUserFile, fileListAfter: UploadUserFile[]) {
  // 同步清理：element-plus 的 on-remove 回调拿到的是删除后的列表
  fileList.value = fileListAfter;
}

function clearFiles() {
  fileList.value = [];
  uploadedResults.value = [];
  uploadProgress.value = { current: 0, total: 0 };
}

const uploadDisabled = computed(() => !fileList.value.length || uploading.value);

defineExpose({ clearFiles });
</script>

<template>
  <div class="fu">
    <el-upload
      v-model:file-list="fileList"
      class="fu-zone"
      drag
      multiple
      :auto-upload="false"
      :before-upload="beforeUpload"
      :on-remove="handleRemove"
      accept=".png,.jpg,.jpeg,.pdf,.docx,.xlsx,.txt"
    >
      <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
      <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
      <template #tip>
        <div class="el-upload__tip">
          PNG / JPG / PDF / DOCX / XLSX / TXT，≤20MB，支持多文件
        </div>
      </template>
    </el-upload>
    <div v-if="fileList.length" style="margin-top: 12px; text-align: right">
      <span v-if="uploading && uploadProgress.total > 1" style="margin-right: 12px; color: #667085">
        上传中 {{ uploadProgress.current }}/{{ uploadProgress.total }}
      </span>
      <el-button type="primary" :loading="uploading" :disabled="uploadDisabled" @click="handleUpload">
        {{ uploading ? '上传中...' : `上传 ${fileList.length} 个文件` }}
      </el-button>
    </div>
    <div v-if="uploadedResults.length" style="margin-top: 8px">
      <el-tag
        v-for="result in uploadedResults"
        :key="result.file_id"
        type="success"
        style="margin-right: 8px; margin-bottom: 4px"
      >
        ✓ {{ result.original_name || result.file_id }}
      </el-tag>
    </div>
    <div v-if="ocrLoading" style="margin-top: 8px">
      <el-alert type="info" :closable="false" title="OCR 识别中..." show-icon />
    </div>
  </div>
</template>

<style scoped>
.fu {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.fu-preview {
  text-align: center;
}
.fu-preview img {
  max-width: 100%;
  max-height: 360px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  object-fit: contain;
}
</style>
