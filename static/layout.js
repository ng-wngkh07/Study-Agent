/* Bố cục giao diện: thu gọn / mở thanh bên, ngăn kéo trên điện thoại,
   và ẩn màn hình chào khi cuộc trò chuyện đã bắt đầu.
   File này chỉ xử lý giao diện, không đụng tới logic hỏi đáp. */
(function () {
    "use strict";
    const body = document.body;
    const mobileQuery = window.matchMedia("(max-width: 900px)");
    const STORE_KEY = "sidebar_collapsed";

    function isMobile() { return mobileQuery.matches; }

    function readCollapsed() {
        try { return localStorage.getItem(STORE_KEY) === "1"; } catch (e) { return false; }
    }
    function saveCollapsed(value) {
        try { localStorage.setItem(STORE_KEY, value ? "1" : "0"); } catch (e) { /* bỏ qua */ }
    }

    function closeSidebar() {
        if (isMobile()) {
            body.classList.remove("sidebar-open");
        } else {
            body.classList.add("sidebar-collapsed");
            saveCollapsed(true);
        }
    }
    function openSidebar() {
        if (isMobile()) {
            body.classList.add("sidebar-open");
        } else {
            body.classList.remove("sidebar-collapsed");
            saveCollapsed(false);
        }
    }

    if (readCollapsed() && !isMobile()) body.classList.add("sidebar-collapsed");

    document.getElementById("btn-collapse-sidebar")?.addEventListener("click", closeSidebar);
    document.getElementById("btn-open-sidebar")?.addEventListener("click", openSidebar);
    document.getElementById("sidebar-backdrop")?.addEventListener("click", () => body.classList.remove("sidebar-open"));
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") body.classList.remove("sidebar-open");
    });

    // Trên điện thoại: chọn chế độ / cuộc trò chuyện / chat mới xong thì tự đóng ngăn kéo.
    document.getElementById("sidebar")?.addEventListener("click", (e) => {
        if (!isMobile()) return;
        if (e.target.closest(".mode-button, #btn-new-chat-sidebar, .session-info, .history-open, #btn-open-timetable")) {
            body.classList.remove("sidebar-open");
        }
    });
    mobileQuery.addEventListener?.("change", () => body.classList.remove("sidebar-open"));

    // Ẩn màn hình chào khi đã có tin nhắn thật trong khung chat.
    const container = document.getElementById("messages-container");
    if (container) {
        const sync = () => {
            const hasChat = !!container.querySelector(":scope > .message:not(.welcome-card)");
            container.classList.toggle("has-chat", hasChat);
        };
        new MutationObserver(sync).observe(container, { childList: true });
        sync();
    }
})();
