import {
  ShoppingCart,
  UtensilsCrossed,
  ShoppingBag,
  Car,
  Clapperboard,
  FileText,
  Package,
  Plane,
  Banknote,
  Briefcase,
  PiggyBank,
  Home,
  Wifi,
  Heart,
  GraduationCap,
  Dumbbell,
  Gift,
  Baby,
  Wrench,
  Coffee,
  Beer,
  Smartphone,
  CreditCard,
  TrendingUp,
  HelpCircle,
  Folder,
  Sparkles,
  TrendingDown,
  Landmark,
  Umbrella,
  ArrowDownLeft,
  type LucideIcon,
} from "lucide-react";

export const categoryIcons: Record<string, LucideIcon> = {
  groceries: ShoppingCart,
  eating_out: UtensilsCrossed,
  shopping: ShoppingBag,
  transport: Car,
  entertainment: Clapperboard,
  bills: FileText,
  general: Package,
  holidays: Plane,
  cash: Banknote,
  expenses: Briefcase,
  savings: PiggyBank,
  rent: Home,
  mortgage: Home,
  utilities: Wifi,
  health: Heart,
  education: GraduationCap,
  fitness: Dumbbell,
  gifts: Gift,
  childcare: Baby,
  maintenance: Wrench,
  coffee: Coffee,
  drinks: Beer,
  phone: Smartphone,
  subscriptions: CreditCard,
  investments: TrendingUp,
  income: ArrowDownLeft,
};

/**
 * Returns the appropriate lucide icon for a category.
 * Falls back to HelpCircle for unknown categories.
 */
export function getCategoryIcon(category: string): LucideIcon {
  const normalised = category.toLowerCase().replace(/\s+/g, "_");
  return categoryIcons[normalised] || HelpCircle;
}

/**
 * Standard icon styling for category icons in table/list rows.
 */
export const categoryIconProps = {
  size: 14,
  strokeWidth: 1.5,
  className: "text-stone",
} as const;

/**
 * Larger icon variant for dashboard/summary contexts.
 */
export const categoryIconPropsLg = {
  size: 20,
  strokeWidth: 1.5,
  className: "text-stone",
} as const;

// Budget group icons
export const groupIcons: Record<string, LucideIcon> = {
  essential: Home,
  lifestyle: Sparkles,
  savings: PiggyBank,
  debt: TrendingDown,
  fixed: Landmark,
  emergency: Umbrella,
  default: Folder,
};

/**
 * Returns the appropriate lucide icon for a budget group.
 */
export function getGroupIcon(iconName?: string): LucideIcon {
  if (!iconName) return Folder;
  return groupIcons[iconName.toLowerCase()] || Folder;
}
