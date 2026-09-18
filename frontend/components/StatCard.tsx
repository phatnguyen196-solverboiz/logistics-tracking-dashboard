export function StatCard({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <article className="stat-card">
      <span className={`stat-icon ${tone}`} />
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
      </div>
    </article>
  );
}
