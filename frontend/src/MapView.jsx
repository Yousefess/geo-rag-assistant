import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";
import { useEffect, useState } from "react";
import axios from "axios";
import "leaflet/dist/leaflet.css";
import { API_BASE_URL } from "./config";

const LONDON_CENTER = [51.5074, -0.1278];

function MapView({ selectedBorough }) {
  const [geoData, setGeoData] = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/boroughs/geojson/all`).then((response) => {
      setGeoData(response.data);
    });
  }, []);

  const style = (feature) => {
    const isSelected = feature.properties.name === selectedBorough;
    return {
      color: isSelected ? "#ff6b00" : "#2563eb",
      weight: isSelected ? 3 : 1,
      fillOpacity: isSelected ? 0.4 : 0.1,
    };
  };

  return (
    <MapContainer
      center={LONDON_CENTER}
      zoom={10}
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />
      {geoData && (
        <GeoJSON key={selectedBorough} data={geoData} style={style} />
      )}
    </MapContainer>
  );
}

export default MapView;
