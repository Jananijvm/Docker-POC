import { useEffect, useState } from "react";

// API URL is set at build time (VITE_API_URL); defaults to local Flask
const API = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function App() {
  const [items, setItems] = useState([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const res = await fetch(`${API}/items`);
      if (!res.ok) throw new Error(`API returned ${res.status}`);
      setItems(await res.json());
      setError("");
    } catch (e) {
      setError(`Cannot reach API: ${e.message}`);
    }
  };

  const add = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    await fetch(`${API}/items`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    setName("");
    load();
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div style={{ fontFamily: "sans-serif", maxWidth: 500, margin: "40px auto" }}>
      <h1>Docker POC</h1>
      <p>React → Flask → MySQL</p>

      <form onSubmit={add} style={{ display: "flex", gap: 8 }}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter item name"
          style={{ flex: 1, padding: 8 }}
        />
        <button type="submit" style={{ padding: "8px 16px" }}>Add</button>
      </form>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <ul>
        {items.map((i) => (
          <li key={i.id}>{i.name}</li>
        ))}
      </ul>
    </div>
  );
}
