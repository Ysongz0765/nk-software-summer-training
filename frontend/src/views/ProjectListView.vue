<script setup lang="ts">
import { Edit, FolderOpened, Plus, View } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import { archiveProject, createProject, updateProject } from '@/api/reportflow';
import { useAppStore } from '@/stores/app';
import type { Project } from '@/types/reportflow';

const router = useRouter();
const appStore = useAppStore();
const statusFilter = ref('');
const dialogVisible = ref(false);
const saving = ref(false);
const editingId = ref<number | null>(null);
const techStackText = ref('');
const form = reactive({
  name: '',
  description: '',
  project_type: '',
  status: 'active',
  current_stage: '',
  start_date: '',
  end_date: '',
  background_summary: '',
});

const projects = computed(() =>
  appStore.projects.filter(
    (project) => !statusFilter.value || project.status === statusFilter.value,
  ),
);

const statusLabel = (status: string) =>
  ({ active: '进行中', completed: '已完成', archived: '已归档' })[status] || status;
const statusTag = (status: string) =>
  ({ active: 'success', completed: 'primary', archived: 'info' })[status] || 'info';

onMounted(load);

async function load() {
  await appStore.refreshProjects();
}

function openCreate() {
  editingId.value = null;
  Object.assign(form, {
    name: '',
    description: '',
    project_type: '',
    status: 'active',
    current_stage: '',
    start_date: '',
    end_date: '',
    background_summary: '',
  });
  techStackText.value = '';
  dialogVisible.value = true;
}

function openEdit(project: Project) {
  editingId.value = project.id;
  Object.assign(form, {
    name: project.name,
    description: project.description || '',
    project_type: project.project_type || '',
    status: project.status,
    current_stage: project.current_stage || '',
    start_date: project.start_date || '',
    end_date: project.end_date || '',
    background_summary: project.background_summary || '',
  });
  techStackText.value = (project.tech_stack || []).join('、');
  dialogVisible.value = true;
}

async function saveProject() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写项目名称');
    return;
  }
  saving.value = true;
  try {
    const payload = {
      ...form,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      tech_stack: techStackText.value
        .split(/[、,，\n]/)
        .map((item) => item.trim())
        .filter(Boolean),
    };
    if (editingId.value) await updateProject(editingId.value, payload);
    else await createProject(payload);
    await load();
    dialogVisible.value = false;
    ElMessage.success('项目已保存');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '项目保存失败');
  } finally {
    saving.value = false;
  }
}

async function handleArchive(project: Project) {
  try {
    await ElMessageBox.confirm(`确定归档「${project.name}」？`, '归档确认', { type: 'warning' });
    await archiveProject(project.id);
    await load();
    ElMessage.success('项目已归档');
  } catch (error) {
    if (error instanceof Error) ElMessage.error(error.message);
  }
}

function completionText(project: Project) {
  const total = project.task_total || 0;
  const done = project.task_completed || 0;
  return total ? `${done}/${total}` : '-';
}
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h2>项目空间</h2>
        <p class="muted">按项目管理文件、任务、成员、模板和报表上下文</p>
      </div>
      <div class="inline-actions">
        <el-select v-model="statusFilter" clearable placeholder="状态筛选" style="width: 140px">
          <el-option label="进行中" value="active" />
          <el-option label="已完成" value="completed" />
          <el-option label="已归档" value="archived" />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="openCreate">创建项目</el-button>
      </div>
    </div>

    <el-card shadow="never" v-loading="appStore.projectsLoading">
      <el-table
        :data="projects"
        empty-text="暂无项目"
        @row-dblclick="(row: Project) => router.push(`/projects/${row.id}`)"
      >
        <el-table-column prop="name" label="项目名称" min-width="180">
          <template #default="{ row }">
            <el-link type="primary" @click="router.push(`/projects/${row.id}`)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="project_type" label="类型" width="120">
          <template #default="{ row }">{{ row.project_type || '-' }}</template>
        </el-table-column>
        <el-table-column prop="current_stage" label="当前阶段" min-width="140">
          <template #default="{ row }">{{ row.current_stage || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small">{{
              statusLabel(row.status)
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="文件" width="80" align="center" prop="file_count" />
        <el-table-column label="报表" width="80" align="center" prop="report_count" />
        <el-table-column label="任务" width="90" align="center">
          <template #default="{ row }">{{ completionText(row) }}</template>
        </el-table-column>
        <el-table-column prop="last_activity_at" label="最近更新" min-width="170">
          <template #default="{ row }">{{ row.last_activity_at || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text :icon="View" @click="router.push(`/projects/${row.id}`)">
              详情
            </el-button>
            <el-button size="small" text :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button
              size="small"
              text
              type="warning"
              :icon="FolderOpened"
              :disabled="row.status === 'archived'"
              @click="handleArchive(row)"
            >
              归档
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" width="640px" :title="editingId ? '编辑项目' : '创建项目'">
      <el-form label-position="top">
        <el-row :gutter="14">
          <el-col :span="12">
            <el-form-item label="项目名称">
              <el-input v-model="form.name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="项目类型">
              <el-input v-model="form.project_type" placeholder="课程项目、实习项目..." />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="当前阶段">
              <el-input v-model="form.current_stage" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option label="进行中" value="active" />
                <el-option label="已完成" value="completed" />
                <el-option label="已归档" value="archived" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="技术栈">
          <el-input v-model="techStackText" placeholder="Vue、FastAPI、MySQL" />
        </el-form-item>
        <el-form-item label="项目介绍">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="项目背景摘要">
          <el-input v-model="form.background_summary" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveProject">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.inline-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
