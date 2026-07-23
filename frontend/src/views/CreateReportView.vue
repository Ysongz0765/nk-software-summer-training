<script setup lang="ts">
import { ArrowLeft, ArrowRight, Check, MagicStick } from '@element-plus/icons-vue';
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { extractTasks, checkMissingInfo, generateReport } from '@/api/reportflow';
import FileUploader from '@/components/FileUploader.vue';
import TaskEditor from '@/components/TaskEditor.vue';
import ReportPreview from '@/components/ReportPreview.vue';
import type { FileUploadResult, MissingInformationResult, OCRResult, ReportContent, TaskItem } from '@/types/reportflow';

const route = useRoute(); const router = useRouter();
const step = ref(0);
const reportType = ref((route.query.type as string) || 'daily');

const uploadedFile = ref<FileUploadResult | null>(null);
const ocrText = ref(''); const ocrLoading = ref(false); const manualText = ref('');
function onUploaded(f: FileUploadResult) { uploadedFile.value = f; }
function onOCRResult(r: OCRResult) { ocrText.value = r.text; manualText.value = r.text; }
function onOCRLoading(v: boolean) { ocrLoading.value = v; }
const sourceText = computed(() => manualText.value.trim());

const tasks = ref<TaskItem[]>([]); const extracting = ref(false);
async function doExtract() {
  if (!sourceText.value) return;
  extracting.value = true;
  try { const res = await extractTasks({ source_text: sourceText.value, report_type: reportType.value }); tasks.value = (res.data || []).map(t => ({ ...t, user_confirmed: false })); }
  catch { } finally { extracting.value = false; }
}

const missing = ref<MissingInformationResult | null>(null); const checking = ref(false);
const answers = ref<Record<string, string>>({});
async function doCheckMissing() {
  checking.value = true;
  try { const res = await checkMissingInfo(tasks.value); missing.value = res.data; }
  catch { missing.value = null; } finally { checking.value = false; }
}

const report = ref<ReportContent | null>(null); const generating = ref(false);
const reportTitle = ref(''); const reportDate = ref(new Date().toISOString().slice(0, 10));
async function doGenerate() {
  generating.value = true;
  try {
    const res = await generateReport({ report_type: reportType.value, title: reportTitle.value || `${reportType.value === 'daily' ? '日报' : '周报'} - ${reportDate.value}`, report_date: reportDate.value, tasks: tasks.value, source_data: answers.value ? { answers: answers.value } : {} });
    report.value = res.data;
  } catch { } finally { generating.value = false; }
}
function goEdit() { if (report.value) router.push({ path: '/reports/1/edit', query: { data: JSON.stringify(report.value) } }); }
</script>

<template>
  <section>
    <div class="page-header"><div><h2>创建报表</h2><p class="muted">{{ reportType === 'daily' ? '日报' : '周报' }} · 四步生成</p></div></div>
    <el-steps :active="step" align-center finish-status="success" style="margin-bottom:28px">
      <el-step title="上传素材" description="截图或文档" />
      <el-step title="确认任务" description="AI 自动提取" />
      <el-step title="补充信息" description="检查缺失项" />
      <el-step title="生成预览" description="确认并导出" />
    </el-steps>

    <!-- 步骤0 -->
    <div v-show="step===0">
      <el-card shadow="never">
        <FileUploader @uploaded="onUploaded" @ocr-result="onOCRResult" @ocr-loading="onOCRLoading" />
        <el-divider>或直接输入文本</el-divider>
        <el-input v-model="manualText" type="textarea" :rows="6" placeholder="输入或粘贴工作内容，每行一项任务..." :disabled="ocrLoading" />
        <div style="margin-top:18px;text-align:right">
          <el-button type="primary" :icon="ArrowRight" :disabled="!sourceText" @click="step=1">下一步</el-button>
        </div>
      </el-card>
    </div>

    <!-- 步骤1 -->
    <div v-show="step===1">
      <el-card shadow="never">
        <template #header>
          <div class="card-hd">
            <strong>任务列表</strong>
            <el-button size="small" type="primary" :loading="extracting" :icon="MagicStick" @click="doExtract" :disabled="!sourceText">AI 提取任务</el-button>
          </div>
        </template>
        <div v-if="!tasks.length" class="step-empty"><span style="font-size:40px">📋</span><p>点击「AI 提取任务」从素材中自动识别，或手动添加</p></div>
        <TaskEditor v-else v-model:tasks="tasks" />
        <div style="margin-top:18px;display:flex;justify-content:space-between">
          <el-button :icon="ArrowLeft" @click="step=0">上一步</el-button>
          <el-button type="primary" :icon="ArrowRight" :disabled="!tasks.length" @click="doCheckMissing();step=2">下一步</el-button>
        </div>
      </el-card>
    </div>

    <!-- 步骤2 -->
    <div v-show="step===2">
      <el-card shadow="never">
        <template #header><div class="card-hd"><strong>信息补充</strong><el-button size="small" :loading="checking" @click="doCheckMissing">检查缺失信息</el-button></div></template>
        <div v-if="!missing" class="step-empty"><span style="font-size:40px">🔍</span><p>点击「检查缺失信息」让 AI 分析</p></div>
        <div v-else>
          <div v-if="!missing.missing_fields.length"><el-result icon="success" title="信息完整" sub-title="可以直接生成报表" /></div>
          <div v-else>
            <el-alert type="warning" :closable="false" :title="`以下 ${missing.questions.length} 项建议补充：`" style="margin-bottom:16px" />
            <div v-for="(q,i) in missing.questions" :key="i" style="margin-bottom:12px">
              <label class="f-label">{{ i+1 }}. {{ q }}</label>
              <el-input v-model="answers[missing.missing_fields[i]]" placeholder="请输入..." />
            </div>
          </div>
        </div>
        <el-divider />
        <el-row :gutter="16">
          <el-col :span="6"><label class="f-label">报表标题</label><el-input v-model="reportTitle" placeholder="例：项目日报" /></el-col>
          <el-col :span="6"><label class="f-label">日期</label><el-date-picker v-model="reportDate" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-col>
        </el-row>
        <div style="margin-top:18px;display:flex;justify-content:space-between">
          <el-button :icon="ArrowLeft" @click="step=1">上一步</el-button>
          <el-button type="primary" :icon="ArrowRight" @click="doGenerate();step=3">生成报表预览</el-button>
        </div>
      </el-card>
    </div>

    <!-- 步骤3 -->
    <div v-show="step===3">
      <el-card v-if="generating" shadow="never" style="text-align:center;padding:60px 0">
        <span style="font-size:36px">⏳</span><p style="margin-top:12px">AI 正在生成报表...</p>
      </el-card>
      <div v-else-if="report">
        <ReportPreview :report="report" />
        <div style="margin-top:20px;display:flex;justify-content:space-between">
          <el-button :icon="ArrowLeft" @click="step=2">上一步</el-button>
          <div style="display:flex;gap:8px">
            <el-button @click="doGenerate()">重新生成</el-button>
            <el-button type="primary" :icon="Check" @click="goEdit">进入在线编辑</el-button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.card-hd { display:flex; justify-content:space-between; align-items:center; }
.step-empty { text-align:center; padding:48px 0; color:#667085; }
.step-empty p { margin-top:10px; }
.f-label { display:block; margin-bottom:4px; font-size:13px; font-weight:500; color:#374151; }
</style>
