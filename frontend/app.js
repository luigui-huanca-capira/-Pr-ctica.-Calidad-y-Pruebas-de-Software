const API_BASE = "http://127.0.0.1:8000/api";

const kpiAccidentes = document.getElementById("kpiAccidentes");
const kpiFallecidos = document.getElementById("kpiFallecidos");
const kpiHeridos = document.getElementById("kpiHeridos");
const kpiDepartamentos = document.getElementById("kpiDepartamentos");
const heroAccidentes = document.getElementById("heroAccidentes");
const statDep = document.getElementById("statDep");
const topDepartamento = document.getElementById("topDepartamento");
const topModalidad = document.getElementById("topModalidad");

let map;
let geoLayer;

const DEPARTAMENTO_EQUIV = {
  "LIMA METROPOLITANA": "LIMA",
  "CALLAO": "CALLAO",
  "CUZCO": "CUSCO",
  "MADRE DE DIOS": "MADRE DE DIOS",
  "LA LIBERTAD": "LA LIBERTAD"
};

function normalizeName(name = "") {
  return name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .toUpperCase();
}

function normalizeDepartamento(name = "") {
  const dep = normalizeName(name);
  return DEPARTAMENTO_EQUIV[dep] || dep;
}

function mapCategory(value, q1, q2) {
  if (value <= 0) return "nodata";
  if (value >= q2) return "alta";
  if (value >= q1) return "media";
  return "baja";
}

function getColor(cat) {
  if (cat === "alta") return "#e74c3c";
  if (cat === "media") return "#f39c12";
  if (cat === "baja") return "#1abc9c";
  return "#5d6d7e";
}

function setText(node, value) {
  if (node) node.textContent = value;
}

async function fetchSummary() {
  const res = await fetch(`${API_BASE}/dashboard/summary?_=${Date.now()}`, {
    cache: "no-store"
  });
  if (!res.ok) throw new Error("No se pudo obtener summary");
  return res.json();
}

function renderKpis(summary) {
  const k = summary.kpis || {};
  const porDepartamento = summary.por_departamento || [];
  const porModalidad = summary.por_modalidad || [];
  const departamentos = porDepartamento.length;

  setText(kpiAccidentes, (k.total_accidentes ?? 0).toLocaleString("es-PE"));
  setText(kpiFallecidos, (k.total_fallecidos ?? 0).toLocaleString("es-PE"));
  setText(kpiHeridos, (k.total_heridos ?? 0).toLocaleString("es-PE"));
  setText(kpiDepartamentos, departamentos.toLocaleString("es-PE"));
  setText(heroAccidentes, (k.total_accidentes ?? 0).toLocaleString("es-PE"));
  setText(statDep, departamentos.toLocaleString("es-PE"));

  const dep = porDepartamento[0];
  const mod = porModalidad[0];
  setText(topDepartamento, dep ? `${dep.departamento} · ${Number(dep.accidentes || 0).toLocaleString("es-PE")}` : "Sin datos");
  setText(topModalidad, mod ? `${mod.modalidad} · ${Number(mod.accidentes || 0).toLocaleString("es-PE")}` : "Sin datos");
}

function buildIncidenceMapData(summary) {
  const rows = summary.por_departamento || [];
  const values = rows.map(r => Number(r.accidentes || 0)).filter(v => Number.isFinite(v));
  const sorted = [...values].sort((a, b) => a - b);

  const q1 = sorted.length ? sorted[Math.floor(sorted.length * 0.33)] : 0;
  const q2 = sorted.length ? sorted[Math.floor(sorted.length * 0.66)] : 0;

  const byDep = {};
  rows.forEach((r) => {
    const dep = normalizeDepartamento(r.departamento || "");
    const val = Number(r.accidentes || 0);
    byDep[dep] = {
      accidentes: val,
      categoria: mapCategory(val, q1, q2)
    };
  });

  return byDep;
}

async function initMap(byDep) {
  if (!map) {
    map = L.map("mapPeru", { zoomControl: true }).setView([-9.19, -75.0152], 5);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);
  }

  const geoRes = await fetch("https://raw.githubusercontent.com/juaneladio/peru-geojson/master/peru_departamental_simple.geojson");
  const geojson = await geoRes.json();

  console.info("Datos reales cargados para mapa:", {
    cusco: byDep.CUSCO?.accidentes,
    lima: byDep.LIMA?.accidentes,
    totalDepartamentos: Object.keys(byDep).length
  });

  if (geoLayer) {
    map.removeLayer(geoLayer);
  }

  geoLayer = L.geoJSON(geojson, {
    style: (feature) => {
      const depName = normalizeDepartamento(feature?.properties?.NOMBDEP || "");
      const info = byDep[depName] || { categoria: "nodata" };
      return {
        fillColor: getColor(info.categoria),
        weight: 1.2,
        opacity: 1,
        color: "#173257",
        fillOpacity: 0.7
      };
    },
    onEachFeature: (feature, layer) => {
      const depName = normalizeDepartamento(feature?.properties?.NOMBDEP || "");
      const info = byDep[depName] || { accidentes: 0, categoria: "nodata" };
      const catLabel = info.categoria === "alta"
        ? "Alta incidencia"
        : info.categoria === "media"
          ? "Media incidencia"
          : info.categoria === "baja"
            ? "Baja incidencia"
            : "Sin dato";

      layer.bindPopup(`
        <strong>${feature?.properties?.NOMBDEP || "Departamento"}</strong><br/>
        Accidentes: ${Number(info.accidentes || 0).toLocaleString("es-PE")}<br/>
        Nivel: ${catLabel}
      `);
    }
  }).addTo(map);
}

async function init() {
  try {
    const health = await fetch(`${API_BASE}/health`);
    if (!health.ok) throw new Error("Backend no disponible");

    const summary = await fetchSummary();
    renderKpis(summary);
    const byDep = buildIncidenceMapData(summary);
    await initMap(byDep);
  } catch (error) {
    console.error(error);
    alert("No se pudo cargar el sistema. Verifica backend en http://127.0.0.1:8000");
  }
}

init();
