import { useEffect, useState } from "react";
import { getFavourites, removeFavourite, fileUrl, formatDate, type PublicationResponse } from "../api";
import { useToast } from "../contexts/ToastContext";

export default function FavouritesPage() {
  const { toast } = useToast();
  const [pubs, setPubs] = useState<PublicationResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getFavourites()
      .then(setPubs)
      .catch(e => toast(e instanceof Error ? e.message : String(e), "error"))
      .finally(() => setLoading(false));
  }, []);

  async function handleRemove(pub: PublicationResponse) {
    try {
      await removeFavourite(pub.id);
      setPubs(prev => prev.filter(p => p.id !== pub.id));
      toast("Removed from favourites.", "info");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2 className="page-title">Favourites</h2>
          <p className="page-subtitle">Analyses you saved for later</p>
        </div>
        <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
          {pubs.length} saved
        </span>
      </div>

      {loading && <div className="status-line"><div className="spinner" /> Loading…</div>}

      {!loading && pubs.length === 0 && (
        <div className="empty-state">
          <p>
            No favourites yet.{" "}
            <a href="/explore" className="link-btn">Browse Explore</a> and save analyses that interest you.
          </p>
        </div>
      )}

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
        gap: 20,
      }}>
        {pubs.map(pub => (
          <div key={pub.id} className="card" style={{ padding: 0, overflow: "hidden" }}>
            {/* Image */}
            <div style={{ height: 160, overflow: "hidden", background: "#0a0a14", position: "relative" }}>
              <img
                src={fileUrl(pub.overlay_url)}
                alt={pub.headline}
                style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.9 }}
              />
              <button
                onClick={() => handleRemove(pub)}
                style={{
                  position: "absolute", top: 10, left: 10,
                  background: "rgba(0,0,0,0.6)", border: "none", borderRadius: 20,
                  padding: "6px 10px", cursor: "pointer", fontSize: 16, color: "#f87171",
                }}
                title="Remove from favourites"
              >
                ♥
              </button>
            </div>

            {/* Content */}
            <div style={{ padding: 16 }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 6 }}>{pub.headline}</div>
              <div style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.5, marginBottom: 12 }}>
                {pub.description.length > 100 ? pub.description.slice(0, 100) + "…" : pub.description}
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "var(--text-muted)" }}>
                <span>🔬 <strong style={{ color: "var(--text)" }}>{pub.cell_count}</strong> cells · {pub.username}</span>
                <span style={{ fontSize: 11 }}>{formatDate(pub.created_at)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
