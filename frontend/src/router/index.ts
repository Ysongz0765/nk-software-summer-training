import { createRouter, createWebHistory } from 'vue-router';

import MainLayout from '@/layouts/MainLayout.vue';
import CreateReportView from '@/views/CreateReportView.vue';
import DashboardView from '@/views/DashboardView.vue';
import LoginView from '@/views/LoginView.vue';
import ReportEditorView from '@/views/ReportEditorView.vue';
import ReportHistoryView from '@/views/ReportHistoryView.vue';
import TemplateListView from '@/views/TemplateListView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'dashboard',
          component: DashboardView,
        },
        {
          path: 'reports/create',
          name: 'create-report',
          component: CreateReportView,
        },
        {
          path: 'reports/:id/edit',
          name: 'report-editor',
          component: ReportEditorView,
        },
        {
          path: 'templates',
          name: 'templates',
          component: TemplateListView,
        },
        {
          path: 'reports',
          name: 'report-history',
          component: ReportHistoryView,
        },
      ],
    },
  ],
});

router.beforeEach((to) => {
  const token = localStorage.getItem('reportflow_token');
  if (to.name !== 'login' && !token) {
    return { name: 'login', query: { redirect: to.fullPath } };
  }
  if (to.name === 'login' && token) {
    return { name: 'dashboard' };
  }
  return true;
});

export default router;
