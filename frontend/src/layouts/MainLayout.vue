<template>
  <el-container class="layout">
    <el-aside width="220px" class="sidebar">
      <h1>ReportFlow AI</h1>
      <el-menu router default-active="/">
        <el-menu-item index="/">工作台</el-menu-item>
        <el-menu-item index="/reports/create">创建报表</el-menu-item>
        <el-menu-item index="/reports">历史报表</el-menu-item>
        <el-menu-item index="/templates">模板库</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="topbar">
        <span class="muted">智能报表生成平台</span>
        <el-button type="primary" plain @click="$router.push('/login')">登录占位</el-button>
      </el-header>
      <el-main>
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  min-height: 100vh;
}

.sidebar {
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
}

.sidebar h1 {
  margin: 20px;
  font-size: 18px;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
}
</style>
