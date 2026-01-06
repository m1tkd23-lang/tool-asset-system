//src/tool_asset_system/web/static/tooling_lists_new.js

(() => {
    "use strict";

    const STORE_KEY = "tool-asset-system:tooling_list_new:selected_asms:v1";

    /** @typedef {{assembly_code:string, tool_no:string, qty:number}} SelAsm */

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

    function saveStore(store) {
        try {
            localStorage.setItem(STORE_KEY, JSON.stringify(store));
        } catch { }
    }

    function clearStore(store) {
        for (const k of Object.keys(store)) delete store[k];
        try {
            localStorage.removeItem(STORE_KEY);
        } catch { }
    }

    const form = document.getElementById("tl_new_form");
    const hiddenBox = document.getElementById("selected-asm-hidden");
    if (!form || !hiddenBox) return;

    const store = loadStore();

    function normToolNo(v) {
        return (v ?? "").toString().trim();
    }

    function normQty(v) {
        const s = (v ?? "").toString().trim();
        if (!s) return 1;
        const n = Number(s);
        return Number.isFinite(n) && n > 0 ? n : 1;
    }

    function setRowSelected(tr, selected) {
        if (selected) tr.classList.add("is-selected");
        else tr.classList.remove("is-selected");
    }

    function readRow(tr) {
        const assembly_code = tr.dataset.assemblyCode || "";
        const toolNoEl = tr.querySelector(".pick-toolno");
        const qtyEl = tr.querySelector(".pick-qty");
        const tool_no = normToolNo(toolNoEl ? toolNoEl.value : "");
        const qty = normQty(qtyEl ? qtyEl.value : "1");
        return { assembly_code, tool_no, qty };
    }

    function restoreUI() {
        const rows = document.querySelectorAll(".pick-asm-table tbody tr");
        rows.forEach((tr) => {
            if (!(tr instanceof HTMLTableRowElement)) return;
            const ac = tr.dataset.assemblyCode || "";
            const chk = tr.querySelector(".pick-check");
            const toolNoEl = tr.querySelector(".pick-toolno");
            const qtyEl = tr.querySelector(".pick-qty");

            const it = store[ac];
            const isSel = !!it;

            if (chk && chk instanceof HTMLInputElement) chk.checked = isSel;
            setRowSelected(tr, isSel);

            if (isSel) {
                if (toolNoEl && "value" in toolNoEl) toolNoEl.value = it.tool_no ?? "";
                if (qtyEl && qtyEl instanceof HTMLInputElement) qtyEl.value = String(it.qty ?? 1);
            }
        });
    }

    function attachHandlers() {
        const rows = document.querySelectorAll(".pick-asm-table tbody tr");
        rows.forEach((tr) => {
            if (!(tr instanceof HTMLTableRowElement)) return;
            const ac = tr.dataset.assemblyCode || "";
            const chk = tr.querySelector(".pick-check");
            const toolNoEl = tr.querySelector(".pick-toolno");
            const qtyEl = tr.querySelector(".pick-qty");

            if (chk && chk instanceof HTMLInputElement) {
                chk.addEventListener("change", () => {
                    if (chk.checked) {
                        store[ac] = readRow(tr);
                        setRowSelected(tr, true);
                    } else {
                        delete store[ac];
                        setRowSelected(tr, false);
                    }
                    saveStore(store);
                });
            }

            const onChange = () => {
                if (!store[ac]) return;
                store[ac] = readRow(tr);
                saveStore(store);
            };

            if (toolNoEl) toolNoEl.addEventListener("input", onChange);
            if (toolNoEl) toolNoEl.addEventListener("change", onChange);
            if (qtyEl) qtyEl.addEventListener("input", onChange);
            if (qtyEl) qtyEl.addEventListener("change", onChange);
        });
    }

    function clearHiddenBox() {
        while (hiddenBox.firstChild) hiddenBox.removeChild(hiddenBox.firstChild);
    }

    function addHidden(name, value) {
        const inp = document.createElement("input");
        inp.type = "hidden";
        inp.name = name;
        inp.value = value;
        hiddenBox.appendChild(inp);
    }

    function showToast(message) {
        const el = document.createElement("div");
        el.className = "copy-toast";
        el.textContent = message;
        document.body.appendChild(el);
        el.style.top = "14px";
        el.style.right = "14px";
        requestAnimationFrame(() => el.classList.add("is-visible"));
        window.setTimeout(() => {
            el.classList.remove("is-visible");
            window.setTimeout(() => el.remove(), 250);
        }, 1400);
    }

    function detectCreatedCode() {
        const url = new URL(window.location.href);
        const created = url.searchParams.get("created");
        if (created) return created;

        const flashRoot = document.querySelector(".flash-messages") || document.body;
        const text = (flashRoot.textContent || "").trim();
        const m = text.match(/Created:\s*(TL_\d+)/);
        if (m) return m[1];

        return null;
    }

    function cleanupCreatedParam() {
        const url = new URL(window.location.href);
        if (!url.searchParams.has("created")) return;
        url.searchParams.delete("created");
        window.history.replaceState({}, "", url.pathname + (url.search ? url.search : ""));
    }

    form.addEventListener("submit", (ev) => {
        const selected = Object.values(store);

        if (selected.length === 0) {
            ev.preventDefault();
            alert("選択された ASM がありません（チェックしてください）");
            return;
        }

        // tool_no 未入力のチェック（ここで止める：DBのUNIQUEより親切）
        const missing = selected.find((it) => !normToolNo(it.tool_no));
        if (missing) {
            ev.preventDefault();
            alert(`tool_no が未入力です：${missing.assembly_code}`);
            return;
        }

        clearHiddenBox();

        // 注入
        for (const it of selected) addHidden("selected_assemblies", it.assembly_code);
        for (const it of selected) {
            addHidden(`tool_no_${it.assembly_code}`, it.tool_no);
            addHidden(`qty_${it.assembly_code}`, String(it.qty ?? 1));
        }
    });

    // init
    attachHandlers();
    restoreUI();

    const created = detectCreatedCode();
    if (created) {
        showToast(`Created: ${created}`);
        clearStore(store);
        restoreUI();
        cleanupCreatedParam();
    }
})();
