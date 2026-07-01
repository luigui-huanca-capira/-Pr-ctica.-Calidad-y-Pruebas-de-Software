const API_BASE = "http://127.0.0.1:8000/api";

let chartLine = null;
let chartDonut = null;
let chartBar = null;

function destroyChart(c) {
  try { if (c) c.destroy(); } catch (_) {}
}

function safeNumber(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

function heatmapMatrixFromHeatmapTemporal(items) {
  // items: [{dia_semana, hora, accidentes}, ...]
  const diasOrden = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];
  const x = [...Array(24).keys()];
  const y = diasOrden;

  const map = new Map();
  (items || []).forEach(it => {
    const dia = it.dia_semana;
    const h = Number(it.hora);
    const acc = safeNumber(it.accidentes);
    if (!dia || !Number.isFinite(h)) return;
    map.set(`${dia}|${h}`, acc);
  });

  const matrix = y.map(dia => x.map(h => map.get(`${dia}|${h}`) ?? 0));
  return { x, y, matrix };
}

function renderHeatmap(items) {
  // Dependemos de Plotly si está cargado; si no, mostramos tabla mínima.
  const container = document.getElementById("heatmapTemporal");
  if (!container) return;

  const plotlyReady = typeof Plotly !== "undefined";
  if (!plotlyReady) {
    container.innerHTML = "<div style='color:rgba(255,255,255,0.6);font-size:12px'>Plotly no cargó. Heatmap no disponible.</div>";
    return;
  }

  const { x, y, matrix } = heatmapMatrixFromHeatmapTemporal(items);

  Plotly.newPlot(
    "heatmapTemporal",
    [{
      z: matrix,
      x,
      y,
      type: "heatmap",
      colorscale: "YlOrRd",
      showscale: true
    }],
    {
      paper_bgcolor: "#0d1f3c",
      plot_bgcolor: "#0d1f3c",
      font: { color: "#e5e7eb" },
      margin: { t: 30, r: 10, b: 40, l: 70 },
      xaxis: { tickfont: { size: 10 } },
      yaxis: { tickfont: { size: 10 } }
    },
    { responsive: true }
  );
}

function renderKpis(summary) {
  const k = summary.kpis || {};
  // En este prototipo usaremos los 4 KPIs del diseño original
  const kpis = [
    { id: "kpiTotalAcc", val: safeNumber(k.total_accidentes) },
    { id: "kpiFallecidos", val: safeNumber(k.total_fallecidos) },
    { id: "kpiHeridos", val: safeNumber(k.total_heridos) },
  ];

  const setText = (id, v) => {
    const el = document.getElementById(id);
    if (el) el.textContent = v.toLocaleString("es-PE");
  };

  setText("kpiTotalAcc", safeNumber(k.total_accidentes));
  setText("kpiFallecidos", safeNumber(k.total_fallecidos));
  setText("kpiHeridos", safeNumber(k.total_heridos));

  // Departamentos afectados: estimación por cantidad de filas en por_departamento
  const depRows = summary.por_departamento || [];
  setText("kpiDepartamentos", depRows.length ? depRows.length.toLocaleString("es-PE") : "0");
}

function renderLine(series) {
  const labels = (series || []).map(x => x.periodo);
  const values = (series || []).map(x => safeNumber(x.accidentes));

  destroyChart(chartLine);
  const canvas = document.getElementById("lineChart");
  if (!canvas) return;

  chartLine = new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Accidentes",
        data: values,
        borderColor: "#2a78d6",
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: "#2a78d6",
        fill: true,
        backgroundColor: "rgba(42,120,214,0.08)",
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { mode: "index", intersect: false } },
      scales: {
        x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "rgba(255,255,255,0.4)", font: { size: 10 } } },
        y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "rgba(255,255,255,0.4)", font: { size: 10 } } }
      }
    }
  });
}

function renderDonut(items) {
  const rows = items || [];
  // Tomamos top 4
  const top = rows.slice(0, 4);
  const labels = top.map(x => x.modalidad);
  const values = top.map(x => safeNumber(x.accidentes));

  destroyChart(chartDonut);
  const canvas = document.getElementById("donutChart");
  if (!canvas) return;

