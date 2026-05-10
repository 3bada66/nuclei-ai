import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  addFavourite, removeFavourite, getExplore, getComments, addComment, deleteComment,
  downloadPdfReport, fileUrl, formatDate, type PublicationResponse, type CommentResponse,
} from "../api";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";
import CustomSelect from "../components/CustomSelect";

function PublicationModal({
  pub, onClose, onFavouriteToggle,
}: {
  pub: PublicationResponse;
  onClose: () => void;
  onFavouriteToggle: (pub: PublicationResponse) => void;
}) {
  const { user } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [comments, setComments] = useState<CommentResponse[]>([]);
  const [commentText, setCommentText] = useState("");
  const [commenting, setCommenting] = useState(false);

  useEffect(() => {
    getComments(pub.id).then(setComments).catch(() => {});
  }, [pub.id]);

  async function handleFav() {
    setBusy(true);
    await onFavouriteToggle(pub);
    setBusy(false);
  }

  async function handleAddComment(e: React.FormEvent) {
    e.preventDefault();
    if (!commentText.trim()) return;
    setCommenting(true);
    try {
      const c = await addComment(pub.id, commentText.trim());
      setComments(prev => [...prev, c]);
      setCommentText("");
    } catch (err) { toast(err instanceof Error ? err.message : String(err), "error"); }
    finally { setCommenting(false); }
  }

  async function handleDeleteComment(id: number) {
    try {
      await deleteComment(id);
      setComments(prev => prev.filter(c => c.id !== id));
    } catch (err) { toast(err instanceof Error ? err.message : String(err), "error"); }
  }

  function downloadImage(url: string, name: string) {
    const token = localStorage.getItem("token") ?? "";
    const API = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8000";
    fetch(`${API}${url}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.blob()).then(blob => {
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = name;
        a.click();
      });
  }

  return (
    <div
      style={{
        position: "fixed", inset: 0, background: "rgba(20,20,20,0.88)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: 1000, padding: 20, backdropFilter: "blur(4px)",
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="card" style={{ width: "100%", maxWidth: 820, maxHeight: "92vh", overflowY: "auto", padding: 0 }}>
        {/* Header */}
        <div style={{ padding: "20px 24px 0", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 20 }}>{pub.headline}</h2>
            <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 4 }}>
              by{" "}
              <button className="link-btn" onClick={() => { onClose(); navigate(`/users/${pub.username}`); }}>
                <strong>{pub.username}</strong>
              </button>
              {" · "}{formatDate(pub.created_at)}
            </div>
          </div>
          <button onClick={onClose}
            style={{ background: "none", border: "none", fontSize: 22, cursor: "pointer", color: "var(--text-muted)" }}>
            ×
          </button>
        </div>

        {/* Images */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, padding: "20px 24px" }}>
          {[
            { label: "Original", url: pub.input_url, filename: `original-${pub.id}.png` },
            { label: "Mask", url: pub.mask_url, filename: `mask-${pub.id}.png` },
            { label: "Overlay", url: pub.overlay_url, filename: `overlay-${pub.id}.png` },
          ].map(({ label, url, filename }) => (
            <div key={label}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                <span style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1 }}>{label}</span>
                <button className="btn-ghost" style={{ fontSize: 11, padding: "2px 6px" }}
                  onClick={() => downloadImage(url, filename)} title={`Download ${label}`}>↓</button>
              </div>
              <img src={fileUrl(url)} alt={label}
                style={{ width: "100%", borderRadius: 10, objectFit: "cover", maxHeight: 200 }} />
            </div>
          ))}
        </div>

        {/* Stats */}
        <div style={{ display: "flex", gap: 12, padding: "0 24px" }}>
          {[
            { label: "Cells Detected", value: pub.cell_count },
            { label: "Mode", value: pub.mode },
            { label: "File", value: pub.original_filename.length > 22 ? pub.original_filename.slice(0, 22) + "…" : pub.original_filename },
            { label: "Comments", value: comments.length },
          ].map(({ label, value }) => (
            <div key={label} style={{ flex: 1, background: "var(--surface-2, #1a1a2e)", borderRadius: 10, padding: "12px 16px" }}>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 }}>{label}</div>
              <div style={{ fontWeight: 700, fontSize: 18 }}>{value}</div>
            </div>
          ))}
        </div>

        {/* Description */}
        <div style={{ padding: "16px 24px 0" }}>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>Description</div>
          <p style={{ margin: 0, lineHeight: 1.7, color: "var(--text-muted)", fontSize: 14 }}>{pub.description}</p>
        </div>

        {/* Comments */}
        <div style={{ padding: "16px 24px" }}>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 10, textTransform: "uppercase", letterSpacing: 1 }}>
            Comments ({comments.length})
          </div>
          {comments.map(c => (
            <div key={c.id} style={{
              background: "var(--surface-2, #1a1a2e)", borderRadius: 8,
              padding: "10px 14px", marginBottom: 8, fontSize: 13,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <button className="link-btn" onClick={() => { onClose(); navigate(`/users/${c.username}`); }}>
                  <strong>{c.username}</strong>
                </button>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{formatDate(c.created_at)}</span>
                  {(user?.id === c.user_id || user?.role === "admin" || user?.role === "manager") && (
                    <button className="btn-ghost btn-danger" style={{ fontSize: 11, padding: "1px 6px" }}
                      onClick={() => handleDeleteComment(c.id)}>✕</button>
                  )}
                </div>
              </div>
              <div style={{ color: "var(--text-muted)" }}>{c.text}</div>
            </div>
          ))}
          <form onSubmit={handleAddComment} style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <input className="field-input" style={{ flex: 1 }} placeholder="Add a comment…"
              value={commentText} onChange={e => setCommentText(e.target.value)} maxLength={1000} />
            <button className="btn" type="submit" disabled={commenting || !commentText.trim()}>
              {commenting ? "…" : "Post"}
            </button>
          </form>
        </div>

        {/* Actions */}
        <div style={{ padding: "0 24px 24px", display: "flex", flexDirection: "column", gap: 8 }}>
          <button
            className={`btn btn-full${pub.is_favourited ? " btn-secondary" : ""}`}
            disabled={busy} onClick={handleFav}
          >
            {pub.is_favourited ? "♥ Remove from Favourites" : "♡ Save to Favourites"}
          </button>
          <button className="btn btn-secondary btn-full" onClick={() => downloadPdfReport(pub.job_uid).catch(e => toast(e.message, "error"))}>
            ↓ Download PDF Report
          </button>
        </div>
      </div>
    </div>
  );
}

function PublicationCard({
  pub, onFavouriteToggle, onOpen,
}: {
  pub: PublicationResponse;
  onFavouriteToggle: (pub: PublicationResponse) => void;
  onOpen: (pub: PublicationResponse) => void;
}) {
  const [busy, setBusy] = useState(false);

  async function handleFav(e: React.MouseEvent) {
    e.stopPropagation();
    setBusy(true);
    await onFavouriteToggle(pub);
    setBusy(false);
  }

  return (
    <div className="card"
      style={{ display: "flex", flexDirection: "column", gap: 0, padding: 0, overflow: "hidden", cursor: "pointer" }}
      onClick={() => onOpen(pub)}
    >
      <div style={{ position: "relative", height: 180, overflow: "hidden", background: "#0a0a14" }}>
        <img src={fileUrl(pub.overlay_url)} alt={pub.headline}
          style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.9 }} />
        <div style={{ position: "absolute", top: 10, right: 10, background: "rgba(0,0,0,0.6)", borderRadius: 20, padding: "4px 10px" }}>
          <span className={`badge ${pub.mode === "model" ? "badge-model" : "badge-fallback"}`} style={{ fontSize: 11 }}>
            {pub.mode}
          </span>
        </div>
        <button onClick={handleFav} disabled={busy}
          style={{
            position: "absolute", top: 10, left: 10,
            background: "rgba(0,0,0,0.6)", border: "none", borderRadius: 20,
            padding: "6px 10px", cursor: "pointer", fontSize: 16,
            color: pub.is_favourited ? "#f87171" : "#888",
          }}
        >{pub.is_favourited ? "♥" : "♡"}</button>
      </div>
      <div style={{ padding: 16, flex: 1, display: "flex", flexDirection: "column", gap: 8 }}>
        <div style={{ fontWeight: 700, fontSize: 15, lineHeight: 1.4 }}>{pub.headline}</div>
        <div style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.5, flex: 1 }}>
          {pub.description.length > 120 ? pub.description.slice(0, 120) + "…" : pub.description}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
          <div style={{ display: "flex", gap: 12, fontSize: 13, color: "var(--text-muted)" }}>
            <span>🔬 <strong style={{ color: "var(--text)" }}>{pub.cell_count}</strong></span>
            <span>💬 {pub.comment_count}</span>
            <span>👤 {pub.username}</span>
          </div>
          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{formatDate(pub.created_at)}</span>
        </div>
      </div>
    </div>
  );
}

export default function ExplorePage() {
  const { toast } = useToast();
  const [pubs, setPubs] = useState<PublicationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [modeFilter, setModeFilter] = useState<"all" | "model" | "fallback-demo">("all");
  const [minCells, setMinCells] = useState("");
  const [maxCells, setMaxCells] = useState("");
  const [selected, setSelected] = useState<PublicationResponse | null>(null);

  useEffect(() => {
    getExplore()
      .then(setPubs)
      .catch(e => toast(e instanceof Error ? e.message : String(e), "error"))
      .finally(() => setLoading(false));
  }, []);

  async function handleFavouriteToggle(pub: PublicationResponse) {
    try {
      if (pub.is_favourited) {
        await removeFavourite(pub.id);
        toast("Removed from favourites.", "info");
      } else {
        await addFavourite(pub.id);
        toast("Added to favourites!", "success");
      }
      const updated = { ...pub, is_favourited: !pub.is_favourited };
      setPubs(prev => prev.map(p => p.id === pub.id ? updated : p));
      if (selected?.id === pub.id) setSelected(updated);
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    }
  }

  const filtered = pubs.filter(p => {
    if (modeFilter !== "all" && p.mode !== modeFilter) return false;
    if (minCells && p.cell_count < parseInt(minCells)) return false;
    if (maxCells && p.cell_count > parseInt(maxCells)) return false;
    const q = search.toLowerCase();
    return !q || p.headline.toLowerCase().includes(q) ||
      p.description.toLowerCase().includes(q) || p.username.toLowerCase().includes(q);
  });

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2 className="page-title">Explore</h2>
          <p className="page-subtitle">Discover published analyses from the community</p>
        </div>
        <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
          {pubs.length} publication{pubs.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Search + Filters */}
      {pubs.length > 0 && (
        <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap" }}>
          <input className="field-input" style={{ flex: "1 1 200px", maxWidth: 300 }}
            placeholder="Search headline, description or author…"
            value={search} onChange={e => setSearch(e.target.value)} />
          <CustomSelect
            value={modeFilter}
            onChange={v => setModeFilter(v)}
            options={[
              { value: "all", label: "All modes" },
              { value: "model", label: "Model only" },
              { value: "fallback-demo", label: "Fallback only" },
            ]}
          />
          <input className="field-input" style={{ width: 110 }} type="number" placeholder="Min cells"
            value={minCells} onChange={e => setMinCells(e.target.value)} />
          <input className="field-input" style={{ width: 110 }} type="number" placeholder="Max cells"
            value={maxCells} onChange={e => setMaxCells(e.target.value)} />
          {(search || modeFilter !== "all" || minCells || maxCells) && (
            <button className="btn-ghost" onClick={() => { setSearch(""); setModeFilter("all"); setMinCells(""); setMaxCells(""); }}>
              Clear ✕
            </button>
          )}
        </div>
      )}

      {loading && <div className="status-line"><div className="spinner" /> Loading…</div>}
      {!loading && pubs.length === 0 && (
        <div className="empty-state">
          <p>No publications yet. Be the first to <a href="/analyze" className="link-btn">publish an analysis</a>!</p>
        </div>
      )}
      {!loading && pubs.length > 0 && filtered.length === 0 && (
        <div className="empty-state"><p>No publications match your filters.</p></div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 20 }}>
        {filtered.map(pub => (
          <PublicationCard key={pub.id} pub={pub} onFavouriteToggle={handleFavouriteToggle} onOpen={setSelected} />
        ))}
      </div>

      {selected && (
        <PublicationModal pub={selected} onClose={() => setSelected(null)} onFavouriteToggle={handleFavouriteToggle} />
      )}
    </div>
  );
}
