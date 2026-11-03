import { useState } from "react";
import MapView from "./MapView";
import ChatPanel from "./ChatPanel";

function App() {
  const [selectedBorough, setSelectedBorough] = useState(null);

  return (
    <div style={{ display: "flex", height: "100vh", width: "100vw" }}>
      <div style={{ flex: 1 }}>
        <MapView selectedBorough={selectedBorough} />
      </div>
      <ChatPanel onBoroughMatch={setSelectedBorough} />
    </div>
  );
}

export default App;
