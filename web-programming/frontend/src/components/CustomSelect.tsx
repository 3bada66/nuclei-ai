import { useEffect, useRef, useState } from "react";

interface Option<T extends string> {
  value: T;
  label: string;
}

interface Props<T extends string> {
  value: T;
  onChange: (value: T) => void;
  options: Option<T>[];
  style?: React.CSSProperties;
}

export default function CustomSelect<T extends string>({ value, onChange, options, style }: Props<T>) {
  const [open, setOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState<number>(-1);
  const ref = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const selected = options.find(o => o.value === value);
  const currentIndex = options.findIndex(o => o.value === value);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  useEffect(() => {
    if (open) setFocusedIndex(currentIndex >= 0 ? currentIndex : 0);
    else setFocusedIndex(-1);
  }, [open, currentIndex]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!open) {
      if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown") {
        e.preventDefault();
        setOpen(true);
      }
      return;
    }
    if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      buttonRef.current?.focus();
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setFocusedIndex(i => Math.min(i + 1, options.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setFocusedIndex(i => Math.max(i - 1, 0));
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (focusedIndex >= 0) {
        onChange(options[focusedIndex].value);
        setOpen(false);
        buttonRef.current?.focus();
      }
    }
  }

  return (
    <div ref={ref} style={{ position: "relative", flex: "0 0 auto", ...style }} onKeyDown={handleKeyDown}>
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setOpen(o => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
          background: "rgba(255,255,255,0.04)",
          border: "1px solid var(--border-hairline)",
          borderRadius: "var(--radius-input)",
          color: "var(--text-primary)",
          fontFamily: "inherit",
          fontSize: 15,
          padding: "10px 12px",
          cursor: "pointer",
          whiteSpace: "nowrap",
          minWidth: 130,
        }}
      >
        {selected?.label ?? value}
        <span style={{ fontSize: 11, opacity: 0.6, marginLeft: 4 }}>▾</span>
      </button>

      {open && (
        <div
          role="listbox"
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            zIndex: 200,
            background: "#1a1a2e",
            border: "1px solid var(--border-hairline)",
            borderRadius: "var(--radius-input)",
            minWidth: "100%",
            boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
            overflow: "hidden",
          }}
        >
          {options.map((opt, i) => (
            <div
              key={opt.value}
              role="option"
              aria-selected={opt.value === value}
              onClick={() => { onChange(opt.value); setOpen(false); buttonRef.current?.focus(); }}
              onMouseEnter={() => setFocusedIndex(i)}
              style={{
                padding: "10px 14px",
                fontSize: 14,
                cursor: "pointer",
                color: opt.value === value ? "var(--accent-violet)" : "var(--text-primary)",
                background: i === focusedIndex
                  ? "rgba(255,255,255,0.08)"
                  : opt.value === value ? "rgba(139,92,246,0.12)" : "transparent",
                transition: "background 0.1s",
              }}
            >
              {opt.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
