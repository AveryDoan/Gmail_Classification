document.addEventListener('DOMContentLoaded', async () => {
    const scanBtn = document.getElementById('scan-btn');
    const emailsAnalyzed = document.getElementById('emails-analyzed');
    const sendersGrouped = document.getElementById('senders-grouped');
    const senderList = document.getElementById('sender-list');

    // Load recent senders
    chrome.storage.local.get(['stats'], (result) => {
        if (result.stats) {
            emailsAnalyzed.textContent = result.stats.emailsAnalyzed || 0;
            sendersGrouped.textContent = result.stats.sendersGrouped || 0;
        }
    });

    async function updateSenderList() {
        // This would ideally come from IndexedDB, but for MVP we'll show a mockup or limited set
        // In a real app, we'd query storage.js (which we can't directly here without ES modules support in popup)
        // We'll use messages to background to get data
        chrome.runtime.sendMessage({ type: 'GET_RECENT_SENDERS' }, (senders) => {
            if (senders && senders.length > 0) {
                senderList.innerHTML = '';
                senders.forEach(sender => {
                    const div = document.createElement('div');
                    div.className = 'sender-item';
                    div.innerHTML = `
            <div class="sender-info">
              <span class="sender-name">${sender.email}</span>
              <div class="sender-tags">
                <span class="sender-tag tag-purpose">${sender.purpose || sender.classification}</span>
                <span class="sender-tag tag-topic">${sender.topic || 'General'}</span>
                <span class="sender-tag tag-type">${sender.sender_type || 'Unknown'}</span>
              </div>
              <span class="sender-confidence">${Math.round((sender.confidence || 0) * 100)}% Match</span>
            </div>
            <div class="sender-actions">
              <button class="action-btn unsubscribe" data-email="${sender.email}">Unsubscribe</button>
              <button class="action-btn delete" data-email="${sender.email}">Delete</button>
            </div>
          `;
                    senderList.appendChild(div);
                });

                // Add event listeners to newly created buttons
                document.querySelectorAll('.sender-item').forEach(item => {
                    item.addEventListener('dblclick', () => {
                        const email = item.querySelector('.sender-name').textContent;
                        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                            const activeTab = tabs[0];
                            if (activeTab && activeTab.url.includes('mail.google.com')) {
                                chrome.tabs.sendMessage(activeTab.id, {
                                    action: 'FILTER_INBOX',
                                    query: `from:${email}`
                                });
                            }
                        });
                    });
                });

                document.querySelectorAll('.action-btn.unsubscribe').forEach(btn => {
                    btn.addEventListener('click', (e) => handleAction(e.target.dataset.email, 'UNSUBSCRIBE'));
                });
                document.querySelectorAll('.action-btn.delete').forEach(btn => {
                    btn.addEventListener('click', (e) => handleAction(e.target.dataset.email, 'DELETE'));
                });
            }
        });
    }

    function handleAction(email, action) {
        if (confirm(`Are you sure you want to ${action.toLowerCase()} from ${email}?`)) {
            chrome.runtime.sendMessage({ type: 'PERFORM_ACTION', data: { email, action } }, (response) => {
                if (response.success) {
                    alert(`Action ${action} initiated for ${email}.`);
                    updateSenderList();
                }
            });
        }
    }

    updateSenderList();

    const dashboardBtn = document.getElementById('dashboard-btn');
    dashboardBtn.addEventListener('click', () => {
        window.open('http://127.0.0.1:8050', '_blank');
    });

    scanBtn.addEventListener('click', () => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            const activeTab = tabs[0];
            if (activeTab && activeTab.url.includes('mail.google.com')) {
                chrome.tabs.sendMessage(activeTab.id, { action: 'SCAN_INBOX' });
            } else {
                alert('Please open Gmail to scan your inbox.');
            }
        });
    });

    // Listen for updates from background/content script
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.type === 'UPDATE_STATS') {
            emailsAnalyzed.textContent = request.data.emailsAnalyzed;
            sendersGrouped.textContent = request.data.sendersGrouped;
            updateSenderList(); // Refresh list when stats update
        }
    });
});
