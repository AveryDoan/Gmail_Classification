from flask import Flask, request, jsonify
import torch
from transformers import pipeline
import re

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
        # Determine device (use MPS for Mac if available, otherwise CPU)
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        try:
            # Use faster models to prevent extension timeouts
            self.purpose_classifier = pipeline("text-classification", 
                                               model="distilbert-base-uncased-finetuned-sst-2-english",
                                               device=self.device)
            self.topic_classifier = pipeline("text-classification", 
                                             model="distilbert-base-uncased",
                                             device=self.device)
            # Use a lighter zero-shot model
            self.sender_classifier = pipeline("zero-shot-classification", 
                                              model="valhalla/distilbart-mnli-12-1",
                                              device=self.device)
        except Exception as e:
            print(f"Error loading models: {e}")
            self.purpose_classifier = None
            self.topic_classifier = None
            self.sender_classifier = None

    def classify_purpose(self, text):
        if not self.purpose_classifier: return "personal", 0.5
        result = self.purpose_classifier(text[:512])
        return result[0]["label"].lower(), result[0]["score"]

    def classify_topic(self, text):
        if not self.topic_classifier: return "general", 0.5
        result = self.topic_classifier(text[:512])
        return result[0]["label"].lower(), result[0]["score"]

    def classify_sender_ml(self, sender_info):
        if not self.sender_classifier: return "company"
        candidate_labels = ["individual person", "automated platform", "commercial company", "government agency"]
        result = self.sender_classifier(sender_info, candidate_labels)
        label_map = {
            "individual person": "individual",
            "automated platform": "platform",
            "commercial company": "company",
            "government agency": "government"
        }
        return label_map.get(result["labels"][0], "company")

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
        
        return {
            "purpose": purpose,
            "topic": topic,
            "sender_type": sender_type,
            "confidence": float(p_conf)
        }

# Flask API
app = Flask(__name__)
engine = ClassifierEngine()

@app.route('/classify', methods=['POST'])
def classify_route():
    data = request.json
    result = engine.process_email(data)
    return jsonify(result)

if __name__ == "__main__":
    app.run(port=5001)
