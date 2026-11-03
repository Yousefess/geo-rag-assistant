import { useState, useEffect } from "react";
import MapView from "./MapView";
import ChatPanel from "./ChatPanel";

function App() {
  const [selectedBorough, setSelectedBorough] = useState(null);
  const [theme, setTheme] = useState("dark");
  const [autoSelect, setAutoSelect] = useState(true);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const handleBoroughMatch = (name) => {
    if (autoSelect) setSelectedBorough(name);
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        width: "100vw",
      }}
    >
      <header style={{ ...styles.header, borderColor: "var(--border)" }}>
        <h1 style={styles.title}>GeoRAG London</h1>
        <span style={{ ...styles.subtitle, color: "var(--text-muted)" }}>
          AI planning assistant · The London Plan 2021
        </span>

        <div style={styles.controls}>
          <label style={{ ...styles.toggleLabel, color: "var(--text-muted)" }}>
            <input
              type="checkbox"
              checked={autoSelect}
              onChange={(e) => setAutoSelect(e.target.checked)}
              style={{ accentColor: "var(--accent-strong)" }}
            />
            Auto-select borough
          </label>

          {selectedBorough && (
            <button
              onClick={() => setSelectedBorough(null)}
              style={styles.clearButton}
            >
              ✕ {selectedBorough}
            </button>
          )}

          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            style={{
              ...styles.themeSwitch,
              background: theme === "dark" ? "#242a35" : "#e2e5e9",
            }}
          >
            <span
              style={{
                ...styles.themeKnob,
                transform:
                  theme === "dark" ? "translateX(0px)" : "translateX(20px)",
              }}
            >
              {theme === "dark" ? "🌙" : "☀️"}
            </span>
          </button>
        </div>
      </header>

      <div
        style={{
          display: "flex",
          flex: 1,
          overflow: "hidden",
          gap: "16px",
          padding: "16px",
        }}
      >
        <div style={{ ...styles.mapCard, background: "var(--bg-map-wrap)" }}>
          <MapView selectedBorough={selectedBorough} />
        </div>
        <ChatPanel onBoroughMatch={handleBoroughMatch} />
      </div>
    </div>
  );
}

const styles = {
  header: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "14px 20px",
    borderBottom: "1px solid",
  },
  title: {
    fontFamily: "'Sora', sans-serif",
    fontSize: "21px",
    fontWeight: 800,
    color: "var(--accent)",
    letterSpacing: "-0.03em",
  },
  subtitle: {
    fontFamily: "'Inter', sans-serif",
    fontSize: "13px",
  },
  controls: {
    marginLeft: "auto",
    display: "flex",
    alignItems: "center",
    gap: "14px",
  },
  toggleLabel: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    fontSize: "13px",
    cursor: "pointer",
  },
  clearButton: {
    padding: "6px 12px",
    background: "var(--accent-strong)",
    color: "white",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "12px",
    fontWeight: 600,
  },
  themeSwitch: {
    width: "44px",
    height: "24px",
    borderRadius: "999px",
    border: "none",
    cursor: "pointer",
    position: "relative",
    padding: "2px",
  },
  themeKnob: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: "20px",
    height: "20px",
    borderRadius: "50%",
    background: "white",
    fontSize: "12px",
    transition: "transform 0.2s ease",
  },
  mapCard: {
    flex: 1,
    position: "relative",
    borderRadius: "16px",
    overflow: "hidden",
    boxShadow: "var(--shadow)",
  },
};

export default App;
