// ─── auth.js — shared across all pages ───────────────────────────────────────
const Auth = {
  save(token, user) {
    localStorage.setItem("crop_token", token);
    localStorage.setItem("crop_user", JSON.stringify(user));
  },
  getToken() { return localStorage.getItem("crop_token"); },
  getUser()  { const u=localStorage.getItem("crop_user"); return u?JSON.parse(u):null; },
  isLoggedIn(){ return !!this.getToken(); },
  isAdmin()  { const u=this.getUser(); return u&&u.role==="admin"; },
  logout()   { localStorage.removeItem("crop_token"); localStorage.removeItem("crop_user"); window.location.href="/"; },

  // Attach token to every fetch
  async fetch(url, opts={}) {
    const token = this.getToken();
    opts.headers = opts.headers || {};
    if (token) opts.headers["Authorization"] = "Bearer " + token;
    opts.headers["Content-Type"] = opts.headers["Content-Type"] || "application/json";
    const resp = await fetch(url, opts);
    if (resp.status === 401) { this.logout(); return; }
    return resp;
  },

  // Guard — redirect to login if not authenticated
  guard(adminRequired=false) {
    if (!this.isLoggedIn()) { window.location.href="/"; return false; }
    if (adminRequired && !this.isAdmin()) { window.location.href="/app"; return false; }
    return true;
  },

  // Show user name in header
  renderHeader() {
    const u = this.getUser();
    const el = document.getElementById("userDisplay");
    if (el && u) el.innerHTML = `<span class="user-name"><i class="fa fa-user"></i> ${u.name}</span>`;
    const roleEl = document.getElementById("userRole");
    if (roleEl && u) { roleEl.innerText=u.role==="admin"?"Admin":"Farmer"; roleEl.className="role-badge role-"+u.role; }
  }
};

// Toast helper
function showToast(msg, type="info") {
  let t = document.getElementById("toast");
  if (!t) { t=document.createElement("div"); t.id="toast"; document.body.appendChild(t); }
  t.className = "toast toast-"+type;
  t.innerText = msg; t.classList.add("show");
  setTimeout(()=>t.classList.remove("show"), 3000);
}

// ─── I18n Helper ─────────────────────────────────────────────────────────────
const I18n = {
  getLang() {
    return localStorage.getItem("cropLang") || "en";
  },
  tr(key, T) {
    const lang = this.getLang();
    if (!T) return key;
    return (T[lang] && T[lang][key]) || (T.en && T.en[key]) || key;
  },
  crop(c, T) {
    const lang = this.getLang();
    if (!T) return c;
    return (T[lang] && T[lang].crops && T[lang].crops[c]) || (T.en && T.en.crops && T.en.crops[c]) || c;
  },
  intercrop(ic, T) {
    const lang = this.getLang();
    if (!T) return ic;
    return (T[lang] && T[lang].intercrops && T[lang].intercrops[ic]) || (T.en && T.en.intercrops && T.en.intercrops[ic]) || ic;
  },
  fertilizer(f, T) {
    const lang = this.getLang();
    if (!T) return f;
    return (T[lang] && T[lang].fertilizers && T[lang].fertilizers[f]) || (T.en && T.en.fertilizers && T.en.fertilizers[f]) || f;
  },
  season(s, T) {
    const lang = this.getLang();
    if (!T) return s;
    return (T[lang] && T[lang].seasons && T[lang].seasons[s]) || (T.en && T.en.seasons && T.en.seasons[s]) || s;
  },
  irrigationFreq(freq, T) {
    const lang = this.getLang();
    if (!T) return freq;
    return (T[lang] && T[lang].irrigation_freq && T[lang].irrigation_freq[freq]) || (T.en && T.en.irrigation_freq && T.en.irrigation_freq[freq]) || freq;
  },
  diseaseType(dt, T) {
    const lang = this.getLang();
    if (!T) return dt;
    return (T[lang] && T[lang].disease_types && T[lang].disease_types[dt]) || (T.en && T.en.disease_types && T.en.disease_types[dt]) || dt;
  },
  riskLevel(rl, T) {
    const lang = this.getLang();
    if (!T) return rl;
    return (T[lang] && T[lang].risk_levels && T[lang].risk_levels[rl]) || (T.en && T.en.risk_levels && T.en.risk_levels[rl]) || rl;
  },
  diseaseAdvice(da, T) {
    const lang = this.getLang();
    if (!T) return da;
    return (T[lang] && T[lang].disease_advice && T[lang].disease_advice[da]) || (T.en && T.en.disease_advice && T.en.disease_advice[da]) || da;
  },
  marketStatus(ms, T) {
    const lang = this.getLang();
    if (!T) return ms;
    return (T[lang] && T[lang].market_status && T[lang].market_status[ms]) || (T.en && T.en.market_status && T.en.market_status[ms]) || ms;
  },
  marketTrend(mt, T) {
    const lang = this.getLang();
    if (!T) return mt;
    return (T[lang] && T[lang].market_trend && T[lang].market_trend[mt]) || (T.en && T.en.market_trend && T.en.market_trend[mt]) || mt;
  },
  scheme(sc, T) {
    const lang = this.getLang();
    if (!T) return sc;
    return (T[lang] && T[lang].schemes && T[lang].schemes[sc]) || (T.en && T.en.schemes && T.en.schemes[sc]) || sc;
  },
  soilTip(tip, T) {
    const lang = this.getLang();
    if (!T) return tip;
    return (T[lang] && T[lang].soil_tips && T[lang].soil_tips[tip]) || (T.en && T.en.soil_tips && T.en.soil_tips[tip]) || tip;
  },
  waterNeed(wn, T) {
    const lang = this.getLang();
    if (!T) return wn;
    return (T[lang] && T[lang].water_need && T[lang].water_need[wn]) || (T.en && T.en.water_need && T.en.water_need[wn]) || wn;
  },
  stageName(name, T) {
    const lang = this.getLang();
    if (!T) return name;
    return (T[lang] && T[lang].stage_names && T[lang].stage_names[name]) || (T.en && T.en.stage_names && T.en.stage_names[name]) || name;
  },
  stageExplanation(exp, T) {
    const lang = this.getLang();
    if (!T) return exp;
    return (T[lang] && T[lang].stage_explanations && T[lang].stage_explanations[exp]) || (T.en && T.en.stage_explanations && T.en.stage_explanations[exp]) || exp;
  }
};
