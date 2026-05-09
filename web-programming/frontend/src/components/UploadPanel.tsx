import { useRef, useState, type DragEvent, type ChangeEvent } from "react";

interface Props {
  file: File | null;
  previewUrl: string | null;
  busy: boolean;
  error: string | null;
  onFileSelected: (file: File) => void;
  onAnalyze: () => void;
}

export default function UploadPanel({
  file,
  previewUrl,
  busy,
  error,
  onFileSelected,
  onAnalyze,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) onFileSelected(f);
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) onFileSelected(f);
  }

  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(true);
  }

  return (
    <div className="card">
      <h3>1 · Upload</h3>
      <div
        className={`upload-zone ${dragging ? "dragging" : ""}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={() => setDragging(false)}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload a microscopy image"
      >
        <p>
          {file
            ? <strong>{file.name}</strong>
            : <>Drop a microscopy image here, or click to browse.<br />PNG, JPG, or TIFF up to 10 MB.</>}
        </p>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          style={{ display: "none" }}
          onChange={handleChange}
        />
      </div>

      {previewUrl && (
        <div className="preview">
          <img src={previewUrl} alt="Selected microscopy preview" />
        </div>
      )}

      <button
        type="button"
        className="btn"
        disabled={!file || busy}
        onClick={onAnalyze}
      >
        {busy ? "Analysing…" : "Run analysis"}
      </button>

      {busy && (
        <div className="status-line">
          <span className="spinner" aria-hidden />
          <span>Running U-Net inference and connected-component counting…</span>
        </div>
      )}

      {error && <div className="error" role="alert">{error}</div>}
    </div>
  );
}
