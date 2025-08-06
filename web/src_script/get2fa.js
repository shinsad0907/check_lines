// Khởi tạo biến global
let is2FARunning = false;
let selected2FAAccounts = [];

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('enable-2fa')) {
        setup2FAContextMenu();
        bind2FAEvents();
    }
});

// ===== THÊM CÁC HÀM WRAPPER ĐỂ KẾT NỐI VỚI HTML =====
function toggle2FASelectAll() {
    const checkbox = document.getElementById('twofa-select-all');
    if (checkbox) {
        select2FAAllRows(checkbox.checked);
    }
}

function update2FASelectedCount() {
    const selectedRows = document.querySelectorAll('#twofa-tbody tr.selected');
    const count = selectedRows.length;
    const countEl = document.getElementById('twofa-selected-count');
    if (countEl) {
        countEl.textContent = `Đã chọn: ${count}`;
    }
    updateSelectAllCheckbox();
}

function start2FAEnable() {
    if (is2FARunning) return;
    
    const selectedRows = document.querySelectorAll('#twofa-tbody tr.selected');
    if (selectedRows.length === 0) {
        alert('Vui lòng chọn ít nhất một tài khoản!');
        return;
    }

    // Reset status for all selected accounts to "Pending"
    selectedRows.forEach(row => {
        const statusCell = row.querySelector('td:nth-child(8)');
        if (statusCell) {
            statusCell.innerHTML = '<span style="color: #dcdcaa;">⏳ Pending</span>';
        }
    });

    // Lấy danh sách tài khoản đã chọn và cập nhật trạng thái
    const accounts = [];
    selectedRows.forEach(row => {
        const uid = row.cells[2].textContent;
        const pass = row.cells[3].textContent;
        const cookie = row.cells[4].textContent;
        
        // Cập nhật trạng thái thành Pending ngay khi bắt đầu
        const statusCell = row.querySelector('td:nth-child(8)');
        if (statusCell) {
            statusCell.innerHTML = '<span style="color: #dcdcaa">⏳ Đang xử lý...</span>';
        }
        
        accounts.push({
            uid: uid,
            pass: pass,
            cookie: cookie
        });
    });

    // Lấy cấu hình
    const threadInput = document.getElementById('2fa-thread-count');
    let thread = threadInput ? parseInt(threadInput.value) : 3;
    
    const useProxy = document.getElementById('2fa-use-proxy').checked;
    const proxyType = document.getElementById('2fa-proxy-type').value;
    const createBackupCodes = document.getElementById('2fa-backup-codes').checked;

    // Tạo object data
    const data = {
        accounts: accounts,
        thread_count: thread,
        use_proxy: useProxy,
        proxy_type: proxyType,
        backup_codes: createBackupCodes
    };

    console.log("Starting 2FA process with data:", data);

    // Cập nhật UI
    is2FARunning = true;
    const startBtn = document.getElementById('twofa-start-btn');
    const stopBtn = document.getElementById('twofa-stop-btn');
    
    if (startBtn) {
        startBtn.disabled = true;
        startBtn.textContent = '⏳ ĐANG XỬ LÝ...';
    }
    if (stopBtn) {
        stopBtn.disabled = false;
    }

    // Gửi request sang Python
    eel.start_2fa_process(data);
}

function stop2FAEnable() {
    is2FARunning = false;
    const startBtn = document.getElementById('2fa-start-btn');
    const stopBtn = document.getElementById('2fa-stop-btn');
    
    if (startBtn) {
        startBtn.disabled = false;
        startBtn.textContent = '▶️ BẮT ĐẦU';
    }
    if (stopBtn) {
        stopBtn.disabled = true;
    }
    
    console.log('2FA process stopped');
}

function export2FAData() {
    // Fix: Use correct class name without leading "2"
    const checkedRows = Array.from(document.querySelectorAll('#twofa-tbody .twofa-row-checkbox:checked'));
    if (checkedRows.length === 0) {
        alert('Vui lòng chọn ít nhất một tài khoản để xuất!');
        return;
    }

    // Lấy dữ liệu từng dòng, chỉ lấy cột 2,3,4,5 (tds[1] đến tds[4]), ngăn cách bởi |
    const lines = checkedRows.map(cb => {
        const tds = cb.closest('tr').querySelectorAll('td');
        // tds[1]: STT, tds[2]: UID, tds[3]: PASS, tds[4]: COOKIE
        const values = [
            tds[2]?.textContent.trim() || "",
            tds[3]?.textContent.trim() || "",
            tds[4]?.textContent.trim() || "",
            tds[5]?.textContent.trim() || ""
        ];
        return values.join('|');
    });
    
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

// ===== CÁC HÀM GỐC =====

// Setup context menu riêng cho tab 2FA
function setup2FAContextMenu() {
    const contextMenu2FA = document.createElement('div');
    contextMenu2FA.className = 'context-menu context-menu-2fa';
    contextMenu2FA.innerHTML = `
        <div class="context-menu-item" id="add-mail">Nhập UID|PASS|COOKIE</div>
        <div class="context-menu-item" id="add-proxy">Nhập Proxy</div>
        <div class="context-menu-separator"></div>
        <div class="context-menu-item" id="select-all-menu">Chọn tất cả</div>
        <div class="context-menu-item" id="deselect-all-menu">Bỏ chọn tất cả</div>
        <div class="context-menu-item" id="select-errors">Chọn tài khoản bôi đen</div>
        <div class="context-menu-separator"></div>
        <div class="context-menu-item" id="delete-mail">Xóa mail</div>
    `;
    document.body.appendChild(contextMenu2FA);

    // Lắng nghe right-click trên toàn bộ tab 2FA
    const enable2FATab = document.getElementById('enable-2fa');
    if (enable2FATab) {
        enable2FATab.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            e.stopPropagation();
            showContextMenu(e.pageX, e.pageY);
        });
    }

    // Chặn context menu mặc định cho toàn bộ tab 2FA
    document.addEventListener('contextmenu', function(e) {
        if (e.target.closest('#enable-2fa')) {
            e.preventDefault();
        }
    });

    // Ẩn menu khi click ra ngoài
    document.addEventListener('click', function(e) {
        if (!contextMenu2FA.contains(e.target)) {
            contextMenu2FA.style.display = 'none';
        }
    });

    // Xử lý các action trong menu
    contextMenu2FA.addEventListener('click', handle2FAContextMenuClick);

    function showContextMenu(x, y) {
        contextMenu2FA.style.display = 'block';
        contextMenu2FA.style.left = x + 'px';
        contextMenu2FA.style.top = y + 'px';
    }
}

// Bind events cho tab 2FA
function bind2FAEvents() {
    bind2FATableEvents();
    bind2FARowCheckboxEvents();

    // Thêm event cho select all checkbox
    const selectAllCheckbox = document.getElementById('2fa-select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            select2FAAllRows(this.checked);
        });
    }

    // Thêm shortcut Ctrl+A để chọn tất cả
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'a') {
            const enable2FATab = document.getElementById('enable-2fa');
            if (enable2FATab && enable2FATab.style.display !== 'none') {
                select2FAAllRows(true);
                e.preventDefault();
            }
        }
    });
}

function bind2FATableEvents() {
    const tbody = document.getElementById('twofa-tbody');
    if (!tbody) return;

    let lastSelectedRow = null;
    tbody.addEventListener('click', function(e) {
        if (e.target.classList.contains('2fa-row-checkbox')) return;
        
        const row = e.target.closest('tr');
        if (!row) return;
        
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        if (e.ctrlKey || e.metaKey) {
            row.classList.toggle('selected');
            const checkbox = row.querySelector('.2fa-row-checkbox');
            if (checkbox) {
                checkbox.checked = row.classList.contains('selected');
            }
        } else if (e.shiftKey && lastSelectedRow) {
            const start = rows.indexOf(lastSelectedRow);
            const end = rows.indexOf(row);
            const [min, max] = [Math.min(start, end), Math.max(start, end)];
            rows.forEach((r, i) => {
                if (i >= min && i <= max) {
                    r.classList.add('selected');
                    const checkbox = r.querySelector('.2fa-row-checkbox');
                    if (checkbox) {
                        checkbox.checked = true;
                    }
                }
            });
        } else {
            rows.forEach(r => {
                r.classList.remove('selected');
                const checkbox = r.querySelector('.2fa-row-checkbox');
                if (checkbox) {
                    checkbox.checked = false;
                }
            });
            row.classList.add('selected');
            const checkbox = row.querySelector('.2fa-row-checkbox');
            if (checkbox) {
                checkbox.checked = true;
            }
        }
        
        lastSelectedRow = row;
        update2FASelectedCount();
    });
}

function bind2FARowCheckboxEvents() {
    document.querySelectorAll('.twofa-row-checkbox').forEach(cb => {
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
    update2FASelectedCount();
}

function handle2FAContextMenuClick(e) {
    const id = e.target.id;
    if (!id) return;
    document.querySelector('.context-menu-2fa').style.display = 'none';

    switch (id) {
        case 'add-mail':
            try {
                navigator.clipboard.readText().then(text => {
                    if (text) {
                        add2FAAccountsFromText(text);
                    } else {
                        alert('Clipboard trống!');
                    }
                });
            } catch (err) {
                console.error('Clipboard error:', err);
                alert('Không thể đọc clipboard. Hãy cấp quyền truy cập clipboard cho trình duyệt.');
            }
            break;
        case 'add-proxy':
            try {
                navigator.clipboard.readText().then(text => {
                    if (text) {
                        const proxies = text.trim().split('\n').filter(p => p.trim());
                        if (proxies.length > 0) {
                            const rows = document.querySelectorAll('#2fa-tbody tr.selected');
                            if (rows.length === 0) {
                                alert('Vui lòng chọn ít nhất một dòng để thêm proxy!');
                                return;
                            }
                            rows.forEach((row, index) => {
                                const proxyCell = row.cells[5]; // Cột proxy
                                if (proxyCell) {
                                    proxyCell.textContent = proxies[index % proxies.length];
                                }
                            });
                        } else {
                            alert('Không tìm thấy proxy trong clipboard!');
                        }
                    } else {
                        alert('Clipboard trống!');
                    }
                });
            } catch (err) {
                console.error('Clipboard error:', err);
                alert('Không thể đọc clipboard. Hãy cấp quyền truy cập clipboard cho trình duyệt.');
            }
            break;
        case 'select-all-menu':
            select2FAAllRows(true);
            break;
        case 'deselect-all-menu':
            select2FAAllRows(false);
            break;
        case 'select-errors':
            select2FAErrorRows();
            break;
        case 'delete-mail':
            deleteSelected2FARows();
            break;
    }
}

function add2FAAccountsFromText(inputText) {
    const tbody = document.getElementById('twofa-tbody');
    const lines = inputText.split('\n').map(line => line.trim()).filter(line => line);
    let stt = tbody.querySelectorAll('tr').length + 1;

    lines.forEach(line => {
        const parts = line.split('|');
        if (parts.length < 2) return; // Kiểm tra có đủ UID và PASS không
        
        const [uid, pass, cookie] = parts;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><input type="checkbox" class="twofa-row-checkbox" onchange="update2FASelectedCount()"></td>
            <td>${stt++}</td>
            <td>${uid || ''}</td>
            <td>${pass || ''}</td>
            <td>${cookie || ''}</td>
            <td></td>
            <td></td>
            <td><span style="color: #dcdcaa;">⏳ Pending</span></td>
        `;
        tbody.appendChild(tr);
    });

    // Bind lại events cho các checkbox mới
    bind2FARowCheckboxEvents();
    update2FASelectedCount();
}

function select2FAAllRows(checked) {
    document.querySelectorAll('#twofa-tbody tr').forEach(tr => {
        tr.classList.toggle('selected', checked);
        tr.querySelector('.twofa-row-checkbox').checked = checked;
    });
    const selectAllCheckbox = document.getElementById('2fa-select-all');
    if (selectAllCheckbox) selectAllCheckbox.checked = checked;
    update2FASelectedCount();
}

function select2FAErrorRows() {
    document.querySelectorAll('#twofa-tbody tr').forEach(tr => {
        if (tr.classList.contains('selected')) {
            tr.querySelector('.twofa-row-checkbox').checked = true;
        } else {
            tr.querySelector('.twofa-row-checkbox').checked = false;
        }
    });
    update2FASelectedCount();
}

function deleteSelected2FARows() {
    const tbody = document.getElementById('twofa-tbody');
    if (!tbody) {
        console.error('Không tìm thấy tbody');
        return;
    }

    const selectedRows = tbody.querySelectorAll('tr.selected');
    if (selectedRows.length === 0) {
        alert('Vui lòng chọn ít nhất một dòng để xóa!');
        return;
    }

    if (confirm(`Bạn có chắc muốn xóa ${selectedRows.length} dòng đã chọn?`)) {
        selectedRows.forEach(tr => tbody.removeChild(tr));

        // Cập nhật lại số thứ tự
        const remainingRows = tbody.querySelectorAll('tr');
        remainingRows.forEach((row, index) => {
            const sttCell = row.querySelector('td:nth-child(2)');
            if (sttCell) {
                sttCell.textContent = index + 1;
            }
        });

        update2FASelectedCount();
    }
}

function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('2fa-select-all');
    if (!selectAllCheckbox) return;
    
    const allRows = document.querySelectorAll('#twofa-tbody tr');
    const selectedRows = document.querySelectorAll('#twofa-tbody tr.selected');
    
    if (allRows.length === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    } else if (selectedRows.length === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    } else if (selectedRows.length === allRows.length) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    }
}

// Thêm hàm callback để Python có thể gọi cập nhật trạng thái
eel.expose(update2FAStatus);
function update2FAStatus(uid, status) {
    const tbody = document.getElementById('twofa-tbody');
    if (!tbody) return;

    // Tìm row chứa uid
    const rows = tbody.querySelectorAll('tr');
    for (const row of rows) {
        const uidCell = row.cells[2];
        if (uidCell && uidCell.textContent === uid) {
            const statusCell = row.cells[7];
            if (statusCell) {
                // Set màu dựa vào trạng thái
                let color = '#dcdcaa'; // Default color
                if (status.includes('✅')) color = '#4EC9B0';
                if (status.includes('❌')) color = '#F44747';
                
                statusCell.innerHTML = `<span style="color: ${color}">${status}</span>`;
            }
            break;
        }
    }
}

// Thêm hàm để cập nhật kết quả từ Python
eel.expose(update2FAResult);
function update2FAResult(uid, code2fa, status) {
    console.log(`Updating status for ${uid}: ${code2fa}, ${status}`); // Debug log
    
    // Tìm dòng trong bảng dựa vào UID
    const rows = document.querySelectorAll('#twofa-tbody tr');
    console.log(`Found ${rows.length} rows`); // Debug log
    
    for (let row of rows) {
        const uidCell = row.querySelector('td:nth-child(3)'); // Cột UID là cột thứ 3
        if (uidCell && uidCell.textContent === uid) {
            console.log(`Found row for UID ${uid}`); // Debug log
            
            // Cập nhật mã 2FA (cột thứ 5)
            const code2faCell = row.querySelector('td:nth-child(6)');
            if (code2faCell) {
                code2faCell.textContent = code2fa || '';
                console.log(`Updated 2FA code to ${code2fa}`); // Debug log
            } else {
                console.log('2FA code cell not found'); // Debug log
            }
            
            // Cập nhật trạng thái (cột thứ 8)
            const statusCell = row.querySelector('td:nth-child(8)');
            if (statusCell) {
                const color = status.includes('✅') ? '#4ec9b0' : 
                            status.includes('❌') ? '#f14c4c' : '#dcdcaa';
                statusCell.innerHTML = `<span style="color: ${color}">${status}</span>`;
                console.log(`Updated status to ${status} with color ${color}`); // Debug log
            } else {
                console.log('Status cell not found'); // Debug log
            }
            break;
        }
    }
}