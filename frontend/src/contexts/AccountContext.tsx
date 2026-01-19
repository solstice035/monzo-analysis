import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Account } from "@/lib/api";

interface AccountContextValue {
  accounts: Account[];
  selectedAccount: Account | null;
  setSelectedAccount: (account: Account) => void;
  isLoading: boolean;
  error: Error | null;
}

const AccountContext = createContext<AccountContextValue | null>(null);

const STORAGE_KEY = "monzo-selected-account-id";

export function AccountProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [selectedAccount, setSelectedAccountState] = useState<Account | null>(
    null
  );

  const {
    data: accounts = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ["accounts"],
    queryFn: api.getAccounts,
  });

  // Initialize selected account from localStorage or default to joint account
  useEffect(() => {
    if (accounts.length > 0 && !selectedAccount) {
      const savedAccountId = localStorage.getItem(STORAGE_KEY);

      let accountToSelect: Account | undefined;

      if (savedAccountId) {
        accountToSelect = accounts.find((a) => a.id === savedAccountId);
      }

      // Default to joint account (type contains "joint"), or first account
      if (!accountToSelect) {
        accountToSelect =
          accounts.find((a) => a.type.includes("joint")) || accounts[0];
      }

      if (accountToSelect) {
        setSelectedAccountState(accountToSelect);
      }
    }
  }, [accounts, selectedAccount]);

  const setSelectedAccount = (account: Account) => {
    setSelectedAccountState(account);
    localStorage.setItem(STORAGE_KEY, account.id);

    // Invalidate all account-scoped queries to refetch with new account
    queryClient.invalidateQueries({ queryKey: ["transactions"] });
    queryClient.invalidateQueries({ queryKey: ["budgets"] });
    queryClient.invalidateQueries({ queryKey: ["budgetStatuses"] });
    queryClient.invalidateQueries({ queryKey: ["rules"] });
    queryClient.invalidateQueries({ queryKey: ["dashboardSummary"] });
    queryClient.invalidateQueries({ queryKey: ["dashboardTrends"] });
    queryClient.invalidateQueries({ queryKey: ["recurringTransactions"] });
  };

  return (
    <AccountContext.Provider
      value={{
        accounts,
        selectedAccount,
        setSelectedAccount,
        isLoading,
        error: error as Error | null,
      }}
    >
      {children}
    </AccountContext.Provider>
  );
}

export function useAccount() {
  const context = useContext(AccountContext);
  if (!context) {
    throw new Error("useAccount must be used within an AccountProvider");
  }
  return context;
}
