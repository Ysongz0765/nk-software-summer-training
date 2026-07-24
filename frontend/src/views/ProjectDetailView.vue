<script setup lang="ts">
import { ArrowLeft, MagicStick, Plus } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import {
  createProjectMember,
  createProjectTask,
  deleteProjectMember,
  deleteProjectTask,
  generateProjectSummary,
  getProject,
  getProjectContext,
  updateProjectTask,
} from '@/api/reportflow';
import FileUploader from '@/components/FileUploader.vue';
import { useAppStore } from '@/stores/app';
import type { Project, ProjectContext, ProjectMember, ProjectTask } from '@/types/reportflow';

const route = useRoute();
const router = useRouter();
const appStore = useAppStore();
const projectId = Number(route.params.id);
const loading = ref(false);
const activeTab = ref('overview');
const project = ref<Project | null>(null);
const context = ref<ProjectContext | null>(null);
const summaryText = ref('');
const taskDialogVisible = ref(false);
const memberDialogVisible = ref(false);
const taskSaving = ref(false);
const memberSaving = ref(false);
const taskForm = reactive({
  title: '',
  description: '',
  module: '',
  status: 'pending',
  priority: '',
  owner: '',
  due_date: '',
});
const memberForm = reactive({
  name: '',
  role: '',
  responsibility: '',
});

const taskStats = computed(() => {
  const tasks = context.value?.recent_tasks || [];
  return {
    total: project.value?.task_total || tasks.length,
    completed: tasks.filter((task) => task.status === 'completed').length,
    inProgress: tasks.filter((task) => task.status === 'in_progress').length,
    blocked: tasks.filter((task) => task.status === 'blocked').length,
  };
});

const statusLabel = (status: string) =>
  ({ active: '进行中', completed: '已完成', archived: '已归档' })[status] || status;
const taskStatusLabel = (status: string) =>
  ({ pending: '待处理', in_progress: '进行中', completed: '已完成', blocked: '阻塞' })[status] ||
  status;
const taskStatusTag = (status: string) =>
  ({ pending: 'info', in_progress: 'warning', completed: 'success', blocked: 'danger' })[status] ||
  'info';

onMounted(load);

async function load() {
  loading.value = true;
  try {
    const [projectResponse, contextResponse] = await Promise.all([
      getProject(projectId),
      getProjectContext(projectId),
    ]);
    project.value = projectResponse.data;
    context.value = contextResponse.data;
    appStore.setCurrentProject(projectId);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '项目加载失败');
  } finally {
    loading.value = false;
  }
}

function openTaskDialog() {
  Object.assign(taskForm, {
    title: '',
    description: '',
    module: '',
    status: 'pending',
    priority: '',
    owner: '',
    due_date: '',
  });
  taskDialogVisible.value = true;
}

async function saveTask() {
  if (!taskForm.title.trim()) {
    ElMessage.warning('请填写任务标题');
    return;
  }
  taskSaving.value = true;
  try {
    await createProjectTask(projectId, {
      ...taskForm,
      due_date: taskForm.due_date || null,
    });
    taskDialogVisible.value = false;
    await load();
    ElMessage.success('任务已创建');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '任务保存失败');
  } finally {
    taskSaving.value = false;
  }
}

async function markTaskDone(task: ProjectTask) {
  await updateProjectTask(projectId, task.id, { status: 'completed' });
  await load();
}

async function removeTask(task: ProjectTask) {
  try {
    await ElMessageBox.confirm(`确定删除任务「${task.title}」？`, '删除确认', { type: 'warning' });
    await deleteProjectTask(projectId, task.id);
    await load();
  } catch (error) {
    if (error instanceof Error) ElMessage.error(error.message);
  }
}

function openMemberDialog() {
  Object.assign(memberForm, { name: '', role: '', responsibility: '' });
  memberDialogVisible.value = true;
}

async function saveMember() {
  if (!memberForm.name.trim()) {
    ElMessage.warning('请填写成员姓名');
    return;
  }
  memberSaving.value = true;
  try {
    await createProjectMember(projectId, memberForm);
    memberDialogVisible.value = false;
    await load();
    ElMessage.success('成员已添加');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '成员保存失败');
  } finally {
    memberSaving.value = false;
  }
}

async function removeMember(member: ProjectMember) {
  try {
    await ElMessageBox.confirm(`确定删除成员「${member.name}」？`, '删除确认', { type: 'warning' });
    await deleteProjectMember(projectId, member.id);
    await load();
  } catch (error) {
    if (error instanceof Error) ElMessage.error(error.message);
  }
}

async function doGenerateSummary() {
  try {
    const response = await generateProjectSummary(projectId);
    summaryText.value = response.data?.generated_summary || '';
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '摘要生成失败');
  }
}
</script>

<template>
  <section v-loading="loading">
    <div class="page-header">
      <div>
        <el-button text :icon="ArrowLeft" @click="router.push('/projects')">返回项目</el-button>
        <h2 style="margin-top: 8px">{{ project?.name || '项目详情' }}</h2>
        <p class="muted">
          {{ project?.project_type || '未设置类型' }} · {{ statusLabel(project?.status || '') }} ·
          {{ project?.current_stage || '未设置阶段' }}
        </p>
      </div>
      <el-button
        type="primary"
        @click="router.push({ path: '/reports/create', query: { project_id: projectId } })"
      >
        在项目中生成报表
      </el-button>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="项目概览" name="overview">
        <el-row :gutter="16">
          <el-col :span="16">
            <el-card shadow="never">
              <template #header><strong>项目背景</strong></template>
              <p>{{ context?.background_summary || project?.description || '暂无项目背景。' }}</p>
              <div class="tag-row">
                <el-tag v-for="tech in project?.tech_stack || []" :key="tech" effect="plain">
                  {{ tech }}
                </el-tag>
              </div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="never">
              <template #header><strong>任务统计</strong></template>
              <div class="stat-grid">
                <span>总数：{{ taskStats.total }}</span>
                <span>已完成：{{ taskStats.completed }}</span>
                <span>推进中：{{ taskStats.inProgress }}</span>
                <span>阻塞：{{ taskStats.blocked }}</span>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="项目文件" name="files">
        <el-card shadow="never">
          <FileUploader :project-id="projectId" @uploaded="load" />
          <el-divider />
          <el-table :data="context?.recent_files || []" empty-text="暂无项目文件">
            <el-table-column prop="original_name" label="文件名" min-width="220" />
            <el-table-column prop="file_type" label="类型" width="90" />
            <el-table-column prop="file_size" label="大小" width="110" />
            <el-table-column prop="created_at" label="上传时间" min-width="170" />
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="项目任务" name="tasks">
        <el-card shadow="never">
          <template #header>
            <div class="card-hd">
              <strong>任务列表</strong>
              <el-button size="small" type="primary" :icon="Plus" @click="openTaskDialog">
                添加任务
              </el-button>
            </div>
          </template>
          <el-table :data="context?.recent_tasks || []" empty-text="暂无任务">
            <el-table-column prop="title" label="任务" min-width="200" />
            <el-table-column prop="module" label="模块" width="120" />
            <el-table-column prop="owner" label="负责人" width="120" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="taskStatusTag(row.status)" size="small">
                  {{ taskStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="due_date" label="截止日期" width="120" />
            <el-table-column label="操作" width="170">
              <template #default="{ row }">
                <el-button
                  size="small"
                  text
                  type="success"
                  :disabled="row.status === 'completed'"
                  @click="markTaskDone(row)"
                >
                  完成
                </el-button>
                <el-button size="small" text type="danger" @click="removeTask(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="项目成员" name="members">
        <el-card shadow="never">
          <template #header>
            <div class="card-hd">
              <strong>成员与分工</strong>
              <el-button size="small" type="primary" :icon="Plus" @click="openMemberDialog">
                添加成员
              </el-button>
            </div>
          </template>
          <el-table :data="context?.members || []" empty-text="暂无成员">
            <el-table-column prop="name" label="姓名" width="140" />
            <el-table-column prop="role" label="角色" width="160" />
            <el-table-column prop="responsibility" label="分工" min-width="220" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button size="small" text type="danger" @click="removeMember(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="历史报表" name="reports">
        <el-card shadow="never">
          <el-table :data="context?.recent_reports || []" empty-text="暂无项目报表">
            <el-table-column prop="title" label="标题" min-width="200" />
            <el-table-column prop="report_type" label="类型" width="90" />
            <el-table-column prop="report_date" label="日期" width="120" />
            <el-table-column prop="task_count" label="任务数" width="90" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button
                  size="small"
                  text
                  type="primary"
                  @click="router.push(`/reports/${row.id}/edit`)"
                >
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="项目背景" name="background">
        <el-card shadow="never">
          <template #header>
            <div class="card-hd">
              <strong>AI 项目摘要</strong>
              <el-button size="small" :icon="MagicStick" @click="doGenerateSummary">
                生成摘要建议
              </el-button>
            </div>
          </template>
          <p>{{ summaryText || context?.background_summary || '暂无摘要。' }}</p>
          <el-divider />
          <el-table :data="context?.project_memories || []" empty-text="暂无项目记忆">
            <el-table-column prop="memory_type" label="类型" width="150" />
            <el-table-column prop="content" label="内容" min-width="260" />
            <el-table-column prop="is_user_confirmed" label="已确认" width="90" />
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="taskDialogVisible" width="560px" title="添加项目任务">
      <el-form label-position="top">
        <el-form-item label="任务标题"><el-input v-model="taskForm.title" /></el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="模块"><el-input v-model="taskForm.module" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="负责人"><el-input v-model="taskForm.owner" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="状态">
          <el-select v-model="taskForm.status" style="width: 100%">
            <el-option label="待处理" value="pending" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="阻塞" value="blocked" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述"
          ><el-input v-model="taskForm.description" type="textarea"
        /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="taskSaving" @click="saveTask">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="memberDialogVisible" width="520px" title="添加成员">
      <el-form label-position="top">
        <el-form-item label="姓名"><el-input v-model="memberForm.name" /></el-form-item>
        <el-form-item label="角色"><el-input v-model="memberForm.role" /></el-form-item>
        <el-form-item label="分工">
          <el-input v-model="memberForm.responsibility" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="memberDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="memberSaving" @click="saveMember">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.card-hd,
.tag-row {
  display: flex;
  align-items: center;
}

.card-hd {
  justify-content: space-between;
}

.tag-row {
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  color: #374151;
}

p {
  margin: 0;
  line-height: 1.8;
}
</style>
