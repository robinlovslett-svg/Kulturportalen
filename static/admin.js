const LABELS = {
  gender: { "Kvinne": "Kvinne", "Mann": "Mann", "Annet / ønsker ikke å svare": "Annet" },
  tenure: {},
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

async function load(group) {
  const res = await fetch("/api/stats" + (group ? "?group=" + group : ""));
  const d = await res.json();
  if (!d.count) {
    document.getElementById("kpis").innerHTML = '<p class="muted">Ingen svar ennå. Del lenken til forsiden for å samle inn svar.</p>';
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

  const trendEl = document.getElementById("trend");
  if (d.trend.length) {
    trendEl.innerHTML = "<table><tr><th>Måned</th><th>n</th><th>TL</th><th>FK</th></tr>" +
      d.trend.map(t => `<tr><td>${t.month}</td><td>${t.n}</td><td>${t.tl ?? "–"}</td><td>${t.fk ?? "–"}</td></tr>`).join("") +
      "</table>";
  } else trendEl.innerHTML = '<p class="muted">Ingen data ennå.</p>';

  const gEl = document.getElementById("groups");
  if (d.groups) {
    gEl.innerHTML = "<table><tr><th>Gruppe</th><th>n</th><th>TL</th><th>FK</th></tr>" +
      Object.entries(d.groups).map(([k, v]) =>
        `<tr><td>${(LABELS[d.group_filter] && LABELS[d.group_filter][k]) || k}</td><td>${v.n}</td><td>${v.tl ?? "–"}</td><td>${v.fk ?? "–"}</td></tr>`
      ).join("") + "</table>";
  } else gEl.innerHTML = '<p class="muted">Velg en variabel over for å sammenligne grupper.</p>';
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

document.getElementById("groupSelect").addEventListener("change", (e) => load(e.target.value));
load("");
