import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeImage, type AnalysisResponse } from "../api";
import WorkflowSteps, { type WorkflowStage } from "../components/WorkflowSteps";
import UploadPanel from "../components/UploadPanel";
import ResultViewer from "../components/ResultViewer";

export default function AnalyzePage() {
  const [stage, setStage] = useState<WorkflowStage>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const prevUrl = useRef<string | null>(null);

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
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setStage("upload");
    } finally {
      setBusy(false);
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
        <UploadPanel
          file={file}
          previewUrl={previewUrl}
          busy={busy}
          onFileSelected={handleFileSelected}
          onAnalyze={handleAnalyze}
          error={error}
        />
        <ResultViewer result={result} busy={busy} />
      </div>
    </div>
  );
}
