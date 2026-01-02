// content.js - DOM interaction for Gmail

console.log('Gmail-Cleaner content script loaded.');

// Debounce utility to prevent too many scans
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

const debouncedDetectEmails = debounce(detectEmails, 100);

// Observe Gmail's DOM to detect when new emails are listed or opened
const observer = new MutationObserver((mutations) => {
    debouncedDetectEmails();
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

function detectEmails() {
    // Try multiple selectors for Gmail rows to handle different views/layouts
    const selectors = ['tr.zA', 'tr[role="row"]', '.v1', 'div[role="main"] tr'];
    let emailRows = [];
    selectors.forEach(selector => {
        const found = document.querySelectorAll(selector);
        if (found.length > 0) {
            emailRows = [...emailRows, ...found];
        }
    });

    // De-duplicate rows and filter out already processed ones
    emailRows = [...new Set(emailRows)].filter(row =>
        !row.hasAttribute('data-cleanflow-processed') &&
        !row.hasAttribute('data-cleanflow-processing')
    );

    if (emailRows.length === 0) return;
    console.log(`Gmail-Cleaner: Processing ${emailRows.length} new/pending rows.`);

    emailRows.forEach((row, index) => {
        // Try multiple selectors for sender cells
        const senderSelector = ['.yX', '.yW', 'span.bA4', '[email]', '[data-hovercard-id]', '.b9.cl'];
        let senderCell = null;
        for (const sel of senderSelector) {
            senderCell = row.querySelector(sel);
            if (senderCell) break;
        }

        if (!senderCell) {
            if (index < 5) console.warn(`Gmail-Cleaner: Row ${index} missing sender cell.`, row);
            return;
        }

        if (!row.hasAttribute('data-cleanflow-processed') && !row.hasAttribute('data-cleanflow-processing')) {
            row.setAttribute('data-cleanflow-processing', 'true');

            const senderText = senderCell.innerText.trim() || senderCell.getAttribute('email') || senderCell.getAttribute('data-hovercard-id') || 'Unknown';
            const subjectText = (row.querySelector('.y6')?.innerText || row.querySelector('.bog')?.innerText || '').trim();
            const contentText = (row.querySelector('.y2')?.innerText || '').trim();

            console.log(`Gmail-Cleaner: Analyzing email from "${senderText}"`);

            chrome.runtime.sendMessage({
                type: 'EMAIL_DETECTED',
                data: {
                    sender: senderText,
                    subject: subjectText,
                    body: contentText,
                    headers: {}
                }
            }, (response) => {
                row.removeAttribute('data-cleanflow-processing');
                if (chrome.runtime.lastError) {
                    console.error('Gmail-Cleaner: Message failed:', chrome.runtime.lastError.message);
                    return; // Don't mark as processed if it failed
                }

                row.setAttribute('data-cleanflow-processed', 'true');
                if (response && response.classification) {
                    injectBadge(senderCell, response.classification);
                }
            });
        }
    });
}

function injectBadge(container, classification) {
    if (container.querySelector('.cleanflow-badge')) return;
    const badge = document.createElement('span');
    badge.className = `cleanflow-badge badge-${classification.toLowerCase()}`;
    badge.textContent = classification;
    container.appendChild(badge);
}

// Diagnostic tool
window.cleanFlowDiagnostic = () => {
    console.log('--- Gmail-Cleaner Diagnostic Report ---');
    const selectors = ['tr.zA', 'tr[role="row"]', '.v1', 'div[role="main"] tr'];
    selectors.forEach(sel => {
        const count = document.querySelectorAll(sel).length;
        console.log(`Selector "${sel}": ${count} elements found.`);
    });

    const processing = document.querySelectorAll('[data-cleanflow-processing]').length;
    const processed = document.querySelectorAll('[data-cleanflow-processed]').length;
    console.log(`Rows in "processing" state: ${processing}`);
    console.log(`Rows in "processed" state: ${processed}`);

    const rows = [...new Set(selectors.flatMap(sel => [...document.querySelectorAll(sel)]))];
    console.log(`Total unique rows detected: ${rows.length}`);

    if (rows.length > 0) {
        console.log('Sample Row Sender Cells:');
        rows.slice(0, 5).forEach((row, i) => {
            const senderSelector = ['.yX', '.yW', 'span.bA4', '[email]', '[data-hovercard-id]', '.b9.cl'];
            let found = null;
            for (const sel of senderSelector) {
                if (row.querySelector(sel)) { found = sel; break; }
            }
            console.log(`  Row ${i}: ${found ? 'Found with ' + found : 'NOT FOUND'}`);
        });
    }
    console.log('---------------------------------------');
    return 'Diagnostic run complete. Check the console above.';
};

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'SCAN_INBOX') {
        console.log('Gmail-Cleaner: Full scan requested, clearing processed flags...');
        // Clear flags to allow re-scanning for download
        document.querySelectorAll('[data-cleanflow-processed]').forEach(el => {
            el.removeAttribute('data-cleanflow-processed');
        });
        detectEmails();
        sendResponse({ status: 'Scan started' });
    }

    if (request.action === 'FILTER_INBOX') {
        const query = request.query;
        console.log(`Filtering inbox for: ${query}`);

        // Find Gmail's search input
        const searchInput = document.querySelector('input[name="q"]');
        if (searchInput) {
            searchInput.value = query;
            // Trigger the search by clicking the search button or pressing Enter
            const searchButton = document.querySelector('button[aria-label="Search mail"]') ||
                document.querySelector('button[aria-label="Search"]');
            if (searchButton) {
                searchButton.click();
            } else {
                // Fallback: Dispatch Enter key event
                const enterEvent = new KeyboardEvent('keydown', {
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true
                });
                searchInput.dispatchEvent(enterEvent);
            }
        }
    }
});
