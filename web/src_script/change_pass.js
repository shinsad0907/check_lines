document.addEventListener('DOMContentLoaded', function () {
    setupContextMenu();
    bindTableEvents();
    bindControlEvents();
    togglePasswordInput();
});

// Lắng nghe click nút tắt và get cookie
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('chrome-close-btn')) {
        const uid = e.target.getAttribute('data-uid');
        eel.close_chrome_by_uid(uid);
        e.target.disabled = true;
        e.target.textContent = "Đang tắt...";
    }
    if (e.target.classList.contains('get-cookie-btn')) {
        const uid = e.target.getAttribute('data-uid');
        console.log("Getting cookie for UID:", uid); // Debug log
        eel.get_cookie_by_uid(uid);
        e.target.disabled = true;
        e.target.textContent = "Đang lấy...";
    }
});

// ====== CONTEXT MENU ======
function setupContextMenu() {
    const contextMenu = document.createElement('div');
    contextMenu.className = 'context-menu';
    contextMenu.innerHTML = `
        <div class="context-menu-item" id="add-mail">Nhập Mail Email/Pass hoặc Email</div>
        <div class="context-menu-item" id="add-proxy">Nhập Proxy</div>
        <div class="context-menu-separator"></div>
        <div class="context-menu-item" id="select-all-menu">Chọn tất cả</div>
        <div class="context-menu-item" id="deselect-all-menu">Bỏ chọn tất cả</div>
        <div class="context-menu-item" id="select-errors">Chọn tài khoản bôi đen</div>
        <div class="context-menu-separator"></div>
        <div class="context-menu-item" id="delete-mail">Xóa mail</div>
    `;
    document.body.appendChild(contextMenu);

    document.addEventListener('contextmenu', function (e) {
        e.preventDefault();
        contextMenu.style.display = 'block';
        contextMenu.style.left = e.pageX + 'px';
        contextMenu.style.top = e.pageY + 'px';
    });

    document.addEventListener('click', function () {
        contextMenu.style.display = 'none';
    });

    contextMenu.addEventListener('click', handleContextMenuClick);
}

async function handleContextMenuClick(e) {
    const id = e.target.id;
    if (!id) return;
    document.querySelector('.context-menu').style.display = 'none';
    switch (id) {
        case 'add-mail':
            try {
                const text = await navigator.clipboard.readText();
                if (text) {
                    addMailsFromText(text);
                } else {
                    alert('Clipboard trống!');
                }
            } catch (err) {
                alert('Không thể đọc clipboard. Hãy cấp quyền truy cập clipboard cho trình duyệt.');
            }
            break;
        case 'add-proxy':
            alert('Nhập Proxy');
            break;
        case 'select-all-menu':
            selectAllRows(true);
            break;
        case 'deselect-all-menu':
            selectAllRows(false);
            break;
        case 'select-errors':
            selectErrorRows();
            break;
        case 'delete-mail':
            deleteSelectedRows();
            break;
    }
}

// ====== TABLE EVENTS ======
function bindTableEvents() {
    bindRowCheckboxEvents();

    const tbody = document.getElementById('account-tbody');
    let lastSelectedRow = null;
    tbody.addEventListener('click', function (e) {
        if (e.target.classList.contains('row-checkbox')) return;
        const row = e.target.closest('tr');
        if (!row) return;
        const rows = Array.from(tbody.querySelectorAll('tr'));
        if (e.ctrlKey || e.metaKey) {
            row.classList.toggle('selected');
        } else if (e.shiftKey && lastSelectedRow) {
            const start = rows.indexOf(lastSelectedRow);
            const end = rows.indexOf(row);
            const [min, max] = [Math.min(start, end), Math.max(start, end)];
            rows.forEach((r, i) => {
                if (i >= min && i <= max) r.classList.add('selected');
            });
        } else {
            rows.forEach(r => r.classList.remove('selected'));
            row.classList.add('selected');
        }
        lastSelectedRow = row;
        updateSelectedCount();
    });

    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function () {
            selectAllRows(this.checked);
        });
    }

    document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'a') {
            const rows = document.querySelectorAll('#account-tbody tr');
            rows.forEach(row => row.classList.add('selected'));
            updateSelectedCount();
            e.preventDefault();
        }
    });
}

function bindRowCheckboxEvents() {
    document.querySelectorAll('.row-checkbox').forEach(cb => {
        cb.removeEventListener('change', rowCheckboxHandler);
        cb.addEventListener('change', rowCheckboxHandler);
    });
}

function rowCheckboxHandler() {
    const row = this.closest('tr');
    if (this.checked) {
        row.classList.add('selected');
    } else {
        row.classList.remove('selected');
    }
    updateSelectedCount();
}

function addMailsFromText(inputText) {
    const tbody = document.getElementById('account-tbody');
    const lines = inputText.split('\n').map(line => line.trim()).filter(line => line);
    let stt = tbody.querySelectorAll('tr').length + 1;
    lines.forEach(line => {
        const parts = line.split('|');
        if (parts.length < 3) return;
        const [uid, mail, code] = parts;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><input type="checkbox" class="row-checkbox"></td>
            <td>${stt++}</td>
            <td>${uid}</td>
            <td></td>
            <td>${mail}</td>
            <td></td>
            <td></td>
            <td>${code}</td>
            <td><span style="color: #dcdcaa;">⏳ Pending</span></td>
            <td></td>
        `;
        tbody.appendChild(tr);
    });
    bindRowCheckboxEvents();
    updateSelectedCount();
}

function selectAllRows(checked) {
    document.querySelectorAll('#account-tbody tr').forEach(tr => {
        tr.classList.toggle('selected', checked);
        tr.querySelector('.row-checkbox').checked = checked;
    });
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) selectAllCheckbox.checked = checked;
    updateSelectedCount();
}

function selectErrorRows() {
    document.querySelectorAll('#account-tbody tr').forEach(tr => {
        if (tr.classList.contains('selected')) {
            tr.querySelector('.row-checkbox').checked = true;
        } else {
            tr.querySelector('.row-checkbox').checked = false;
        }
    });
    updateSelectedCount();
}

function deleteSelectedRows() {
    document.querySelectorAll('#account-tbody tr.selected').forEach(tr => tr.remove());
    updateSelectedCount();
    
}

function updateSelectedCount() {
    const count = document.querySelectorAll('#account-tbody tr.selected').length;
    const countEl = document.getElementById('selected-count');
    if (countEl) countEl.textContent = 'Đã chọn: ' + count;
}

// ====== CONTROL PANEL EVENTS ======
function bindControlEvents() {
    const passwordTypeSelect = document.getElementById('password-type');
    if (passwordTypeSelect) {
        passwordTypeSelect.addEventListener('change', togglePasswordInput);
    }

    const startBtn = document.getElementById('start-btn');
    if (startBtn) {
        startBtn.addEventListener('click', handleStartClick);
    }
}

function togglePasswordInput() {
    const passwordTypeSelect = document.getElementById('password-type');
    const passwordInput = document.getElementById('password-input');
    if (passwordTypeSelect && passwordInput) {
        if (passwordTypeSelect.selectedIndex === 0) {
            passwordInput.disabled = false;
            passwordInput.style.backgroundColor = '';
        } else {
            passwordInput.disabled = true;
            passwordInput.value = '';
            passwordInput.style.backgroundColor = '#eee';
        }
    }
}

// Hiển thị nút Chrome khi chạy
function showChromeButtonsForRunningAccounts(accounts, autoGetCookie) {
    console.log("showChromeButtonsForRunningAccounts called with:", accounts, autoGetCookie);
    
    // Xóa nút cũ trước - cập nhật selector cho đúng
    document.querySelectorAll('#account-tbody tr').forEach(row => {
        const chromeTd = row.querySelector('td:nth-child(10)'); // Cột CHROME là cột thứ 10
        if (chromeTd) {
            chromeTd.innerHTML = '';
        }
    });
    
    accounts.forEach((acc, idx) => {
        const rows = document.querySelectorAll('#account-tbody tr');
        rows.forEach(row => {
            const uidTd = row.querySelector('td:nth-child(3)'); // Cột UID là cột thứ 3
            const chromeTd = row.querySelector('td:nth-child(10)'); // Cột CHROME là cột thứ 10
            
            if (uidTd && chromeTd && uidTd.textContent.trim() === String(acc.uid)) {
                console.log(`Updating Chrome buttons for UID: ${acc.uid}`);
                
                if (autoGetCookie) {
                    chromeTd.innerHTML = `<span class="chrome-name">Chrome ${idx + 1}</span>`;
                } else {
                    chromeTd.innerHTML = `
                        <span class="chrome-name">Chrome ${idx + 1}</span> 
                        <button class="get-cookie-btn" data-uid="${acc.uid}">Lấy Cookie</button>
                        <button class="chrome-close-btn" data-uid="${acc.uid}">Tắt</button>
                    `;
                }
            }
        });
    });
}

function handleStartClick() {
    // Lấy các dòng đã chọn
    const checkedRows = document.querySelectorAll('#account-tbody .row-checkbox:checked');
    if (checkedRows.length === 0) {
        alert('Vui lòng chọn tài khoản để xử lý!');
        return;
    }

    // Lấy loại mật khẩu
    const passwordTypeSelect = document.getElementById('password-type');
    let type_password = 2; // 2: ngẫu nhiên, 1: tự nhập
    if (passwordTypeSelect && passwordTypeSelect.selectedIndex === 0) {
        type_password = 1;
    }

    // Lấy mật khẩu
    const passwordInput = document.getElementById('password-input');
    const password = passwordInput ? passwordInput.value.trim() : '';
    if (type_password === 1 && !password) {
        alert('Vui lòng nhập mật khẩu!');
        return;
    }

    // Lấy số luồng
    const threadInput = document.getElementById('thread-count');
    let thread = threadInput ? threadInput.value.trim() : '5';
    thread = Number(thread);

    // Lấy proxy
    const proxyInput = document.getElementById('proxy-input');
    const proxy = proxyInput ? proxyInput.value.trim() : 'no ()';

    // Reset status for all selected accounts to "Pending"
    checkedRows.forEach(cb => {
        const row = cb.closest('tr');
        const statusCell = row.querySelector('td:nth-last-child(2)');
        if (statusCell) {
            statusCell.innerHTML = '<span style="color: #dcdcaa;">⏳ Pending</span>';
        }
    });

    // Lấy danh sách tài khoản đã chọn
    const accounts = [];
    checkedRows.forEach(cb => {
        const row = cb.closest('tr');
        const uid = row.cells[2].textContent;
        const cookie = row.cells[3].textContent;
        const mail = row.cells[4].textContent;
        const oldPass = row.cells[5].textContent;
        const proxy = row.cells[6].textContent;
        const code = row.cells[7].textContent;
        
        accounts.push({
            uid: uid,
            cookie: cookie,
            mail: mail,
            pass: oldPass,
            proxy: proxy,
            code: code
        });
    });

    // Create data object
    const autoGetCookie = document.getElementById('auto-get-cookie').checked;
    const data = {
        account: accounts,
        proxy: proxy,
        type_password: type_password,
        password: password,
        thread: thread,
        type: "change_pass",
        auto_get_cookie: autoGetCookie
    };

    console.log("Starting password change process with data:", data);

    // Disable start button and enable stop button
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-change-pass');
    if (startBtn) startBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = false;

    // Start the process
    eel.process_2fa_data(data);
}

// Update UI when process stops
eel.expose(onProcessStopped);
function onProcessStopped() {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-change-pass');
    if (startBtn) startBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
}

// Update UI when a batch completes
eel.expose(onBatchComplete);
function onBatchComplete() {
    console.log("Batch completed");
}

// Handle account status updates
eel.expose(updateAccountStatus);
function updateAccountStatus(uid, statusText, color) {
    console.log(`Updating status for ${uid}: ${statusText}`);
    
    if (uid === "ALL") {
        // Update all accounts
        const rows = document.querySelectorAll('#account-tbody tr');
        rows.forEach(row => {
            const statusCell = row.querySelector('td:nth-last-child(2)');
            if (statusCell) {
                statusCell.innerHTML = `<span style="color: ${color}">${statusText}</span>`;
            }
        });
        
        // Re-enable start button
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-change-pass');
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
        return;
    }
    
    // Update specific account
    const rows = document.querySelectorAll('#account-tbody tr');
    rows.forEach(row => {
        if (row.cells[2].textContent === uid) {
            const statusCell = row.querySelector('td:nth-last-child(2)');
            if (statusCell) {
                statusCell.innerHTML = `<span style="color: ${color}">${statusText}</span>`;
            }
        }
    });
}

// Stop process
function stopProcess() {
    console.log("Stopping password change process...");
    eel.stop_all_selenium()();
    
    const stopBtn = document.getElementById('stop-change-pass');
    if (stopBtn) stopBtn.disabled = true;
}
function exportData() {
    // Lấy các dòng được tích checkbox
    const checkedRows = Array.from(document.querySelectorAll('#account-tbody .row-checkbox:checked'));
    if (checkedRows.length === 0) {
        alert('Vui lòng chọn ít nhất một tài khoản để xuất!');
        return;
    }

    // Lấy dữ liệu từng dòng, chỉ lấy cột 2,3,4,5 (tds[1] đến tds[4]), ngăn cách bởi |
    const lines = checkedRows.map(cb => {
        const tds = cb.closest('tr').querySelectorAll('td');
        // tds[1]: STT, tds[2]: UID, tds[3]: COOKIE, tds[4]: EMAIL
        const values = [
            tds[2]?.textContent.trim() || "",
            tds[3]?.textContent.trim() || "",
            tds[4]?.textContent.trim() || "",
            tds[5]?.textContent.trim() || ""
        ];
        return values.join('|');
    });

    // Gửi sang Python để lưu file
    eel.save_exported_accounts(lines)(function(result) {
        if (result && result.success) {
            alert('Xuất file thành công!');
        } else if (result && result.cancelled) {
            // Người dùng bấm Cancel
        } else {
            alert('Có lỗi khi lưu file!');
        }
    });
}
eel.expose(onGetCookie);
function onGetCookie(uid, newPass, cookies) {
    console.log(`Received cookies for ${uid}:`, cookies); // Debug log
    const rows = document.querySelectorAll('#account-tbody tr');
    rows.forEach(row => {
        const tds = row.querySelectorAll('td');
        if (tds[2] && tds[2].textContent.trim() === String(uid)) {
            // Cập nhật cột PASS (tds[5])
            if (newPass) tds[5].textContent = newPass;

            // Chuyển cookies thành string
            const cookieStr = cookies.map(c => `${c.name}=${c.value}`).join('; ');
            tds[3].textContent = cookieStr;
            console.log(`Updated cookie for ${uid}: ${cookieStr}`); // Debug log
            
            // Ẩn nút "Lấy Cookie" sau khi lấy thành công
            const chromeCell = tds[9];
            if (chromeCell) {
                const getCookieBtn = chromeCell.querySelector('.get-cookie-btn');
                if (getCookieBtn) {
                    getCookieBtn.style.display = 'none';
                }
            }
        }
    });
}