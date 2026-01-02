// background.js - Service worker for Gmail-Cleaner
import { classify } from './classifier.js';
import { updateSenderProfile, getSenderProfile, openDB } from './storage.js';

chrome.runtime.onInstalled.addListener(() => {
    console.log('Gmail-Cleaner extension installed.');
    chrome.storage.local.set({
        stats: {
            emailsAnalyzed: 0,
            sendersGrouped: 0
        }
    });
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'EMAIL_DETECTED') {
        handleEmailDetected(message.data).then(sendResponse);
        return true;
    }
    if (message.type === 'GET_STATS') {
        chrome.storage.local.get(['stats'], (result) => sendResponse(result.stats));
        return true;
    }
    if (message.type === 'GET_RECENT_SENDERS') {
        getRecentSenders().then(sendResponse);
        return true;
    }
    if (message.type === 'PERFORM_ACTION') {
        handlePerformAction(message.data).then(sendResponse);
        return true;
    }
});

async function handlePerformAction(data) {
    const { email, action } = data;
    console.log(`Performing action ${action} for ${email}`);

    // Update sender profile with decision
    const profile = await getSenderProfile(email);
    profile.lastAction = action;
    if (action === 'UNSUBSCRIBE') {
        profile.unsubscribed = true;
    }
    await updateSenderProfile(profile);

    // In a real extension, we'd trigger the actual Gmail action here
    // For now, we'll simulate success
    return { success: true };
}


const profileLocks = new Map();

async function acquireLock(email) {
    while (profileLocks.get(email)) {
        await new Promise(resolve => setTimeout(resolve, 50));
    }
    profileLocks.set(email, true);
}

function releaseLock(email) {
    profileLocks.delete(email);
}

async function getRecentSenders() {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction('senderProfiles', 'readonly');
        const store = transaction.objectStore('senderProfiles');
        const request = store.getAll(); // Simplified for MVP: get all
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            // Return top 10 most recent
            const sorted = request.result.sort((a, b) => b.lastInteraction - a.lastInteraction);
            resolve(sorted.slice(0, 10));
        };
    });
}


let isUpdatingStats = false;
const statsQueue = [];

async function updateStatsSequentially() {
    if (isUpdatingStats || statsQueue.length === 0) return;
    isUpdatingStats = true;

    const incrementData = statsQueue.shift();
    const result = await chrome.storage.local.get(['stats']);
    const stats = result.stats || { emailsAnalyzed: 0, sendersGrouped: 0 };

    stats.emailsAnalyzed++;
    if (incrementData.isNewSender) {
        stats.sendersGrouped++;
    }

    await chrome.storage.local.set({ stats });
    console.log('Gmail-Cleaner: Stats updated, total analyzed:', stats.emailsAnalyzed);
    chrome.runtime.sendMessage({ type: 'UPDATE_STATS', data: stats });

    isUpdatingStats = false;
    updateStatsSequentially();
}

async function handleEmailDetected(emailData) {
    console.log('Gmail-Cleaner: Background received detection:', emailData.sender);

    await acquireLock(emailData.sender);
    try {
        const profile = await getSenderProfile(emailData.sender);

        // 1. Check for manual override first
        let classification = profile.userOverride;
        let mlResults = { purpose: null, topic: null, sender_type: null, confidence: 0 };

        if (!classification) {
            try {
                console.log('Gmail-Cleaner: Fetching ML classification (with timeout)...');
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout

                const response = await fetch('http://127.0.0.1:5001/classify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(emailData),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                mlResults = await response.json();
                classification = mlResults.purpose;
                console.log('Gmail-Cleaner: ML Result:', classification);
            } catch (error) {
                console.error('Gmail-Cleaner: ML API Error or Timeout:', error);
                // Fallback to rule-based if API fails or times out
                classification = classify(emailData);
                console.log('Gmail-Cleaner: Rule-based Fallback:', classification);
            }
        }

        const isNewSender = profile.totalReceived === 0;
        profile.totalReceived++;
        profile.lastInteraction = Date.now();
        profile.classification = classification;
        profile.purpose = mlResults.purpose || classification;
        profile.topic = mlResults.topic;
        profile.sender_type = mlResults.sender_type;
        profile.confidence = mlResults.confidence;

        await updateSenderProfile(profile);

        // Queue the stats update to prevent race conditions
        statsQueue.push({ isNewSender });
        updateStatsSequentially();

        return { classification };
    } finally {
        releaseLock(emailData.sender);
    }
}
