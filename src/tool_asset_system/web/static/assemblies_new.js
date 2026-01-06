// static/assemblies_new.js
(() => {
    "use strict";

    // =========================
    // Business rule: layer order
    // =========================
    const LAYER_ORDER = [
        "HOLDER",
        "SUB_HOLDER",
        "TOOL_BODY",
        "INSERT",
        "SOLID_TOOL",
        "SCREW",
        "ACCESSORY",
    ];
    const layerRank = Object.fromEntries(LAYER_ORDER.map((k, i) => [k, i]));

    // =========================
    // Storage (keep selection across filter GET reloads)
    // =========================
    const STORE_KEY = "tool-asset-system:asm_new:selected_parts:v1";

    /** @typedef {{asset_code:string, layer:string, role:string, qty:number}} SelItem */

    /** @returns {Record<string, SelItem>} */
    function loadStore() {
        try {
            const raw = localStorage.getItem(STORE_KEY);
            if (!raw) return {};
            const obj = JSON.parse(raw);
            if (!obj || typeof obj !== "object") return {};
            return obj;
        } catch {
            return {};
        }
    }

    /** @param {Record<string, SelItem>} store */
    function saveStore(store) {
        try {
            localStorage.setItem(STORE_KEY, JSON.stringify(store));
        } catch {
            // ignore
        }
    }

    /** @param {Record<string, SelItem>} store */
    function clearStore(store) {
        for (const k of Object.keys(store)) delete store[k];
        try {
            localStorage.removeItem(STORE_KEY);
        } catch {
            // ignore
        }
    }

    // =========================
    // DOM
    // =========================
    const asmForm = document.getElementById("asm_new_form");
    const previewEl = document.getElementById("signature-preview");
    const hiddenBox = document.getElementById("selected-parts-hidden");

    // hiddenBox は「selected_parts を hidden で注入」するため必須
    if (!asmForm || !previewEl || !hiddenBox) return;

    // store: asset_code -> SelItem
    const store = loadStore();

    // =========================
    // Helpers
    // =========================
    function normRole(v) {
        return (v ?? "").toString().trim();
    }
    function normQty(v) {
        const s = (v ?? "").toString().trim();
        if (!s) return 1;
        const n = Number(s);
        return Number.isFinite(n) && n > 0 ? n : 1;
    }

    /** @param {SelItem} a @param {SelItem} b */
    function compareSel(a, b) {
        const ra = layerRank[a.layer] ?? 999;
        const rb = layerRank[b.layer] ?? 999;
        if (ra !== rb) return ra - rb;
        return a.asset_code.localeCompare(b.asset_code);
    }

    function buildSignature() {
        const items = Object.values(store).sort(compareSel);
        return items.map((x) => x.asset_code).join("_");
    }

    function updatePreview() {
        const sig = buildSignature();
        previewEl.textContent = sig || "(none)";
    }

    function setRowSelected(tr, selected) {
        if (selected) tr.classList.add("is-selected");
        else tr.classList.remove("is-selected");
    }

    /** @param {HTMLTableRowElement} tr */
    function readRow(tr) {
        const asset_code = tr.dataset.assetCode || "";
        const layer = tr.dataset.layer || "";
        const roleEl = tr.querySelector(".pick-role");
        const qtyEl = tr.querySelector(".pick-qty");
        const role = normRole(roleEl ? roleEl.value : "");
        const qty = normQty(qtyEl ? qtyEl.value : "1");
        return { asset_code, layer, role, qty };
    }

    function restoreUIFromStore() {
        const rows = document.querySelectorAll(".pick-parts-table tbody tr");
        rows.forEach((tr) => {
            if (!(tr instanceof HTMLTableRowElement)) return;
            const ac = tr.dataset.assetCode || "";
            const chk = tr.querySelector(".pick-check");
            const roleEl = tr.querySelector(".pick-role");
            const qtyEl = tr.querySelector(".pick-qty");

            const it = store[ac];
            const isSel = !!it;

            if (chk && chk instanceof HTMLInputElement) chk.checked = isSel;
            setRowSelected(tr, isSel);

            if (isSel) {
                if (roleEl && "value" in roleEl) roleEl.value = it.role ?? "";
                if (qtyEl && qtyEl instanceof HTMLInputElement)
                    qtyEl.value = String(it.qty ?? 1);
            }
        });

        updatePreview();
    }

    // =========================
    // Wire: checkbox + role/qty
    // =========================
    function attachHandlers() {
        const rows = document.querySelectorAll(".pick-parts-table tbody tr");
        rows.forEach((tr) => {
            if (!(tr instanceof HTMLTableRowElement)) return;
            const ac = tr.dataset.assetCode || "";
            const layer = tr.dataset.layer || "";
            const chk = tr.querySelector(".pick-check");
            const roleEl = tr.querySelector(".pick-role");
            const qtyEl = tr.querySelector(".pick-qty");

            if (chk && chk instanceof HTMLInputElement) {
                chk.addEventListener("change", () => {
                    if (chk.checked) {
                        const data = readRow(tr);
                        data.layer = data.layer || layer;
                        store[ac] = data;
                        setRowSelected(tr, true);
                    } else {
                        delete store[ac];
                        setRowSelected(tr, false);
                    }
                    saveStore(store);
                    updatePreview();
                });
            }

            const onRoleQtyChange = () => {
                if (!store[ac]) return;
                const data = readRow(tr);
                data.layer = data.layer || store[ac].layer || layer;
                store[ac] = data;
                saveStore(store);
                updatePreview();
            };

            if (roleEl) roleEl.addEventListener("change", onRoleQtyChange);
            if (qtyEl) {
                qtyEl.addEventListener("change", onRoleQtyChange);
                qtyEl.addEventListener("input", onRoleQtyChange);
            }
        });
    }

    // =========================
    // Create ASM submit: inject hidden fields
    // =========================
    function clearHiddenBox() {
        while (hiddenBox.firstChild) hiddenBox.removeChild(hiddenBox.firstChild);
    }

    function hasInputNamed(name) {
        // CSS.escape が無い環境の保険
        const esc = window.CSS && CSS.escape ? CSS.escape(name) : name.replace(/"/g, '\\"');
        return asmForm.querySelector(`[name="${esc}"]`) !== null;
    }

    function addHidden(name, value) {
        const inp = document.createElement("input");
        inp.type = "hidden";
        inp.name = name;
        inp.value = value;
        hiddenBox.appendChild(inp);
    }

    function getSubmitter(ev) {
        // ev.submitter が取れない環境の保険
        return ev.submitter || document.activeElement;
    }

    asmForm.addEventListener("submit", (ev) => {
        const submitter = getSubmitter(ev);

        // createボタン以外のsubmitが来たら何もしない（保険）
        if (
            submitter &&
            submitter instanceof HTMLElement &&
            submitter.getAttribute("name") === "action" &&
            submitter.getAttribute("value") !== "create"
        ) {
            return;
        }

        const selected = Object.values(store);
        if (selected.length === 0) {
            ev.preventDefault();
            alert("選択された parts がありません（チェックしてください）");
            return;
        }

        clearHiddenBox();

        selected.sort(compareSel);

        for (const it of selected) addHidden("selected_parts", it.asset_code);

        for (const it of selected) {
            const roleName = `role_${it.asset_code}`;
            const qtyName = `qty_${it.asset_code}`;

            if (!hasInputNamed(roleName)) addHidden(roleName, it.role ?? "");
            if (!hasInputNamed(qtyName)) addHidden(qtyName, String(it.qty ?? 1));
        }
    });

    // =========================
    // Toast (light notification)
    // =========================
    function showToast(message) {
        const el = document.createElement("div");
        el.className = "copy-toast";
        el.textContent = message;
        document.body.appendChild(el);

        // position (top-right)
        el.style.top = "14px";
        el.style.right = "14px";

        requestAnimationFrame(() => el.classList.add("is-visible"));

        window.setTimeout(() => {
            el.classList.remove("is-visible");
            window.setTimeout(() => el.remove(), 250);
        }, 1400);
    }

    // =========================
    // Success detection
    // 1) URL ?created=ASM_xxx
    // 2) Flash text includes "Created: ASM_xxx" (200返しでも拾う)
    // =========================
    function detectCreatedCode() {
        const url = new URL(window.location.href);
        const created = url.searchParams.get("created");
        if (created) return { code: created, via: "query" };

        // flash のテキストから拾う（base.html が flash を表示している前提）
        const flashRoot = document.querySelector(".flash-messages") || document.body;
        const text = (flashRoot.textContent || "").trim();
        const m = text.match(/Created:\s*(ASM_\d+)/);
        if (m) return { code: m[1], via: "flash" };

        return null;
    }

    function cleanupCreatedParamInUrl() {
        const url = new URL(window.location.href);
        if (!url.searchParams.has("created")) return;
        url.searchParams.delete("created");
        window.history.replaceState({}, "", url.pathname + (url.search ? url.search : ""));
    }

    function resetAfterSuccess(createdCode) {
        // toast
        showToast(`Created: ${createdCode}`);

        // clear localStorage selection
        clearStore(store);

        // uncheck in UI + preview update
        restoreUIFromStore();

        // URL掃除（created付きで戻ってきた場合）
        cleanupCreatedParamInUrl();
    }

    // =========================
    // Init
    // =========================
    attachHandlers();
    restoreUIFromStore();

    const createdInfo = detectCreatedCode();
    if (createdInfo && createdInfo.code) {
        resetAfterSuccess(createdInfo.code);
    }

    // Optional: expose manual clear
    window.asmNewClearSelection = function () {
        clearStore(store);
        restoreUIFromStore();
        showToast("Selection cleared");
    };
})();
