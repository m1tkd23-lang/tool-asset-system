// src/tool_asset_system/web/static/tooling_lists_new.js
(() => {
    "use strict";

    const ctx = window.__TL_CTX__ || { mode: "new", list_code: "" };
    const mode = ctx.mode || "new";
    const listCode = ctx.list_code || "";

    // ★ listごとにキーを分ける（編集時に他listの選択と混ざらない）
    const STORE_KEY =
        mode === "edit" && listCode
            ? `tool-asset-system:tooling_list_edit:${listCode}:selected_asms:v1`
            : "tool-asset-system:tooling_list_new:selected_asms:v1";

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
        // qtyは整数運用（あなたの要望）
        const m = Math.floor(Number.isFinite(n) && n > 0 ? n : 1);
        return m > 0 ? m : 1;
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

    // ★ 編集初回：DBの既存itemsをbootstrapしてstoreへ
    function bootstrapFromServerIfNeeded() {
        const boot = window.__TL_BOOTSTRAP__ || [];
        if (!Array.isArray(boot) || boot.length === 0) return;

        // すでにstoreに何かあるなら、ユーザー作業優先で上書きしない
        if (Object.keys(store).length > 0) return;

        for (const it of boot) {
            const ac = (it.assembly_code || "").toString().trim();
            if (!ac) continue;
            store[ac] = {
                assembly_code: ac,
                tool_no: (it.tool_no || "").toString().trim(),
                qty: normQty(it.qty ?? 1),
            };
        }
        saveStore(store);
    }

    form.addEventListener("submit", (ev) => {
        const selected = Object.values(store);

        if (selected.length === 0) {
            ev.preventDefault();
            alert("選択された ASM がありません（チェックしてください）");
            return;
        }

        const missing = selected.find((it) => !normToolNo(it.tool_no));
        if (missing) {
            ev.preventDefault();
            alert(`tool_no が未入力です：${missing.assembly_code}`);
            return;
        }

        clearHiddenBox();

        for (const it of selected) addHidden("selected_assemblies", it.assembly_code);
        for (const it of selected) {
            addHidden(`tool_no_${it.assembly_code}`, it.tool_no);
            addHidden(`qty_${it.assembly_code}`, String(normQty(it.qty ?? 1)));
        }
    });

    // init
    bootstrapFromServerIfNeeded();
    attachHandlers();
    restoreUI();

    // newだけ成功toast/clear（editは“詳細に戻る”ので不要）
    if (mode !== "edit") {
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

        function detectReset() {
            const url = new URL(window.location.href);
            return url.searchParams.get("reset");
        }

        function cleanupResetParam() {
            const url = new URL(window.location.href);
            if (!url.searchParams.has("reset")) return;
            url.searchParams.delete("reset");
            window.history.replaceState({}, "", url.pathname + (url.search ? url.search : ""));
        }


        attachHandlers();

        const reset = detectReset();
        if (reset) {
            clearStore(store);
            cleanupResetParam();
        }

        restoreUI();

        const created = detectCreatedCode();
        if (created) {
            showToast(`Created: ${created}`);
            clearStore(store);

            // 画面の入力欄も初期化（これが今回の肝）
            clearInputsOnPage();

            // 念のため：store空で復元（チェック状態の整合）
            restoreUI();

            cleanupCreatedParam();
        }

        function clearInputsOnPage() {
            const rows = document.querySelectorAll(".pick-asm-table tbody tr");
            rows.forEach((tr) => {
                if (!(tr instanceof HTMLTableRowElement)) return;

                const chk = tr.querySelector(".pick-check");
                const toolNoEl = tr.querySelector(".pick-toolno");
                const qtyEl = tr.querySelector(".pick-qty");

                if (chk && chk instanceof HTMLInputElement) chk.checked = false;
                setRowSelected(tr, false);

                if (toolNoEl && "value" in toolNoEl) toolNoEl.value = "";
                if (qtyEl && qtyEl instanceof HTMLInputElement) qtyEl.value = "1";
            });
        }
    }
})();
