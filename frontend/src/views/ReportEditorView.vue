<script setup lang="ts">
import { ArrowLeft, Check, Download, Edit, View } from '@element-plus/icons-vue';
import { onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { createReport, exportReport as exportReportApi, updateReport } from '@/api/reportflow';
import TaskEditor from '@/components/TaskEditor.vue';
import ReportPreview from '@/components/ReportPreview.vue';
import type { ReportContent, TaskItem } from '@/types/reportflow';

const route = useRoute(); const router = useRouter();
const reportId = ref(Number(route.params.id) || 1);

const report = ref<ReportContent>({
  report_type: 'daily', title: '', date: new Date().toISOString().slice(0, 10),
  summary: '', completed_tasks: [], in_progress_tasks: [], problems: [],
  solutions: [], next_plan: [], custom_fields: {}, missing_fields: [], style: 'concise',
});

const editMode = ref<'form' | 'preview'>('form');
const saving = ref(false); const exporting = ref(false); const saved = ref(false);

const problemsText = ref(''); const solutionsText = ref(''); const nextPlanText = ref('');

function syncListToText() { problemsText.value = (report.value.problems||[]).join('\n'); solutionsText.value = (report.value.solutions||[]).join('\n'); nextPlanText.value = (report.value.next_plan||[]).join('\n'); }
function syncTextToList() { report.value.problems = problemsText.value.split('\n').filter(s=>s.trim()); report.value.solutions = solutionsText.value.split('\n').filter(s=>s.trim()); report.value.next_plan = nextPlanText.value.split('\n').filter(s=>s.trim()); }

onMounted(() => {
  const d = route.query.data; if (typeof d === 'string') try { Object.assign(report.value, JSON.parse(d)) } catch {}
  syncListToText();
});
watch(() => route.query.data, val => { if (typeof val === 'string') try { Object.assign(report.value, JSON.parse(val)); syncListToText() } catch {} });

function onCompleted(t: TaskItem[]) { report.value.completed_tasks = t.map(x=>({...x,status:'completed'})); }
function onInProgress(t: TaskItem[]) { report.value.in_progress_tasks = t.map(x=>x.status==='completed'?{...x,status:'in_progress'}:x); }

async function handleSave() {
  syncTextToList(); saving.value = true;
  try {
    try { await updateReport(reportId.value, { title: report.value.title, status: 'draft', content: report.value }); }
    catch { const r = await createReport({ report_type: report.value.report_type, title: report.value.title, report_date: report.value.date, source_data: { content: report.value } }); if (r.data?.id) reportId.value = r.data.id; }
    saved.value = true; setTimeout(()=>saved.value=false,1500);
  } catch {} finally { saving.value = false; }
}

async function handleExport(type: string) {
  syncTextToList(); exporting.value = true;
  try {
    await handleSave();
    const res = await exportReportApi(reportId.value, type);
    if (res.data?.download_url) {
      const base = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000';
      const a = document.createElement('a'); a.href = `${base.replace('/api/v1','')}${res.data.download_url}`; a.download = ''; document.body.appendChild(a); a.click(); document.body.removeChild(a);
    }
  } catch {} finally { exporting.value = false; }
}
</script>

<template>
  <section>
    <div class="page-header">
      <div><el-button text :icon="ArrowLeft" @click="router.push('/reports/create')">返回</el-button><h2 style="margin-top:8px">在线编辑</h2></div>
      <div style="display:flex;gap:8px">
        <el-button :type="editMode==='preview'? '':'primary'" size="small" :icon="editMode==='preview'?View:Edit" @click="editMode=editMode==='form'?'preview':'form'">{{ editMode==='form'?'切换预览':'切换编辑' }}</el-button>
        <el-button size="small" :icon="Check" :loading="saving" :type="saved?'success':''" @click="handleSave">{{ saved?'已保存':'保存' }}</el-button>
        <el-dropdown @command="(t:string)=>handleExport(t)">
          <el-button size="small" :icon="Download" :loading="exporting">导出</el-button>
          <template #dropdown><el-dropdown-menu><el-dropdown-item command="docx">Word (.docx)</el-dropdown-item><el-dropdown-item command="json">JSON</el-dropdown-item></el-dropdown-menu></template>
        </el-dropdown>
      </div>
    </div>

    <div v-show="editMode==='form'" class="ef">
      <el-card shadow="never" class="es">
        <el-row :gutter="16">
          <el-col :span="8"><label class="fl">报表类型</label><el-select v-model="report.report_type" style="width:100%"><el-option label="日报" value="daily"/><el-option label="周报" value="weekly"/></el-select></el-col>
          <el-col :span="8"><label class="fl">标题</label><el-input v-model="report.title" placeholder="报表标题"/></el-col>
          <el-col :span="8"><label class="fl">日期</label><el-date-picker v-model="report.date" type="date" style="width:100%" value-format="YYYY-MM-DD"/></el-col>
        </el-row>
      </el-card>
      <el-card shadow="never" class="es"><template #header><strong>工作总结</strong></template><el-input v-model="report.summary" type="textarea" :rows="3" placeholder="概述工作内容和进展..."/></el-card>
      <el-card shadow="never" class="es"><TaskEditor :tasks="report.completed_tasks" title="已完成任务" @update:tasks="onCompleted"/></el-card>
      <el-card shadow="never" class="es"><TaskEditor :tasks="report.in_progress_tasks" title="进行中任务" @update:tasks="onInProgress"/></el-card>
      <el-row :gutter="16">
        <el-col :span="12"><el-card shadow="never" class="es"><template #header><strong>问题与风险</strong></template><el-input v-model="problemsText" type="textarea" :rows="4" placeholder="每行一个问题..."/></el-card></el-col>
        <el-col :span="12"><el-card shadow="never" class="es"><template #header><strong>解决方案</strong></template><el-input v-model="solutionsText" type="textarea" :rows="4" placeholder="每行一个方案..."/></el-card></el-col>
      </el-row>
      <el-card shadow="never" class="es"><template #header><strong>下一步计划</strong></template><el-input v-model="nextPlanText" type="textarea" :rows="4" placeholder="每行一个计划..."/></el-card>
    </div>

    <div v-show="editMode==='preview'"><ReportPreview :report="report"/></div>

    <div class="bottom-bar">
      <el-button :icon="ArrowLeft" @click="router.push('/reports/create')">返回创建</el-button>
      <div style="display:flex;gap:8px">
        <el-button :icon="Check" :loading="saving" @click="handleSave">保存草稿</el-button>
        <el-button type="primary" :icon="Download" :loading="exporting" @click="handleExport('docx')">导出 Word</el-button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ef{display:flex;flex-direction:column;}.es{margin-bottom:12px;}.fl{display:block;margin-bottom:4px;font-size:13px;font-weight:500;color:#374151;}
.bottom-bar{margin-top:24px;padding-top:16px;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between;}
</style>
