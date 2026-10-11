<template>
  <div class="chat-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-logo"><GirlAvatar :size="40" hair="#262626" bow /></div>
        <div>
          <div class="brand-title">小满 · 商品问答</div>
          <div class="brand-sub">RAG 智能知识库</div>
        </div>
      </div>

      <el-button type="primary" class="new-btn" @click="newChat">
        <el-icon><Plus /></el-icon> 新建对话
      </el-button>

      <nav class="menu">
        <div class="menu-item active" @click="goChat">
          <el-icon><Comment /></el-icon><span>我的会话</span>
        </div>

        <div class="menu-item" @click="showHistory = !showHistory">
          <el-icon><Clock /></el-icon><span>历史会话</span>
          <el-icon class="arrow" :class="{ open: showHistory }"><ArrowDown /></el-icon>
        </div>
        <div v-show="showHistory" class="sub-panel conv-list">
          <div
            v-for="c in conversations"
            :key="c.id"
            class="conv-item"
            :class="{ active: c.id === currentId }"
            @click="selectConversation(c)"
          >
            <span class="conv-title">{{ c.title }}</span>
            <el-icon class="conv-del" @click.stop="removeConversation(c)"><Delete /></el-icon>
          </div>
          <el-empty v-if="!conversations.length" description="暂无历史会话" :image-size="50" />
        </div>

        <div class="menu-item" @click="$router.push('/knowledge')">
          <el-icon><FolderOpened /></el-icon><span>知识库管理</span>
        </div>

        <div class="menu-item" @click="showProfile = !showProfile">
          <el-icon><User /></el-icon><span>个人中心</span>
          <el-icon class="arrow" :class="{ open: showProfile }"><ArrowDown /></el-icon>
        </div>
        <div v-show="showProfile" class="sub-panel">
          <div class="profile-user">
            <GirlAvatar :size="28" hair="#8a5a2b" />
            <span class="profile-name">{{ auth.user?.username }}</span>
            <el-tag v-if="auth.isAdmin" size="small" type="danger" effect="light">管理员</el-tag>
          </div>
          <div class="profile-action" @click="pwdDialog = true">
            <el-icon><Key /></el-icon> 修改密码
          </div>
          <div class="profile-action danger" @click="logout">
            <el-icon><SwitchButton /></el-icon> 退出登录
          </div>
        </div>
      </nav>
    </aside>

    <!-- 主区域 -->
    <main class="main">
      <header class="chat-header">
        <div class="header-left">
          <div class="mini-avatar"><GirlAvatar :size="36" hair="#262626" bow /></div>
          <div>
            <div class="header-title">{{ currentTitle || '与小满聊天' }}</div>
            <div class="header-sub">小满会根据知识库认真回答你哦</div>
          </div>
        </div>
      </header>

      <div ref="msgBox" class="messages">
        <!-- 欢迎页 -->
        <div v-if="!messages.length && !streaming" class="welcome">
          <div class="welcome-avatar"><GirlAvatar :size="84" hair="#262626" bow /></div>
          <h2>你好呀，我是小满～</h2>
          <p>我是这家店的智能客服小助手，关于商品的问题都可以问我哦 😊</p>
          <div class="suggestions">
            <span class="suggest-label">你可以这样问我：</span>
            <el-tag
              v-for="q in suggestions"
              :key="q"
              class="suggest-tag"
              effect="plain"
              @click="quickAsk(q)"
            >
              {{ q }}
            </el-tag>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-for="(m, i) in messages" :key="m.id ?? i" class="msg-row" :class="m.role">
          <div v-if="m.role === 'assistant'" class="avatar-wrap">
            <GirlAvatar :size="42" hair="#262626" bow />
            <span class="avatar-name">小满</span>
          </div>

          <div class="msg-body">
            <div class="bubble" :class="m.role">
              <template v-if="m.role === 'assistant'">
                <span v-if="m.streaming && !m.content" class="typing">
                  <i></i><i></i><i></i>
                </span>
                <template v-else>
                  <template v-for="(seg, si) in citationSegments(m.content)" :key="si">
                    <span v-if="seg.citation" class="cite" @click="highlightCitation(m, seg.n)">
                      [{{ seg.n }}]
                    </span>
                    <span v-else>{{ seg.text }}</span>
                  </template>
                  <span v-if="m.streaming" class="cursor">▍</span>
                </template>
              </template>
              <template v-else>{{ m.content }}</template>
            </div>

            <div v-if="m.role === 'assistant' && m.citations && m.citations.length" class="citations">
              <div class="cite-title">
                <el-icon><Notebook /></el-icon>&nbsp;参考来源（{{ m.citations.length }}）
              </div>
              <div
                v-for="src in m.citations"
                :key="src.index"
                class="cite-item"
                :class="{ hl: m._highlight === src.index }"
              >
                <div class="cite-src">
                  📄 【{{ src.index }}】{{ src.source }}<template v-if="src.kb_name"> · {{ src.kb_name }}</template>
                </div>
                <div class="cite-content">{{ src.content }}</div>
              </div>
            </div>

            <div v-if="m.role === 'assistant' && !m.streaming && m.id > 0" class="feedback">
              <el-button text size="small" :type="m.feedback === 'like' ? 'primary' : ''" @click="feedback(m, 'like')">
                👍
              </el-button>
              <el-button text size="small" :type="m.feedback === 'dislike' ? 'primary' : ''" @click="feedback(m, 'dislike')">
                👎
              </el-button>
            </div>
          </div>

          <div v-if="m.role === 'user'" class="avatar-wrap">
            <GirlAvatar :size="42" hair="#8a5a2b" />
            <span class="avatar-name">我</span>
          </div>
        </div>
      </div>

      <div class="input-area">
        <div class="input-box">
          <el-input
            v-model="input"
            type="textarea"
            :rows="2"
            placeholder="输入你想问的商品问题，比如「保温杯多少钱？」"
            resize="none"
            @keydown.ctrl.enter.prevent="send"
          />
          <div class="input-tip">Ctrl + Enter 发送 · 小满会温柔地回复你</div>
        </div>
        <el-button type="primary" class="send-btn" :loading="streaming" @click="send">
          <el-icon v-if="!streaming"><Promotion /></el-icon>&nbsp;发送
        </el-button>
      </div>
    </main>

    <!-- 修改密码 -->
    <el-dialog v-model="pwdDialog" title="修改密码" width="420">
      <el-input v-model="oldPwd" type="password" placeholder="旧密码" show-password :prefix-icon="Lock" style="margin-bottom: 10px" />
      <el-input v-model="newPwd" type="password" placeholder="新密码（至少 6 位）" show-password :prefix-icon="Lock" style="margin-bottom: 10px" />
      <el-input v-model="confirmPwd" type="password" placeholder="确认新密码" show-password :prefix-icon="Lock" />
      <template #footer>
        <el-button @click="pwdDialog = false">取消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="changePwd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import { authApi, chatApi, convApi } from '../api'
import { streamChat } from '../api/stream'
import { useAuthStore } from '../stores/auth'
import GirlAvatar from '../components/GirlAvatar.vue'
import type { Conversation, Message } from '../types'

const auth = useAuthStore()
const conversations = ref<Conversation[]>([])
const currentId = ref<number | null>(null)
const messages = ref<Message[]>([])
const input = ref('')
const streaming = ref(false)
const msgBox = ref<HTMLElement>()

const showHistory = ref(true)
const showProfile = ref(false)

const pwdDialog = ref(false)
const pwdLoading = ref(false)
const oldPwd = ref('')
const newPwd = ref('')
const confirmPwd = ref('')

const suggestions = [
  '保温杯多少钱？',
  '保温杯有哪些颜色？',
  '保温效果怎么样？',
  '支持退换货吗？',
]

const currentTitle = computed(
  () => conversations.value.find((c) => c.id === currentId.value)?.title || ''
)

function citationSegments(content: string) {
  const segs: { text?: string; citation?: boolean; n?: number }[] = []
  const re = /(\[\d+\])/g
  let last = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(content))) {
    if (m.index > last) segs.push({ text: content.slice(last, m.index) })
    segs.push({ citation: true, n: parseInt(m[1].slice(1, -1), 10) })
    last = m.index + m[1].length
  }
  if (last < content.length) segs.push({ text: content.slice(last) })
  return segs
}

function highlightCitation(msg: Message, n: number) {
  msg._highlight = n
  nextTick(() => {
    const el = document.querySelector('.cite-item.hl')
    el?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  })
}

function scrollBottom() {
  nextTick(() => {
    if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
  })
}

function goChat() {
  const ta = document.querySelector<HTMLTextAreaElement>('.input-box textarea')
  ta?.focus()
}

async function loadConversations() {
  conversations.value = await convApi.list()
}

async function newChat() {
  if (streaming.value) return
  const c = await convApi.create()
  conversations.value.unshift(c)
  currentId.value = c.id
  messages.value = []
}

async function selectConversation(c: Conversation) {
  currentId.value = c.id
  messages.value = await convApi.messages(c.id)
  scrollBottom()
}

async function removeConversation(c: Conversation) {
  await convApi.remove(c.id)
  conversations.value = conversations.value.filter((x) => x.id !== c.id)
  if (currentId.value === c.id) {
    currentId.value = null
    messages.value = []
  }
}

function quickAsk(q: string) {
  input.value = q
  send()
}

async function send() {
  const text = input.value.trim()
  if (!text || streaming.value) return
  input.value = ''

  if (!currentId.value) {
    const c = await convApi.create()
    conversations.value.unshift(c)
    currentId.value = c.id
  }

  messages.value.push({
    id: -Date.now(),
    conversation_id: currentId.value!,
    role: 'user',
    content: text,
    citations: null,
  })
  const assistantMsg: Message = {
    id: -Date.now() - 1,
    conversation_id: currentId.value!,
    role: 'assistant',
    content: '',
    citations: null,
    streaming: true,
  }
  messages.value.push(assistantMsg)
  streaming.value = true
  scrollBottom()

  await streamChat(auth.token, currentId.value, text, {
    onDelta: (t) => {
      assistantMsg.content += t
      scrollBottom()
    },
    onSources: (sources) => {
      assistantMsg.citations = sources
    },
    onError: (msg) => {
      assistantMsg.content += (assistantMsg.content ? '\n\n' : '') + '⚠️ ' + msg
    },
    onDone: async () => {
      streaming.value = false
      await loadConversations()
      if (currentId.value) messages.value = await convApi.messages(currentId.value)
      scrollBottom()
    },
  })
}

async function feedback(m: Message, val: string) {
  try {
    await chatApi.feedback(m.id, val)
    m.feedback = val
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function changePwd() {
  if (newPwd.value !== confirmPwd.value) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  pwdLoading.value = true
  try {
    await authApi.changePassword({ old_password: oldPwd.value, new_password: newPwd.value })
    ElMessage.success('密码修改成功')
    pwdDialog.value = false
    oldPwd.value = newPwd.value = confirmPwd.value = ''
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '修改失败')
  } finally {
    pwdLoading.value = false
  }
}

function logout() {
  auth.logout()
  location.hash = '#/login'
}

onMounted(async () => {
  await loadConversations()
  if (conversations.value.length) await selectConversation(conversations.value[0])
})
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100%;
}

/* 侧边栏 */
.sidebar {
  width: 264px;
  background: #fff;
  border-right: 1px solid #eef0f4;
  display: flex;
  flex-direction: column;
  padding: 18px 14px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.brand-logo {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: linear-gradient(135deg, #ffd6e8, #c9b6ff);
  display: flex;
  align-items: center;
  justify-content: center;
}
.brand-title {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
}
.brand-sub {
  font-size: 12px;
  color: #a0a4ab;
}
.new-btn {
  width: 100%;
  margin-bottom: 12px;
  border-radius: 10px;
  font-weight: 600;
}

/* 菜单 */
.menu {
  flex: 1;
  overflow-y: auto;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 11px 12px;
  border-radius: 10px;
  cursor: pointer;
  color: #4b5563;
  font-size: 14px;
  transition: background 0.15s;
}
.menu-item:hover {
  background: #f5f6fa;
}
.menu-item.active {
  background: linear-gradient(90deg, #eef0ff, #f7ecff);
  color: #6c5ce7;
  font-weight: 600;
}
.menu-item .arrow {
  margin-left: auto;
  color: #c0c4cc;
  font-size: 12px;
  transition: transform 0.2s;
}
.menu-item .arrow.open {
  transform: rotate(180deg);
}

.sub-panel {
  margin: 2px 0 8px 20px;
}
.conv-list {
  max-height: 220px;
  overflow-y: auto;
}
.conv-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 2px;
  color: #4b5563;
  font-size: 13px;
}
.conv-item:hover {
  background: #f5f6fa;
}
.conv-item.active {
  background: #eef0ff;
  color: #6c5ce7;
}
.conv-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conv-del {
  visibility: hidden;
  color: #c0c4cc;
}
.conv-item:hover .conv-del {
  visibility: visible;
}
.conv-del:hover {
  color: #f56c6c;
}

.profile-user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
}
.profile-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.profile-action {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #4b5563;
}
.profile-action:hover {
  background: #f5f6fa;
}
.profile-action.danger:hover {
  background: #fef0f0;
  color: #f56c6c;
}

/* 主区域 */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: linear-gradient(180deg, #fafbff 0%, #f5f3ff 100%);
}
.chat-header {
  height: 62px;
  padding: 0 26px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid #eef0f4;
  display: flex;
  align-items: center;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.mini-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ffd6e8, #c9b6ff);
  display: flex;
  align-items: center;
  justify-content: center;
}
.header-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.header-sub {
  font-size: 12px;
  color: #a0a4ab;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 26px 28px;
}

/* 欢迎页 */
.welcome {
  max-width: 560px;
  margin: 60px auto 0;
  text-align: center;
}
.welcome-avatar {
  width: 88px;
  height: 88px;
  border-radius: 28px;
  background: linear-gradient(135deg, #ffd6e8, #c9b6ff);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 18px;
  box-shadow: 0 8px 24px rgba(201, 182, 255, 0.4);
}
.welcome h2 {
  color: #303133;
  margin-bottom: 8px;
}
.welcome p {
  color: #909399;
  font-size: 14px;
}
.suggestions {
  margin-top: 22px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}
.suggest-label {
  width: 100%;
  font-size: 13px;
  color: #b0b4bb;
}
.suggest-tag {
  cursor: pointer;
  padding: 6px 14px;
  border-radius: 16px;
  transition: all 0.15s;
}
.suggest-tag:hover {
  color: #6c5ce7;
  border-color: #6c5ce7;
}

/* 消息 */
.msg-row {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 12px;
  margin-bottom: 22px;
}
.msg-row.user {
  justify-content: flex-end;
}
.avatar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}
.avatar-wrap :deep(svg) {
  filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.12));
}
.avatar-name {
  font-size: 11px;
  color: #a0a4ab;
}
.msg-body {
  max-width: 70%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.msg-row.user .msg-body {
  align-items: flex-end;
}
.bubble {
  padding: 12px 16px;
  border-radius: 16px;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
}
.bubble.user {
  background: linear-gradient(135deg, #6c5ce7, #8e7cf3);
  color: #fff;
  border-bottom-right-radius: 4px;
  box-shadow: 0 4px 14px rgba(108, 92, 231, 0.3);
}
.bubble.assistant {
  background: #fff;
  color: #303133;
  border: 1px solid #eef0f4;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

/* 打字动画 */
.typing {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  padding: 4px 0;
}
.typing i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #c9b6ff;
  animation: blink 1.2s infinite;
}
.typing i:nth-child(2) {
  animation-delay: 0.2s;
}
.typing i:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes blink {
  0%,
  80%,
  100% {
    opacity: 0.25;
  }
  40% {
    opacity: 1;
  }
}
.cursor {
  animation: blink 1s infinite;
}
.cite {
  color: #6c5ce7;
  cursor: pointer;
  font-weight: 600;
  padding: 0 1px;
}
.cite:hover {
  text-decoration: underline;
}

/* 引用 */
.citations {
  margin-top: 8px;
  width: 100%;
}
.cite-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
}
.cite-item {
  background: #fff;
  border: 1px solid #eef0f4;
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 6px;
  transition: all 0.15s;
}
.cite-item.hl {
  border-color: #6c5ce7;
  box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.15);
}
.cite-src {
  font-size: 12px;
  color: #6c5ce7;
  font-weight: 600;
  margin-bottom: 4px;
}
.cite-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  max-height: 96px;
  overflow-y: auto;
}
.feedback {
  margin-top: 4px;
}

/* 输入区 */
.input-area {
  display: flex;
  gap: 12px;
  padding: 16px 26px 18px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  border-top: 1px solid #eef0f4;
  align-items: flex-end;
}
.input-box {
  flex: 1;
}
.input-box :deep(.el-textarea__inner) {
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.6;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
}
.input-tip {
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 4px;
  padding-left: 4px;
}
.send-btn {
  height: 48px;
  width: 100px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 14px;
}
</style>
