import type { JobSummary } from "../api";

interface Props {
  jobs: JobSummary[];
  days?: number;
}

/** Pure-SVG bar chart — cells counted per day over the last N days. No deps. */
export default function TrendChart({ jobs, days = 7 }: Props) {
  // Build a map: dateStr → total cell count
  const now = new Date();
  const buckets: { label: string; date: string; cells: number }[] = [];

  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().slice(0, 10);
    buckets.push({
      label: i === 0 ? "Today" : i === 1 ? "Yesterday" : d.toLocaleDateString(undefined, { weekday: "short" }),
      date: dateStr,
      cells: 0,
    });
  }

  for (const job of jobs) {
    const dateStr = new Date(job.created_at).toISOString().slice(0, 10);
    const bucket = buckets.find(b => b.date === dateStr);
    if (bucket) bucket.cells += job.cell_count;
  }

  const maxCells = Math.max(...buckets.map(b => b.cells), 1);

  // SVG dimensions
  const W = 560;
  const H = 120;
  const BAR_W = Math.floor((W - 40) / days) - 6;
  const BAR_AREA_H = 80;
  const LABEL_Y = H - 4;

  return (
    <div style={{ overflowX: "auto" }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        style={{ display: "block", maxWidth: W }}
        aria-label={`Cell count trend — last ${days} days`}
      >
        {buckets.map((b, i) => {
          const barH = b.cells === 0 ? 2 : Math.max(4, Math.round((b.cells / maxCells) * BAR_AREA_H));
          const x = 20 + i * ((W - 40) / days);
          const y = BAR_AREA_H - barH + 8;
          const isEmpty = b.cells === 0;
          return (
            <g key={b.date}>
              <rect
                x={x}
                y={y}
                width={BAR_W}
                height={barH}
                rx={3}
                fill={isEmpty ? "var(--border, #2a2a3a)" : "var(--accent-teal, #3ecfb2)"}
                opacity={isEmpty ? 0.4 : 0.85}
              />
              {b.cells > 0 && (
                <text
                  x={x + BAR_W / 2}
                  y={y - 3}
                  textAnchor="middle"
                  fontSize={9}
                  fill="var(--text-muted, #888)"
                >
                  {b.cells.toLocaleString()}
                </text>
              )}
              <text
                x={x + BAR_W / 2}
                y={LABEL_Y}
                textAnchor="middle"
                fontSize={9}
                fill="var(--text-muted, #888)"
              >
                {b.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
