export function StatusBadge({ status }: { status: string }) {
  const key = status.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  return <span className={`status status-${key}`}>{status}</span>;
}
