<template>
  <main class="login-page">
    <el-card class="login-card" shadow="never">
      <h1>ReportFlow AI</h1>
      <p class="muted">认证接口已预留，当前页面为登录占位。</p>
      <el-button type="primary" @click="$router.push('/')">进入工作台</el-button>
    </el-card>
  </main>
</template>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  place-items: center;
  background: #f5f7fb;
}

.login-card {
  width: min(420px, calc(100vw - 32px));
}
</style>
