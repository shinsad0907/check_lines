function activateKey() {
    const key = document.getElementById('activation-key').value.trim();
    const statusEl = document.getElementById('activation-status');
    if (!key) {
        statusEl.textContent = "Vui lòng nhập key!";
        statusEl.style.color = "#f44747";
        return;
    }
    eel.check_activation_key(key)(function(result) {
        // result là object: {status: true/false, message: "..."}
        if (result.status === true) {
            statusEl.textContent = result.message || "Kích hoạt thành công!";
            statusEl.style.color = "#4ec9b0";
            setTimeout(() => {
                eel.reload_main();
            }, 1000);
        } else {
            statusEl.textContent = result.message || "Key không hợp lệ!";
            statusEl.style.color = "#f44747";
        }
    });
}