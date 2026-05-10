import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeImage, publishJob, type AnalysisResponse, type PublicationResponse } from "../api";
import WorkflowSteps, { type WorkflowStage } from "../components/WorkflowSteps";
import UploadPanel from "../components/UploadPanel";
import ResultViewer from "../components/ResultViewer";
import { useToast } from "../contexts/ToastContext";

export default function AnalyzePage() {
  const [stage, setStage] = useState<WorkflowStage>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const prevUrl = useRef<string | null>(null);
  const { toast } = useToast();

  // Batch queue
  const [batchQueue, setBatchQueue] = useState<File[]>([]);
  const [batchResults, setBatchResults] = useState<{ file: string; cells: number; jobId: string }[]>([]);

  // Publish modal state
  const [showPublish, setShowPublish] = useState(false);
  const [headline, setHeadline] = useState("");
  const [description, setDescription] = useState("");
  const [publishing, setPublishing] = useState(false);
  const [published, setPublished] = useState<PublicationResponse | null>(null);

  useEffect(() => {
    if (prevUrl.current) URL.revokeObjectURL(prevUrl.current);
    if (!file) { setPreviewUrl(null); return; }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    prevUrl.current = url;
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [file]);

  function handleFileSelected(f: File) {
    setFile(f);
    setResult(null);
    setError(null);
    setStage("upload");
    setPublished(null);
    setBatchQueue([]);
    setBatchResults([]);
  }

  async function handleFilesSelected(files: File[]) {
    if (files.length === 0) return;
    setFile(files[0]);
    setResult(null);
    setError(null);
    setStage("upload");
    setPublished(null);
    setBatchQueue(files.slice(1));
    setBatchResults([]);
  }

  async function handleAnalyze() {
    if (!file) return;
    setBusy(true);
    setError(null);
    setResult(null);
    setStage("segment");
    try {
      const r = await analyzeImage(file);
      setStage("count");
      setResult(r);
      setStage("report");
      setBatchResults(prev => [...prev, { file: file.name, cells: r.cell_count, jobId: r.job_id }]);
      // Auto-process queue
      if (batchQueue.length > 0) {
        const [next, ...rest] = batchQueue;
        setBatchQueue(rest);
        setFile(next);
        setResult(null);
        setStage("segment");
        setBusy(true);
        try {
          const r2 = await analyzeImage(next);
          setResult(r2);
          setStage("report");
          setBatchResults(prev => [...prev, { file: next.name, cells: r2.cell_count, jobId: r2.job_id }]);
        } catch { /* handled below */ }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setStage("upload");
    } finally {
      setBusy(false);
    }
  }

  async function handlePublish(e: React.FormEvent) {
    e.preventDefault();
    if (!result) return;
    setPublishing(true);
    try {
      const pub = await publishJob(result.job_id, headline, description);
      setPublished(pub);
      setShowPublish(false);
      setHeadline("");
      setDescription("");
      toast("Analysis published to Explore!", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    } finally {
      setPublishing(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2 className="page-title">New Analysis</h2>
          <p className="page-subtitle">Upload a microscopy image to count nuclei</p>
        </div>
        {result && (
          <button className="btn btn-secondary" onClick={() => navigate(`/jobs/${result.job_id}`)}>
            View Full Job →
          </button>
        )}
      </div>

      <div className="panel" style={{ marginBottom: 24 }}>
        <WorkflowSteps stage={stage} />
      </div>

      <div className="grid-2">
        <div>
          <UploadPanel
            file={file}
            previewUrl={previewUrl}
            busy={busy}
            onFileSelected={handleFileSelected}
            onFilesSelected={handleFilesSelected}
            onAnalyze={handleAnalyze}
            error={error}
          />
          {batchQueue.length > 0 && (
            <div className="card" style={{ marginTop: 12, fontSize: 13 }}>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>Queue: {batchQueue.length} remaining</div>
              {batchQueue.map((f, i) => (
                <div key={i} style={{ color: "var(--text-muted)", padding: "2px 0" }}>⏳ {f.name}</div>
              ))}
            </div>
          )}
          {batchResults.length > 1 && (
            <div className="card" style={{ marginTop: 12, fontSize: 13 }}>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>Batch Results ({batchResults.length})</div>
              {batchResults.map((r, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px solid var(--border, #2a2a3a)" }}>
                  <span style={{ color: "var(--text-muted)", maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.file}</span>
                  <span><strong>{r.cells}</strong> cells</span>
                </div>
              ))}
            </div>
          )}
        </div>
        <ResultViewer
          result={result}
          busy={busy}
          onPublish={result ? () => setShowPublish(true) : undefined}
          published={!!published}
        />
      </div>

      {/* Publish Modal */}
      {showPublish && result && (
        <div
          style={{
            position: "fixed", inset: 0, background: "rgba(20,20,20,0.88)",
            display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
            backdropFilter: "blur(4px)",
          }}
          onClick={e => { if (e.target === e.currentTarget) setShowPublish(false); }}
        >
          <div className="card" style={{ width: 480, padding: 28 }}>
            <h3 style={{ marginBottom: 4 }}>Publish to Explore</h3>
            <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 20 }}>
              Share your analysis with the community. Others will be able to view and save it.
            </p>

            {/* Analysis summary */}
            <div style={{
              background: "var(--surface-2, #1a1a2e)", borderRadius: 10,
              padding: 14, marginBottom: 20, fontSize: 13,
              display: "flex", gap: 20,
            }}>
              <div><span style={{ color: "var(--text-muted)" }}>Cells detected</span><br /><strong style={{ fontSize: 20 }}>{result.cell_count}</strong></div>
              <div><span style={{ color: "var(--text-muted)" }}>Mode</span><br /><strong>{result.metadata.mode}</strong></div>
              <div><span style={{ color: "var(--text-muted)" }}>File</span><br /><strong style={{ wordBreak: "break-all" }}>{result.metadata.original_filename}</strong></div>
            </div>

            <form onSubmit={handlePublish} className="auth-form">
              <label className="field-label">Headline</label>
              <input
                className="field-input"
                required
                minLength={3}
                maxLength={150}
                placeholder="e.g. High-density nuclei in tumour tissue sample"
                value={headline}
                onChange={e => setHeadline(e.target.value)}
                autoFocus
              />
              <label className="field-label" style={{ marginTop: 12 }}>Description</label>
              <textarea
                className="note-input"
                required
                minLength={10}
                maxLength={2000}
                rows={4}
                placeholder="Describe your sample, findings, or methodology…"
                value={description}
                onChange={e => setDescription(e.target.value)}
              />
              <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
                <button className="btn btn-full" type="submit" disabled={publishing}>
                  {publishing ? "Publishing…" : "Publish"}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-full"
                  onClick={() => setShowPublish(false)}
                  disabled={publishing}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
