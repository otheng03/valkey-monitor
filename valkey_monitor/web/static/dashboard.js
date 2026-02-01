"use strict";

const Dashboard = (() => {
  const MAX_POINTS = 300;

  const CHART_COLORS = {
    blue:   "rgb( 56, 132, 244)",
    green:  "rgb( 63, 185,  80)",
    orange: "rgb(210, 153,  34)",
    red:    "rgb(248,  81,  73)",
    purple: "rgb(163, 113, 247)",
    cyan:   "rgb( 57, 211, 197)",
  };

  const COMMON = {
    responsive: true,
    animation: false,
    interaction: { intersect: false, mode: "index" },
    scales: {
      x: {
        type: "time",
        time: { tooltipFormat: "HH:mm:ss", displayFormats: { second: "HH:mm:ss" } },
        ticks: { color: "#8b949e", maxTicksLimit: 10 },
        grid: { color: "#21262d" },
      },
      y: {
        ticks: { color: "#8b949e" },
        grid: { color: "#21262d" },
      },
    },
    plugins: {
      legend: { labels: { color: "#c9d1d9", boxWidth: 12 } },
    },
  };

  function makeChart(id, title, datasets) {
    const ctx = document.getElementById(id).getContext("2d");
    return new Chart(ctx, {
      type: "line",
      data: { datasets },
      options: {
        ...COMMON,
        plugins: {
          ...COMMON.plugins,
          title: { display: true, text: title, color: "#c9d1d9" },
        },
      },
    });
  }

  function ds(label, color) {
    return { label, data: [], borderColor: color, backgroundColor: color, borderWidth: 1.5, pointRadius: 0, tension: 0.2 };
  }

  let charts = {};

  function createCharts() {
    charts.ops  = makeChart("chart-ops",  "OPS / sec",       [ds("OPS/s",    CHART_COLORS.blue)]);
    charts.cpu  = makeChart("chart-cpu",  "CPU (per sec)",   [ds("CPU user",  CHART_COLORS.green), ds("CPU sys", CHART_COLORS.orange)]);
    charts.mem  = makeChart("chart-mem",  "Valkey Memory (MiB)", [ds("Used", CHART_COLORS.blue), ds("RSS", CHART_COLORS.purple), ds("Peak", CHART_COLORS.red)]);
    charts.frag = makeChart("chart-frag", "Fragmentation Ratio", [ds("Frag", CHART_COLORS.orange)]);
    charts.sys  = makeChart("chart-sys",  "System Memory (MiB)", [ds("Cache", CHART_COLORS.cyan), ds("Buffers", CHART_COLORS.green), ds("Kernel", CHART_COLORS.red)]);
  }

  function pushPoint(snap) {
    const t = new Date(snap.epoch * 1000);

    function add(chart, values) {
      values.forEach((v, i) => {
        chart.data.datasets[i].data.push({ x: t, y: v });
        if (chart.data.datasets[i].data.length > MAX_POINTS) {
          chart.data.datasets[i].data.shift();
        }
      });
      chart.update("none");
    }

    add(charts.ops,  [snap.ops_per_sec]);
    add(charts.cpu,  [snap.cpu_user_per_sec, snap.cpu_sys_per_sec]);
    add(charts.mem,  [snap.used_mib, snap.rss_mib, snap.peak_mib]);
    add(charts.frag, [snap.frag_ratio]);
    add(charts.sys,  [snap.cache_mib, snap.buffers_mib, snap.kernel_mib]);
  }

  function setStatus(connected) {
    const el = document.getElementById("status");
    el.textContent = connected ? "connected" : "disconnected";
    el.className = "status " + (connected ? "connected" : "disconnected");
  }

  function init(interval) {
    createCharts();

    // Backfill from history
    fetch("/api/history")
      .then(r => r.json())
      .then(data => {
        data.forEach(pushPoint);
      })
      .catch(() => {});

    // Live stream via SSE
    const es = new EventSource("/api/stream");
    es.onopen = () => setStatus(true);
    es.onmessage = (e) => {
      const snap = JSON.parse(e.data);
      pushPoint(snap);
    };
    es.onerror = () => setStatus(false);
  }

  return { init };
})();
