import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, type Budget, type CategoryRule } from '@/lib/api';
import { useAccount } from '@/contexts/AccountContext';

// Query keys - now include accountId for account-scoped data
export const queryKeys = {
  auth: ['auth'] as const,
  accounts: ['accounts'] as const,
  transactions: (accountId: string, params?: Record<string, unknown>) =>
    ['transactions', accountId, params] as const,
  budgets: (accountId: string) => ['budgets', accountId] as const,
  budgetStatuses: (accountId: string) => ['budgetStatuses', accountId] as const,
  rules: (accountId: string) => ['rules', accountId] as const,
  syncStatus: ['syncStatus'] as const,
  dashboardSummary: (accountId: string) => ['dashboardSummary', accountId] as const,
  dashboardTrends: (accountId: string, days: number) => ['dashboardTrends', accountId, days] as const,
  recurringTransactions: (accountId: string) => ['recurringTransactions', accountId] as const,
};

// Auth hooks
export function useAuthStatus() {
  return useQuery({
    queryKey: queryKeys.auth,
    queryFn: api.getAuthStatus,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Transaction hooks
export function useTransactions(params?: {
  limit?: number;
  offset?: number;
  category?: string;
  since?: string;
  until?: string;
}) {
  const { selectedAccount } = useAccount();
  const accountId = selectedAccount?.id || '';

  return useQuery({
    queryKey: queryKeys.transactions(accountId, params),
    queryFn: () => api.getTransactions({ account_id: accountId, ...params }),
    enabled: !!accountId,
  });
}

export function useUpdateTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: { custom_category?: string; notes?: string };
    }) => api.updateTransaction(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
  });
}

// Budget hooks
export function useBudgets() {
  const { selectedAccount } = useAccount();
  const accountId = selectedAccount?.id || '';

  return useQuery({
    queryKey: queryKeys.budgets(accountId),
    queryFn: () => api.getBudgets(accountId),
    enabled: !!accountId,
  });
}

export function useBudgetStatuses() {
  const { selectedAccount } = useAccount();
  const accountId = selectedAccount?.id || '';

  return useQuery({
    queryKey: queryKeys.budgetStatuses(accountId),
    queryFn: () => api.getBudgetStatuses(accountId),
    enabled: !!accountId,
  });
}

export function useCreateBudget() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Omit<Budget, 'id'>) => api.createBudget(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] });
      queryClient.invalidateQueries({ queryKey: ['budgetStatuses'] });
    },
  });
}

export function useUpdateBudget() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Budget> }) =>
      api.updateBudget(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] });
      queryClient.invalidateQueries({ queryKey: ['budgetStatuses'] });
    },
  });
}

export function useDeleteBudget() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.deleteBudget(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] });
      queryClient.invalidateQueries({ queryKey: ['budgetStatuses'] });
    },
  });
}

export function useImportBudgets() {
  const { selectedAccount } = useAccount();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => {
      if (!selectedAccount) {
        throw new Error('No account selected');
      }
      return api.importBudgets(file, selectedAccount.id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] });
      queryClient.invalidateQueries({ queryKey: ['budgetStatuses'] });
    },
  });
}

// Rule hooks
export function useRules() {
  const { selectedAccount } = useAccount();
  const accountId = selectedAccount?.id || '';

  return useQuery({
    queryKey: queryKeys.rules(accountId),
    queryFn: () => api.getRules(accountId),
    enabled: !!accountId,
  });
}

export function useCreateRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Omit<CategoryRule, 'id'>) => api.createRule(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] });
    },
  });
}

export function useUpdateRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CategoryRule> }) =>
      api.updateRule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] });
    },
  });
}

export function useDeleteRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.deleteRule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] });
    },
  });
}

// Sync hooks
export function useSyncStatus() {
  return useQuery({
    queryKey: queryKeys.syncStatus,
    queryFn: api.getSyncStatus,
    refetchInterval: 10000, // Refresh every 10 seconds
  });
}

export function useTriggerSync() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.triggerSync,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.syncStatus });
    },
  });
}

// Dashboard hooks
export function useDashboardSummary() {
  const { selectedAccount } = useAccount();
  const accountId = selectedAccount?.id || '';

  return useQuery({
    queryKey: queryKeys.dashboardSummary(accountId),
    queryFn: () => api.getDashboardSummary(accountId),
    enabled: !!accountId,
  });
}

export function useDashboardTrends(days = 30) {
  const { selectedAccount } = useAccount();
  const accountId = selectedAccount?.id || '';

  return useQuery({
    queryKey: queryKeys.dashboardTrends(accountId, days),
    queryFn: () => api.getDashboardTrends(accountId, days),
    enabled: !!accountId,
  });
}

export function useRecurringTransactions() {
  const { selectedAccount } = useAccount();
  const accountId = selectedAccount?.id || '';

  return useQuery({
    queryKey: queryKeys.recurringTransactions(accountId),
    queryFn: () => api.getRecurringTransactions(accountId),
    enabled: !!accountId,
  });
}
