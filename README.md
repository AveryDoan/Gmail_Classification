# Gmail-Cleaner: AI-Powered Email Intelligence & Analytics

Gmail-Cleaner (CleanFlow) is a privacy-first Chrome extension that brings advanced Machine Learning (ML) classification and interactive Business Intelligence (BI) analytics to your Gmail inbox. It helps you understand your email patterns, identify senders, and manage your inbox with data-driven insights.

## ✨ Key Features

- **AI Classification**: Real-time analysis of emails using DistilBERT and Zero-Shot models (distilbart) to categorize purpose, topic, and sender type.
- **Interactive Dashboard**: A powerful BI dashboard powered by Dash and Plotly to visualize your email ecosystem.
- **Inbox Intelligence**:
    - **Sender Profiling**: Tracking interactions, frequency, and reputation.
    - **Double-Click to Filter**: Instantly search for all emails from a specific sender by double-clicking them in the extension popup.
- **Hardware Optimized**: Native support for Apple Silicon (MPS acceleration) for high-performance ML processing locally.
- **Privacy First**: All data is stored locally in IndexedDB; classification happens on your local machine via a Python Flask API.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.8+
- Google Chrome
- Apple Silicon Mac (highly recommended for hardware acceleration)

### 2. Setup the AI Engine
```bash
# Install dependencies
pip install torch transformers flask pandas plotly dash datasets accelerate

# Start the classification server
python classifier_engine.py
```

### 3. Launch the Dashboard
```bash
# Start the BI dashboard
python dashboard.py
```
View the analytics at `http://127.0.0.1:8050`.

### 4. Install the Chrome Extension
1. Open Chrome and go to `chrome://extensions`.
2. Enable **Developer mode**.
3. Click **Load unpacked** and select the Gmail-Cleaner project directory.

## 🛠 Tech Stack

- **Frontend**: Vanilla JS, CSS (Chrome Extension)
- **Backend AI**: Python, Flask, HuggingFace Transformers (PyTorch)
- **Analytics**: Dash, Plotly, Pandas
- **Storage**: IndexedDB (Browser), Local Storage

## 📊 Interaction Model

1. **Detection**: The extension monitors your Gmail DOM and detects email rows.
2. **Analysis**: Row metadata is sent to the local Flask API for ML classification.
3. **UI Injection**: Categorization badges are injected directly into the Gmail UI.
4. **BI Dashboard**: Aggregated data is sent to the Dash server for interactive visualization.
5. **Action**: Double-click senders in the popup to filter your inbox or use the "Open Dashboard" button for deep insights.

## 🔒 Privacy

Gmail-Cleaner is designed with privacy as the core principle. No email content ever leaves your machine. The classification happens locally via your own Python environment, and all historical data is kept in your browser's private IndexedDB storage.

---
Built with ❤️ for a cleaner inbox.
