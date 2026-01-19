import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, type Budget, type CategoryRule } from '@/lib/api';

// Query keys
export const queryKeys = {
  auth: ['auth'] as const,
  transactions: (params?: Record<string, unknown>) =>
    ['transactions', params] as const,
  budgets: ['budgets'] as const,
  budgetStatuses: ['budgetStatuses'] as const,
  rules: ['rules'] as const,
  syncStatus: ['syncStatus'] as const,
  dashboardSummary: ['dashboardSummary'] as const,
  dashboardTrends: (days: number) => ['dashboardTrends', days] as const,
  recurringTransactions: ['recurringTransactions'] as const,
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
  return useQuery({
    queryKey: queryKeys.transactions(params),
    queryFn: () => api.getTransactions(params),
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
  return useQuery({
    queryKey: queryKeys.budgets,
    queryFn: api.getBudgets,
  });
}

export function useBudgetStatuses() {
  return useQuery({
    queryKey: queryKeys.budgetStatuses,
    queryFn: api.getBudgetStatuses,
  });
}

export function useCreateBudget() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Omit<Budget, 'id'>) => api.createBudget(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.budgets });
      queryClient.invalidateQueries({ queryKey: queryKeys.budgetStatuses });
    },
  });
}

export function useUpdateBudget() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Budget> }) =>
      api.updateBudget(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.budgets });
      queryClient.invalidateQueries({ queryKey: queryKeys.budgetStatuses });
    },
  });
}

export function useDeleteBudget() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.deleteBudget(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.budgets });
      queryClient.invalidateQueries({ queryKey: queryKeys.budgetStatuses });
    },
  });
}

export function useImportBudgets() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => api.importBudgets(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.budgets });
      queryClient.invalidateQueries({ queryKey: queryKeys.budgetStatuses });
    },
  });
}

// Rule hooks
export function useRules() {
  return useQuery({
    queryKey: queryKeys.rules,
    queryFn: api.getRules,
  });
}

export function useCreateRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Omit<CategoryRule, 'id'>) => api.createRule(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.rules });
    },
  });
}

export function useUpdateRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CategoryRule> }) =>
      api.updateRule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.rules });
    },
  });
}

export function useDeleteRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.deleteRule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.rules });
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
  return useQuery({
    queryKey: queryKeys.dashboardSummary,
    queryFn: api.getDashboardSummary,
  });
}

export function useDashboardTrends(days = 30) {
  return useQuery({
    queryKey: queryKeys.dashboardTrends(days),
    queryFn: () => api.getDashboardTrends(days),
  });
}

export function useRecurringTransactions() {
  return useQuery({
    queryKey: queryKeys.recurringTransactions,
    queryFn: api.getRecurringTransactions,
  });
}
