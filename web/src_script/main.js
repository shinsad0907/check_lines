window.addEventListener('DOMContentLoaded', async () => {
    if (typeof eel !== "undefined") {
        try {
            const info = await eel.get_key_info()();
            if (info && info.key) {
                document.getElementById('key-value').innerText = info.key;
            }
            if (info && info.expiry) {
                document.getElementById('expiry-value').innerText = info.expiry;
                // Đổi màu nếu còn <= 7 ngày
                if (info.expiry.includes('ngày')) {
                    const days = parseInt(info.expiry);
                    if (!isNaN(days)) {
                        document.getElementById('expiry-value').style.color = days <= 7 ? 'red' : '#28a745';
                        document.getElementById('expiry-value').style.fontWeight = days <= 7 ? 'bold' : '';
                    }
                } else {
                    document.getElementById('expiry-value').style.color = '';
                    document.getElementById('expiry-value').style.fontWeight = '';
                }
            }
        } catch (e) {
            document.getElementById('expiry-value').innerText = "Lỗi kết nối";
        }
    }
});
// ...existing code...

// Tab chuyển qua lại
function switchTab(tabId) {
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    const idx = Array.from(document.querySelector('.tab-nav').children).findIndex(btn => btn.onclick && btn.onclick.toString().includes(tabId));
    if (idx >= 0) document.querySelectorAll('.tab-button')[idx].classList.add('active');
}
