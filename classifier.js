// classifier.js - Rule-based classification engine

export const CLASSIFICATION_TYPES = {
    PERSONAL: 'Personal',
    WORK: 'Work',
    TRANSACTIONAL: 'Transactional',
    SUBSCRIPTION: 'Subscription',
    PROMOTION: 'Promotion',
    SPAM: 'Spam'
};

const RULES = {
    DOMAIN_MAP: {
        'amazon.com': CLASSIFICATION_TYPES.TRANSACTIONAL,
        'stripe.com': CLASSIFICATION_TYPES.TRANSACTIONAL,
        'paypal.com': CLASSIFICATION_TYPES.TRANSACTIONAL,
        'substack.com': CLASSIFICATION_TYPES.SUBSCRIPTION,
        'medium.com': CLASSIFICATION_TYPES.SUBSCRIPTION,
        'linkedin.com': CLASSIFICATION_TYPES.PROMOTION,
        'facebookmail.com': CLASSIFICATION_TYPES.PROMOTION,
        'twitter.com': CLASSIFICATION_TYPES.PROMOTION,
        'no-reply@': CLASSIFICATION_TYPES.TRANSACTIONAL // Partial match handle
    },
    HEADER_SIGNALS: {
        LIST_UNSUBSCRIBE: 'List-Unsubscribe',
        PRECEDENCE_BULK: 'Precedence: bulk',
        X_MAILER: 'X-Mailer',
        X_CAMPAIGN: 'X-Campaign-ID'
    },
    KEYWORDS: {
        TRANSACTIONAL: ['receipt', 'invoice', 'order', 'receipt', 'confirmation', 'otp', 'bill', 'statement'],
        PROMOTION: ['sale', 'discount', 'off', 'limited time', 'price', 'deal', 'offer', 'exclusive'],
        SUBSCRIPTION: ['newsletter', 'weekly', 'digest', 'edition', 'update', 'monthly']
    }
};

function extractFeatures(emailData) {
    const { subject, body, sender } = emailData;
    const content = (subject + ' ' + body).toLowerCase();

    return {
        hasUnsubscribe: content.includes('unsubscribe') || content.includes('opt out'),
        isHtml: body.includes('<') && body.includes('>'),
        length: content.length,
        hasPromoKeywords: RULES.KEYWORDS.PROMOTION.some(kw => content.includes(kw)),
        hasTransactionalKeywords: RULES.KEYWORDS.TRANSACTIONAL.some(kw => content.includes(kw))
    };
}

export function classify(emailData) {
    const { sender, subject, body, headers } = emailData;

    // 1. Rule-based (Deterministic)
    const domain = sender.split('@')[1];
    if (RULES.DOMAIN_MAP[domain]) return RULES.DOMAIN_MAP[domain];
    if (headers && headers[RULES.HEADER_SIGNALS.LIST_UNSUBSCRIBE]) return CLASSIFICATION_TYPES.SUBSCRIPTION;

    // 2. ML-inspired Probabilistic Scoring (Phase 2)
    const features = extractFeatures(emailData);
    let probabilities = {
        TRANSACTIONAL: 0.1,
        PROMOTION: 0.1,
        SUBSCRIPTION: 0.1,
        PERSONAL: 0.7 // Default prior
    };

    // Adjust probabilities based on features
    if (features.hasUnsubscribe) {
        probabilities.SUBSCRIPTION += 0.4;
        probabilities.PROMOTION += 0.2;
        probabilities.PERSONAL -= 0.3;
    }
    if (features.hasPromoKeywords) probabilities.PROMOTION += 0.5;
    if (features.hasTransactionalKeywords) probabilities.TRANSACTIONAL += 0.5;
    if (features.length > 500) probabilities.SUBSCRIPTION += 0.2; // Newsletters are usually long

    // Find max probability
    const winner = Object.keys(probabilities).reduce((a, b) => probabilities[a] > probabilities[b] ? a : b);
    return CLASSIFICATION_TYPES[winner];
}


