export interface StreamHandlers {
  onDelta: (text: string) => void
  onSources: (sources: any[]) => void
  onError: (message: string) => void
  onDone: () => void
}

interface SSEMessage {
  type: 'delta' | 'sources' | 'done' | 'error'
  content?: string
  sources?: any[]
  message?: string
}

export async function streamChat(
  token: string,
  conversationId: number | null,
  message: string,
  handlers: StreamHandlers
): Promise<void> {
  let resp: Response
  try {
    resp = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ conversation_id: conversationId, message }),
    })
  } catch (e: any) {
    handlers.onError('网络错误，请检查后端服务是否启动')
    handlers.onDone()
    return
  }

  if (!resp.ok || !resp.body) {
    let detail = `请求失败 (${resp.status})`
    try {
      const j = await resp.json()
      if (j.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
    } catch {
      /* ignore */
    }
    handlers.onError(detail)
    handlers.onDone()
    return
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  const dispatch = (payload: SSEMessage) => {
    if (payload.type === 'delta' && payload.content) handlers.onDelta(payload.content)
    else if (payload.type === 'sources') handlers.onSources(payload.sources || [])
    else if (payload.type === 'error') handlers.onError(payload.message || '生成失败')
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let idx: number
      while ((idx = buffer.indexOf('\n\n')) >= 0) {
        const chunk = buffer.slice(0, idx)
        buffer = buffer.slice(idx + 2)
        for (const line of chunk.split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              dispatch(JSON.parse(line.slice(6)))
            } catch {
              /* partial line, skip */
            }
          }
        }
      }
    }
  } catch {
    handlers.onError('连接中断')
  } finally {
    handlers.onDone()
  }
}
