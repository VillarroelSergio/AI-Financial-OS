import { EmptyState as PremiumEmptyState } from "./Dashboard";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: React.ReactNode;
}

export default function EmptyState({ title, description, action }: EmptyStateProps) {
  return <PremiumEmptyState title={title} description={description} action={action} />;
}
