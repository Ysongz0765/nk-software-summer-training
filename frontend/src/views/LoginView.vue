<script setup lang="ts">
import { Lock, Message, User } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { login, register } from '@/api/reportflow';
import type { AuthResponse } from '@/types/reportflow';

const route = useRoute();
const router = useRouter();
const formRef = ref<FormInstance>();
const mode = ref<'login' | 'register'>('login');
const loading = ref(false);
const form = reactive({
  username: '',
  email: '',
  password: '',
});

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  email: [
    {
      required: true,
      message: '请输入邮箱',
      trigger: 'blur',
    },
  ],
};

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) return;

  loading.value = true;
  try {
    const response =
      mode.value === 'login'
        ? await login({ username: form.username, password: form.password })
        : await register({
            username: form.username,
            email: form.email,
            password: form.password,
          });

    if (response.code !== 0 || !response.data) {
      ElMessage.error(response.message || '操作失败');
      return;
    }

    saveAuth(response.data);
    ElMessage.success(mode.value === 'login' ? '登录成功' : '注册成功');
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/';
    await router.replace(redirect);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '请求失败');
  } finally {
    loading.value = false;
  }
}

function saveAuth(auth: AuthResponse) {
  localStorage.setItem('reportflow_token', auth.access_token);
  localStorage.setItem('reportflow_user', JSON.stringify(auth.user));
}

function switchMode(nextMode: 'login' | 'register') {
  mode.value = nextMode;
  formRef.value?.clearValidate();
}

function handleModeChange(value: string | number | boolean) {
  switchMode(value === 'register' ? 'register' : 'login');
}
</script>

<template>
  <main class="login-page">
    <section class="login-box">
      <div class="brand">
        <h1>ReportFlow AI</h1>
        <p>智能日报、周报生成平台</p>
      </div>

      <el-card shadow="never" class="login-card">
        <el-segmented
          :model-value="mode"
          :options="[
            { label: '登录', value: 'login' },
            { label: '注册', value: 'register' },
          ]"
          style="width: 100%; margin-bottom: 22px"
          @change="handleModeChange"
        />

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          size="large"
          @submit.prevent="handleSubmit"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item v-if="mode === 'register'" label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="请输入邮箱" :prefix-icon="Message" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              show-password
              :prefix-icon="Lock"
            />
          </el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">
            {{ loading ? '处理中...' : mode === 'login' ? '登录' : '注册并登录' }}
          </el-button>
        </el-form>
      </el-card>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  display: flex;
  min-height: 100vh;
  align-items: center;
  justify-content: center;
  background: #f5f7fb;
}

.login-box {
  width: min(420px, calc(100vw - 32px));
}

.brand {
  margin-bottom: 28px;
  text-align: center;
}

.brand h1 {
  margin: 0;
  color: #1f2937;
  font-size: 30px;
}

.brand p {
  margin: 8px 0 0;
  color: #667085;
}

.login-card {
  border-radius: 10px;
}
</style>
