import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getUserPublications, addFavourite, removeFavourite, fileUrl, formatDate, type PublicationResponse } from "../api";
import { useToast } from "../contexts/ToastContext";

export default function UserProfilePage() {
  const { username } = useParams<{ username: string }>();
  const { toast } = useToast();
  const [pubs, setPubs] = useState<PublicationResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!username) return;
    getUserPublications(username)
      .then(setPubs)
      .catch(e => toast(e instanceof Error ? e.message : String(e), "error"))
      .finally(() => setLoading(false));
  }, [username]);

  async function handleFav(pub: PublicationResponse) {
    try {
      if (pub.is_favourited) {
        await removeFavourite(pub.id);
        toast("Removed from favourites.", "info");
      } else {
        await addFavourite(pub.id);
        toast("Saved to favourites!", "success");
      }
      setPubs(prev => prev.map(p => p.id === pub.id ? { ...p, is_favourited: !p.is_favourited } : p));
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div style={{ fontSize: 48, fontWeight: 700, lineHeight: 1, marginBottom: 8 }}>
            {username?.[0]?.toUpperCase()}
          </div>
          <h2 className="page-title">{username}</h2>
          <p className="page-subtitle">{pubs.length} publication{pubs.length !== 1 ? "s" : ""}</p>
        </div>
      </div>

      {loading && <div className="status-line"><div className="spinner" /> Loading…</div>}

      {!loading && pubs.length === 0 && (
        <div className="empty-state"><p>This user hasn't published any analyses yet.</p></div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 20 }}>
        {pubs.map(pub => (
          <div key={pub.id} className="card" style={{ padding: 0, overflow: "hidden" }}>
            <div style={{ height: 160, overflow: "hidden", background: "#0a0a14", position: "relative" }}>
              <img src={fileUrl(pub.overlay_url)} alt={pub.headline}
                style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.9 }} />
              <button
                onClick={() => handleFav(pub)}
                style={{
                  position: "absolute", top: 10, left: 10,
                  background: "rgba(0,0,0,0.6)", border: "none", borderRadius: 20,
                  padding: "6px 10px", cursor: "pointer", fontSize: 16,
                  color: pub.is_favourited ? "#f87171" : "#888",
                }}
              >{pub.is_favourited ? "♥" : "♡"}</button>
            </div>
            <div style={{ padding: 16 }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 6 }}>{pub.headline}</div>
              <div style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.5, marginBottom: 10 }}>
                {pub.description.length > 100 ? pub.description.slice(0, 100) + "…" : pub.description}
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "var(--text-muted)" }}>
                <span>🔬 <strong style={{ color: "var(--text)" }}>{pub.cell_count}</strong> cells</span>
                <span style={{ fontSize: 11 }}>{formatDate(pub.created_at)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
