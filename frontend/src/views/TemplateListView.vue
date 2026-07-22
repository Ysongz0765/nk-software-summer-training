<script setup lang="ts">
import { Delete, Plus, Upload } from '@element-plus/icons-vue';
import { ElMessageBox } from 'element-plus';
import { onMounted, ref } from 'vue';
import { http } from '@/api/http';
import { listTemplates, uploadFile } from '@/api/reportflow';
import type { Template } from '@/types/reportflow';

const templates = ref<Template[]>([]); const loading = ref(false); const uploading = ref(false);
const typeLabel = (t:string)=>({daily:'日报',weekly:'周报',monthly:'月报',custom:'自定义'}[t]||t);
const typeTag = (t:string)=>({daily:'primary',weekly:'success',monthly:'warning',custom:'info'}[t]||'info');

async function load(){loading.value=true;try{const r=await listTemplates();templates.value=r.data||[]}catch{templates.value=[]}finally{loading.value=false}}
function handleUpload(){
  const i=document.createElement('input');i.type='file';i.accept='.docx,.xlsx';
  i.onchange=async(e:any)=>{const f=e.target?.files?.[0];if(!f)return;uploading.value=true;try{const r=await uploadFile(f);if(r.code!==0||!r.data)return;await http.post('/templates',{name:f.name.replace(/\.[^.]+$/,''),file_path:r.data.file_id,template_type:'daily'});await load()}catch{}finally{uploading.value=false}};
  i.click();
}
async function handleDelete(row:Template){try{await ElMessageBox.confirm(`确定删除「${row.name}」？`,'删除确认',{type:'warning'});await load()}catch{}}

onMounted(load);
</script>

<template>
  <section>
    <div class="page-header"><div><h2>模板库</h2><p class="muted">管理 Word / Excel 报表模板</p></div><el-button type="primary" :icon="Upload" :loading="uploading" @click="handleUpload">上传模板</el-button></div>
    <el-card shadow="never" v-loading="loading">
      <div v-if="!templates.length&&!loading" style="text-align:center;padding:64px 0"><span style="font-size:48px">📁</span><p class="muted" style="margin:12px 0">还没有上传模板</p><el-button type="primary" :icon="Upload" @click="handleUpload">上传第一份模板</el-button></div>
      <el-table v-else :data="templates">
        <el-table-column prop="name" label="模板名称" min-width="180"/>
        <el-table-column label="类型" width="100"><template #default="{row}"><el-tag :type="typeTag(row.template_type)" size="small" effect="plain">{{typeLabel(row.template_type)}}</el-tag></template></el-table-column>
        <el-table-column prop="description" label="描述" min-width="200"><template #default="{row}">{{row.description||'-'}}</template></el-table-column>
        <el-table-column label="字段数" width="80" align="center"><template #default="{row}">{{Object.keys(row.field_config||{}).length||'-'}}</template></el-table-column>
        <el-table-column label="操作" width="160"><template #default="{row}"><el-button size="small" text type="primary">使用</el-button><el-button size="small" text type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button></template></el-table-column>
      </el-table>
    </el-card>
  </section>
</template>
