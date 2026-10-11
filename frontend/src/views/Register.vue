<template>
  <div class="auth-wrap">
    <el-card class="auth-card">
      <div class="mascot">✨</div>
      <h2 class="title">创建账号</h2>
      <p class="sub">注册后即可和小满聊天啦</p>
      <el-form @submit.prevent="onSubmit">
        <el-form-item>
          <el-input v-model="username" placeholder="用户名（2~32 字符）" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="密码（至少 6 位）"
            size="large"
            show-password
            :prefix-icon="Lock"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="confirm"
            type="password"
            placeholder="确认密码"
            size="large"
            show-password
            :prefix-icon="Lock"
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="submit-btn"
          :loading="loading"
          @click="onSubmit"
        >
          注册
        </el-button>
      </el-form>
      <div class="foot">
        已有账号？<router-link to="/login">去登录</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { authApi } from '../api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const confirm = ref('')
const loading = ref(false)

async function onSubmit() {
  if (password.value !== confirm.value) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    const data = await authApi.register({ username: username.value, password: password.value })
    auth.setAuth(data.access_token, data.user)
    ElMessage.success('注册成功，欢迎加入～')
    router.push('/chat')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-wrap {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 50%, #a6c1ee 100%);
}
.auth-card {
  width: 410px;
  padding: 18px 10px;
  border-radius: 20px;
  border: none;
  box-shadow: 0 20px 60px rgba(80, 60, 160, 0.25);
}
.mascot {
  width: 76px;
  height: 76px;
  border-radius: 24px;
  background: linear-gradient(135deg, #ffd6e8, #c9b6ff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 42px;
  margin: 0 auto 14px;
  box-shadow: 0 8px 24px rgba(201, 182, 255, 0.4);
}
.title {
  text-align: center;
  margin-bottom: 6px;
  color: #303133;
}
.sub {
  text-align: center;
  color: #a0a4ab;
  font-size: 13px;
  margin-bottom: 24px;
}
.submit-btn {
  width: 100%;
  border-radius: 10px;
  font-weight: 600;
}
.foot {
  margin-top: 16px;
  text-align: center;
  color: #909399;
  font-size: 13px;
}
</style>
