/**
 * API client for the Monzo Analysis backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
  status: number;
  data?: unknown;

  constructor(status: number, message: string, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Make an API request with proper error handling.
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new ApiError(
      response.status,
      data?.detail || response.statusText,
      data
    );
  }

  return response.json();
}

// API Types
export interface AuthStatus {
  authenticated: boolean;
  user_id?: string;
  expires_at?: string;
}

export interface Account {
  id: string;
  monzo_id: string;
  account_type: string;
  description?: string;
}

export interface Transaction {
  id: string;
  monzo_id: string;
  amount: number;
  merchant_name?: string;
  monzo_category?: string;
  custom_category?: string;
  created_at: string;
  settled_at?: string;
  notes?: string;
}

export interface Budget {
  id: string;
  category: string;
  amount: number;
  period: 'monthly' | 'weekly';
  start_day: number;
}

export interface BudgetStatus {
  budget_id: string;
  category: string;
  amount: number;
  spent: number;
  remaining: number;
  percentage: number;
  status: 'under' | 'warning' | 'over';
  period_start: string;
  period_end: string;
}

export interface CategoryRule {
  id: string;
  name: string;
  conditions: Record<string, unknown>;
  target_category: string;
  priority: number;
  enabled: boolean;
}

export interface SyncStatus {
  last_sync?: string;
  transactions_synced?: number;
  status: 'idle' | 'running' | 'success' | 'failed';
  error?: string;
}

// API Methods

export const api = {
  // Auth
  getAuthStatus: () => apiRequest<AuthStatus>('/api/v1/auth/status'),
  getLoginUrl: () => apiRequest<{ url: string }>('/api/v1/auth/login'),

  // Transactions
  getTransactions: (params?: {
    limit?: number;
    offset?: number;
    category?: string;
    since?: string;
    until?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    if (params?.category) searchParams.set('category', params.category);
    if (params?.since) searchParams.set('since', params.since);
    if (params?.until) searchParams.set('until', params.until);

    const query = searchParams.toString();
    return apiRequest<{ items: Transaction[]; total: number }>(
      `/api/v1/transactions${query ? `?${query}` : ''}`
    );
  },

  updateTransaction: (id: string, data: { custom_category?: string; notes?: string }) =>
    apiRequest<Transaction>(`/api/v1/transactions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  // Budgets
  getBudgets: () => apiRequest<Budget[]>('/api/v1/budgets'),
  getBudgetStatuses: () => apiRequest<BudgetStatus[]>('/api/v1/budgets/status'),
  createBudget: (data: Omit<Budget, 'id'>) =>
    apiRequest<Budget>('/api/v1/budgets', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateBudget: (id: string, data: Partial<Budget>) =>
    apiRequest<Budget>(`/api/v1/budgets/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  deleteBudget: (id: string) =>
    apiRequest<void>(`/api/v1/budgets/${id}`, { method: 'DELETE' }),

  // Rules
  getRules: () => apiRequest<CategoryRule[]>('/api/v1/rules'),
  createRule: (data: Omit<CategoryRule, 'id'>) =>
    apiRequest<CategoryRule>('/api/v1/rules', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateRule: (id: string, data: Partial<CategoryRule>) =>
    apiRequest<CategoryRule>(`/api/v1/rules/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  deleteRule: (id: string) =>
    apiRequest<void>(`/api/v1/rules/${id}`, { method: 'DELETE' }),

  // Sync
  getSyncStatus: () => apiRequest<SyncStatus>('/api/v1/sync/status'),
  triggerSync: () =>
    apiRequest<{ message: string }>('/api/v1/sync/trigger', { method: 'POST' }),

  // Dashboard summary
  getDashboardSummary: () =>
    apiRequest<{
      balance: number;
      spend_today: number;
      spend_this_month: number;
      transaction_count: number;
      top_categories: Array<{ category: string; amount: number }>;
    }>('/api/v1/dashboard/summary'),
};
