const LABELS = {
  gender: { "Kvinne": "Kvinne", "Mann": "Mann", "Annet / ønsker ikke å svare": "Annet" },
  leadership_role: { "Ja": "Med personalansvar", "Nei": "Uten personalansvar" },
};

function bar(label, s, cls) {
  if (!s) return `<div class="bar-row"><div>${label}</div><div></div><div class="bar-val">–</div></div>`;
  const pct = ((s.mean - 1) / 4) * 100;
  const color = s.mean >= 4 ? "var(--good)" : s.mean >= 3 ? "var(--warn)" : "var(--bad)";
  return `<div class="bar-row"><div>${label}</div>
    <div class="bar-track"><div class="bar-fill ${cls || ""}" style="width:${pct}%;background:${color}"></div></div>
    <div class="bar-val">${s.mean.toFixed(2)} (n=${s.n})</div></div>`;
}

function labelOf(group, key) {
  const map = {
    idealisert_inflytelse: "Idealisert innflytelse",
    inspirerende_motivasjon: "Inspirerende motivasjon",
    intellektuell_stimulering: "Intellektuell stimulering",
    "individuell_oppfølging": "Individuell oppfølging",
    psykologisk_trygghet: "Psykologisk trygghet",
    organisasjonens_verdier: "Organisasjonens verdier",
    "støttende_ledelse": "Støttende ledelse",
    engasjement_empowerment: "Engasjement og empowerment",
    "lærende_organisasjon": "Lærende organisasjon",
    prosesstenkning_forbedring: "Prosesstenkning og kontinuerlig forbedring",
  };
  return map[key] || key;
}

async function load(group) {
  const res = await fetch("/api/stats" + (group ? "?group=" + group : ""));
  const d = await res.json();
  if (!d.count) {
    document.getElementById("kpis").innerHTML = '<p class="muted">Ingen svar ennå. Klikk «Fyll med demodata» for å teste rapporten, eller del lenken til forsiden.</p>';
    return;
  }
  document.getElementById("kpis").innerHTML = `
    <div class="kpi"><div class="num">${d.count}</div><div class="lbl">Antall svar</div></div>
    <div class="kpi"><div class="num">${d.tl ? d.tl.mean.toFixed(2) : "–"}</div><div class="lbl">Transformasjonsledelse (1–5)</div></div>
    <div class="kpi"><div class="num">${d.fk ? d.fk.mean.toFixed(2) : "–"}</div><div class="lbl">Forbedringskultur (1–5)</div></div>`;
  document.getElementById("corr").textContent = d.correlation_tl_fk != null
    ? `Pearsons r mellom TL og FK: ${d.correlation_tl_fk} (samvariasjon, ikke kausalitet)` : "";

  document.getElementById("dimsTl").innerHTML =
    Object.entries(d.dimensions.tl).map(([k, s]) => bar(labelOf("tl", k), s)).join("");
  document.getElementById("dimsFk").innerHTML =
    Object.entries(d.dimensions.fk).map(([k, s]) => bar(labelOf("fk", k), s, "fk")).join("");

  // Radar over FK-dimensjoner
  const radarData = Object.entries(d.dimensions.fk).map(([k, s]) => ({ dim: labelOf("fk", k), verdi: s ? s.mean : 0 }));
  const ctx = document.getElementById("radar");
  if (window._radar) window._radar.destroy();
  window._radar = new Chart(ctx, {
    type: "radar",
    data: {
      labels: radarData.map((x) => x.dim),
      datasets: [{
        label: "Alle ansatte",
        data: radarData.map((x) => x.verdi),
        borderColor: "#0e7c7b", backgroundColor: "rgba(14,124,123,0.25)", pointBackgroundColor: "#0e7c7b",
      }],
    },
    options: { scales: { r: { min: 1, max: 5, ticks: { stepSize: 1 } } }, plugins: { legend: { labels: { color: "#5b6b7a" } } } },
  });

  // Gap ledere vs medarbeidere
  document.getElementById("gap").innerHTML = (d.gap || []).map((g) => {
    const pct = Math.min(100, Math.abs(g.gap) / 1.5 * 100);
    const color = g.gap >= 0.3 ? "var(--bad)" : g.gap <= -0.05 ? "var(--accent)" : "#94a3b8";
    return `<div class="bar-row"><div>${g.dim}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${color};margin-left:${g.gap < 0 ? 0 : 0}"></div></div>
      <div class="bar-val">${g.gap >= 0 ? "+" : ""}${g.gap}</div></div>`;
  }).join("");

  // Avdelinger
  const avd = Object.entries(d.avdelinger || {});
  document.getElementById("avdelinger").innerHTML = avd.length
    ? "<table><tr><th>Avdeling</th><th>n</th><th>Trygghet (P9–P10)</th><th>TL</th><th>FK</th><th>Signal</th></tr>" +
      avd.map(([a, v]) => {
        const stille = v.trygghet != null && v.trygghet < 3.2 && v.fk != null && v.fk < 3.4;
        const signal = stille ? '<span class="badge badge-bad">Mistenkelig stille</span>'
          : v.trygghet != null && v.trygghet < 3.4 ? '<span class="badge badge-warn">Følg med</span>'
          : '<span class="badge badge-good">Normalbilde</span>';
        return `<tr><td>${a}</td><td>${v.n}</td><td>${v.trygghet ?? "–"}</td><td>${v.tl ?? "–"}</td><td>${v.fk ?? "–"}</td><td>${signal}</td></tr>`;
      }).join("") + "</table>"
    : '<p class="muted">Ingen avdelingsdata.</p>';

  // Trend
  const trendEl = document.getElementById("trend");
  if (d.trend && d.trend.length) {
    trendEl.innerHTML = "<table><tr><th>Måned</th><th>n</th><th>TL</th><th>FK</th></tr>" +
      d.trend.map(t => `<tr><td>${t.month}</td><td>${t.n}</td><td>${t.tl ?? "–"}</td><td>${t.fk ?? "–"}</td></tr>`).join("") +
      "</table>";
  } else trendEl.innerHTML = '<p class="muted">Ingen data ennå.</p>';

  // Grupper
  const gEl = document.getElementById("groups");
  if (d.groups) {
    gEl.innerHTML = "<table><tr><th>Gruppe</th><th>n</th><th>TL</th><th>FK</th></tr>" +
      Object.entries(d.groups).map(([k, v]) =>
        `<tr><td>${(LABELS[d.group_filter] && LABELS[d.group_filter][k]) || k}</td><td>${v.n}</td><td>${v.tl ?? "–"}</td><td>${v.fk ?? "–"}</td></tr>`
      ).join("") + "</table>";
  } else gEl.innerHTML = '<p class="muted">Velg en variabel over for å sammenligne grupper.</p>';

  // Kommentarer
  const kEl = document.getElementById("kommentarer");
  kEl.innerHTML = (d.kommentarer && d.kommentarer.length)
    ? d.kommentarer.map(k => `<p class="comment">«${k.replace(/</g, "&lt;")}»</p>`).join("")
    : '<p class="muted">Ingen kommentarer ennå.</p>';
}

document.getElementById("groupSelect").addEventListener("change", (e) => load(e.target.value));
document.getElementById("demoBtn").addEventListener("click", async () => {
  const r = await fetch("/api/demo"); await r.json(); load("");
});
load("");
