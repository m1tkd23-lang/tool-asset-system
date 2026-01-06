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
            // ignore (private mode etc.)
        }
    }

    // =========================
    // DOM
    // =========================
    const asmForm = document.getElementById("asm_new_form");
    const previewEl = document.getElementById("signature-preview");
    const hiddenBox = document.getElementById("selected-parts-hidden");

    if (!asmForm || !previewEl || !hiddenBox) {
        // Template not ready or IDs changed
        return;
    }

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

    /** @param {string} asset_code */
    function ensureStoreHasLayer(asset_code) {
        if (store[asset_code] && store[asset_code].layer) return;

        // try find on current page
        const tr = document.querySelector(
            `.pick-parts-table tbody tr[data-asset-code="${CSS.escape(asset_code)}"]`
        );
        if (tr && tr instanceof HTMLTableRowElement) {
            const layer = tr.dataset.layer || "";
            if (store[asset_code]) store[asset_code].layer = layer;
        }
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

            if (chk && chk instanceof HTMLInputElement) {
                chk.checked = isSel;
            }
            setRowSelected(tr, isSel);

            // restore role/qty for selected rows
            if (isSel) {
                if (roleEl && "value" in roleEl) roleEl.value = it.role ?? "";
                if (qtyEl && qtyEl instanceof HTMLInputElement) qtyEl.value = String(it.qty ?? 1);
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
                        // ensure layer known
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
                // only update store if currently selected
                if (!store[ac]) return;
                const data = readRow(tr);
                data.layer = data.layer || store[ac].layer || layer;
                store[ac] = data;
                saveStore(store);
                updatePreview();
            };

            if (roleEl) roleEl.addEventListener("change", onRoleQtyChange);
            if (qtyEl) qtyEl.addEventListener("change", onRoleQtyChange);
            if (qtyEl) qtyEl.addEventListener("input", onRoleQtyChange);
        });
    }

    // =========================
    // Create ASM submit: inject hidden fields
    // - selected_parts (list)
    // - role_{ac}, qty_{ac} for parts NOT on current page
    // =========================
    function clearHiddenBox() {
        while (hiddenBox.firstChild) hiddenBox.removeChild(hiddenBox.firstChild);
    }

    function hasInputNamed(name) {
        return asmForm.querySelector(`[name="${CSS.escape(name)}"]`) !== null;
    }

    function addHidden(name, value) {
        const inp = document.createElement("input");
        inp.type = "hidden";
        inp.name = name;
        inp.value = value;
        hiddenBox.appendChild(inp);
    }

    asmForm.addEventListener("submit", (ev) => {
        // If user pressed "Search" by mistake inside POST form (should be GET), still avoid creating.
        // But now Search is in separate GET form, so normally not needed.
        // We keep it safe anyway:
        const submitter = ev.submitter;
        if (submitter && submitter.name === "action" && submitter.value === "search") {
            return;
        }

        const selected = Object.values(store);

        // server expects at least one selected_parts when creating
        if (submitter && submitter.name === "action" && submitter.value === "create") {
            if (selected.length === 0) {
                // Let server show flash, but we can block earlier to be kind
                ev.preventDefault();
                alert("選択された parts がありません（チェックしてください）");
                return;
            }
        }

        clearHiddenBox();

        // Always ensure deterministic order on submission (so signature is stable)
        selected.sort(compareSel);

        // 1) selected_parts list
        for (const it of selected) {
            addHidden("selected_parts", it.asset_code);
        }

        // 2) For parts not currently rendered, add role/qty hidden so server can read them
        for (const it of selected) {
            const roleName = `role_${it.asset_code}`;
            const qtyName = `qty_${it.asset_code}`;

            // if inputs exist on page, keep them (user might have edited)
            if (!hasInputNamed(roleName)) addHidden(roleName, it.role ?? "");
            if (!hasInputNamed(qtyName)) addHidden(qtyName, String(it.qty ?? 1));
        }
    });

    // =========================
    // Nice-to-have: clear selection after successful create
    // (We can't detect success from here reliably, but we can clear on leaving detail page etc.)
    // => Do nothing automatically. User can keep picking many assemblies.
    // Provide global helper if needed.
    // =========================
    window.asmNewClearSelection = function () {
        for (const k of Object.keys(store)) delete store[k];
        saveStore(store);
        restoreUIFromStore();
    };

    // =========================
    // Init
    // =========================
    attachHandlers();
    restoreUIFromStore();
})();
