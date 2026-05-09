import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  getJob,
  createAnnotation,
  deleteAnnotation,
  fileUrl,
  type JobDetail,
  type AnnotationResponse,
} from "../api";
import { useConfirm } from "../components/ConfirmModal";
import { useToast } from "../contexts/ToastContext";

export default function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noteText, setNoteText] = useState("");
  const [saving, setSaving] = useState(false);
  const noteRef = useRef<HTMLTextAreaElement>(null);
  const { toast } = useToast();
  const confirm = useConfirm();

  useEffect(() => {
    if (!jobId) return;
    setLoading(true);
    getJob(jobId)
      .then(setJob)
      .catch(e => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [jobId]);

  async function handleAddNote(e: React.FormEvent) {
    e.preventDefault();
    if (!job || !noteText.trim()) return;
    setSaving(true);
    try {
      const ann = await createAnnotation(job.job_id, noteText.trim());
      setJob(prev => prev ? { ...prev, annotations: [...prev.annotations, ann] } : prev);
      setNoteText("");
      toast("Annotation saved.", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteAnnotation(ann: AnnotationResponse) {
    if (!await confirm("Delete this annotation?")) return;
    try {
      await deleteAnnotation(ann.id);
      setJob(prev => prev ? { ...prev, annotations: prev.annotations.filter(a => a.id !== ann.id) } : prev);
      toast("Annotation deleted.", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    }
  }

  if (loading) return <div className="page"><div className="status-line"><div className="spinner" /> Loading…</div></div>;
  if (error) return <div className="page"><div className="error">{error}</div></div>;
  if (!job) return null;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <button className="link-btn" onClick={() => navigate("/dashboard")}>← Dashboard</button>
          <h2 className="page-title" style={{ marginTop: 8 }}>Job <code className="job-id">{job.job_id}</code></h2>
          <p className="page-subtitle">{job.original_filename}</p>
        </div>
        <span className={`badge ${job.mode === "model" ? "badge-model" : "badge-fallback"}`}>
          {job.mode} · {job.device}
        </span>
      </div>

      {/* Stats */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="metric-value">{job.cell_count}</div>
          <div className="metric-caption">Cells Detected</div>
        </div>
        <div className="stat-card">
          <div className="metric-value">{job.processing_ms} ms</div>
          <div className="metric-caption">Processing Time</div>
        </div>
        <div className="stat-card">
          <div className="metric-value">{job.image_size}px</div>
          <div className="metric-caption">Input Size</div>
        </div>
        <div className="stat-card">
          <div className="metric-value">{job.min_area}</div>
          <div className="metric-caption">Min Area Filter</div>
        </div>
      </div>

      {/* Images */}
      <div className="results-grid">
        {[
          { label: "Input", url: job.input_url },
          { label: "Mask", url: job.mask_url },
          { label: "Overlay", url: job.overlay_url },
        ].map(({ label, url }) => (
          <div key={label} className="result-tile card">
            <h3>{label}</h3>
            <img src={fileUrl(url)} alt={label} loading="lazy" />
          </div>
        ))}
      </div>

      {/* Annotations */}
      <div className="card" style={{ marginTop: 24 }}>
        <h3>Annotations ({job.annotations.length})</h3>

        {job.annotations.length === 0 && (
          <p style={{ color: "var(--text-muted)", fontSize: 14 }}>No annotations yet.</p>
        )}

        {job.annotations.map(ann => (
          <div key={ann.id} className="annotation-row">
            <p className="annotation-text">{ann.note}</p>
            <div className="annotation-meta">
              <span>{new Date(ann.created_at).toLocaleString()}</span>
              <button
                className="btn-ghost btn-danger"
                onClick={() => handleDeleteAnnotation(ann)}
                title="Delete annotation"
              >
                ✕
              </button>
            </div>
          </div>
        ))}

        <form className="annotation-form" onSubmit={handleAddNote}>
          <textarea
            ref={noteRef}
            className="note-input"
            rows={3}
            placeholder="Add a research note…"
            value={noteText}
            onChange={e => setNoteText(e.target.value)}
            disabled={saving}
            maxLength={1000}
          />
          <button className="btn" type="submit" disabled={saving || !noteText.trim()}>
            {saving ? "Saving…" : "Add Note"}
          </button>
        </form>
      </div>
    </div>
  );
}
