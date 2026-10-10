/* Công tắc giao diện Sáng / Tối.
   - Lưu lựa chọn trong localStorage (khóa "theme").
   - Việc áp dụng theme lúc tải trang được làm bằng script nhỏ trong <head>
     của index.html để không bị nháy màu; file này lo phần bấm công tắc. */
(function () {
    "use strict";
    var KEY = "theme";
    var root = document.documentElement;
    var btn = document.getElementById("theme-toggle");
    if (!btn) return;

    function current() {
        return root.getAttribute("data-theme") === "light" ? "light" : "dark";
    }

    function sync() {
        var isLight = current() === "light";
        btn.setAttribute("aria-checked", isLight ? "true" : "false");
        var label = isLight ? "Đang dùng giao diện sáng. Bấm để chuyển sang giao diện tối"
                            : "Đang dùng giao diện tối. Bấm để chuyển sang giao diện sáng";
        btn.setAttribute("aria-label", label);
        btn.title = isLight ? "Chuyển sang giao diện tối" : "Chuyển sang giao diện sáng";
    }

    function apply(theme) {
        root.classList.add("theme-animating");
        root.setAttribute("data-theme", theme);
        try { localStorage.setItem(KEY, theme); } catch (e) { /* bỏ qua */ }
        sync();
        window.setTimeout(function () { root.classList.remove("theme-animating"); }, 350);
    }

    btn.addEventListener("click", function () {
        apply(current() === "light" ? "dark" : "light");
    });

    sync();
})();
