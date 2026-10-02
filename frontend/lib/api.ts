const getApiBase = (): string => {
  let url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    if (typeof window !== 'undefined') {
      return `${window.location.origin}/api`;
    }
    return 'http://localhost:8000/api';
  }
  if (url.startsWith('/')) {
    if (typeof window !== 'undefined') {
      const cleanPath = url.endsWith('/api') ? url : `${url.replace(/\/+$/, '')}/api`;
      return `${window.location.origin}${cleanPath}`;
    }
    return `http://localhost:8000${url}`;
  }
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = `https://${url}`;
  }
  url = url.replace(/\/+$/, '');
  if (!url.endsWith('/api')) {
    url = `${url}/api`;
  }
  return url;
};

const API_BASE = getApiBase();


export interface DocumentItem {
  id: string;
  name: string;
  original_filename: string;
  file_size: number;
  page_count: number;
  status: 'UPLOADING' | 'PROCESSING' | 'READY' | 'FAILED';
  processing_error?: string;
  chunk_count?: number;
  chunks_count?: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  content: string;
  page_number: number;
  chunk_index: number;
  section_title?: string;
  metadata?: any;
  created_at?: string;
}

export interface ConversationItem {
  id: string;
  customer_id: string;
  customer_name?: string;
  customer_phone?: string;
  status: 'ACTIVE' | 'HUMAN_HANDOFF' | 'CLOSED' | 'ORDER_CONFIRMED' | string;
  assigned_agent?: string;
  ai_enabled: boolean;
  last_message?: string;
  last_message_at?: string;
  created_at: string;
  updated_at: string;
}

export interface MessageItem {
  id: string;
  conversation_id: string;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM' | 'HUMAN';
  content: string;
  message_type: string;
  whatsapp_message_id?: string;
  metadata?: any;
  created_at: string;
}

export interface CustomerItem {
  id: string;
  whatsapp_number: string;
  name?: string;
  email?: string;
  created_at: string;
  total_messages?: number;
}

export interface AnalyticsSummary {
  total_customers: number;
  total_conversations: number;
  total_messages: number;
  active_conversations: number;
  ai_resolved_conversations: number;
  human_handoffs: number;
  ready_documents: number;
  total_knowledge_chunks: number;
  average_latency_ms: number;
  retrieval_success_rate: number;
  daily_messages: { date: string; incoming: number; outgoing: number }[];
}

export interface SystemSettings {
  id: string;
  llm_provider: string;
  llm_model: string;
  embedding_provider: string;
  embedding_model: string;
  temperature: number;
  top_k: number;
  similarity_threshold: number;
  system_prompt: string;
  bot_enabled?: boolean;
}

const cacheMap = new Map<string, { data: any; expiry: number }>();

async function cachedFetch<T>(url: string, ttlMs = 8000): Promise<T> {
  const now = Date.now();
  const cached = cacheMap.get(url);
  if (cached && cached.expiry > now) {
    return cached.data as T;
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP error ${res.status} for ${url}`);
  const data = await res.json();
  cacheMap.set(url, { data, expiry: now + ttlMs });
  return data as T;
}

export function invalidateApiCache(prefix?: string) {
  if (!prefix) {
    cacheMap.clear();
  } else {
    cacheMap.forEach((_, key) => {
      if (key.includes(prefix)) {
        cacheMap.delete(key);
      }
    });
  }
}

export const api = {
  // Documents
  async listDocuments(): Promise<DocumentItem[]> {
    return cachedFetch<DocumentItem[]>(`${API_BASE}/documents`, 10000);
  },

  async uploadDocument(file: File, name?: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (name) formData.append('name', name);
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('Failed to upload document');
    invalidateApiCache('documents');
    invalidateApiCache('analytics');
    return res.json();
  },

  async deleteDocument(id: string): Promise<any> {
    const res = await fetch(`${API_BASE}/documents/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete document');
    invalidateApiCache('documents');
    invalidateApiCache('analytics');
    return res.json();
  },

  async reindexDocument(id: string): Promise<any> {
    const res = await fetch(`${API_BASE}/documents/${id}/reindex`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reindex document');
    invalidateApiCache('documents');
    return res.json();
  },

  async getDocumentChunks(id: string): Promise<DocumentChunk[]> {
    return cachedFetch<DocumentChunk[]>(`${API_BASE}/documents/${id}/chunks`, 15000);
  },

  // Conversations
  async listConversations(status?: string): Promise<ConversationItem[]> {
    const url = status ? `${API_BASE}/conversations?status=${status}` : `${API_BASE}/conversations`;
    return cachedFetch<ConversationItem[]>(url, 5000);
  },

  async getMessages(conversationId: string): Promise<MessageItem[]> {
    return cachedFetch<MessageItem[]>(`${API_BASE}/conversations/${conversationId}/messages`, 2500);
  },

  async sendAgentMessage(conversationId: string, content: string, role = 'HUMAN'): Promise<any> {
    const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, role }),
    });
    if (!res.ok) throw new Error('Failed to send message');
    invalidateApiCache('conversations');
    return res.json();
  },

  async updateConversation(conversationId: string, update: { status?: string; ai_enabled?: boolean }): Promise<any> {
    const res = await fetch(`${API_BASE}/conversations/${conversationId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(update),
    });
    if (!res.ok) throw new Error('Failed to update conversation');
    invalidateApiCache('conversations');
    invalidateApiCache('analytics');
    return res.json();
  },

  // Customers
  async listCustomers(): Promise<CustomerItem[]> {
    return cachedFetch<CustomerItem[]>(`${API_BASE}/customers`, 10000);
  },

  // Settings & Playground
  async getSettings(): Promise<SystemSettings> {
    return cachedFetch<SystemSettings>(`${API_BASE}/settings`, 15000);
  },

  async updateSettings(settings: Partial<SystemSettings>): Promise<SystemSettings> {
    const res = await fetch(`${API_BASE}/settings`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!res.ok) throw new Error('Failed to update settings');
    invalidateApiCache('settings');
    return res.json();
  },

  async toggleBot(bot_enabled?: boolean): Promise<{ bot_enabled: boolean; status: string; message: string }> {
    const res = await fetch(`${API_BASE}/settings/toggle-bot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bot_enabled !== undefined ? { bot_enabled } : {}),
    });
    if (!res.ok) throw new Error('Failed to toggle bot status');
    invalidateApiCache('settings');
    return res.json();
  },

  async resetAllData(): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/settings/reset-all-data`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error('Failed to reset system data');
    invalidateApiCache();
    return res.json();
  },

  async testPlayground(query: string, top_k?: number, similarity_threshold?: number): Promise<any> {
    const res = await fetch(`${API_BASE}/settings/test-playground`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k, similarity_threshold }),
    });
    if (!res.ok) throw new Error('Failed to test query');
    return res.json();
  },

  // Analytics
  async getAnalytics(): Promise<AnalyticsSummary> {
    return cachedFetch<AnalyticsSummary>(`${API_BASE}/analytics/summary`, 10000);
  },

  // Health
  async getHealth(): Promise<any> {
    return cachedFetch<any>(`${API_BASE}/health`, 10000);
  },

  // Authentication & Admin Credentials
  async login(username: string, password: string): Promise<{ success: boolean; access_token: string; user: any }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Invalid email/username or password');
    }
    const data = await res.json();
    if (typeof window !== 'undefined') {
      localStorage.setItem('dhoodh_auth_token', data.access_token);
      localStorage.setItem('dhoodh_auth_user', JSON.stringify(data.user));
    }
    return data;
  },

  async getProfile(): Promise<any> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('dhoodh_auth_token') : null;
    const res = await fetch(`${API_BASE}/auth/profile`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error('Failed to fetch profile');
    return res.json();
  },

  async changeCredentials(current_password: string, new_email?: string, new_password?: string): Promise<{ success: boolean; message: string; email?: string }> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('dhoodh_auth_token') : null;
    const res = await fetch(`${API_BASE}/auth/change-credentials`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify({ current_password, new_email, new_password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to update credentials' }));
      throw new Error(err.detail || 'Failed to update credentials');
    }
    const data = await res.json();
    if (typeof window !== 'undefined' && data.email) {
      try {
        const u = JSON.parse(localStorage.getItem('dhoodh_auth_user') || '{}');
        u.email = data.email;
        localStorage.setItem('dhoodh_auth_user', JSON.stringify(u));
      } catch (e) {}
    }
    return data;
  },

  logout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('dhoodh_auth_token');
      localStorage.removeItem('dhoodh_auth_user');
      window.location.href = '/login';
    }
  },

  getAuthUser(): any {
    if (typeof window !== 'undefined') {
      try {
        return JSON.parse(localStorage.getItem('dhoodh_auth_user') || 'null');
      } catch (e) {
        return null;
      }
    }
    return null;
  },

  isAuthenticated(): boolean {
    if (typeof window !== 'undefined') {
      return Boolean(localStorage.getItem('dhoodh_auth_token'));
    }
    return false;
  },

  async getWhatsAppStatus(): Promise<{ connected: boolean; phone: string | null; status?: string }> {
    if (typeof window !== 'undefined') {
      try {
        const gatewayBase = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
          ? 'http://localhost:3001'
          : `${window.location.origin}/gateway`;
        const gwRes = await fetch(`${gatewayBase}/api/status`, { cache: 'no-store' });
        if (gwRes.ok) {
          const gwData = await gwRes.json();
          if (gwData.connected && gwData.phone) {
            return {
              connected: true,
              phone: String(gwData.phone).replace(/[^0-9]/g, ''),
              status: gwData.status
            };
          } else {
            return {
              connected: false,
              phone: null,
              status: gwData.status || 'disconnected'
            };
          }
        }
      } catch (gwErr) {}
    }

    try {
      const res = await fetch(`${API_BASE}/whatsapp/connect/status`, { cache: 'no-store' });
      if (res.ok) {
        const data = await res.json();
        return {
          connected: Boolean(data.connected && data.phone),
          phone: data.phone ? String(data.phone).replace(/[^0-9]/g, '') : null,
          status: data.status,
        };
      }
    } catch (e) {}

    return { connected: false, phone: null, status: 'offline' };
  }
};
