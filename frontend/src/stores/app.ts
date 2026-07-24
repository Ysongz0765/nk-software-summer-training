import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

import { getHealth, listProjects } from '@/api/reportflow';
import type { HealthStatus, Project } from '@/types/reportflow';

export const useAppStore = defineStore('app', () => {
  const health = ref<HealthStatus | null>(null);
  const projects = ref<Project[]>([]);
  const currentProjectId = ref<number | null>(readProjectId());
  const loading = ref(false);
  const projectsLoading = ref(false);

  const currentProject = computed(
    () => projects.value.find((project) => project.id === currentProjectId.value) || null,
  );

  async function refreshHealth(): Promise<void> {
    loading.value = true;
    try {
      const response = await getHealth();
      health.value = response.data;
    } finally {
      loading.value = false;
    }
  }

  async function refreshProjects(): Promise<void> {
    projectsLoading.value = true;
    try {
      const response = await listProjects();
      projects.value = response.data || [];
      if (
        currentProjectId.value &&
        !projects.value.some((project) => project.id === currentProjectId.value)
      ) {
        setCurrentProject(null);
      }
      if (!currentProjectId.value && projects.value.length) {
        setCurrentProject(projects.value[0].id);
      }
    } finally {
      projectsLoading.value = false;
    }
  }

  function setCurrentProject(projectId: number | null): void {
    currentProjectId.value = projectId;
    if (projectId) localStorage.setItem('reportflow_current_project_id', String(projectId));
    else localStorage.removeItem('reportflow_current_project_id');
  }

  return {
    health,
    projects,
    currentProjectId,
    currentProject,
    loading,
    projectsLoading,
    refreshHealth,
    refreshProjects,
    setCurrentProject,
  };
});

function readProjectId(): number | null {
  const raw = localStorage.getItem('reportflow_current_project_id');
  if (!raw) return null;
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}
