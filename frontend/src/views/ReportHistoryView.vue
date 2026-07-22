<script setup lang="ts">
import { Delete, Download, Edit, Plus, View } from '@element-plus/icons-vue';
import { ElMessageBox } from 'element-plus';
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { exportReport, listReports } from '@/api/reportflow';
import type { ReportSummary } from '@/types/reportflow';

const router = useRouter();
const reports = ref<ReportSummary[]>([]); const loading = ref(false); const exportingId = ref<number|null>(null);
const typeLabel = (t:string)=>({daily:'日报',weekly:'周报',monthly:'月报'}[t]||t);
const statusTag = (s:string)=>({draft:'info',published:'success',archived:'warning'}[s]||'info');
const statusLabel = (s:string)=>({draft:'草稿',published:'已发布',archived:'已归档'}[s]||s);

async function load() { loading.value=true; try{const r=await listReports();reports.value=r.data||[]}catch{reports.value=[]}finally{loading.value=false} }
async function handleExport(id:number,type:string){exportingId.value=id;try{const r=await exportReport(id,type);if(r.data?.download_url){const b=(import.meta as any).env?.VITE_API_BASE_URL||'http://localhost:8000';const a=document.createElement('a');a.href=`${b.replace('/api/v1','')}${r.data.download_url}`;a.download='';document.body.appendChild(a);a.click();document.body.removeChild(a)}}catch{}finally{exportingId.value=null}}
async function handleDelete(row:ReportSummary){try{await ElMessageBox.confirm(`确定删除「${row.title}」？`,'删除确认',{type:'warning'});await load()}catch{}}

onMounted(load);
</script>

<template>
  <section>
    <div class="page-header"><div><h2>历史报表</h2><p class="muted">管理已创建的所有报表</p></div><el-button type="primary" :icon="Plus" @click="router.push('/reports/create')">创建新报表</el-button></div>
    <el-card shadow="never" v-loading="loading">
      <el-table :data="reports" empty-text="暂无报表">
        <el-table-column prop="title" label="标题" min-width="180"><template #default="{row}"><el-link type="primary" @click="router.push({path:`/reports/${row.id||1}/edit`,query:{data:JSON.stringify(row)}})">{{row.title}}</el-link></template></el-table-column>
        <el-table-column label="类型" width="80"><template #default="{row}">{{typeLabel(row.report_type)}}</template></el-table-column>
        <el-table-column prop="report_date" label="日期" width="120"/>
        <el-table-column label="状态" width="90"><template #default="{row}"><el-tag :type="statusTag(row.status)" size="small">{{statusLabel(row.status)}}</el-tag></template></el-table-column>
        <el-table-column prop="task_count" label="任务数" width="80" align="center"/>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{row}">
            <el-button size="small" text :icon="View" @click="router.push({path:`/reports/${row.id||1}/edit`,query:{data:JSON.stringify(row)}})">查看</el-button>
            <el-button size="small" text :icon="Edit" @click="router.push({path:`/reports/${row.id||1}/edit`,query:{data:JSON.stringify(row)}})">编辑</el-button>
            <el-dropdown @command="(t:string)=>handleExport(row.id||1,t)"><el-button size="small" text :icon="Download" :loading="exportingId===(row.id||1)">导出</el-button><template #dropdown><el-dropdown-menu><el-dropdown-item command="docx">Word</el-dropdown-item><el-dropdown-item command="json">JSON</el-dropdown-item></el-dropdown-menu></template></el-dropdown>
            <el-button size="small" text :icon="Delete" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!reports.length&&!loading" style="text-align:center;padding:60px 0"><span style="font-size:48px">📋</span><p class="muted" style="margin:12px 0">还没有创建任何报表</p><el-button type="primary" :icon="Plus" @click="router.push('/reports/create')">创建第一份报表</el-button></div>
    </el-card>
  </section>
</template>
