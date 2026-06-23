interface EmptyStateProps {
  title: string;
  description: string;
  action?: React.ReactNode;
}

export default function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-3xl text-center">
      <p className="text-heading-sm text-on-dark-mute">{title}</p>
      <p className="text-body-sm text-stone mt-xs max-w-xs">{description}</p>
      {action && <div className="mt-xl">{action}</div>}
    </div>
  );
}
