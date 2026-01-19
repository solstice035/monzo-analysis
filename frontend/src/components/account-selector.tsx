import { useAccount } from "@/contexts/AccountContext";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function AccountSelector() {
  const { accounts, selectedAccount, setSelectedAccount, isLoading } =
    useAccount();

  if (isLoading) {
    return (
      <div className="w-[200px] h-10 bg-navy-deep rounded-md animate-pulse" />
    );
  }

  if (accounts.length === 0) {
    return null;
  }

  const getAccountLabel = (type: string, name?: string) => {
    if (name) return name;
    if (type.includes("joint")) return "Joint Account";
    if (type.includes("retail")) return "Personal Account";
    return type;
  };

  return (
    <Select
      value={selectedAccount?.id || ""}
      onValueChange={(id) => {
        const account = accounts.find((a) => a.id === id);
        if (account) {
          setSelectedAccount(account);
        }
      }}
    >
      <SelectTrigger className="w-[200px] bg-navy-deep border-navy-mid text-white">
        <SelectValue placeholder="Select account" />
      </SelectTrigger>
      <SelectContent className="bg-navy-deep border-navy-mid">
        {accounts.map((account) => (
          <SelectItem
            key={account.id}
            value={account.id}
            className="text-white hover:bg-navy-mid focus:bg-navy-mid"
          >
            {getAccountLabel(account.type, account.name)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
