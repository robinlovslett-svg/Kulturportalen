let SURVEY = null;
let itemCounter = 0;
const itemOrder = [];

async function loadSurvey() {
  const res = await fetch("/api/survey");
  SURVEY = await res.json();
  buildQuestions();
}

function buildQuestions() {
  const container = document.getElementById("questions");
  for (const groupKey of ["tl", "fk"]) {
    const group = SURVEY[groupKey];
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `<h2>${group.title}</h2><p class="muted">${group.instruction}</p>` +
      `<div class="scale-labels"><span>1 = Helt uenig</span><span>5 = Helt enig</span></div>`;
    for (const [dimKey, dim] of Object.entries(group.dimensions)) {
      for (const text of dim.items) {
        itemCounter++;
        itemOrder.push(itemCounter);
        const q = document.createElement("div");
        q.className = "q";
        q.innerHTML = `<p>${itemCounter}. ${text}</p>`;
        const row = document.createElement("div");
        row.className = "likert";
        for (let v = 1; v <= 5; v++) {
          row.innerHTML += `<label><input type="radio" name="q${itemCounter}" value="${v}" required> ${v}</label>`;
        }
        q.appendChild(row);
        card.appendChild(q);
      }
    }
    container.appendChild(card);
  }
}

document.getElementById("startBtn").addEventListener("click", () => {
  document.getElementById("landing").hidden = true;
  const hero = document.querySelector(".hero, .hero-landing");
  if (hero) hero.hidden = true;
  document.body.classList.remove("landing-body");
  document.getElementById("surveyWrap").hidden = false;
  window.scrollTo(0, 0);
});

document.getElementById("surveyForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const err = document.getElementById("formError");
  err.hidden = true;
  const answers = {};
  for (const n of itemOrder) {
    const sel = document.querySelector(`input[name="q${n}"]:checked`);
    if (!sel) {
      err.textContent = `Vennligst svar på påstand ${n} av ${itemOrder.length}.`;
      err.hidden = false;
      sel?.closest(".q")?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    answers[n] = parseInt(sel.value, 10);
  }
  const payload = {
    answers,
    gender: document.getElementById("gender").value,
    tenure: document.getElementById("tenure").value,
    leadership_role: document.getElementById("leadership_role").value,
    avdeling: document.getElementById("avdeling").value,
    comment: document.getElementById("comment").value,
  };
  const btn = document.getElementById("submitBtn");
  btn.disabled = true;
  btn.textContent = "Sender…";
  try {
    const res = await fetch("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Noe gikk galt");
    window.location.href = "/result?id=" + data.id;
  } catch (e2) {
    err.textContent = e2.message;
    err.hidden = false;
    btn.disabled = false;
    btn.textContent = "Send inn svar";
  }
});

loadSurvey();
