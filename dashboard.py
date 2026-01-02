import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table
import datetime
import os

def generate_mock_data():
    data = []
    purposes = ["transactional", "newsletter", "promotion", "personal"]
    topics = ["finance", "tech", "shopping", "travel", "work", "social"]
    senders = ["amazon.com", "github.com", "newsletter@ai.com", "mom@gmail.com", "hr@company.com"]
    
    start_date = datetime.datetime(2023, 12, 1)
    for i in range(100):
        date = start_date + datetime.timedelta(days=i/5)
        purpose = purposes[i % 4]
        topic = topics[i % 6]
        sender_domain = senders[i % 5]
        data.append({
            "date": date,
            "sender name": f"user{i}@{sender_domain}",
            "purpose": purpose,
            "subject": f"Sample subject {i}",
            "content": f"Example content for email {i}",
            "topic": topic,
            "sender_type": "company" if "com" in sender_domain else "individual",
            "confidence": 0.85 + (i % 15) / 100.0
        })
    return pd.DataFrame(data)

# Data Loading (Load real data if available, else mock)
def load_data():
    filename = "emails_classified.csv"
    if os.path.isfile(filename):
        try:
            df = pd.read_csv(filename)
            if not df.empty:
                # Ensure date is parsed
                df['date'] = pd.to_datetime(df['date'])
                return df
        except Exception as e:
            print(f"Error loading CSV: {e}")
    
    return generate_mock_data()

df = load_data()

# Initialize App
app = Dash(__name__)

# Figures
def create_pie(data):
    return px.pie(data, names="purpose", title="Email Purpose Distribution", hole=.3, color_discrete_sequence=px.colors.qualitative.Pastel)

def create_sunburst(data):
    return px.sunburst(data, path=["sender_type", "purpose"], title="Sender Type → Purpose Breakdown", color_discrete_sequence=px.colors.qualitative.Safe)

def create_histogram(data):
    return px.histogram(data, x="date", color="topic", title="Email Topics Over Time", barmode="stack")

def create_sender_bar(data):
    sender_counts = data['sender name'].value_counts().reset_index()
    sender_counts.columns = ['sender name', 'count']
    return px.bar(sender_counts.head(15), x="sender name", y="count", title="Top Senders", color="count", color_continuous_scale="Viridis")

app.layout = html.Div(style={'fontFamily': 'system-ui, -apple-system, sans-serif', 'padding': '20px', 'backgroundColor': '#f8fafc'}, children=[
    html.H1("Gmail Analytics Dashboard", style={'textAlign': 'center', 'color': '#1e293b', 'marginBottom': '30px'}),
    
    html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'justifyContent': 'center'}, children=[
        html.Div(style={'flex': '1', 'minWidth': '400px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px -1px rgb(0 0 0 / 0.1)'}, children=[
            dcc.Graph(id="purpose_chart", figure=create_pie(df))
        ]),
        html.Div(style={'flex': '1', 'minWidth': '400px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px -1px rgb(0 0 0 / 0.1)'}, children=[
            dcc.Graph(id="sender_chart", figure=create_sunburst(df))
        ])
    ]),
    
    html.Div(style={'marginTop': '20px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px -1px rgb(0 0 0 / 0.1)'}, children=[
        dcc.Graph(id="topic_chart", figure=create_histogram(df))
    ]),

    html.Div(style={'marginTop': '20px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px -1px rgb(0 0 0 / 0.1)'}, children=[
        dcc.Graph(id="sender_bar_chart", figure=create_sender_bar(df))
    ]),

    dcc.Interval(
        id='interval-component',
        interval=5*1000, # in milliseconds (5 seconds)
        n_intervals=0
    ),
    
    html.Div(style={'marginTop': '30px', 'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px -1px rgb(0 0 0 / 0.1)'}, children=[
        html.H3("Filtered Email List", style={'color': '#334155'}),
        dash_table.DataTable(
            id="email_table",
            columns=[
                {"name": "Date", "id": "date"},
                {"name": "Sender", "id": "sender name"},
                {"name": "Purpose", "id": "purpose"},
                {"name": "Subject", "id": "subject"},
                {"name": "Content", "id": "content"},
                {"name": "Topic", "id": "topic"},
                {"name": "Confidence", "id": "confidence"}
            ],
            data=df.to_dict("records"),
            page_size=10,
            style_header={'backgroundColor': '#f1f5f9', 'fontWeight': 'bold', 'color': '#475569'},
            style_cell={'textAlign': 'left', 'padding': '12px', 'fontSize': '14px'},
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8fafc'}
            ]
        )
    ])
])

# Callback to update data periodically
@app.callback(
    Output("email_table", "data"),
    Output("purpose_chart", "figure"),
    Output("sender_chart", "figure"),
    Output("topic_chart", "figure"),
    Output("sender_bar_chart", "figure"),
    Input("interval-component", "n_intervals"),
    Input("purpose_chart", "clickData"),
    Input("sender_chart", "clickData"),
    Input("topic_chart", "clickData"),
    Input("sender_bar_chart", "clickData")
)
def update_dashboard(n, purpose_click, sender_click, topic_click, sender_bar_click):
    current_df = load_data()
    
    # Filtering logic
    filtered_df = current_df.copy()
    
    from dash import callback_context
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
    
    if triggered_id == "purpose_chart" and purpose_click:
        label = purpose_click["points"][0]["label"]
        filtered_df = current_df[current_df["purpose"] == label]
    
    elif triggered_id == "sender_chart" and sender_click:
        label = sender_click["points"][0]["label"]
        if label in ["company", "individual", "platform", "government"]:
            filtered_df = current_df[current_df["sender_type"] == label]
        else:
            filtered_df = current_df[current_df["purpose"] == label]
            
    elif triggered_id == "sender_bar_chart" and sender_bar_click:
        label = sender_bar_click["points"][0]["x"]
        filtered_df = current_df[current_df["sender name"] == label]
            
    return (
        filtered_df.to_dict("records"),
        create_pie(current_df),
        create_sunburst(current_df),
        create_histogram(current_df),
        create_sender_bar(current_df)
    )

if __name__ == "__main__":
    app.run(debug=True)
