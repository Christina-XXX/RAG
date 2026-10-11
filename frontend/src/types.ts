export interface User {
  id: number
  username: string
  is_admin: boolean
  created_at: string
}

export interface Conversation {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export interface Citation {
  index?: number
  content: string
  source: string
  score: number
  kb_id?: number
  kb_name?: string
  doc_id?: number
}

export interface Message {
  id: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[] | null
  latency_ms?: number
  created_at?: string
  feedback?: string | null
  streaming?: boolean
  _highlight?: number
}

export interface KnowledgeBase {
  id: number
  name: string
  description: string
  doc_count: number
  chunk_count: number
  created_at: string
  docs?: Doc[]
}

export interface Doc {
  id: number
  kb_id: number
  filename: string
  file_type: string
  status: string
  chunk_count: number
  size: number
  created_at: string
}
