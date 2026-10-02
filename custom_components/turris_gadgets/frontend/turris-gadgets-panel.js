const COPY = {
  cs: {
    title: "Turris Gadgets",
    subtitle: "Správa periferií uložených v Turris Donglu",
    connected: "Připojeno",
    disconnected: "Odpojeno",
    firmware: "Firmware",
    port: "Sériový port",
    occupied: "Obsazeno",
    free: "Volné sloty",
    addTitle: "Přidat čidlo",
    addHelp:
      "Zadejte posledních 8 číslic kódu čidla nebo je načtěte fotoaparátem. Vyberte volný slot a uložte čidlo do paměti donglu.",
    deviceId: "ID čidla (8 číslic)",
    slot: "Cílový slot",
    model: "Model zařízení",
    automaticModel: "Automaticky rozpoznat",
    add: "Přidat do donglu",
    adding: "Ukládám…",
    scanCode: "Skenovat kód fotoaparátem",
    stopCamera: "Vypnout fotoaparát",
    cameraHelp:
      "Namiřte fotoaparát na čárový kód na štítku čidla. Pokud prohlížeč kód nerozpozná, opište posledních 8 číslic ručně.",
    cameraUnsupported:
      "Tento prohlížeč nepodporuje rozpoznání čárových kódů. ID lze zadat ručně.",
    detected: "Rozpoznané kódy",
    use: "Použít",
    slotsTitle: "Paměť donglu",
    slotsHelp: "Dongle má 32 registračních slotů (00–31).",
    empty: "Prázdný",
    remove: "Odebrat",
    removeConfirm: (id, slot) =>
      `Opravdu odebrat čidlo ${id} ze slotu ${slot}?`,
    removing: "Odebírám…",
    monitorTitle: "Živý RF monitor",
    monitorHelp:
      "Zobrazuje v reálném čase zprávy, které dongle přijal od registrovaných čidel.",
    limitation:
      "Firmware donglu neposílá přes USB zprávy dosud neregistrovaných čidel. Nové čidlo proto přidejte načtením kódu ze štítku nebo ručním zadáním ID.",
    startMonitor: "Spustit monitor",
    stopMonitor: "Zastavit monitor",
    monitoring: "Monitor běží",
    stopped: "Monitor zastaven",
    noMessages: "Zatím nebyla přijata žádná zpráva.",
    lastSeen: "Naposledy",
    messages: "Zpráv",
    message: "Poslední zpráva",
    saved: "Čidlo bylo uloženo a jeho entity byly přidány.",
    removed: "Čidlo bylo odebráno včetně jeho entit.",
    backup: "Stáhnout zálohu",
    restore: "Obnovit ze zálohy",
    restoreConfirm: (slots) =>
      `Záloha změní sloty: ${slots}. Nahradit obsah paměti donglu? Tuto operaci nelze vrátit zpět.`,
    restored: "Paměť donglu byla obnovena ze zálohy.",
    invalidBackup: "Soubor není platná záloha Turris Gadgets.",
    invalidId: "ID musí být osmimístná dekadická 24bitová adresa.",
    noSlot: "Není k dispozici žádný volný slot.",
    cameraError: "Fotoaparát se nepodařilo spustit.",
    loadError: "Stav integrace se nepodařilo načíst.",
    integrationUnloaded: "Integrace Turris Gadgets není načtena nebo se právě znovu načítá.",
  },
  en: {
    title: "Turris Gadgets",
    subtitle: "Manage peripherals stored in the Turris Dongle",
    connected: "Connected",
    disconnected: "Disconnected",
    firmware: "Firmware",
    port: "Serial port",
    occupied: "Occupied",
    free: "Free slots",
    addTitle: "Add sensor",
    addHelp:
      "Enter the last 8 digits of the sensor code or scan them with a camera. Select a free slot and save the sensor to dongle memory.",
    deviceId: "Sensor ID (8 digits)",
    slot: "Target slot",
    model: "Device model",
    automaticModel: "Detect automatically",
    add: "Add to dongle",
    adding: "Saving…",
    scanCode: "Scan code with camera",
    stopCamera: "Stop camera",
    cameraHelp:
      "Point the camera at the barcode on the sensor label. If the browser cannot recognize it, enter the last 8 digits manually.",
    cameraUnsupported:
      "This browser does not support barcode recognition. Enter the ID manually.",
    detected: "Detected codes",
    use: "Use",
    slotsTitle: "Dongle memory",
    slotsHelp: "The dongle has 32 registration slots (00–31).",
    empty: "Empty",
    remove: "Remove",
    removeConfirm: (id, slot) =>
      `Remove sensor ${id} from slot ${slot}?`,
    removing: "Removing…",
    monitorTitle: "Live RF monitor",
    monitorHelp:
      "Shows messages received by the dongle from registered sensors in real time.",
    limitation:
      "The dongle firmware does not forward messages from unregistered sensors over USB. Add a new sensor by scanning its label or entering its ID.",
    startMonitor: "Start monitor",
    stopMonitor: "Stop monitor",
    monitoring: "Monitor running",
    stopped: "Monitor stopped",
    noMessages: "No messages received yet.",
    lastSeen: "Last seen",
    messages: "Messages",
    message: "Last message",
    saved: "Sensor saved and its entities were added.",
    removed: "Sensor and its entities were removed.",
    backup: "Download backup",
    restore: "Restore backup",
    restoreConfirm: (slots) =>
      `The backup changes slots: ${slots}. Replace dongle memory? This operation cannot be undone.`,
    restored: "Dongle memory was restored from the backup.",
    invalidBackup: "The file is not a valid Turris Gadgets backup.",
    invalidId: "The ID must be an 8-digit decimal 24-bit address.",
    noSlot: "No free slot is available.",
    cameraError: "Could not start the camera.",
    loadError: "Could not load the integration state.",
    integrationUnloaded: "The Turris Gadgets integration is not loaded or is currently reloading.",
  },
};

const esc = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const DEVICE_IMAGE_VERSION = "0.3.0";
const DEVICE_IMAGE_MODELS = new Set([
  "AC-88",
  "JA-80L",
  "JA-81M",
  "JA-82SH",
  "JA-83M",
  "JA-83P",
  "JA-85ST",
  "RC-86K",
  "TP-82N",
]);
const KNOWN_MODELS = [...DEVICE_IMAGE_MODELS].sort();

const modelOptions = (selected, automaticLabel) =>
  [
    `<option value="auto"${selected === "auto" ? " selected" : ""}>${esc(automaticLabel)}</option>`,
    ...KNOWN_MODELS.map(
      (model) =>
        `<option value="${model}"${selected === model ? " selected" : ""}>${model}</option>`,
    ),
  ].join("");

const modelCell = (model, compact = false) => {
  const normalized = model || "Unknown";
  const image = DEVICE_IMAGE_MODELS.has(normalized)
    ? `<img class="device-image${compact ? " compact" : ""}" src="/turris_gadgets_static/devices/${normalized.toLowerCase()}.png?v=${DEVICE_IMAGE_VERSION}" alt="" loading="lazy">`
    : "";
  return `<div class="model-cell">${image}<span>${esc(model || "—")}</span></div>`;
};

class TurrisGadgetsPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._state = null;
    this._unsubscribe = null;
    this._cameraStream = null;
    this._scanTimer = null;
    this._detectedCodes = new Set();
    this._busy = false;
    this._narrow = false;
  }

  set hass(value) {
    const first = !this._hass;
    this._hass = value;
    this._copy = COPY[value?.language === "cs" ? "cs" : "en"];
    if (first && this.isConnected) this._initialize();
  }

  get hass() {
    return this._hass;
  }

  set narrow(value) {
    this._narrow = value;
    this.toggleAttribute("narrow", Boolean(value));
  }

  set panel(value) {
    this._panel = value;
  }

  connectedCallback() {
    if (this._hass) this._initialize();
  }

  disconnectedCallback() {
    this._unsubscribe?.();
    this._unsubscribe = null;
    this._stopCamera();
  }

  async _initialize() {
    if (this._initialized) return;
    this._initialized = true;
    this._renderShell();
    this._bindEvents();
    try {
      this._unsubscribe = await this._hass.connection.subscribeMessage(
        (state) => {
          if (state.loaded === false) {
            if (this._state) {
              this._state = { ...this._state, connected: false };
              this._renderState();
              return;
            }
            this._showNotice(this._copy.integrationUnloaded, "warning");
            return;
          }
          this._state = state;
          this._renderState();
        },
        { type: "turris_gadgets/subscribe" },
      );
      this._state = await this._hass.callWS({
        type: "turris_gadgets/get_state",
      });
      this._renderState();
    } catch (error) {
      this._showNotice(error?.message || this._copy.loadError, "error");
    }
  }

  _renderShell() {
    const t = this._copy;
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          min-height: 100%;
          box-sizing: border-box;
          background: var(--primary-background-color);
          color: var(--primary-text-color);
          font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
        }
        * { box-sizing: border-box; }
        main { max-width: 1180px; margin: 0 auto; padding: 28px 24px 48px; }
        header { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; margin-bottom: 22px; }
        h1 { font-size: 30px; line-height: 1.15; margin: 0 0 5px; font-weight: 600; }
        h2 { font-size: 20px; margin: 0 0 8px; font-weight: 600; }
        p { margin: 0; color: var(--secondary-text-color); line-height: 1.5; }
        .status { display: flex; align-items: center; gap: 8px; white-space: nowrap; padding: 8px 12px; border-radius: 999px; background: var(--card-background-color); box-shadow: var(--ha-card-box-shadow, 0 1px 2px rgba(0,0,0,.12)); }
        .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--error-color, #db4437); }
        .dot.on { background: var(--success-color, #43a047); box-shadow: 0 0 0 4px color-mix(in srgb, var(--success-color, #43a047) 18%, transparent); }
        .meta { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 18px; }
        .meta-item, .card { background: var(--card-background-color); border-radius: 14px; box-shadow: var(--ha-card-box-shadow, 0 1px 3px rgba(0,0,0,.16)); }
        .meta-item { padding: 14px 16px; min-width: 0; }
        .meta-label { display: block; font-size: 12px; color: var(--secondary-text-color); margin-bottom: 4px; }
        .meta-value { display: block; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .grid { display: grid; grid-template-columns: minmax(280px, .85fr) minmax(420px, 1.4fr); gap: 18px; align-items: start; }
        .stack { display: grid; gap: 18px; }
        .card { padding: 20px; overflow: hidden; }
        .field { display: grid; gap: 6px; margin-top: 16px; }
        label { font-size: 13px; color: var(--secondary-text-color); }
        input, select { width: 100%; height: 44px; padding: 0 12px; color: var(--primary-text-color); background: var(--card-background-color); border: 1px solid var(--divider-color); border-radius: 8px; font: inherit; outline: none; }
        input:focus, select:focus { border-color: var(--primary-color); box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-color) 20%, transparent); }
        .actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }
        button { appearance: none; border: 0; border-radius: 9px; min-height: 40px; padding: 0 15px; font: inherit; font-weight: 600; cursor: pointer; color: var(--text-primary-color, #fff); background: var(--primary-color); }
        button.secondary { color: var(--primary-color); background: color-mix(in srgb, var(--primary-color) 12%, transparent); }
        button.danger { color: var(--error-color, #db4437); background: color-mix(in srgb, var(--error-color, #db4437) 10%, transparent); }
        button.small { min-height: 32px; padding: 0 10px; font-size: 13px; }
        button:disabled { opacity: .5; cursor: not-allowed; }
        .notice { display: none; margin-bottom: 16px; padding: 12px 14px; border-radius: 10px; background: color-mix(in srgb, var(--info-color, #039be5) 14%, var(--card-background-color)); }
        .notice.show { display: block; }
        .notice.error { background: color-mix(in srgb, var(--error-color, #db4437) 14%, var(--card-background-color)); }
        .notice.warning { background: color-mix(in srgb, var(--warning-color, #ff9800) 15%, var(--card-background-color)); }
        .limitation { margin-top: 16px; padding: 12px 14px; border-left: 3px solid var(--warning-color, #ff9800); background: color-mix(in srgb, var(--warning-color, #ff9800) 9%, transparent); border-radius: 0 8px 8px 0; font-size: 13px; line-height: 1.45; }
        .camera { display: none; margin-top: 14px; }
        .camera.active { display: block; }
        video { width: 100%; max-height: 260px; object-fit: cover; border-radius: 10px; background: #111; }
        .camera p { font-size: 13px; margin-top: 8px; }
        .codes { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
        .code { display: flex; align-items: center; gap: 8px; padding: 6px 7px 6px 10px; border: 1px solid var(--divider-color); border-radius: 999px; }
        .code button { min-height: 26px; padding: 0 8px; font-size: 12px; }
        .section-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; margin-bottom: 14px; }
        .monitor-state { display: inline-flex; align-items: center; gap: 7px; font-size: 13px; margin-top: 6px; color: var(--secondary-text-color); }
        .monitor-state .dot { width: 7px; height: 7px; }
        .table-wrap { overflow-x: auto; margin: 0 -20px -20px; }
        table { width: 100%; border-collapse: collapse; min-width: 590px; }
        th, td { padding: 12px 14px; text-align: left; border-top: 1px solid var(--divider-color); vertical-align: middle; }
        th { font-size: 12px; color: var(--secondary-text-color); font-weight: 500; }
        td { font-size: 14px; }
        td.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
        .slot { display: inline-grid; place-items: center; width: 34px; height: 28px; border-radius: 7px; font: 600 13px ui-monospace, monospace; background: var(--secondary-background-color); }
        .model-cell { display: flex; align-items: center; gap: 10px; min-width: 122px; }
        .device-image { width: 48px; height: 48px; flex: 0 0 48px; object-fit: contain; filter: drop-shadow(0 2px 3px rgba(0,0,0,.16)); }
        .device-image.compact { width: 38px; height: 38px; flex-basis: 38px; }
        tr.empty-row { color: var(--secondary-text-color); }
        .raw { max-width: 360px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: ui-monospace, monospace; font-size: 12px; }
        .empty-state { padding: 24px 12px; text-align: center; color: var(--secondary-text-color); }
        @media (max-width: 850px) {
          main { padding: 18px 12px 36px; }
          header { align-items: stretch; flex-direction: column; }
          .status { align-self: flex-start; }
          .meta { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .grid { grid-template-columns: 1fr; }
        }
        @media (max-width: 480px) {
          .meta { grid-template-columns: 1fr; }
          .section-head { flex-direction: column; }
          .card { padding: 16px; }
          .table-wrap { margin: 0 -16px -16px; }
        }
      </style>
      <main>
        <header>
          <div><h1>${esc(t.title)}</h1><p>${esc(t.subtitle)}</p></div>
          <div class="status"><span class="dot" id="connection-dot"></span><strong id="connection-label">—</strong></div>
        </header>
        <div class="notice" id="notice" role="status"></div>
        <section class="meta">
          <div class="meta-item"><span class="meta-label">${esc(t.firmware)}</span><span class="meta-value" id="firmware">—</span></div>
          <div class="meta-item"><span class="meta-label">${esc(t.port)}</span><span class="meta-value" id="port">—</span></div>
          <div class="meta-item"><span class="meta-label">${esc(t.occupied)}</span><span class="meta-value" id="occupied">—</span></div>
          <div class="meta-item"><span class="meta-label">${esc(t.free)}</span><span class="meta-value" id="free">—</span></div>
        </section>
        <div class="grid">
          <div class="stack">
            <section class="card">
              <h2>${esc(t.addTitle)}</h2><p>${esc(t.addHelp)}</p>
              <div class="field"><label for="device-id">${esc(t.deviceId)}</label><input id="device-id" inputmode="numeric" autocomplete="off" maxlength="8" placeholder="01234567"></div>
              <div class="field"><label for="target-slot">${esc(t.slot)}</label><select id="target-slot"></select></div>
              <div class="field"><label for="device-model">${esc(t.model)}</label><select id="device-model">${modelOptions("auto", t.automaticModel)}</select></div>
              <div class="actions"><button id="add-button">${esc(t.add)}</button><button class="secondary" id="camera-button">${esc(t.scanCode)}</button></div>
              <div class="camera" id="camera"><video id="video" playsinline muted></video><p>${esc(t.cameraHelp)}</p><div id="codes-block" hidden><label>${esc(t.detected)}</label><div class="codes" id="codes"></div></div></div>
            </section>
            <section class="card">
              <div class="section-head"><div><h2>${esc(t.monitorTitle)}</h2><p>${esc(t.monitorHelp)}</p><div class="monitor-state"><span class="dot" id="monitor-dot"></span><span id="monitor-label">${esc(t.stopped)}</span></div></div><button class="secondary" id="monitor-button">${esc(t.startMonitor)}</button></div>
              <div class="limitation">${esc(t.limitation)}</div>
              <div class="table-wrap" id="observations"></div>
            </section>
          </div>
          <section class="card">
            <div class="section-head"><div><h2>${esc(t.slotsTitle)}</h2><p>${esc(t.slotsHelp)}</p></div><div class="actions"><button class="secondary small" id="backup-button">${esc(t.backup)}</button><button class="secondary small" id="restore-button">${esc(t.restore)}</button><input type="file" id="restore-file" accept="application/json,.json" hidden></div></div>
            <div class="table-wrap" id="slots"></div>
          </section>
        </div>
      </main>`;
  }

  _bindEvents() {
    const root = this.shadowRoot;
    root.getElementById("device-id").addEventListener("input", (event) => {
      event.target.value = event.target.value.replace(/\D/g, "").slice(0, 8);
      this._updateControls();
    });
    root.getElementById("target-slot").addEventListener("change", () =>
      this._updateControls(),
    );
    root.getElementById("add-button").addEventListener("click", () =>
      this._addSensor(),
    );
    root.getElementById("camera-button").addEventListener("click", () =>
      this._cameraStream ? this._stopCamera() : this._startCamera(),
    );
    root.getElementById("monitor-button").addEventListener("click", () =>
      this._setMonitor(!this._state?.scan_active),
    );
    root.getElementById("backup-button").addEventListener("click", () =>
      this._downloadBackup(),
    );
    root.getElementById("restore-button").addEventListener("click", () =>
      root.getElementById("restore-file").click(),
    );
    root.getElementById("restore-file").addEventListener("change", (event) =>
      this._restoreBackup(event.target.files?.[0]),
    );
    root.getElementById("slots").addEventListener("click", (event) => {
      const button = event.target.closest("button[data-remove]");
      if (button) this._removeSensor(Number(button.dataset.remove));
    });
    root.getElementById("slots").addEventListener("change", (event) => {
      const select = event.target.closest("select[data-model-device]");
      if (select) {
        this._setModel(Number(select.dataset.modelDevice), select.value);
      }
    });
    root.getElementById("codes").addEventListener("click", (event) => {
      const button = event.target.closest("button[data-code]");
      if (!button) return;
      root.getElementById("device-id").value = button.dataset.code;
      this._updateControls();
      this._stopCamera();
    });
  }

  _renderState() {
    if (!this._state) return;
    const t = this._copy;
    const root = this.shadowRoot;
    const slots = this._state.slots || [];
    const occupied = slots.filter((item) => item.device_id);
    const free = slots.filter((item) => !item.device_id);
    root.getElementById("connection-dot").classList.toggle("on", this._state.connected);
    root.getElementById("connection-label").textContent = this._state.connected ? t.connected : t.disconnected;
    root.getElementById("firmware").textContent = this._state.firmware || "—";
    root.getElementById("port").textContent = this._state.port || "—";
    root.getElementById("occupied").textContent = `${occupied.length} / 32`;
    root.getElementById("free").textContent = String(free.length);

    const select = root.getElementById("target-slot");
    const previous = select.value;
    select.innerHTML = free.length
      ? free.map((item) => `<option value="${item.slot}">${String(item.slot).padStart(2, "0")}</option>`).join("")
      : `<option value="">${esc(t.noSlot)}</option>`;
    if (free.some((item) => String(item.slot) === previous)) select.value = previous;

    root.getElementById("slots").innerHTML = `
      <table><thead><tr><th>${esc(t.slot)}</th><th>${esc(t.deviceId)}</th><th>${esc(t.model)}</th><th></th></tr></thead>
      <tbody>${slots.map((item) => `<tr class="${item.device_id ? "" : "empty-row"}"><td><span class="slot">${String(item.slot).padStart(2, "0")}</span></td><td class="mono">${item.device_id ? esc(item.device_id) : esc(t.empty)}</td><td>${item.device_id ? `${modelCell(item.model)}<select data-model-device="${Number(item.device_id)}">${modelOptions(item.model_overridden ? item.model : "auto", t.automaticModel)}</select>` : modelCell(null)}</td><td>${item.device_id ? `<button class="danger small" data-remove="${item.slot}">${esc(t.remove)}</button>` : ""}</td></tr>`).join("")}</tbody></table>`;

    const active = Boolean(this._state.scan_active);
    root.getElementById("monitor-dot").classList.toggle("on", active);
    root.getElementById("monitor-label").textContent = active ? t.monitoring : t.stopped;
    root.getElementById("monitor-button").textContent = active ? t.stopMonitor : t.startMonitor;
    const observations = this._state.observations || [];
    root.getElementById("observations").innerHTML = observations.length
      ? `<table><thead><tr><th>${esc(t.deviceId)}</th><th>Model</th><th>${esc(t.lastSeen)}</th><th>${esc(t.messages)}</th><th>${esc(t.message)}</th></tr></thead><tbody>${observations.map((item) => `<tr><td class="mono">${esc(item.device_id)}</td><td>${modelCell(item.model, true)}</td><td>${esc(this._formatDate(item.last_seen))}</td><td>${item.count}</td><td class="raw" title="${esc(item.raw)}">${esc(item.raw)}</td></tr>`).join("")}</tbody></table>`
      : `<div class="empty-state">${esc(t.noMessages)}</div>`;
    this._updateControls();
  }

  _updateControls() {
    const root = this.shadowRoot;
    const id = root.getElementById("device-id")?.value || "";
    const slot = root.getElementById("target-slot")?.value || "";
    const add = root.getElementById("add-button");
    const validId = /^\d{8}$/.test(id) && Number(id) <= 0xffffff;
    if (add) add.disabled = this._busy || !this._state?.connected || !validId || slot === "";
    root.querySelectorAll("button[data-remove]").forEach((button) => {
      button.disabled = this._busy || !this._state?.connected;
    });
    root.querySelectorAll("select[data-model-device]").forEach((select) => {
      select.disabled = this._busy || !this._state?.connected;
    });
    for (const id of ["monitor-button", "restore-button"]) {
      const button = root.getElementById(id);
      if (button) button.disabled = this._busy || !this._state?.connected;
    }
    const backup = root.getElementById("backup-button");
    if (backup) backup.disabled = this._busy || !this._state;
  }

  async _addSensor() {
    const t = this._copy;
    const idInput = this.shadowRoot.getElementById("device-id");
    const slotInput = this.shadowRoot.getElementById("target-slot");
    const modelInput = this.shadowRoot.getElementById("device-model");
    if (!/^\d{8}$/.test(idInput.value) || Number(idInput.value) > 0xffffff) {
      this._showNotice(t.invalidId, "error");
      return;
    }
    if (slotInput.value === "") {
      this._showNotice(t.noSlot, "warning");
      return;
    }
    await this._runBusy(t.adding, async () => {
      this._state = await this._hass.callWS({
        type: "turris_gadgets/set_slot",
        slot: Number(slotInput.value),
        device_id: Number(idInput.value),
      });
      if (modelInput.value !== "auto") {
        this._state = await this._hass.callWS({
          type: "turris_gadgets/set_model",
          device_id: Number(idInput.value),
          model: modelInput.value,
        });
      }
      idInput.value = "";
      modelInput.value = "auto";
      this._renderState();
      this._showNotice(t.saved);
    });
  }

  async _removeSensor(slot) {
    const item = this._state.slots.find((candidate) => candidate.slot === slot);
    if (!item || !confirm(this._copy.removeConfirm(item.device_id, String(slot).padStart(2, "0")))) return;
    await this._runBusy(null, async () => {
      this._state = await this._hass.callWS({
        type: "turris_gadgets/clear_slot",
        slot,
      });
      this._renderState();
      this._showNotice(this._copy.removed);
    });
  }

  async _setMonitor(active) {
    await this._runBusy(null, async () => {
      this._state = await this._hass.callWS({
        type: "turris_gadgets/set_scan",
        active,
      });
      this._renderState();
    });
  }

  async _setModel(deviceId, model) {
    await this._runBusy(null, async () => {
      this._state = await this._hass.callWS({
        type: "turris_gadgets/set_model",
        device_id: deviceId,
        model,
      });
      this._renderState();
    });
  }

  _downloadBackup() {
    const slots = (this._state?.slots || [])
      .filter((item) => item.device_id)
      .map((item) => ({
        slot: item.slot,
        device_id: item.device_id,
        ...(item.model_overridden ? { model_override: item.model } : {}),
      }));
    const payload = JSON.stringify(
      { format: "turris-gadgets-slots", version: 1, slots },
      null,
      2,
    );
    const url = URL.createObjectURL(
      new Blob([payload], { type: "application/json" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = `turris-gadgets-slots-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async _restoreBackup(file) {
    if (!file) return;
    try {
      const backup = JSON.parse(await file.text());
      if (
        backup?.format !== "turris-gadgets-slots" ||
        backup.version !== 1 ||
        !Array.isArray(backup.slots)
      ) {
        throw new Error(this._copy.invalidBackup);
      }
      const slots = backup.slots.map((item) => ({
        slot: Number(item.slot),
        device_id: Number(item.device_id),
        ...(item.model_override
          ? { model_override: item.model_override }
          : {}),
      }));
      const current = new Map(
        (this._state?.slots || [])
          .filter((item) => item.device_id)
          .map((item) => [
            item.slot,
            `${Number(item.device_id)}:${item.model_overridden ? item.model : "auto"}`,
          ]),
      );
      const desired = new Map(
        slots.map((item) => [
          item.slot,
          `${item.device_id}:${item.model_override || "auto"}`,
        ]),
      );
      const changedSlots = [...new Set([...current.keys(), ...desired.keys()])]
        .filter((slot) => current.get(slot) !== desired.get(slot))
        .sort((left, right) => left - right)
        .map((slot) => String(slot).padStart(2, "0"));
      if (changedSlots.length === 0) return;
      if (!confirm(this._copy.restoreConfirm(changedSlots.join(", ")))) return;
      await this._runBusy(null, async () => {
        this._state = await this._hass.callWS({
          type: "turris_gadgets/restore_slots",
          slots,
        });
        this._renderState();
        this._showNotice(this._copy.restored);
      });
    } catch (error) {
      this._showNotice(error?.message || this._copy.invalidBackup, "error");
    } finally {
      this.shadowRoot.getElementById("restore-file").value = "";
    }
  }

  async _runBusy(label, action) {
    const button = this.shadowRoot.getElementById("add-button");
    const original = button.textContent;
    this._busy = true;
    if (label) button.textContent = label;
    this._updateControls();
    try {
      await action();
    } catch (error) {
      this._showNotice(error?.message || String(error), "error");
    } finally {
      this._busy = false;
      button.textContent = original;
      this._updateControls();
    }
  }

  async _startCamera() {
    const t = this._copy;
    if (!("BarcodeDetector" in window)) {
      this._showNotice(t.cameraUnsupported, "warning");
      return;
    }
    try {
      this._cameraStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });
      const video = this.shadowRoot.getElementById("video");
      video.srcObject = this._cameraStream;
      await video.play();
      this.shadowRoot.getElementById("camera").classList.add("active");
      this.shadowRoot.getElementById("camera-button").textContent = t.stopCamera;
      const supported = window.BarcodeDetector.getSupportedFormats
        ? await window.BarcodeDetector.getSupportedFormats()
        : [];
      const preferred = ["code_128", "code_39", "ean_13", "ean_8", "qr_code"];
      const formats = preferred.filter((format) => supported.includes(format));
      this._detector = new window.BarcodeDetector(formats.length ? { formats } : undefined);
      this._scheduleCodeScan();
    } catch (error) {
      this._stopCamera();
      this._showNotice(`${t.cameraError} ${error?.message || ""}`, "error");
    }
  }

  _scheduleCodeScan() {
    if (!this._cameraStream) return;
    this._scanTimer = window.setTimeout(async () => {
      try {
        const codes = await this._detector.detect(this.shadowRoot.getElementById("video"));
        for (const code of codes) {
          const digits = String(code.rawValue || "").replace(/\D/g, "");
          if (digits.length >= 8) this._detectedCodes.add(digits.slice(-8));
        }
        this._renderCodes();
      } catch (_) {
        // A video frame can be unavailable while the camera is warming up.
      }
      this._scheduleCodeScan();
    }, 350);
  }

  _renderCodes() {
    const block = this.shadowRoot.getElementById("codes-block");
    block.hidden = this._detectedCodes.size === 0;
    this.shadowRoot.getElementById("codes").innerHTML = [...this._detectedCodes]
      .map((code) => `<span class="code"><strong>${esc(code)}</strong><button data-code="${code}">${esc(this._copy.use)}</button></span>`)
      .join("");
  }

  _stopCamera() {
    if (this._scanTimer) window.clearTimeout(this._scanTimer);
    this._scanTimer = null;
    this._cameraStream?.getTracks().forEach((track) => track.stop());
    this._cameraStream = null;
    const video = this.shadowRoot?.getElementById("video");
    if (video) video.srcObject = null;
    this.shadowRoot?.getElementById("camera")?.classList.remove("active");
    const button = this.shadowRoot?.getElementById("camera-button");
    if (button) button.textContent = this._copy.scanCode;
  }

  _showNotice(message, kind = "info") {
    const notice = this.shadowRoot.getElementById("notice");
    notice.textContent = message;
    notice.className = `notice show ${kind}`;
    window.clearTimeout(this._noticeTimer);
    this._noticeTimer = window.setTimeout(() => notice.classList.remove("show"), 7000);
  }

  _formatDate(value) {
    if (!value) return "—";
    return new Intl.DateTimeFormat(this._hass.language || undefined, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(new Date(value));
  }
}

if (!customElements.get("turris-gadgets-panel")) {
  customElements.define("turris-gadgets-panel", TurrisGadgetsPanel);
}
