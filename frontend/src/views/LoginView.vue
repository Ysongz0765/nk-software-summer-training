<script setup lang="ts">
import { User, Lock } from '@element-plus/icons-vue';
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const formRef = ref(); const loading = ref(false);
const form = reactive({ username: '', password: '', remember: false });
const rules = { username: [{ required: true, message: '请输入用户名', trigger: 'blur' }], password: [{ required: true, message: '请输入密码', trigger: 'blur' }] };

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) return;
  loading.value = true;
  await new Promise(r => setTimeout(r, 600));
  loading.value = false;
  router.push('/');
}
</script>

<template>
  <main class="lp">
    <div class="lb">
      <div class="lbr"><h1>ReportFlow AI</h1><p>智能报表生成平台</p></div>
      <el-card shadow="never" class="lc"><h2 style="margin:0 0 24px;text-align:center">账号登录</h2>
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" size="large" @submit.prevent="handleLogin">
          <el-form-item label="用户名" prop="username"><el-input v-model="form.username" placeholder="请输入用户名" :prefix-icon="User"/></el-form-item>
          <el-form-item label="密码" prop="password"><el-input v-model="form.password" type="password" placeholder="请输入密码" show-password :prefix-icon="Lock"/></el-form-item>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px"><el-checkbox v-model="form.remember">记住登录</el-checkbox><a href="#" style="font-size:13px;color:#409eff">忘记密码？</a></div>
          <el-button type="primary" native-type="submit" :loading="loading" style="width:100%">{{loading?'登录中...':'登 录'}}</el-button>
        </el-form>
      </el-card>
      <p class="muted" style="text-align:center;margin-top:24px;font-size:13px">ReportFlow AI v0.1.0</p>
    </div>
  </main>
</template>

<style scoped>
.lp{display:flex;min-height:100vh;align-items:center;justify-content:center;background:linear-gradient(135deg,#f5f7fb 0%,#e8ecf1 100%)}.lb{width:min(400px,calc(100vw - 32px))}.lbr{text-align:center;margin-bottom:28px}.lbr h1{margin:0;font-size:28px;letter-spacing:1px;background:linear-gradient(135deg,#409eff,#6366f1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}.lbr p{margin:6px 0 0;font-size:14px;color:#667085}.lc{border-radius:12px}
</style>
