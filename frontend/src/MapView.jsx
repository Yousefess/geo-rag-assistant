import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import { useEffect, useState } from "react";
import axios from "axios";
import "leaflet/dist/leaflet.css";
import { API_BASE_URL } from "./config";

const LONDON_CENTER = [51.5074, -0.1278];

function FlyToBorough({ geoData, selectedBorough }) {
  const map = useMap();

  useEffect(() => {
    if (!geoData || !selectedBorough) {
      map.flyTo(LONDON_CENTER, 10, { duration: 1 });
      return;
    }
    const feature = geoData.features.find(
      (f) => f.properties.name === selectedBorough,
    );
    if (!feature) return;

    const coords = [];
    const collect = (c) => {
      if (typeof c[0] === "number") coords.push(c);
      else c.forEach(collect);
    };
    collect(feature.geometry.coordinates);
    const lats = coords.map((c) => c[1]);
    const lngs = coords.map((c) => c[0]);
    const bounds = [
      [Math.min(...lats), Math.min(...lngs)],
      [Math.max(...lats), Math.max(...lngs)],
    ];
    map.flyToBounds(bounds, { padding: [40, 40], duration: 1 });
  }, [selectedBorough, geoData, map]);

  return null;
}

function MapView({ selectedBorough }) {
  const [geoData, setGeoData] = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/boroughs/geojson/all`).then((response) => {
      setGeoData(response.data);
    });
  }, []);

  const getColors = () => {
    const root = getComputedStyle(document.documentElement);
    return {
      default: root.getPropertyValue("--map-default").trim() || "#38bdf8",
      selected: root.getPropertyValue("--map-selected").trim() || "#f59e0b",
    };
  };

  const style = (feature) => {
    const { default: defaultColor, selected: selectedColor } = getColors();
    const isSelected = feature.properties.name === selectedBorough;
    return {
      color: isSelected ? selectedColor : defaultColor,
      weight: isSelected ? 3 : 1.5,
      fillColor: isSelected ? selectedColor : defaultColor,
      fillOpacity: isSelected ? 0.35 : 0.12,
    };
  };

  const onEachFeature = (feature, layer) => {
    const { name, population } = feature.properties;
    layer.bindPopup(
      `<strong>${name}</strong><br/>Population: ${population?.toLocaleString() ?? "N/A"}`,
    );
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
        <GeoJSON
          key={selectedBorough}
          data={geoData}
          style={style}
          onEachFeature={onEachFeature}
        />
      )}
      <FlyToBorough geoData={geoData} selectedBorough={selectedBorough} />
    </MapContainer>
  );
}

export default MapView;
