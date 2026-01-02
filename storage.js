// storage.js - IndexedDB wrapper for sender reputation

const DB_NAME = 'GmailCleanerDB';
const DB_VERSION = 1;
const STORE_NAME = 'senderProfiles';

export async function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                db.createObjectStore(STORE_NAME, { keyPath: 'email' });
            }
        };
    });
}

export async function getSenderProfile(email) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(STORE_NAME, 'readonly');
        const store = transaction.objectStore(STORE_NAME);
        const request = store.get(email);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result || {
            email,
            sender_domain: email.split('@')[1] || '',
            totalReceived: 0,
            opened: 0,
            deleted: 0,
            lastInteraction: Date.now(),
            classification: null,
            purpose: null,
            topic: null,
            sender_type: null,
            confidence: 0
        });
    });
}

export async function updateSenderProfile(profile) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(STORE_NAME, 'readwrite');
        const store = transaction.objectStore(STORE_NAME);
        const request = store.put(profile);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

export async function setOverride(email, classification) {
    const profile = await getSenderProfile(email);
    profile.userOverride = classification;
    await updateSenderProfile(profile);
}

export async function getOverride(email) {
    const profile = await getSenderProfile(email);
    return profile.userOverride || null;
}
