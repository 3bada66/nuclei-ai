import { fileUrl, downloadPdfReport, type AnalysisResponse } from "../api";
import MetricCard from "./MetricCard";
import { useToast } from "../contexts/ToastContext";

interface Props {
  result: AnalysisResponse | null;
  busy: boolean;
  onPublish?: () => void;
  published?: boolean;
}

export default function ResultViewer({ result, busy, onPublish, published }: Props) {
  const { toast } = useToast();
  if (!result) {
    return (
      <div className="card">
        <h3>2 · Result</h3>
        <p style={{ color: "var(--text-muted)" }}>
          {busy
            ? "Awaiting analysis output…"
            : "Upload an image and click Run analysis to see the segmentation mask, the overlay, and the estimated cell count."}
        </p>
      </div>
    );
  }

  const isModel = result.metadata.mode === "model";

  return (
    <div className="card">
      <h3>2 · Result · job {result.job_id}</h3>

      <div className="results-grid">
        <div className="result-tile">
          <h3>Original</h3>
          <img src={fileUrl(result.input_url)} alt="Resized input" />
        </div>
        <div className="result-tile">
          <h3>Mask</h3>
          <img src={fileUrl(result.mask_url)} alt="Predicted segmentation mask" />
        </div>
        <div className="result-tile">
          <h3>Overlay</h3>
          <img src={fileUrl(result.overlay_url)} alt="Overlay of mask on original" />
        </div>
      </div>

      <div className="metrics-grid">
        <MetricCard
          label="Estimated cell count"
          value={result.cell_count}
          caption={`${result.metadata.processing_ms} ms · ${result.metadata.image_size}×${result.metadata.image_size}`}
        />
        <MetricCard
          label="Status"
          value={result.status === "ok" ? "Complete" : "Complete (fallback)"}
          badge={{
            text: isModel ? "U-Net model" : "fallback demo",
            tone: isModel ? "model" : "fallback",
          }}
          caption={result.message}
        />
      </div>

      {onPublish && (
        <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 8 }}>
          {published ? (
            <button className="btn btn-secondary btn-full" disabled>
              ✓ Published to Explore
            </button>
          ) : (
            <button className="btn btn-full" onClick={onPublish}>
              🌐 Publish to Explore
            </button>
          )}
          <button className="btn btn-secondary btn-full" onClick={() => downloadPdfReport(result.job_id).catch(e => toast(e.message, "error"))}>
            ↓ Download PDF Report
          </button>
        </div>
      )}
    </div>
  );
}
