import { defineStore } from 'pinia';
import { ref } from 'vue';

import { getHealth } from '@/api/reportflow';
import type { HealthStatus } from '@/types/reportflow';

export const useAppStore = defineStore('app', () => {
  const health = ref<HealthStatus | null>(null);
  const loading = ref(false);

  async function refreshHealth(): Promise<void> {
    loading.value = true;
    try {
      const response = await getHealth();
      health.value = response.data;
    } finally {
      loading.value = false;
    }
  }

  return {
    health,
    loading,
    refreshHealth,
  };
});
