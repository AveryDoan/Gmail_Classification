import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table
import datetime

# Mock Data Generation (Mirroring the Data Model)
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
            "id": str(i),
            "sender": f"user{i}@{sender_domain}",
            "sender_domain": sender_domain,
            "subject": f"Sample subject {i}",
            "body": f"This is the body of email {i} which is a {purpose} regarding {topic}.",
            "date": date,
            "purpose": purpose,
            "topic": topic,
            "sender_type": "company" if "com" in sender_domain else "individual",
            "confidence": 0.85 + (i % 15) / 100.0
        })
    return pd.DataFrame(data)

df = generate_mock_data()

# Initialize App
app = Dash(__name__)

# Figures
def create_pie(data):
    return px.pie(data, names="purpose", title="Email Purpose Distribution", hole=.3, color_discrete_sequence=px.colors.qualitative.Pastel)

def create_sunburst(data):
    return px.sunburst(data, path=["sender_type", "purpose"], title="Sender Type → Purpose Breakdown", color_discrete_sequence=px.colors.qualitative.Safe)

def create_histogram(data):
    return px.histogram(data, x="date", color="topic", title="Email Topics Over Time", barmode="stack")

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
    
    html.Div(style={'marginTop': '30px', 'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px -1px rgb(0 0 0 / 0.1)'}, children=[
        html.H3("Filtered Email List", style={'color': '#334155'}),
        dash_table.DataTable(
            id="email_table",
            columns=[
                {"name": "Date", "id": "date"},
                {"name": "Sender", "id": "sender"},
                {"name": "Subject", "id": "subject"},
                {"name": "Purpose", "id": "purpose"},
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

# Callbacks for Interaction
@app.callback(
    Output("email_table", "data"),
    Input("purpose_chart", "clickData"),
    Input("sender_chart", "clickData"),
    Input("topic_chart", "clickData")
)
def filter_emails(purpose_click, sender_click, topic_click):
    filtered_df = df.copy()
    
    # Simple logic: filter based on the last clicked element
    from dash import callback_context
    ctx = callback_context
    if not ctx.triggered:
        return df.to_dict("records")
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    click_data = ctx.triggered[0]["value"]
    
    if trigger_id == "purpose_chart" and click_data:
        label = click_data["points"][0]["label"]
        filtered_df = df[df["purpose"] == label]
    
    elif trigger_id == "sender_chart" and click_data:
        label = click_data["points"][0]["label"]
        # Check if it's sender_type or purpose in sunburst
        if label in ["company", "individual"]:
            filtered_df = df[df["sender_type"] == label]
        else:
            filtered_df = df[df["purpose"] == label]
            
    elif trigger_id == "topic_chart" and click_data:
        # For histogram, we filter by topic
        # Note: histogram clickData structure is slightly different
        try:
            # Custom logic for histogram filtering
            pass 
        except:
            pass
            
    return filtered_df.to_dict("records")

if __name__ == "__main__":
    app.run(debug=True)
