/* POLIS Case Study 2 — study shell + spatial pin page.
   Amendment 2026-08-25: two-step record check (fidelity locked before
   correction), per-event timestamps, disconnect/resume, compliant screener
   with 1 km catchment display, reject option, embedded PIS/debrief.
   Amendment 2026-08-27: screener exports not_team_member (from the existing
   team-membership checkbox); export schema case2-v2 -> case2-v3.
   Amendment 2026-08-28 (v3.1): display-layer i18n via i18n.js — the
   participant-code prefix selects the language (SUZ -> zh-CN, LON/CHI ->
   en). Every exported field name and value stays canonical English
   (schema unchanged: case2-v3); category options now carry explicit
   canonical `value` attributes so translated labels never enter the data.
   See CHANGELOG_amendment.md. Export schema: case2-v3.
   Data capture is local: autosaved to localStorage, exported as one JSON
   per participant that maps 1:1 onto the case2_kit templates. */

const I18N = window.CASE2_I18N;
const t = I18N.t;

/* canonical export values (frozen category list) + display-label keys */
const CATS = ["access & mobility", "shade & comfort", "play & activity",
  "rest & seating", "planting & nature", "safety & lighting", "other"];
const CAT_KEYS = ["cat_access", "cat_shade", "cat_play", "cat_rest",
  "cat_planting", "cat_safety", "cat_other"];
const catLabel = (v) => t(CAT_KEYS[CATS.indexOf(v)]);

const S = {                       // session state
  code: null, city: null, order: null, t0: null,
  step: "consent", stage: 0,      // stage: 0 = first mode, 1 = second mode
  screener: {}, responses: {}, comprehension: {}, experience: {},
  events: {},                     // named per-event ISO timestamps (SOP §5)
  pending: null,                  // mode awaiting record fidelity/confirmation
  tele: {map_moves: 0, zoom_changes: 0, pin_repositions: 0,
         map_opened_at: null, first_pin_ms: null, zoom_final: null},
  map: null, pin: null, geo: null, trace: null, rand: null,
};

const $ = (q) => document.querySelector(q);
const nowISO = () => new Date().toISOString();
/* first occurrence wins so resumed sessions keep original event times */
const ev = (name) => { if (!S.events[name]) S.events[name] = nowISO(); save(); };

const show = (step) => {
  S.step = step;
  document.querySelectorAll("main section").forEach(
    (s) => s.hidden = s.dataset.step !== step);
  window.scrollTo(0, 0);
  $("#progress").textContent = stepLabel(step);
  save();
};
const stepLabel = (s) =>
  (s === "ineligible" || !I18N.items[`step_${s}`]) ? "" : t(`step_${s}`);

/* language is selected by the participant-code prefix (SUZ -> zh) */
function setLang(lang) {
  if (I18N.lang !== lang) I18N.apply(lang);
  relabelCats();
  if ($("#progress").textContent) $("#progress").textContent = stepLabel(S.step);
}
function relabelCats() {
  for (const sel of ["#t_cat", "#s_cat"])
    for (const o of document.querySelectorAll(`${sel} option`))
      o.textContent = catLabel(o.value);
}

const save = () => { try {
  if (S.step === "ineligible") return;      // retain nothing for ineligible
  localStorage.setItem("polis_case2",
    JSON.stringify(S, (k, v) =>
    ["map", "pin", "pinMarker", "geo", "trace", "rand"].includes(k)
      ? undefined : v));
} catch (e) {} };
const wipe = () => { try { localStorage.removeItem("polis_case2"); } catch (e) {} };

/* ---------- likert widgets ---------- */
function likert(el, onSel) {
  el.innerHTML = "";
  for (let i = 1; i <= 7; i++) {
    const b = document.createElement("button");
    b.textContent = i;
    b.onclick = () => {
      el.querySelectorAll("button").forEach((x) => x.classList.remove("sel"));
      b.classList.add("sel");
      el.dataset.value = i;
      if (onSel) onSel(i);
    };
    el.appendChild(b);
  }
}

/* ---------- consent + screener ---------- */
CATS.forEach((c) => {
  for (const sel of ["#t_cat", "#s_cat"]) {
    const o = document.createElement("option");
    o.value = c;                  // canonical export value, never translated
    o.textContent = catLabel(c);  // display label follows the session language
    $(sel).appendChild(o);
  }
});
I18N.apply(I18N.lang);            // render from the string table once at load

$("#c_consent").addEventListener("change", (e) => {
  if (e.target.checked) ev("consent_given");
});

/* 1 km eligibility catchment preview once a listed code is entered (SOP §2).
   Drawn on a canvas straight from the frozen site.geojson: works offline. */
$("#c_code").addEventListener("input", async () => {
  const code = $("#c_code").value.trim().toUpperCase();
  setLang(I18N.langForCode(code));   // SUZ prefix -> zh, otherwise en
  if (!/^[A-Z]{3}-[A-Z0-9]{3,4}$/.test(code)) return;
  if (!S.rand)
    S.rand = await fetch("./data/randomization.json").then((r) => r.json());
  const slot = S.rand.find((r) => r.participant_code === code);
  if (!slot) { $("#catchment_wrap").hidden = true; return; }
  const geo = await fetch(`./data/${slot.city}/site.geojson`)
    .then((r) => r.json());
  drawCatchment(geo);
  $("#catchment_wrap").hidden = false;
});

function drawCatchment(geo) {
  const canvas = $("#catchment_canvas");
  const W = canvas.width = 280, H = canvas.height = 280;
  const ctx = canvas.getContext("2d");
  const c = geo.properties.center;
  const kx = 111320 * Math.cos(c[1] * Math.PI / 180), ky = 110574;
  const R = 1000;                                    // metres
  const scale = (Math.min(W, H) / 2 - 14) / R;       // px per metre
  const px = (p) => [W / 2 + (p[0] - c[0]) * kx * scale,
                     H / 2 - (p[1] - c[1]) * ky * scale];
  ctx.clearRect(0, 0, W, H);
  ctx.beginPath();
  ctx.arc(W / 2, H / 2, R * scale, 0, 2 * Math.PI);
  ctx.fillStyle = "rgba(104,151,109,0.13)"; ctx.fill();
  ctx.strokeStyle = "#68976d"; ctx.lineWidth = 2; ctx.stroke();
  ctx.setLineDash([4, 3]); ctx.strokeStyle = "#2f2f31"; ctx.lineWidth = 1.6;
  for (const f of geo.features) {
    if (f.properties.layer !== "site_boundary") continue;
    const g = f.geometry;
    const rings = g.type === "Polygon" ? g.coordinates
      : g.type === "MultiPolygon" ? g.coordinates.flat(1)
      : g.type === "LineString" ? [g.coordinates]
      : g.type === "MultiLineString" ? g.coordinates : [];
    for (const ring of rings) {
      ctx.beginPath();
      ring.forEach((p, i) => {
        const [x, y] = px(p);
        i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
      });
      ctx.stroke();
    }
  }
  ctx.setLineDash([]);
}

$("#btn_consent").onclick = async () => {
  const code = $("#c_code").value.trim().toUpperCase();
  const ok = ["#c_consent", "#c_adult", "#c_notteam"]
    .every((q) => $(q).checked) && $("#c_conn").value && $("#c_dup").value
    && code;
  if (!ok) { $("#consent_err").textContent = t("err_incomplete"); return; }
  const rand = S.rand ||
    await fetch("./data/randomization.json").then((r) => r.json());
  const slot = rand.find((r) => r.participant_code === code);
  if (!slot) { $("#consent_err").textContent = t("err_unlisted"); return; }
  setLang(I18N.langForCode(code));
  const conn = $("#c_conn").value, dup = $("#c_dup").value;
  if (conn === "neither" || dup === "yes") {       // ineligible: end politely
    S.step = "ineligible";
    document.querySelectorAll("main section").forEach(
      (s) => s.hidden = s.dataset.step !== "ineligible");
    $("#progress").textContent = "";
    wipe();                                         // retain no data
    return;
  }
  ev("consent_given");
  S.code = code; S.city = slot.city; S.order = slot.mode_order;
  S.t0 = Date.now();
  S.screener = {consent_given: 1, adult_18plus: 1,
    not_team_member: $("#c_notteam").checked ? 1 : 0, site_connection: 1,
    connection_type: conn, duplicate_check_passed: 1, eligible: 1};
  ev("screener_completed");
  await loadCity(S.city);
  show("site");
};

async function loadCity(city) {
  const base = `./data/${city}`;
  S.geo = await fetch(`${base}/site.geojson`).then((r) => r.json());
  S.trace = await fetch(`${base}/trace.json`).then((r) => r.json());
  const descEN = await fetch(`${base}/description.txt`).then((r) => r.text());
  /* frozen stimulus text; zh sessions show the reviewed display-layer
     translation, the frozen file itself is untouched */
  $("#site_desc").textContent =
    I18N.stimText(city, "description") || descEN;
  $("#site_map").src = `${base}/site_map.png`;
  $("#site_title").textContent = t(`site_title_${city}`);
}

/* ---------- flow ---------- */
const modeFor = (i) =>
  (S.order === "text_first") === (i === 0) ? "text" : "spatial";

document.querySelector("[data-step=site] [data-next]").onclick =
  () => startMode(0);

function startMode(i) {
  S.stage = i;
  const m = modeFor(i);
  ev(`${m}_start`);
  if (m === "text") { show("text_mode"); }
  else { show("spatial_mode"); initMap(); }
}

/* ---------- text mode ---------- */
$("#btn_text_submit").onclick = () => {
  const text = $("#t_text").value.trim();
  if (!text) return alert(t("al_text_empty"));
  ev("text_submit");
  S.pending = {mode: "text", need_text: text,
    need_category: $("#t_cat").value, location: null,
    t_mode_start: S.events.text_start, t_submit: S.events.text_submit};
  showRecordFidelity();
};

/* ---------- spatial mode ---------- */
function initMap() {
  if (S.map) return;
  const center = S.geo.properties.center;
  S.map = new maplibregl.Map({
    container: "map",
    style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    center, zoom: S.city === "CHI" ? 14.2 : 15.6, attributionControl: true,
  });
  S.map.on("load", () => {
    S.map.addSource("site", {type: "geojson", data: S.geo});
    S.map.addLayer({id: "routes", type: "line", source: "site",
      filter: ["==", ["get", "layer"], "existing_route"],
      paint: {"line-color": "#8e8e93", "line-width": 2.2}});
    S.map.addLayer({id: "bnd", type: "line", source: "site",
      filter: ["==", ["get", "layer"], "site_boundary"],
      paint: {"line-color": "#2f2f31", "line-width": 2,
              "line-dasharray": [3, 2]}});
    S.map.addLayer({id: "ents", type: "circle", source: "site",
      filter: ["==", ["get", "layer"], "existing_entrance"],
      paint: {"circle-radius": 5, "circle-color": "#68976d",
              "circle-stroke-color": "#fff", "circle-stroke-width": 1.5}});
  });
  S.tele.map_opened_at = Date.now();
  S.map.on("moveend", () => S.tele.map_moves++);
  S.map.on("zoomend", () => {
    S.tele.zoom_changes++;
    S.tele.zoom_final = Math.round(S.map.getZoom() * 10) / 10;
  });
  S.map.on("click", (e) => {
    if (S.pinMarker) { S.pinMarker.remove(); S.tele.pin_repositions++; }
    if (S.tele.first_pin_ms === null)
      S.tele.first_pin_ms = Date.now() - S.tele.map_opened_at;
    S.pinMarker = new maplibregl.Marker({color: "#dc312f"})
      .setLngLat(e.lngLat).addTo(S.map);
    S.pin = [e.lngLat.lng, e.lngLat.lat];
    $("#pin_state").textContent = t("pin_at",
      {lng: e.lngLat.lng.toFixed(5), lat: e.lngLat.lat.toFixed(5)});
  });
}

/* --- lightweight geo helpers (WGS84, metres approx) --- */
function inPolygon(pt, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if ((yi > pt[1]) !== (yj > pt[1]) &&
        pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
function distMetres(a, b) {
  const kx = 111320 * Math.cos(a[1] * Math.PI / 180), ky = 110574;
  return Math.hypot((a[0] - b[0]) * kx, (a[1] - b[1]) * ky);
}
function nearestFeature(pt, layer) {
  let best = Infinity;
  for (const f of S.geo.features) {
    if (f.properties.layer !== layer) continue;
    const g = f.geometry;
    const coords = g.type === "Point" ? [g.coordinates]
      : g.type === "LineString" ? g.coordinates
      : (g.coordinates.flat(g.type === "MultiLineString" ? 1 : 2));
    for (const c of coords) best = Math.min(best, distMetres(pt, c));
  }
  return best === Infinity ? null : Math.round(best);
}
function spatialTelemetry() {
  const b = S.geo.features.find(
    (f) => f.properties.layer === "site_boundary");
  const ring = b.geometry.type === "Polygon" ? b.geometry.coordinates[0]
    : b.geometry.coordinates[0][0];
  return {...S.tele,
    time_on_map_s: Math.round((Date.now() - S.tele.map_opened_at) / 1000),
    pin_inside_boundary: inPolygon(S.pin, ring),
    dist_to_route_m: nearestFeature(S.pin, "existing_route"),
    dist_to_entrance_m: nearestFeature(S.pin, "existing_entrance")};
}

$("#btn_spatial_submit").onclick = () => {
  const text = $("#s_text").value.trim();
  if (!S.pin) return alert(t("al_pin_first"));
  if (!text) return alert(t("al_spatial_empty"));
  ev("spatial_submit");
  S.pending = {mode: "spatial", need_text: text,
    need_category: $("#s_cat").value, location: S.pin,
    telemetry: spatialTelemetry(),
    t_mode_start: S.events.spatial_start, t_submit: S.events.spatial_submit};
  showRecordFidelity();
};

/* ---------- structured record check ---------- */
function recordCardHTML() {
  const p = S.pending;
  let loc = t("card_noloc");
  if (p.location) {
    const tm = p.telemetry || {};
    loc = p.location.map((v) => v.toFixed(5)).join(", ") +
      (tm.pin_inside_boundary === false ? t("card_outside")
       : tm.dist_to_route_m !== null && tm.dist_to_route_m !== undefined
       ? t("card_nearroute", {m: tm.dist_to_route_m}) : "");
  }
  return `<b>${t("card_header")}</b><br>
     &ldquo;${p.need_text}&rdquo;<br>
     ${t("card_category")} ${catLabel(p.need_category)}<br>
     ${t("card_place")} ${loc}<br>
     ${t("card_forwhom")}`;
}

/* step A: fidelity rating only; committed before any correction (SOP §3.6) */
function showRecordFidelity() {
  $("#record_card_f").innerHTML = recordCardHTML();
  const l = document.querySelector("[data-step=record_fidelity] .likert");
  likert(l);
  l.dataset.value = "";
  show("record_fidelity");
}

$("#btn_fidelity_next").onclick = () => {
  const fid =
    document.querySelector("[data-step=record_fidelity] .likert").dataset.value;
  if (!fid) return alert(t("al_fid_required"));
  S.pending.fidelity_1to7 = +fid;
  S.pending.t_fidelity = nowISO();
  ev(`${S.pending.mode}_fidelity`);
  save();
  showRecordConfirm();
};

/* step B: confirm / correct / reject, only after the rating is locked */
function showRecordConfirm() {
  $("#record_card_c").innerHTML = recordCardHTML();
  $("#fid_locked").textContent =
    t("fid_locked", {v: S.pending.fidelity_1to7});
  $("#rec_confirm").value = "";
  $("#rec_corrections").value = "";
  $("#rec_corrbox").hidden = true;
  show("record_confirm");
}

/* RES-CF2 is conditional-required: the correction verbatim is collected
   whenever correct OR reject is selected (instrument scoring rule) */
$("#rec_confirm").onchange = () => {
  $("#rec_corrbox").hidden =
    !["corrected", "rejected"].includes($("#rec_confirm").value);
};

$("#btn_record_next").onclick = () => {
  const conf = $("#rec_confirm").value;
  if (!conf) return alert(t("al_conf_required"));
  const corrText = $("#rec_corrections").value.trim();
  if (conf !== "confirmed" && !corrText)
    return alert(t("al_cf2_required"));
  const corr = conf === "confirmed" ? "" : corrText;
  const lines = corr ? corr.split("\n").filter((l) => l.trim()).length : 0;
  const t_confirm = nowISO();
  S.responses[S.pending.mode] = {...S.pending,
    substantive_response: {confirmed: "confirm", corrected: "correct",
                           rejected: "reject"}[conf],
    confirmed_or_corrected: conf,
    material_corrections_n: conf === "confirmed" ? 0 : lines,
    correction_text: corr, t: t_confirm, t_confirm};
  ev(`${S.pending.mode}_confirm`);
  S.pending = null;
  save();
  if (S.stage === 0) startMode(1);
  else buildTrace();
};

/* ---------- provenance trace + comprehension ---------- */
function buildTrace() {
  ev("comprehension_start");
  /* zh sessions render the reviewed display-layer translation of the frozen
     trace texts (i18n.js stim table); option order, radio values and the
     exported item keys/coding are identical in both languages */
  const stageLabel = (st) => I18N.items[`stage_${st}`]
    ? t(`stage_${st}`) : st.replaceAll("_", " ");
  $("#chain").innerHTML = S.trace.chain.map((c, ci) =>
    `<li><b>${stageLabel(c.stage)}</b><span>` +
    `${I18N.stimText(S.city, "chain", ci) || c.record}</span></li>`
  ).join("");
  $("#comp_items").innerHTML = "";
  S.trace.comprehension_items.forEach((q, qi) => {
    const div = document.createElement("div");
    div.className = "compq";
    const qText = I18N.stimText(S.city, "question", q.id) || q.question;
    // options shown in a seeded-shuffled order per participant
    const order = [...q.options.keys()].sort(
      () => hash(`${S.code}:${qi}`) % 2 ? 1 : -1);
    div.innerHTML = `<p>${qi + 1}. ${qText}</p>` + order.map((oi) =>
      `<label><input type="radio" name="q${qi}" value="${oi}"> ` +
      `${I18N.stimText(S.city, "option", {qid: q.id, oi}) || q.options[oi]}` +
      `</label>`).join("");
    $("#comp_items").appendChild(div);
  });
  show("trace");
}
const hash = (s) => [...s].reduce((a, c) => (a * 31 + c.charCodeAt(0)) | 0, 7);

$("#btn_trace_next").onclick = () => {
  const items = S.trace.comprehension_items;
  let score = 0; const ans = {};
  for (let i = 0; i < items.length; i++) {
    const sel = document.querySelector(`input[name=q${i}]:checked`);
    if (!sel) return alert(t("al_trace_all4"));
    const correct = +sel.value === items[i].correct ? 1 : 0;
    ans[items[i].id] = correct;
    score += correct;
  }
  S.comprehension = {...ans, score_0to4: score};
  ev("comprehension_complete");
  showExperience();
};

/* ---------- experience + export ---------- */
function showExperience() {
  document.querySelectorAll(".expitem").forEach((el) => {
    if (el.nextElementSibling &&
        el.nextElementSibling.classList.contains("likert")) return;
    const l = document.createElement("div");
    l.className = "likert";
    el.after(l);
    likert(l);
    l.dataset.name = el.dataset.name;
  });
  show("experience");
}

$("#btn_finish").onclick = () => {
  const vals = {};
  for (const l of document.querySelectorAll("[data-step=experience] .likert")) {
    if (!l.dataset.value) return alert(t("al_exp_all"));
    vals[l.dataset.name + "_1to7"] = +l.dataset.value;
  }
  S.experience = {...vals, free_comment: $("#exp_comment").value.trim(),
    completion_time_min: Math.round((Date.now() - S.t0) / 6000) / 10};
  ev("experience_complete");
  ev("session_complete");
  $("#done_code").textContent = `${S.code}-OK-${S.comprehension.score_0to4}`;
  show("done");
  exportJSON();
  wipe();                       // completed: clear the on-device autosave
};

function exportJSON() {
  const out = {participant_code: S.code, city: S.city, mode_order: S.order,
    screener: S.screener, responses: S.responses,
    comprehension: S.comprehension, experience: S.experience,
    events: S.events,
    exported_at: nowISO(), schema: "case2-v3"};
  const blob = new Blob([JSON.stringify(out, null, 1)],
    {type: "application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${S.code}_case2.json`;
  a.click();
}
$("#btn_download").onclick = exportJSON;

/* ---------- disconnect / resume (SOP §5) ---------- */
function resumeAt(step) {
  switch (step) {
    case "site": show("site"); break;
    case "text_mode": show("text_mode"); break;
    case "spatial_mode": show("spatial_mode"); initMap(); break;
    case "record_fidelity": showRecordFidelity(); break;
    case "record_confirm": showRecordConfirm(); break;
    case "trace": buildTrace(); break;
    case "experience": showExperience(); break;
    default: show("site");
  }
}

(function offerResume() {
  let saved = null;
  try { saved = JSON.parse(localStorage.getItem("polis_case2") || "null"); }
  catch (e) {}
  if (!saved || !saved.code || !saved.step ||
      ["consent", "done", "ineligible"].includes(saved.step)) return;
  setLang(I18N.langForCode(saved.code));   // banner in the session language
  $("#resume_banner").hidden = false;
  $("#resume_code").textContent = saved.code;
  $("#btn_resume").onclick = async () => {
    Object.assign(S, saved);
    S.map = null; S.pinMarker = null;
    setLang(I18N.langForCode(S.code));
    await loadCity(S.city);
    $("#resume_banner").hidden = true;
    resumeAt(S.step);
  };
  $("#btn_startover").onclick = () => {
    wipe();
    $("#resume_banner").hidden = true;
  };
})();
