document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('toggle');
    const status = document.getElementById('status');

    chrome.storage.local.get('enabled', function(result) {
        toggle.checked = result.enabled === true;
        updateStatus(toggle.checked);
    });

    toggle.addEventListener('change', function() {
        const enabled = toggle.checked;
        chrome.storage.local.set({ enabled: enabled });
        updateStatus(enabled);
        
        const tabs = chrome.tabs.query({ url: '*://*.stopots.com/*' }, function(tabs) {
            tabs.forEach(function(tab) {
                chrome.tabs.sendMessage(tab.id, { enabled: enabled });
            });
        });
    });

    function updateStatus(enabled) {
        status.textContent = enabled ? 'Ativado' : 'Desativado';
        status.className = 'status ' + (enabled ? 'active' : 'inactive');
    }
});
