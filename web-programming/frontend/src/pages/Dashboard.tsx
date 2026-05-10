import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listJobs, deleteJob, exportJobsCsv, unpublishPublication, formatDate, type JobSummary } from "../api";
import { useConfirm } from "../components/ConfirmModal";
import TrendChart from "../components/TrendChart";
import { useToast } from "../contexts/ToastContext";
import CustomSelect from "../components/CustomSelect";

const PAGE_SIZE = 10;

export default function Dashboard() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  // Filter state
  const [search, setSearch] = useState("");
  const [modeFilter, setModeFilter] = useState<"all" | "model" | "fallback-demo">("all");

  // Pagination state
  const [page, setPage] = useState(0);

  const navigate = useNavigate();
  const { toast } = useToast();
  const confirm = useConfirm();

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setJobs(await listJobs(0, 200));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  // Reset page when filters change
  useEffect(() => { setPage(0); }, [search, modeFilter]);

  // Derived: filtered list
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return jobs.filter(j => {
      if (modeFilter !== "all" && j.mode !== modeFilter) return false;
      if (q && !j.original_filename.toLowerCase().includes(q) && !j.job_id.includes(q)) return false;
      return true;
    });
  }, [jobs, search, modeFilter]);

  // Derived: paginated slice
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  // Stats from full (unfiltered) list
  const totalCells = jobs.reduce((s, j) => s + j.cell_count, 0);
  const modelJobs = jobs.filter(j => j.mode === "model").length;
  const avgCells = jobs.length > 0 ? Math.round(totalCells / jobs.length) : 0;

  async function handleDelete(e: React.MouseEvent, jobId: string) {
    e.stopPropagation();
    if (!await confirm("Delete this job and its annotations?")) return;
    try {
      await deleteJob(jobId);
      setJobs(prev => prev.filter(j => j.job_id !== jobId));
      toast("Job deleted.", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    }
  }

  async function handleExport() {
    setExporting(true);
    try {
      await exportJobsCsv();
      toast("CSV downloaded.", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2 className="page-title">Dashboard</h2>
          <p className="page-subtitle">All analysis jobs</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            className="btn btn-secondary"
            onClick={handleExport}
            disabled={exporting || jobs.length === 0}
            title="Download job history as CSV"
          >
            {exporting ? "Exporting…" : "↓ Export CSV"}
          </button>
          <button className="btn" onClick={() => navigate("/analyze")}>
            + New Analysis
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="metric-value">{jobs.length}</div>
          <div className="metric-caption">Total Jobs</div>
        </div>
        <div className="stat-card">
          <div className="metric-value">{totalCells.toLocaleString()}</div>
          <div className="metric-caption">Total Cells Counted</div>
        </div>
        <div className="stat-card">
          <div className="metric-value">{avgCells.toLocaleString()}</div>
          <div className="metric-caption">Avg Cells / Job</div>
        </div>
        <div className="stat-card">
          <div className="metric-value">{modelJobs}</div>
          <div className="metric-caption">Model Runs</div>
        </div>
        <div className="stat-card">
          <div className="metric-value">{jobs.length - modelJobs}</div>
          <div className="metric-caption">Demo Runs</div>
        </div>
      </div>

      {/* Trend chart */}
      {jobs.length > 0 && (
        <div className="card" style={{ marginBottom: 20, padding: "16px 20px" }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: "var(--text-muted)" }}>
            CELLS COUNTED — LAST 7 DAYS
          </h3>
          <TrendChart jobs={jobs} days={7} />
        </div>
      )}

      {/* Search + filter toolbar */}
      {jobs.length > 0 && (
        <div style={{ display: "flex", gap: 10, marginBottom: 14, flexWrap: "wrap" }}>
          <input
            className="field-input"
            style={{ flex: "1 1 200px", maxWidth: 320 }}
            placeholder="Search by filename or job ID…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <CustomSelect
            value={modeFilter}
            onChange={v => setModeFilter(v)}
            options={[
              { value: "all", label: "All modes" },
              { value: "model", label: "Model only" },
              { value: "fallback-demo", label: "Demo only" },
            ]}
          />
          {(search || modeFilter !== "all") && (
            <button
              className="btn-ghost"
              onClick={() => { setSearch(""); setModeFilter("all"); }}
              style={{ alignSelf: "center" }}
            >
              Clear ✕
            </button>
          )}
          <span style={{ alignSelf: "center", color: "var(--text-muted)", fontSize: 13, marginLeft: "auto" }}>
            {filtered.length} result{filtered.length !== 1 ? "s" : ""}
          </span>
        </div>
      )}

      {loading && <div className="status-line"><div className="spinner" /> Loading jobs…</div>}
      {error && <div className="error">{error}</div>}

      {!loading && jobs.length === 0 && (
        <div className="empty-state">
          <p>No analyses yet. <button className="link-btn" onClick={() => navigate("/analyze")}>Upload an image</button> to get started.</p>
        </div>
      )}

      {!loading && jobs.length > 0 && filtered.length === 0 && (
        <div className="empty-state">
          <p>No jobs match the current filter.</p>
        </div>
      )}

      {paginated.length > 0 && (
        <>
          <div className="table-wrap">
            <table className="job-table">
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>File</th>
                  <th>Cells</th>
                  <th>Mode</th>
                  <th>Notes</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {paginated.map(job => (
                  <tr key={job.job_id} className="job-row" onClick={() => navigate(`/jobs/${job.job_id}`)}>
                    <td><code className="job-id">{job.job_id}</code></td>
                    <td className="filename">{job.original_filename}</td>
                    <td><span className="metric-value" style={{ fontSize: 18 }}>{job.cell_count}</span></td>
                    <td>
                      <span className={`badge ${job.mode === "model" ? "badge-model" : "badge-fallback"}`}>
                        {job.mode}
                      </span>
                      {job.publication_id && (
                        <span className="badge" style={{ marginLeft: 6, fontSize: 10, background: "var(--accent-teal)", color: "#000" }}>
                          Published
                        </span>
                      )}
                    </td>
                    <td>{job.annotation_count}</td>
                    <td className="ts">{formatDate(job.created_at)}</td>
                    <td>
                      <div style={{ display: "flex", gap: 4 }}>
                        {job.publication_id && (
                          <button
                            className="btn-ghost"
                            title="Unpublish from Explore"
                            onClick={async e => {
                              e.stopPropagation();
                              if (!await confirm("Unpublish this analysis from Explore?")) return;
                              try {
                                await unpublishPublication(job.publication_id!);
                                setJobs(prev => prev.map(j => j.job_id === job.job_id ? { ...j, publication_id: null } : j));
                                toast("Unpublished.", "success");
                              } catch (err) { toast(err instanceof Error ? err.message : String(err), "error"); }
                            }}
                          >🌐✕</button>
                        )}
                        <button
                          className="btn-ghost btn-danger"
                          onClick={e => handleDelete(e, job.job_id)}
                          title="Delete job"
                        >✕</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 12, marginTop: 16 }}>
              <button
                className="btn btn-secondary"
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
              >
                ← Prev
              </button>
              <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
                Page {page + 1} of {totalPages}
              </span>
              <button
                className="btn btn-secondary"
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
