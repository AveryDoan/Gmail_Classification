from flask import Flask, request, jsonify, send_file
import re
import csv
import os
from datetime import datetime

# Data Model
class Email:
    def __init__(self, id, sender, sender_domain, subject, body, date, has_unsubscribe=False, list_unsubscribe_url=None):
        self.id = id
        self.sender = sender
        self.sender_domain = sender_domain
        self.subject = subject
        self.body = body
        self.date = date
        self.has_unsubscribe = has_unsubscribe
        self.list_unsubscribe_url = list_unsubscribe_url

class EmailWithLabels(Email):
    def __init__(self, email, purpose, topic, sender_type, confidence):
        super().__init__(email.id, email.sender, email.sender_domain, email.subject, email.body, email.date, email.has_unsubscribe, email.list_unsubscribe_url)
        self.purpose = purpose
        self.topic = topic
        self.sender_type = sender_type
        self.confidence = confidence

# Classifier Logic
class ClassifierEngine:
    def __init__(self):
        print("Classifier Engine initialized (Rule-based mode)")

    def classify_purpose(self, text):
        text = text.lower()
        if any(w in text for w in ["receipt", "invoice", "order", "bill", "payment", "stript", "paypal"]): return "finance", 0.95
        if any(w in text for w in ["newsletter", "digest", "weekly", "edition", "substack", "medium"]): return "subscription", 0.9
        if any(w in text for w in ["sale", "offer", "discount", "price", "limited time", "off"]): return "promotion", 0.85
        if any(w in text for w in ["meeting", "agenda", "call", "project", "sync"]): return "work", 0.8
        return "personal", 0.5

    def classify_topic(self, text):
        text = text.lower()
        if any(w in text for w in ["finance", "bank", "crypto", "tax"]): return "finance", 0.9
        if any(w in text for w in ["tech", "ai", "software", "code", "github", "stack"]): return "tech", 0.9
        if any(w in text for w in ["shopping", "amazon", "ebay", "cart"]): return "shopping", 0.8
        if any(w in text for w in ["travel", "flight", "hotel", "booking"]): return "travel", 0.8
        return "general", 0.5

    def classify_sender_ml(self, sender_info):
        sender_info = sender_info.lower()
        # platform detection
        if any(w in sender_info for w in ["no-reply", "noreply", "notification", "alert"]): return "platform"
        if ".com" in sender_info or ".org" in sender_info or ".io" in sender_info: return "company"
        return "individual"

    def process_email(self, email_dict):
        email = Email(
            id=email_dict.get("id", "0"),
            sender=email_dict.get("sender", ""),
            sender_domain=email_dict.get("sender_domain", ""),
            subject=email_dict.get("subject", ""),
            body=email_dict.get("body", ""),
            date=email_dict.get("date", ""),
            has_unsubscribe=email_dict.get("has_unsubscribe", False),
            list_unsubscribe_url=email_dict.get("list_unsubscribe_url", None)
        )
        
        combined_text = f"{email.subject} {email.body}"
        purpose, p_conf = self.classify_purpose(combined_text)
        topic, t_conf = self.classify_topic(combined_text)
        sender_info = f"Sender: {email.sender}, Domain: {email.sender_domain}, Subject: {email.subject}"
        sender_type = self.classify_sender_ml(sender_info)
        
        result = {
            "purpose": purpose,
            "topic": topic,
            "sender_type": sender_type,
            "confidence": float(p_conf)
        }
        
        self.save_to_csv(email_dict, result)
        return result

    def save_to_csv(self, email_dict, result):
        filename = "emails_classified.csv"
        file_exists = os.path.isfile(filename)
        
        # Deduplication check
        if file_exists:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("sender name") == email_dict.get("sender") and row.get("subject") == email_dict.get("subject"):
                        return # Already exists
        
        with open(filename, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "date", "sender name", "purpose", "subject", "content", "topic", "sender_type", "confidence"
            ])
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sender name": email_dict.get("sender", "Unknown"),
                "purpose": result["purpose"],
                "subject": email_dict.get("subject", "No Subject"),
                "content": email_dict.get("body", "No Content"),
                "topic": result["topic"],
                "sender_type": result["sender_type"],
                "confidence": f"{result['confidence']:.2f}"
            })
        print(f"Logged classification for {email_dict.get('sender')} to {filename}")

# Flask API
app = Flask(__name__)
engine = ClassifierEngine()

@app.route('/classify', methods=['POST', 'OPTIONS'])
def classify_route():
    if request.method == 'OPTIONS':
        return '', 204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    
    data = request.json
    result = engine.process_email(data)
    return jsonify(result), 200, {'Access-Control-Allow-Origin': '*'}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()}), 200, {'Access-Control-Allow-Origin': '*'}

@app.route('/download', methods=['GET'])
def download_csv():
    filename = "emails_classified.csv"
    if os.path.isfile(filename):
        return send_file(filename, as_attachment=True, download_name="gmail_data.csv")
    else:
        return jsonify({"error": "No data found"}), 404, {'Access-Control-Allow-Origin': '*'}

if __name__ == "__main__":
    app.run(port=5001)
