<template>
  <div class="admin-layout">
    <header class="topbar">
      <el-button text class="back-btn" @click="$router.push('/chat')">
        <el-icon><Back /></el-icon>&nbsp;返回问答
      </el-button>
      <div class="topbar-title">
        <el-icon class="title-icon"><DataAnalysis /></el-icon>
        <h2>管理后台</h2>
      </div>
    </header>

    <div class="stat-grid">
      <el-card v-for="s in statCards" :key="s.label" class="stat-card" shadow="hover">
        <div class="stat-icon" :style="{ background: s.bg }">
          <el-icon :style="{ color: s.color }"><component :is="s.icon" /></el-icon>
        </div>
        <div class="stat-num" :style="{ color: s.color }">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </el-card>
    </div>

    <el-card style="margin-top: 18px" shadow="hover">
      <template #header>
        <div class="section-title">
          <el-icon><User /></el-icon>&nbsp;用户列表
        </div>
      </template>
      <el-table :data="users" style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column label="角色" width="150">
          <template #default="{ row }">
            <el-tag :type="row.is_admin ? 'danger' : 'info'" effect="light">
              {{ row.is_admin ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  Back,
  ChatDotRound,
  Collection,
  DataAnalysis,
  Document,
  Folder,
  Message,
  User,
} from '@element-plus/icons-vue'
import { adminApi } from '../api'
import type { User as UserType } from '../types'

const stats = ref<any>({})
const users = ref<UserType[]>([])

const statCards = computed(() => [
  { label: '用户数', value: stats.value.user_count ?? 0, icon: User, color: '#6c5ce7', bg: '#f0ebff' },
  { label: '会话数', value: stats.value.conversation_count ?? 0, icon: ChatDotRound, color: '#00b894', bg: '#e6fbf4' },
  { label: '消息数', value: stats.value.message_count ?? 0, icon: Message, color: '#0984e3', bg: '#e8f4fd' },
  { label: '知识库', value: stats.value.kb_count ?? 0, icon: Folder, color: '#e17055', bg: '#fdf0ec' },
  { label: '文档数', value: stats.value.doc_count ?? 0, icon: Document, color: '#e67e22', bg: '#fdf4e8' },
  { label: '片段数', value: stats.value.chunk_count ?? 0, icon: Collection, color: '#00bcd4', bg: '#e6f9fc' },
])

onMounted(async () => {
  stats.value = await adminApi.stats()
  users.value = await adminApi.users()
})
</script>

<style scoped>
.admin-layout {
  height: 100%;
  overflow-y: auto;
  padding: 0 28px 28px;
  background: linear-gradient(180deg, #fafbff 0%, #f5f3ff 100%);
}
.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 0;
}
.back-btn {
  color: #606266;
}
.topbar-title {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}
.title-icon {
  font-size: 22px;
  color: #6c5ce7;
}
.topbar-title h2 {
  font-size: 18px;
  color: #303133;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 16px;
}
.stat-card {
  text-align: center;
  border-radius: 16px;
  border: 1px solid #eef0f4;
}
.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  margin: 0 auto 10px;
}
.stat-num {
  font-size: 28px;
  font-weight: 700;
}
.stat-label {
  color: #909399;
  font-size: 13px;
  margin-top: 4px;
}
.section-title {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: #303133;
}
</style>
