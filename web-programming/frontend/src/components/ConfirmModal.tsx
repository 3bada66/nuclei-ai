import { createContext, useCallback, useContext, useState } from "react";

interface ConfirmState {
  message: string;
  resolve: (ok: boolean) => void;
}

interface ConfirmContextValue {
  confirm: (message: string) => Promise<boolean>;
}

const ConfirmContext = createContext<ConfirmContextValue | null>(null);

export function ConfirmProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<ConfirmState | null>(null);

  const confirm = useCallback((message: string): Promise<boolean> => {
    return new Promise(resolve => {
      setState({ message, resolve });
    });
  }, []);

  function answer(ok: boolean) {
    state?.resolve(ok);
    setState(null);
  }

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}
      {state && (
        <div style={{
          position: "fixed", inset: 0,
          background: "rgba(0,0,0,0.6)",
          display: "flex", alignItems: "center", justifyContent: "center",
          zIndex: 10000,
        }}
          onClick={() => answer(false)}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: "var(--panel-bg, #1e1e2e)",
              border: "1px solid var(--border, #2a2a3a)",
              borderRadius: 12,
              padding: "28px 32px",
              maxWidth: 380,
              width: "90%",
              boxShadow: "0 8px 40px rgba(0,0,0,0.5)",
            }}
          >
            <p style={{ fontSize: 15, marginBottom: 24, lineHeight: 1.5 }}>
              {state.message}
            </p>
            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
              <button className="btn btn-secondary" onClick={() => answer(false)}>
                Cancel
              </button>
              <button
                className="btn"
                style={{ background: "var(--accent-coral, #ff6b6b)", borderColor: "var(--accent-coral, #ff6b6b)" }}
                onClick={() => answer(true)}
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

export function useConfirm() {
  const ctx = useContext(ConfirmContext);
  if (!ctx) throw new Error("useConfirm must be used inside ConfirmProvider");
  return ctx.confirm;
}
