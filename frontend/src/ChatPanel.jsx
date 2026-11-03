import { useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import { API_BASE_URL } from "./config";

function ChatPanel({ onBoroughMatch }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    const userMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/geo-chat`, {
        question: userMessage.content,
      });

      const { answer, matched_borough, sources } = response.data;

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: answer, sources },
      ]);
      onBoroughMatch(matched_borough ? matched_borough.name : null);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, something went wrong." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.panel}>
      <div style={styles.messages}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={msg.role === "user" ? styles.userMsg : styles.assistantMsg}
          >
            {msg.role === "assistant" ? (
              <div className="chat-markdown">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            ) : (
              msg.content
            )}
            {msg.sources && (
              <div style={styles.sources}>
                Sources: {msg.sources.join(", ")}
              </div>
            )}
          </div>
        ))}
        {loading && <div style={styles.assistantMsg}>Thinking...</div>}
      </div>

      <form onSubmit={handleSubmit} style={styles.form}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about London planning, e.g. housing in Camden"
          style={styles.input}
        />
        <button type="submit" style={styles.button}>
          Send
        </button>
      </form>
    </div>
  );
}

const styles = {
  panel: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    width: "380px",
    borderLeft: "1px solid var(--border)",
    background: "var(--bg-panel)",
    borderRadius: "16px",
    boxShadow: "var(--shadow)",
    overflow: "hidden",
  },
  messages: {
    flex: 1,
    overflowY: "auto",
    padding: "16px",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  userMsg: {
    alignSelf: "flex-end",
    background: "var(--accent-strong)",
    color: "white",
    padding: "10px 14px",
    borderRadius: "14px",
    maxWidth: "85%",
  },
  assistantMsg: {
    alignSelf: "flex-start",
    background: "var(--border)",
    color: "var(--text)",
    padding: "10px 14px",
    borderRadius: "14px",
    maxWidth: "90%",
  },
  sources: {
    fontSize: "11px",
    color: "var(--text-muted)",
    marginTop: "6px",
  },
  form: {
    display: "flex",
    gap: "8px",
    padding: "14px",
    borderTop: "1px solid var(--border)",
  },
  input: {
    flex: 1,
    padding: "10px 12px",
    border: "1px solid var(--border)",
    borderRadius: "8px",
    background: "var(--bg-input)",
    color: "var(--text)",
  },
  button: {
    padding: "10px 18px",
    background: "var(--accent-strong)",
    color: "white",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: 600,
  },
};

export default ChatPanel;
