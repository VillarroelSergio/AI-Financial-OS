import type { AiProviderStatus } from "../types/aiAssistant.types";

interface Props {
  provider?: AiProviderStatus;
  loading?: boolean;
}

export default function AiStatusBadge({ provider, loading }: Props) {
  if (loading) {
    return (
      <span className="inline-flex items-center gap-1.5 text-caption text-mute">
        <span className="w-1.5 h-1.5 rounded-full bg-stone animate-pulse" />
        Conectando…
      </span>
    );
  }

  if (!provider) {
    return (
      <span className="inline-flex items-center gap-1.5 text-caption text-mute">
        <span className="w-1.5 h-1.5 rounded-full bg-stone" />
        Sin proveedor
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 text-caption">
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          provider.available ? "bg-green-400" : "bg-red-400"
        }`}
      />
      <span className={provider.available ? "text-on-dark" : "text-stone"}>
        {provider.name}
        {provider.model ? ` · ${provider.model.split(":")[0]}` : ""}
      </span>
      {provider.latency_ms != null && provider.available && (
        <span className="text-mute">{provider.latency_ms}ms</span>
      )}
    </span>
  );
}
