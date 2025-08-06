document.addEventListener('DOMContentLoaded', function () {
    setupUnifiedContextMenu();
});

function setupUnifiedContextMenu() {
    // Tạo 1 context menu duy nhất
    const contextMenu = document.createElement('div');
    contextMenu.className = 'context-menu unified-context-menu';
    contextMenu.innerHTML = `
        <div class="context-menu-item" id="add-mail">Nhập UID|PASS|COOKIE</div>
        <div class="context-menu-item" id="add-proxy">Nhập Proxy</div>
        <div class="context-menu-separator"></div>
        <div class="context-menu-item" id="select-all-menu">Chọn tất cả</div>
        <div class="context-menu-item" id="deselect-all-menu">Bỏ chọn tất cả</div>
        <div class="context-menu-item" id="select-errors">Chọn tài khoản bôi đen</div>
        <div class="context-menu-separator"></div>
        <div class="context-menu-item" id="delete-mail">Xóa mail</div>
    `;
    document.body.appendChild(contextMenu);

    // Biến để track tab hiện tại
    let currentTab = 'change-pass';

    // Lắng nghe right-click CHỈ trên các table cụ thể
    const changePassTable = document.getElementById('account-table');
    const scanFriendTable = document.getElementById('scan-friend');
    
    // Event listener cho bảng Change Pass
    if (changePassTable) {
        changePassTable.addEventListener('contextmenu', function (e) {
            e.preventDefault();
            e.stopPropagation();
            currentTab = 'change-pass';
            showContextMenu(e.pageX, e.pageY);
        });
    }

    // Event listener cho bảng Scan Friend
    if (scanFriendTable) {
        scanFriendTable.addEventListener('contextmenu', function (e) {
            e.preventDefault();
            e.stopPropagation();
            currentTab = 'scan-friend';
            showContextMenu(e.pageX, e.pageY);
        });
    }
    
    // Event listener cho bảng 2FA
    const twoFATable = document.getElementById('2fa-table');
    if (twoFATable) {
        twoFATable.addEventListener('contextmenu', function (e) {
            e.preventDefault();
            e.stopPropagation();
            currentTab = 'enable-2fa';
            showContextMenu(e.pageX, e.pageY);
        });
    }

    // QUAN TRỌNG: Chặn context menu mặc định CHỈ cho các table
    document.addEventListener('contextmenu', function (e) {
        // Chỉ preventDefault nếu click vào table
        if (e.target.closest('#account-table') || e.target.closest('#scan-friend')) {
            e.preventDefault();
        }
        // Nếu click ra ngoài table, cho phép context menu mặc định
    });

    // Ẩn menu khi click ra ngoài
    document.addEventListener('click', function (e) {
        if (!contextMenu.contains(e.target)) {
            contextMenu.style.display = 'none';
        }
    });

    // Xử lý click trên menu
    contextMenu.addEventListener('click', function(e) {
        handleUnifiedContextMenuClick(e, currentTab);
    });

    function showContextMenu(x, y) {
        contextMenu.style.display = 'block';
        contextMenu.style.left = x + 'px';
        contextMenu.style.top = y + 'px';
    }
}

async function handleUnifiedContextMenuClick(e, activeTab) {
    const id = e.target.id;
    if (!id) return;
    
    document.querySelector('.unified-context-menu').style.display = 'none';
    
    switch (id) {
        case 'add-mail':
            try {
                const text = await navigator.clipboard.readText();
                if (text) {
                    if (activeTab === 'change-pass') {
                        addMailsFromText(text);
                    } else if (activeTab === 'scan-friend') {
                        addScanFriendMailsFromText(text);
                    }
                } else {
                    alert('Clipboard trống!');
                }
            } catch (err) {
                console.error('Clipboard error:', err);
                alert('Không thể đọc clipboard. Hãy cấp quyền truy cập clipboard cho trình duyệt.');
            }
            break;
        case 'add-proxy':
            if (activeTab === 'change-pass') {
                addProxy();
            } else if (activeTab === 'scan-friend') {
                addScanFriendProxy();
            }
            break;
        case 'select-all-menu':
            if (activeTab === 'change-pass') {
                selectAllRows(true);
            } else if (activeTab === 'scan-friend') {
                selectAllScanFriendRows(true);
            }
            break;
        case 'deselect-all-menu':
            if (activeTab === 'change-pass') {
                selectAllRows(false);
            } else if (activeTab === 'scan-friend') {
                selectAllScanFriendRows(false);
            }
            break;
        case 'select-errors':
            if (activeTab === 'change-pass') {
                selectErrorRows();
            } else if (activeTab === 'scan-friend') {
                selectScanFriendErrorRows();
            }
            break;
        case 'delete-mail':
            if (activeTab === 'change-pass') {
                deleteSelectedRows();
            } else if (activeTab === 'scan-friend') {
                deleteScanFriendSelectedRows();
            }
            break;
    }
}


// ===== FUNCTIONS CHO SCAN FRIEND TAB =====
function addScanFriendMailsFromText(text) {
    const lines = text.split('\n').filter(line => line.trim());
    const tbody = document.getElementById('treeview-tbody-scan-friend');
    
    lines.forEach((line, index) => {
        const parts = line.split('|');
        const row = document.createElement('tr');
        
        const currentRowCount = tbody.querySelectorAll('tr').length;
        
        row.innerHTML = `
            <td><input type="checkbox" class="tree-row-checkbox" onchange="updateTreeSelectedCount()"></td>
            <td>${currentRowCount + 1}</td>
            <td>${parts[0] || ''}</td>
            <td>${parts[1] || ''}</td>
            <td>${parts[2] || ''}</td>
            <td></td>
        `;
        
        tbody.appendChild(row);
    });
    
    console.log(`Đã thêm ${lines.length} dòng dữ liệu vào scan friend`);
}

function addScanFriendProxy() {
    alert('Chức năng thêm proxy cho scan friend');
}

function selectAllScanFriendRows(select) {
    const checkboxes = document.querySelectorAll('#treeview-table .tree-row-checkbox');
    const selectAllCheckbox = document.getElementById('tree-select-all');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = select;
    });
    
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = select;
    }
    updateTreeSelectedCount();
}

function selectScanFriendErrorRows() {
    const rows = document.querySelectorAll('#treeview-table tbody tr');
    rows.forEach(row => {
        const checkbox = row.querySelector('.tree-row-checkbox');
        const statusCell = row.cells[5]; // cột CHROME có thể chứa status
        
        if (row.classList.contains('error') || 
            (statusCell && statusCell.textContent.toLowerCase().includes('error'))) {
            checkbox.checked = true;
        }
    });
    updateTreeSelectedCount();
}

function deleteScanFriendSelectedRows() {
    const selectedCheckboxes = document.querySelectorAll('#treeview-table .tree-row-checkbox:checked');
    
    if (selectedCheckboxes.length === 0) {
        alert('Vui lòng chọn ít nhất một dòng để xóa!');
        return;
    }
    
    if (confirm(`Bạn có chắc muốn xóa ${selectedCheckboxes.length} dòng đã chọn?`)) {
        selectedCheckboxes.forEach(checkbox => {
            const row = checkbox.closest('tr');
            row.remove();
        });
        
        updateScanFriendRowNumbers();
        updateTreeSelectedCount();
    }
}

function updateScanFriendRowNumbers() {
    const rows = document.querySelectorAll('#treeview-table tbody tr');
    rows.forEach((row, index) => {
        row.cells[1].textContent = index + 1; // Cột STT
    });
}

function updateTreeSelectedCount() {
    const count = document.querySelectorAll('#treeview-table .tree-row-checkbox:checked').length;
    const countEl = document.getElementById('tree-selected-count');
    if (countEl) {
        countEl.textContent = `Đã chọn: ${count}`;
    }
}

// Hiển thị nút Chrome khi chạy
function showChromeButtonsForRunningAccounts_scanfriend(accounts, autoGetCookie) {
    // Xóa nút cũ trước
    document.querySelectorAll('#treeview-table tr').forEach(row => {
        const tds = row.querySelectorAll('td');
        if (tds[9]) tds[9].innerHTML = '';
    });
    
    accounts.forEach((acc, idx) => {
        const rows = document.querySelectorAll('#treeview-table tr');
        rows.forEach(row => {
            const tds = row.querySelectorAll('td');
            if (tds[2] && tds[2].textContent.trim() === String(acc.uid)) {
                if (tds[9]) {
                    if (autoGetCookie) {
                        tds[9].innerHTML = `<span class="chrome-name">Chrome ${idx + 1}</span>`;
                    } else {
                        tds[9].innerHTML = `
                            <span class="chrome-name">Chrome ${idx + 1}</span> 
                            <button class="chrome-close-btn" data-uid="${acc.uid}">Tắt</button>
                        `;
                    }
                }
            }
        });
    });
}

function startScanFriend() {
    // Lấy các dòng đã chọn
    const checkedRows = document.querySelectorAll('#treeview-table .tree-row-checkbox:checked');
    if (checkedRows.length === 0) {
        alert('Vui lòng chọn ít nhất một tài khoản để chạy!');
        return;
    }

    // Disable nút start và enable nút stop
    const startBtn = document.getElementById('scan-start-btn');
    const stopBtn = document.getElementById('scan-stop-btn');
    
    if (startBtn) {
        startBtn.disabled = true;
    }
    
    if (stopBtn) {
        stopBtn.disabled = false;
    }

    // Lấy số luồng
    const threadInput = document.getElementById('scan-thread-count');
    let thread = threadInput ? threadInput.value.trim() : '5';
    thread = Number(thread);

    // lấy số delay
    const delayInput = document.getElementById('scan-delay');
    let delay = delayInput ? delayInput.value.trim() : '0';
    delay = Number(delay);

    // Lấy proxy
    const proxyInput = document.getElementById('proxy-input');
    const proxy = proxyInput ? proxyInput.value.trim() : 'no ()';

    // lấy uid
    const rawText = document.getElementById('scan-input-text').value.trim();
    const uidList = rawText
        .split('\n')                 // Tách từng dòng
        .map(line => line.trim())   // Xoá khoảng trắng đầu/cuối mỗi dòng
        .filter(line => line !== ""); // Bỏ dòng trống

    // Lấy danh sách tài khoản đã chọn
    const accounts = [];
    checkedRows.forEach(cb => {
        const row = cb.closest('tr');
        const tds = row.querySelectorAll('td');
        accounts.push({
            selected: true,
            stt: tds[1]?.textContent.trim() || "",
            uid: tds[2]?.textContent.trim() || "",
            pass: tds[3]?.textContent.trim() || "",
            cookie: tds[4]?.textContent.trim() || "",
        });
    });

    // Tạo object json
    const data = {
        uidList: uidList,
        delay: delay,
        account: accounts,
        proxy: proxy,
        thread: thread,
        type: "scan_friend",
    };

    console.log("Sending data:", data);

    // Gọi eel với function đã sửa
    eel.thread_scan_friend(data);
    showChromeButtonsForRunningAccounts_scanfriend(accounts);
}
eel.expose(onScanComplete);
function onScanComplete() {
    const startBtn = document.getElementById('scan-start-btn');
    const stopBtn = document.getElementById('scan-stop-btn');
    
    if (startBtn) {
        startBtn.disabled = false;
    }
    
    if (stopBtn) {
        stopBtn.disabled = true;
    }
    
    const resultDiv = document.getElementById("scan-result-text");
    if (resultDiv) {
        const line = document.createElement("div");
        line.textContent = "✅ Quá trình scan đã hoàn tất!";
        line.style.color = "#4ec9b0";
        resultDiv.appendChild(line);
        resultDiv.scrollTop = resultDiv.scrollHeight;
    }
}

// Các nút thêm:
function clearScanResult() {
    document.getElementById("scan-result-text").innerHTML = "";
}

function copyAllResults() {
    const lines = Array.from(document.getElementById("scan-result-text").children)
        .map(div => div.textContent)
        .join("\n");

    navigator.clipboard.writeText(lines).then(() => {
        alert("Đã copy tất cả kết quả.");
    });
}

function exportScanResult() {
    const lines = Array.from(document.getElementById("scan-result-text").children)
        .map(div => div.textContent)
        .join("\n");

    const blob = new Blob([lines], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "scan_result.txt";
    a.click();
    URL.revokeObjectURL(url);
}

// Sửa lại hàm stopScanFriend trong JavaScript
function stopScanFriend() {
    console.log("Đang gọi stop_all_selenium_scan...");
    
    // Gọi hàm Python
    eel.stop_all_selenium_scan();
    
    // Disable nút stop và enable nút start
    const stopBtn = document.getElementById('scan-stop-btn');
    const startBtn = document.getElementById('scan-start-btn');
    
    if (stopBtn) {
        stopBtn.disabled = true;
        stopBtn.textContent = "⏹️ ĐANG DỪNG...";
    }
    
    if (startBtn) {
        startBtn.disabled = false;
    }
    
    // Thêm thông báo vào kết quả
    const resultDiv = document.getElementById("scan-result-text");
    if (resultDiv) {
        const line = document.createElement("div");
        line.textContent = "🔴 Đang dừng tất cả quá trình scan...";
        line.style.color = "#f44747";
        resultDiv.appendChild(line);
        resultDiv.scrollTop = resultDiv.scrollHeight;
    }
    
    // Reset text của nút stop sau 3 giây
    setTimeout(() => {
        if (stopBtn) {
            stopBtn.textContent = "⏹️ STOP SCAN";
        }
    }, 3000);
}
// Add near the top of the file, with other eel.expose functions

eel.expose(statusscan);
function statusscan(uid, status, color) {
    // Cập nhật status trong bảng
    const rows = document.querySelectorAll('#treeview-table tbody tr');
    rows.forEach(row => {
        const uidCell = row.cells[2];
        if (uidCell && uidCell.textContent === uid) {
            const statusCell = row.cells[5];
            if (statusCell) {
                statusCell.innerHTML = `<span style="color: ${color}">${status}</span>`;
            }
        }
    });

    // Cập nhật kết quả trong scan-result-text
    const resultDiv = document.getElementById("scan-result-text");
    if (resultDiv) {
        // Tìm div hiện tại cho UID này nếu có
        const existingDiv = Array.from(resultDiv.children).find(
            div => div.getAttribute('data-uid') === uid
        );

        if (existingDiv) {
            // Cập nhật nội dung nếu div đã tồn tại
            existingDiv.textContent = `UID: ${uid} - Status: ${status}`;
            existingDiv.style.color = color;
        } else {
            // Tạo div mới nếu chưa có
            const newDiv = document.createElement("div");
            newDiv.textContent = `UID: ${uid} - Status: ${status}`;
            newDiv.style.color = color;
            newDiv.setAttribute('data-uid', uid);

            // Lấy vị trí của UID trong danh sách gốc
            const uidList = document.getElementById('scan-input-text')
                .value.trim()
                .split('\n')
                .map(line => line.trim())
                .filter(line => line !== "");
            
            const uidIndex = uidList.indexOf(uid);

            // Chèn div vào đúng vị trí
            const allDivs = Array.from(resultDiv.children);
            let inserted = false;

            for (let i = 0; i < allDivs.length; i++) {
                const currentUid = allDivs[i].getAttribute('data-uid');
                const currentIndex = uidList.indexOf(currentUid);
                
                if (currentIndex > uidIndex) {
                    resultDiv.insertBefore(newDiv, allDivs[i]);
                    inserted = true;
                    break;
                }
            }

            // Nếu chưa chèn được, thêm vào cuối
            if (!inserted) {
                resultDiv.appendChild(newDiv);
            }
        }

        resultDiv.scrollTop = resultDiv.scrollHeight;
    }
}