interface Props {
  label: string;
  value: string | number;
  caption?: string;
  badge?: { text: string; tone: "model" | "fallback" };
}

export default function MetricCard({ label, value, caption, badge }: Props) {
  return (
    <div className="card">
      <h3>{label}</h3>
      <div className="metric-value">{value}</div>
      {badge && (
        <span className={`badge ${badge.tone === "model" ? "badge-model" : "badge-fallback"}`}>
          {badge.text}
        </span>
      )}
      {caption && <div className="metric-caption" style={{ marginTop: 6 }}>{caption}</div>}
    </div>
  );
}
