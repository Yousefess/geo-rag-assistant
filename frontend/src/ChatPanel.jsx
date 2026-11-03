import { useState } from "react";
import axios from "axios";
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

      const { answer, matched_borough } = response.data;

      setMessages((prev) => [...prev, { role: "assistant", content: answer }]);
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
            {msg.content}
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
    width: "360px",
    borderLeft: "1px solid #ddd",
    background: "white",
  },
  messages: {
    flex: 1,
    overflowY: "auto",
    padding: "12px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  userMsg: {
    alignSelf: "flex-end",
    background: "#2563eb",
    color: "white",
    padding: "8px 12px",
    borderRadius: "12px",
    maxWidth: "80%",
  },
  assistantMsg: {
    alignSelf: "flex-start",
    background: "#f1f1f1",
    color: "#111",
    padding: "8px 12px",
    borderRadius: "12px",
    maxWidth: "80%",
    whiteSpace: "pre-wrap",
  },
  form: {
    display: "flex",
    gap: "8px",
    padding: "12px",
    borderTop: "1px solid #ddd",
  },
  input: {
    flex: 1,
    padding: "8px",
    border: "1px solid #ccc",
    borderRadius: "6px",
  },
  button: {
    padding: "8px 16px",
    background: "#2563eb",
    color: "white",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
  },
};

export default ChatPanel;
