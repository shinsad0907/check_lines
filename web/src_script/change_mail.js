// Global data object
const changeMailData = {
    isRunning: false,
    selectedCount: 0,
    total: 0,
    processed: 0,
    success: 0,
    failed: 0,
    config: {
        threadCount: 3,
        useProxy: true,
        autoCookie: true
    }
};

// Setup context menu for change-mail tab
function setupChangeMailContextMenu() {
    const contextMenu = document.createElement('div');
    contextMenu.className = 'context-menu context-menu-changemail';
    contextMenu.innerHTML = `
        <div class="context-menu-item" id="add-accounts">Nhập UID|PASS|COOKIE</div>
        <div class="context-menu-separator"></div>
        <div class="context-menu-item" id="select-all-change">Chọn tất cả</div>
        <div class="context-menu-item" id="deselect-all-change">Bỏ chọn tất cả</div>
        <div class="context-menu-item" id="select-errors-change">Chọn tài khoản lỗi</div>
        <div class="context-menu-separator"></div>
        <div class="context-menu-item" id="copy-uid">Copy UID</div>
        <div class="context-menu-item" id="copy-cookie">Copy Cookie</div>
        <div class="context-menu-item" id="copy-full">Copy Full Info</div>
        <div class="context-menu-separator"></div>
        <div class="context-menu-item" id="delete-selected-change">❌ Xóa đã chọn</div>
    `;
    document.body.appendChild(contextMenu);

    const changeMailTab = document.getElementById('change-mail');
    if (changeMailTab) {
        changeMailTab.addEventListener('contextmenu', function(e) {
            // Only show menu if change-mail tab is active
            if (!changeMailTab.classList.contains('active')) return;
            
            if (e.target.closest('.data-table-container')) {
                e.preventDefault();
                // Hide all other context menus
                document.querySelectorAll('.context-menu').forEach(menu => {
                    menu.style.display = 'none';
                });
                showContextMenu(e.pageX, e.pageY);
            }
        });
    }

    // Hide menu when clicking outside
    document.addEventListener('click', function(e) {
        if (!contextMenu.contains(e.target)) {
            contextMenu.style.display = 'none';
        }
    });

    // Handle menu item clicks
    contextMenu.addEventListener('click', handleContextMenuClick);

    function showContextMenu(x, y) {
        contextMenu.style.display = 'block';
        contextMenu.style.left = x + 'px';
        contextMenu.style.top = y + 'px';
    }
}

function handleContextMenuClick(e) {
    const id = e.target.id;
    document.querySelector('.context-menu-changemail').style.display = 'none';

    switch (id) {
        case 'add-accounts':
            pasteAccountsFromClipboard();
            break;
        case 'select-all-change':
            toggleChangeMailSelectAll(true);
            break;
        case 'deselect-all-change':
            toggleChangeMailSelectAll(false);
            break;
        case 'select-errors-change':
            selectErrorAccounts();
            break;
        case 'copy-uid':
            copySelectedInfo('uid');
            break;
        case 'copy-cookie':
            copySelectedInfo('cookie');
            break;
        case 'copy-full':
            copySelectedInfo('full');
            break;
        case 'delete-selected-change':
            deleteSelectedAccounts();
            break;
    }
}

// Paste accounts from clipboard
async function pasteAccountsFromClipboard() {
    try {
        const text = await navigator.clipboard.readText();
        const accounts = text.split('\n')
            .map(line => line.trim())
            .filter(line => line)
            .map(line => {
                const [uid, pass, cookie] = line.split('|').map(s => s.trim());
                return { uid, pass, cookie };
            })
            .filter(acc => acc.uid && acc.pass);

        if (accounts.length === 0) {
            alert('Không tìm thấy dữ liệu hợp lệ!\nĐịnh dạng: UID|PASS|COOKIE');
            return;
        }

        accounts.forEach(acc => appendAccountToTable(acc));
        updateChangeMailSelectedCount();
        updateStats();

    } catch (error) {
        console.error('Paste error:', error);
        alert('Không thể paste dữ liệu. Vui lòng thử lại!');
    }
}

// Add account to table
function appendAccountToTable(account) {
    const tbody = document.getElementById('change-mail-tbody');
    const rowCount = tbody.children.length;

    const tr = document.createElement('tr');
    tr.dataset.uid = account.uid;
    tr.innerHTML = `
        <td><input type="checkbox" class="change-mail-row-checkbox" onchange="updateChangeMailSelectedCount()"></td>
        <td>${rowCount + 1}</td>
        <td>${account.uid}</td>
        <td>${account.pass}</td>
        <td>${account.cookie || ''}</td>
        <td></td>
        <td><span style="color: #4ec9b0;">✓ Ready</span></td>
    `;
    tbody.appendChild(tr);
}

// Copy functions
function copySelectedInfo(type) {
    const selectedRows = Array.from(document.querySelectorAll('.change-mail-row-checkbox:checked'))
        .map(checkbox => checkbox.closest('tr'));

    if (selectedRows.length === 0) {
        alert('Vui lòng chọn tài khoản để copy!');
        return;
    }

    let content = '';
    selectedRows.forEach(row => {
        switch(type) {
            case 'uid':
                content += row.cells[2].textContent + '\n';
                break;
            case 'cookie':
                content += row.cells[4].textContent + '\n';
                break;
            case 'full':
                content += `${row.cells[2].textContent}|${row.cells[3].textContent}|${row.cells[4].textContent}\n`;
                break;
        }
    });

    navigator.clipboard.writeText(content.trim())
        .then(() => showToast('Đã copy thành công!'))
        .catch(() => showToast('Không thể copy. Vui lòng thử lại!', 'error'));
}

// Delete selected accounts
function deleteSelectedAccounts() {
    const selectedRows = document.querySelectorAll('.change-mail-row-checkbox:checked');
    if (selectedRows.length === 0) {
        alert('Vui lòng chọn tài khoản cần xóa!');
        return;
    }

    if (confirm(`Bạn có chắc muốn xóa ${selectedRows.length} tài khoản đã chọn?`)) {
        selectedRows.forEach(checkbox => checkbox.closest('tr').remove());
        updateRowNumbers();
        updateStats();
    }
}

// Select error accounts
function selectErrorAccounts() {
    const rows = document.querySelectorAll('#change-mail-tbody tr');
    rows.forEach(row => {
        const statusCell = row.querySelector('td:last-child');
        const checkbox = row.querySelector('.change-mail-row-checkbox');
        if (statusCell.textContent.includes('❌')) {
            checkbox.checked = true;
        }
    });
    updateChangeMailSelectedCount();
}

// Update functions
function updateRowNumbers() {
    const rows = document.querySelectorAll('#change-mail-tbody tr');
    rows.forEach((row, index) => {
        row.cells[1].textContent = index + 1;
    });
}

function updateStats() {
    changeMailData.total = document.querySelectorAll('#change-mail-tbody tr').length;
    document.getElementById('change-mail-total').textContent = changeMailData.total;
}

function updateChangeMailSelectedCount() {
    const count = document.querySelectorAll('.change-mail-row-checkbox:checked').length;
    document.getElementById('change-mail-selected-count').textContent = `Đã chọn: ${count}`;
    changeMailData.selectedCount = count;
}

function toggleChangeMailSelectAll(value) {
    const checkboxes = document.querySelectorAll('.change-mail-row-checkbox');
    checkboxes.forEach(cb => cb.checked = value);
    updateChangeMailSelectedCount();
}

// Button handlers
function openLDPlayer() {
    eel.open_ldplayer()();
    document.getElementById('change-mail-start-btn').disabled = false;
}

async function startChangeMail() {
    updateConfig();
    const selectedAccounts = getSelectedAccounts();
    const newMails = parseNewMails();

    if (!validateInputs(selectedAccounts, newMails)) return;

    changeMailData.isRunning = true;
    updateButtonStates(true);

    try {
        await eel.change_mail_process({
            accounts: selectedAccounts,
            newMails: newMails,
            config: changeMailData.config
        })();
    } catch (error) {
        console.error('Change mail error:', error);
        showToast('Lỗi đổi mail: ' + error.message, 'error');
    } finally {
        stopChangeMail();
    }
}

function stopChangeMail() {
    changeMailData.isRunning = false;
    updateButtonStates(false);
}

// Helper functions
function validateInputs(accounts, mails) {
    if (accounts.length === 0) {
        showToast('Vui lòng chọn tài khoản cần đổi mail!', 'error');
        return false;
    }
    if (mails.length === 0) {
        showToast('Vui lòng nhập mail mới!', 'error');
        return false;
    }
    return true;
}

function updateButtonStates(isRunning) {
    document.getElementById('change-mail-start-btn').disabled = isRunning;
    document.getElementById('change-mail-stop-btn').disabled = !isRunning;
}

function updateConfig() {
    changeMailData.config = {
        threadCount: parseInt(document.getElementById('change-mail-thread-count').value) || 3,
        useProxy: document.getElementById('change-mail-use-proxy').checked,
        autoCookie: document.getElementById('change-mail-auto-cookie').checked
    };
}

function getSelectedAccounts() {
    return Array.from(document.querySelectorAll('.change-mail-row-checkbox:checked'))
        .map(checkbox => {
            const row = checkbox.closest('tr');
            return {
                uid: row.cells[2].textContent,
                pass: row.cells[3].textContent,
                cookie: row.cells[4].textContent,
                currentMail: row.cells[5].textContent
            };
        });
}

function parseNewMails() {
    return document.getElementById('change-mail-input').value
        .split('\n')
        .map(line => line.trim())
        .filter(line => line)
        .map(line => {
            const [email, password] = line.split('|').map(s => s.trim());
            return { email, password };
        })
        .filter(mail => mail.email && mail.password);
}

// Export function
function exportChangeMailData() {
    const table = document.getElementById('change-mail-table');
    if (!table) return;

    const csvContent = generateCSV(table);
    downloadCSV(csvContent);
}

function generateCSV(table) {
    let csvContent = "STT,UID,PASS,COOKIE,MAIL,STATUS\n";
    
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    rows.forEach((row, index) => {
        const cells = Array.from(row.cells);
        const rowData = [
            index + 1,
            cells[2].textContent,
            cells[3].textContent,
            cells[4].textContent,
            cells[5].textContent,
            cells[6].textContent.replace('✓', '').replace('❌', '').trim()
        ];
        csvContent += rowData.join(',') + '\n';
    });
    
    return csvContent;
}

function downloadCSV(csvContent) {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `change_mail_export_${new Date().toISOString().slice(0,10)}.csv`;
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupChangeMailContextMenu();
    updateButtonStates(false);

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (!document.querySelector('#change-mail.tab-pane.active')) return;
        
        if (e.ctrlKey && e.key === 'a') {
            e.preventDefault();
            toggleChangeMailSelectAll(true);
        }
        if (e.key === 'Delete') {
            deleteSelectedAccounts();
        }
    });
});

// Python callback
eel.expose(updateChangeMailProgress);
function updateChangeMailProgress(progress) {
    if (!progress || typeof progress !== 'object') return;

    // Update statistics
    document.getElementById('change-mail-processed').textContent = progress.processed || 0;
    document.getElementById('change-mail-success').textContent = progress.success || 0;
    document.getElementById('change-mail-failed').textContent = progress.failed || 0;

    // Update account status in table
    if (progress.accountStatus) {
        Object.entries(progress.accountStatus).forEach(([uid, status]) => {
            const row = document.querySelector(`tr[data-uid="${uid}"]`);
            if (row) {
                const statusCell = row.querySelector('td:last-child');
                const icon = status.success ? '✓' : '❌';
                const color = status.success ? '#4ec9b0' : '#f44747';
                statusCell.innerHTML = `<span style="color: ${color}">${icon} ${status.message}</span>`;
            }
        });
    }
}