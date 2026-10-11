<template>
  <div class="kb-layout">
    <header class="topbar">
      <el-button text class="back-btn" @click="$router.push('/chat')">
        <el-icon><Back /></el-icon>&nbsp;返回问答
      </el-button>
      <div class="topbar-title">
        <el-icon class="title-icon"><FolderOpened /></el-icon>
        <h2>知识库管理</h2>
      </div>
      <el-button type="primary" class="new-kb-btn" @click="createDialog = true">
        <el-icon><Plus /></el-icon>&nbsp;新建知识库
      </el-button>
    </header>

    <div class="kb-grid">
      <el-card v-for="kb in kbs" :key="kb.id" class="kb-card" shadow="hover">
        <template #header>
          <div class="kb-head">
            <div class="kb-title">
              <div class="kb-icon">📚</div>
              <span class="kb-name">{{ kb.name }}</span>
            </div>
            <el-popconfirm title="确认删除该知识库？" @confirm="removeKb(kb)">
              <template #reference>
                <el-button type="danger" text size="small">
                  <el-icon><Delete /></el-icon>&nbsp;删除
                </el-button>
              </template>
            </el-popconfirm>
          </div>
        </template>

        <p class="kb-desc">{{ kb.description || '（暂无描述）' }}</p>
        <div class="kb-meta">
          <el-tag size="small" effect="plain" type="info">
            <el-icon><Document /></el-icon>&nbsp;{{ kb.doc_count }} 篇文档
          </el-tag>
          <el-tag size="small" effect="plain" type="info">
            <el-icon><Files /></el-icon>&nbsp;{{ kb.chunk_count }} 个片段
          </el-tag>
        </div>

        <el-upload
          drag
          class="upload-area"
          :show-file-list="false"
          :http-request="(opt: any) => upload(kb, opt)"
          accept=".pdf,.docx,.txt,.md,.csv,.xlsx"
          :disabled="uploading"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
          <template #tip>
            <div class="upload-tip">支持 PDF / Word / TXT / Markdown / CSV / Excel</div>
          </template>
        </el-upload>

        <el-divider />

        <div class="doc-list">
          <div class="doc-section-title">
            <el-icon><Collection /></el-icon>&nbsp;文档列表
          </div>
          <div v-for="doc in kb.docs || []" :key="doc.id" class="doc-item">
            <el-icon class="doc-icon"><Document /></el-icon>
            <span class="doc-name" :title="doc.filename">{{ doc.filename }}</span>
            <el-tag size="small" :type="statusType(doc.status)">{{ statusText(doc.status) }}</el-tag>
            <el-popconfirm title="确认删除该文档？" @confirm="removeDoc(kb, doc)">
              <template #reference>
                <el-button type="danger" text size="small">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-popconfirm>
          </div>
          <el-empty v-if="!(kb.docs && kb.docs.length)" description="还没有文档，快上传一份吧" :image-size="56" />
        </div>
      </el-card>

      <el-empty v-if="!kbs.length" description="还没有知识库，点击右上角新建" />
    </div>

    <el-dialog v-model="createDialog" title="新建知识库" width="440">
      <el-input v-model="newName" placeholder="知识库名称" size="large" :prefix-icon="FolderOpened" />
      <el-input v-model="newDesc" placeholder="描述（可选）" size="large" style="margin-top: 12px" :prefix-icon="EditPen" />
      <template #footer>
        <el-button @click="createDialog = false">取消</el-button>
        <el-button type="primary" @click="createKb">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Back,
  Collection,
  Delete,
  Document,
  EditPen,
  Files,
  FolderOpened,
  Plus,
  UploadFilled,
} from '@element-plus/icons-vue'
import { kbApi } from '../api'
import type { Doc, KnowledgeBase } from '../types'

const kbs = ref<KnowledgeBase[]>([])
const createDialog = ref(false)
const newName = ref('')
const newDesc = ref('')
const uploading = ref(false)

function statusType(status: string) {
  return status === 'done' ? 'success' : status === 'failed' ? 'danger' : 'warning'
}
function statusText(status: string) {
  return { pending: '待处理', processing: '处理中', done: '完成', failed: '失败' }[status] || status
}

async function load() {
  try {
    kbs.value = await kbApi.list()
    for (const kb of kbs.value) {
      kb.docs = await kbApi.docs(kb.id)
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '加载知识库失败，请检查后端服务是否启动')
  }
}

async function createKb() {
  if (!newName.value.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  try {
    await kbApi.create({ name: newName.value.trim(), description: newDesc.value.trim() })
    ElMessage.success('知识库已创建')
    createDialog.value = false
    newName.value = newDesc.value = ''
    await load()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '创建失败，请检查后端服务是否启动')
  }
}

async function removeKb(kb: KnowledgeBase) {
  await kbApi.remove(kb.id)
  ElMessage.success('知识库已删除')
  await load()
}

async function upload(kb: KnowledgeBase, opt: any) {
  uploading.value = true
  try {
    await kbApi.upload(kb.id, opt.file)
    ElMessage.success('上传成功，正在处理…')
    await load()
    pollStatus(kb.id)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

function pollStatus(kbId: number) {
  const timer = setInterval(async () => {
    const docs: Doc[] = await kbApi.docs(kbId)
    const kb = kbs.value.find((k) => k.id === kbId)
    if (kb) kb.docs = docs
    if (!docs.some((d) => d.status === 'processing' || d.status === 'pending')) {
      clearInterval(timer)
      await load()
    }
  }, 2000)
}

async function removeDoc(kb: KnowledgeBase, doc: Doc) {
  await kbApi.removeDoc(kb.id, doc.id)
  ElMessage.success('文档已删除')
  await load()
}

onMounted(load)
</script>

<style scoped>
.kb-layout {
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
.new-kb-btn {
  border-radius: 10px;
  font-weight: 600;
}
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 18px;
}
.kb-card {
  border-radius: 16px;
  border: 1px solid #eef0f4;
}
.kb-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.kb-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.kb-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, #ffd6e8, #c9b6ff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
}
.kb-name {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}
.kb-desc {
  color: #606266;
  font-size: 13px;
  margin-bottom: 10px;
  min-height: 18px;
}
.kb-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}
.kb-meta :deep(.el-tag) {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}
.upload-area {
  margin-bottom: 4px;
}
.upload-area :deep(.el-upload-dragger) {
  border-radius: 12px;
  border: 1.5px dashed #d0c8f0;
  padding: 20px 0;
  transition: all 0.2s;
}
.upload-area :deep(.el-upload-dragger:hover) {
  border-color: #6c5ce7;
  background: #faf8ff;
}
.upload-icon {
  font-size: 34px;
  color: #a78bfa;
  margin-bottom: 6px;
}
.upload-tip {
  color: #c0c4cc;
  font-size: 12px;
  margin-top: 6px;
}
.doc-list {
  max-height: 240px;
  overflow-y: auto;
}
.doc-section-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}
.doc-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 0;
  border-bottom: 1px dashed #f0f0f0;
}
.doc-icon {
  color: #a78bfa;
  flex-shrink: 0;
}
.doc-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: #4b5563;
}
</style>
