<script setup lang="ts">
import {
  Document,
  Files,
  Fold,
  HomeFilled,
  Plus,
  SwitchButton,
  UserFilled,
} from '@element-plus/icons-vue';
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const collapsed = ref(false);
const currentUser = computed(() => {
  const raw = localStorage.getItem('reportflow_user');
  if (!raw) return { username: '未登录', email: '' };
  try {
    return JSON.parse(raw) as { username: string; email: string };
  } catch {
    return { username: '未登录', email: '' };
  }
});

function doLogout() {
  localStorage.removeItem('reportflow_token');
  localStorage.removeItem('reportflow_user');
  router.push('/login');
}
</script>

<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo" @click="router.push('/')">
        <span class="logo-icon">📊</span
        ><span v-show="!collapsed" class="logo-text">ReportFlow</span>
      </div>
      <el-menu
        router
        :default-active="router.currentRoute.value.path"
        :collapse="collapsed"
        class="side-menu"
      >
        <el-menu-item index="/"
          ><el-icon><HomeFilled /></el-icon><span>工作台</span></el-menu-item
        >
        <el-menu-item index="/reports/create"
          ><el-icon><Plus /></el-icon><span>创建报表</span></el-menu-item
        >
        <el-menu-item index="/reports"
          ><el-icon><Document /></el-icon><span>历史报表</span></el-menu-item
        >
        <el-menu-item index="/templates"
          ><el-icon><Files /></el-icon><span>模板库</span></el-menu-item
        >
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="topbar">
        <div class="topbar-left">
          <el-button text size="small" @click="collapsed = !collapsed"
            ><el-icon :size="18"><Fold /></el-icon
          ></el-button>
        </div>
        <div class="topbar-right">
          <el-dropdown trigger="click">
            <span class="user-badge">
              <el-avatar :size="28" :icon="UserFilled" />
              <span class="user-name">{{ currentUser.username }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>{{
                  currentUser.email || 'ReportFlow AI'
                }}</el-dropdown-item>
                <el-dropdown-item divided @click="doLogout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main><RouterView /></el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  min-height: 100vh;
}
.sidebar {
  background: #fff;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  transition: width 0.2s;
  overflow: hidden;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 56px;
  padding: 0 18px;
  cursor: pointer;
  white-space: nowrap;
}
.logo-icon {
  font-size: 22px;
}
.logo-text {
  font-weight: 700;
  font-size: 16px;
}
.side-menu {
  border-right: none;
  flex: 1;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  height: 48px;
  padding: 0 20px;
}
.topbar-left {
  display: flex;
  align-items: center;
}
.user-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 2px 0;
}
.user-name {
  font-size: 13px;
  font-weight: 500;
}
</style>
