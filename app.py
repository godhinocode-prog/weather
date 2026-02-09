"""
AI Business Insight Dashboard - Single File Flask App
Deploy: python app.py
Access: http://localhost:5000
"""

# ========== IMPORTS ==========
import os
import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import plotly.graph_objects as go
import plotly.utils
import random
import hashlib
from functools import lru_cache

# ========== CONFIGURATION ==========
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-2026")
DATABASE = 'business_data.db'

# ========== HTML TEMPLATES (Embedded) ==========
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Business Insight AI{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <style>
        :root {
            --primary: #6366f1;
            --secondary: #8b5cf6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .card-hover:hover {
            transform: translateY(-5px);
            transition: transform 0.3s ease;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
        }
        .pulse {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(99, 102, 241, 0); }
            100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
        }
        .insight-card {
            border-left: 4px solid var(--primary);
        }
        .metric-card {
            border-radius: 15px;
            overflow: hidden;
        }
        .trend-up { color: var(--success); }
        .trend-down { color: var(--danger); }
        .loader {
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body class="bg-light">
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark gradient-bg shadow">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">
                <i class="bi bi-graph-up-arrow me-2"></i>BizInsight AI
            </a>
            <div class="navbar-nav">
                <a class="nav-link" href="/"><i class="bi bi-dashboard me-1"></i>Dashboard</a>
                <a class="nav-link" href="/reports"><i class="bi bi-file-earmark-text me-1"></i>Reports</a>
                <a class="nav-link" href="/settings"><i class="bi bi-gear me-1"></i>Settings</a>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>

    <!-- Footer -->
    <footer class="mt-5 py-4 bg-white border-top">
        <div class="container text-center text-muted">
            <p>AI Business Insight Dashboard • v1.0 • Data updates every 15 minutes</p>
            <p class="small">Last updated: {{ current_time }}</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Auto-refresh data every 5 minutes
        setTimeout(() => {
            window.location.reload();
        }, 300000);

        // AJAX for real-time updates
        function updateMetric(metricId) {
            fetch(`/api/metric/${metricId}`)
                .then(r => r.json())
                .then(data => {
                    document.getElementById(`value-${metricId}`).innerText = data.value;
                    document.getElementById(`trend-${metricId}`).innerHTML = data.trend;
                });
        }

        // Initialize tooltips
        document.addEventListener('DOMContentLoaded', function() {
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        });
    </script>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
{% extends "base.html" %}
{% block title %}Dashboard - Business Insight AI{% endblock %}
{% block content %}
<div class="row mb-4">
    <div class="col">
        <h2 class="fw-bold">Business Dashboard</h2>
        <p class="text-muted">AI-powered insights for smarter decisions</p>
    </div>
    <div class="col-auto">
        <button class="btn btn-primary" onclick="location.reload()">
            <i class="bi bi-arrow-clockwise"></i> Refresh
        </button>
    </div>
</div>

<!-- Key Metrics -->
<div class="row mb-4">
    {% for metric in metrics %}
    <div class="col-md-3 mb-3">
        <div class="card metric-card card-hover h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="card-subtitle text-muted">{{ metric.name }}</h6>
                        <h3 class="card-title fw-bold mt-2" id="value-{{ metric.id }}">
                            {{ metric.value }}
                        </h3>
                    </div>
                    <div class="rounded-circle p-2" style="background: {{ metric.color }}20;">
                        <i class="bi {{ metric.icon }} fs-4" style="color: {{ metric.color }};"></i>
                    </div>
                </div>
                <div class="mt-2">
                    <span id="trend-{{ metric.id }}">{{ metric.trend|safe }}</span>
                    <span class="text-muted small ms-2">vs last week</span>
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</div>

<!-- Charts & AI Insights -->
<div class="row">
    <!-- Revenue Chart -->
    <div class="col-lg-8 mb-4">
        <div class="card h-100">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0"><i class="bi bi-bar-chart-line me-2"></i>Revenue Trends</h5>
                <select class="form-select form-select-sm w-auto" onchange="updateChart(this.value)">
                    <option value="7d">Last 7 days</option>
                    <option value="30d">Last 30 days</option>
                    <option value="90d">Last quarter</option>
                </select>
            </div>
            <div class="card-body">
                <div id="revenue-chart"></div>
            </div>
        </div>
    </div>

    <!-- AI Insights -->
    <div class="col-lg-4 mb-4">
        <div class="card h-100">
            <div class="card-header">
                <h5 class="mb-0"><i class="bi bi-robot me-2"></i>AI Insights</h5>
            </div>
            <div class="card-body">
                {% for insight in insights %}
                <div class="insight-card p-3 mb-3 bg-light rounded">
                    <div class="d-flex">
                        <div class="flex-shrink-0">
                            <i class="bi {{ insight.icon }} fs-4 text-{{ insight.type }} me-3"></i>
                        </div>
                        <div class="flex-grow-1">
                            <h6 class="fw-bold">{{ insight.title }}</h6>
                            <p class="small mb-0">{{ insight.message }}</p>
                            <div class="mt-2 small text-muted">
                                <i class="bi bi-clock me-1"></i> {{ insight.time }}
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
                <button class="btn btn-outline-primary w-100" onclick="generateInsight()">
                    <i class="bi bi-magic me-1"></i> Generate New Insight
                </button>
            </div>
        </div>
    </div>
</div>

<!-- Recent Activity -->
<div class="row mt-3">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0"><i class="bi bi-activity me-2"></i>Recent Activity</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Event</th>
                                <th>Impact</th>
                                <th>Details</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for activity in activities %}
                            <tr>
                                <td class="small">{{ activity.time }}</td>
                                <td>{{ activity.event }}</td>
                                <td><span class="badge bg-{{ activity.impact }}">{{ activity.impact|capitalize }}</span></td>
                                <td class="small">{{ activity.details }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // Render Plotly chart
    var graphJSON = {{ chart_json|safe }};
    Plotly.newPlot('revenue-chart', graphJSON.data, graphJSON.layout);

    function updateChart(range) {
        fetch(`/api/chart/${range}`)
            .then(r => r.json())
            .then(data => {
                Plotly.react('revenue-chart', data.data, data.layout);
            });
    }

    function generateInsight() {
        document.querySelector('#ai-insights').innerHTML = `
            <div class="text-center py-4">
                <div class="loader mx-auto mb-3"></div>
                <p>AI is analyzing your data...</p>
            </div>`;
        
        fetch('/api/generate-insight')
            .then(r => r.json())
            .then(data => {
                location.reload();
            });
    }
</script>
{% endblock %}
'''

# ========== DATABASE SETUP ==========
def init_db():
    """Initialize SQLite database with sample data"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY,
            name TEXT,
            value REAL,
            target REAL,
            unit TEXT,
            trend REAL
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS revenue (
            date TEXT PRIMARY KEY,
            amount REAL,
            customers INTEGER,
            avg_order REAL
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            message TEXT,
            type TEXT,
            created_at TIMESTAMP
        )
    ''')
    
    # Check if we need to populate with sample data
    c.execute("SELECT COUNT(*) FROM metrics")
    if c.fetchone()[0] == 0:
        sample_metrics = [
            ('Monthly Revenue', 124850, 120000, '$', 4.2),
            ('Active Customers', 3421, 3500, '', 1.8),
            ('Conversion Rate', 3.42, 3.5, '%', -0.3),
            ('Avg Order Value', 89.50, 85.0, '$', 2.1),
            ('Customer Satisfaction', 4.7, 4.5, '/5', 0.2),
            ('Churn Rate', 2.1, 2.0, '%', -0.1)
        ]
        c.executemany('INSERT INTO metrics (name, value, target, unit, trend) VALUES (?,?,?,?,?)', sample_metrics)
        
        # Generate 30 days of revenue data
        base_date = datetime.now() - timedelta(days=30)
        for i in range(30):
            date = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            amount = 3500 + random.randint(-200, 500) + (i * 15)
            customers = random.randint(80, 120)
            avg_order = 75 + random.randint(-10, 15)
            c.execute('INSERT OR REPLACE INTO revenue VALUES (?,?,?,?)', (date, amount, customers, avg_order))
        
        # Sample insights
        sample_insights = [
            ('Revenue Growth Detected', 'Thursday shows 15% higher revenue than weekly average. Consider promoting Thursday specials.', 'success', datetime.now() - timedelta(hours=2)),
            ('Customer Feedback Alert', '3 customers mentioned slow checkout. Review payment processing flow.', 'warning', datetime.now() - timedelta(hours=5)),
            ('Upsell Opportunity', 'Customers who bought Product A are 40% more likely to buy Product B. Create bundle offer.', 'primary', datetime.now() - timedelta(hours=8))
        ]
        c.executemany('INSERT INTO insights (title, message, type, created_at) VALUES (?,?,?,?)', sample_insights)
    
    conn.commit()
    conn.close()

# ========== BUSINESS LOGIC ==========
class BusinessAnalytics:
    @staticmethod
    def calculate_growth(current, previous):
        if previous == 0:
            return 0
        return round(((current - previous) / previous) * 100, 1)
    
    @staticmethod
    def generate_ai_insight():
        """Generate AI-powered business insight"""
        insights = [
            {
                'title': 'Weekend Performance',
                'message': 'Weekend sales are 22% higher than weekdays. Consider targeted weekend promotions.',
                'type': 'success',
                'icon': 'bi-calendar-week'
            },
            {
                'title': 'Customer Segmentation',
                'message': 'Top 20% of customers generate 65% of revenue. Launch loyalty program.',
                'type': 'primary',
                'icon': 'bi-people'
            },
            {
                'title': 'Operational Efficiency',
                'message': 'Peak hours: 2-4 PM. Consider staffing adjustments for better service.',
                'type': 'warning',
                'icon': 'bi-clock-history'
            },
            {
                'title': 'Product Opportunity',
                'message': 'Accessories have highest margin (42%). Feature them more prominently.',
                'type': 'info',
                'icon': 'bi-box'
            }
        ]
        return random.choice(insights)
    
    @staticmethod
    def predict_next_week():
        """Simple prediction algorithm"""
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT amount FROM revenue ORDER BY date DESC LIMIT 7")
        data = [row[0] for row in c.fetchall()]
        conn.close()
        
        if len(data) >= 2:
            growth = (data[0] - data[-1]) / data[-1]
            prediction = data[0] * (1 + growth * 0.7)  # Conservative projection
            return round(prediction, 2)
        return 0

# ========== ROUTES ==========
@app.route('/')
def dashboard():
    """Main dashboard page"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Get metrics
    c.execute("SELECT rowid, name, value, target, unit, trend FROM metrics")
    metrics_data = []
    colors = ['#6366f1', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4']
    icons = ['bi-cash-coin', 'bi-person-check', 'bi-percent', 'bi-cart', 'bi-star', 'bi-arrow-down-right']
    
    for idx, row in enumerate(c.fetchall()):
        metric_id, name, value, target, unit, trend = row
        trend_html = f'<i class="bi bi-arrow-up-right trend-{"up" if trend > 0 else "down"}"></i> {abs(trend)}%'
        metrics_data.append({
            'id': metric_id,
            'name': name,
            'value': f'{unit}{value:,}' if unit != '%' else f'{value}%',
            'trend': trend_html,
            'color': colors[idx % len(colors)],
            'icon': icons[idx % len(icons)]
        })
    
    # Generate chart data
    c.execute("SELECT date, amount FROM revenue ORDER BY date DESC LIMIT 30")
    revenue_data = c.fetchall()
    dates = [row[0][5:] for row in reversed(revenue_data)]  # MM-DD format
    amounts = [row[1] for row in reversed(revenue_data)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=amounts,
        mode='lines+markers',
        name='Revenue',
        line=dict(color='#6366f1', width=3),
        fill='tozeroy',
        fillcolor='rgba(99, 102, 241, 0.1)'
    ))
    
    fig.update_layout(
        template='plotly_white',
        height=300,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
        xaxis_title=None,
        yaxis_title=None,
        hovermode='x unified'
    )
    
    chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Get AI insights
    c.execute("SELECT title, message, type FROM insights ORDER BY created_at DESC LIMIT 3")
    insights_data = []
    type_icons = {
        'success': 'bi-check-circle',
        'warning': 'bi-exclamation-triangle',
        'primary': 'bi-lightbulb',
        'info': 'bi-info-circle'
    }
    
    for title, message, insight_type in c.fetchall():
        insights_data.append({
            'title': title,
            'message': message,
            'type': insight_type,
            'icon': type_icons.get(insight_type, 'bi-info-circle'),
            'time': '2 hours ago'
        })
    
    # Recent activities
    activities = [
        {'time': '10:30 AM', 'event': 'Revenue target exceeded', 'impact': 'success', 'details': 'Monthly goal achieved 3 days early'},
        {'time': '9:15 AM', 'event': 'New customer segment identified', 'impact': 'primary', 'details': '25-34 age group increased by 18%'},
        {'time': 'Yesterday', 'event': 'Website traffic spike', 'impact': 'warning', 'details': '+42% traffic from social media'},
        {'time': 'Mar 12', 'event': 'Product launch', 'impact': 'info', 'details': 'New premium tier launched'}
    ]
    
    conn.close()
    
    return render_template_string(
        DASHBOARD_TEMPLATE,
        metrics=metrics_data,
        chart_json=chart_json,
        insights=insights_data,
        activities=activities,
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M')
    )

@app.route('/api/metric/<int:metric_id>')
def get_metric(metric_id):
    """API endpoint for live metric updates"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT name, value, unit, trend FROM metrics WHERE rowid=?", (metric_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        name, value, unit, trend = row
        trend_html = f'<i class="bi bi-arrow-up-right trend-{"up" if trend > 0 else "down"}"></i> {abs(trend)}%'
        return jsonify({
            'value': f'{unit}{value:,}' if unit != '%' else f'{value}%',
            'trend': trend_html
        })
    return jsonify({'error': 'Metric not found'}), 404

@app.route('/api/chart/<range>')
def get_chart_data(range):
    """API endpoint for chart updates"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    if range == '7d':
        c.execute("SELECT date, amount FROM revenue ORDER BY date DESC LIMIT 7")
    elif range == '30d':
        c.execute("SELECT date, amount FROM revenue ORDER BY date DESC LIMIT 30")
    else:  # 90d
        c.execute("SELECT date, amount FROM revenue ORDER BY date DESC LIMIT 90")
    
    data = c.fetchall()
    conn.close()
    
    dates = [row[0][5:] for row in reversed(data)]
    amounts = [row[1] for row in reversed(data)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=amounts,
        mode='lines+markers',
        name='Revenue',
        line=dict(color='#6366f1', width=3)
    ))
    
    fig.update_layout(
        template='plotly_white',
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    
    return jsonify(fig.to_dict())

@app.route('/api/generate-insight')
def generate_insight():
    """Generate new AI insight"""
    insight = BusinessAnalytics.generate_ai_insight()
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO insights (title, message, type, created_at) VALUES (?,?,?,?)",
        (insight['title'], insight['message'], insight['type'], datetime.now())
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'insight': insight})

@app.route('/reports')
def reports():
    """Simple reports page"""
    html = '''
    <div class="card">
        <div class="card-header">
            <h4><i class="bi bi-file-earmark-pdf me-2"></i>Business Reports</h4>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-4 mb-3">
                    <div class="card card-hover">
                        <div class="card-body text-center">
                            <i class="bi bi-file-text fs-1 text-primary mb-3"></i>
                            <h5>Monthly Performance</h5>
                            <p class="text-muted">Complete analysis for {{ current_month }}</p>
                            <button class="btn btn-outline-primary">Generate PDF</button>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-3">
                    <div class="card card-hover">
                        <div class="card-body text-center">
                            <i class="bi bi-graph-up fs-1 text-success mb-3"></i>
                            <h5>Growth Trends</h5>
                            <p class="text-muted">Year-over-year comparison</p>
                            <button class="btn btn-outline-success">View Analysis</button>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-3">
                    <div class="card card-hover">
                        <div class="card-body text-center">
                            <i class="bi bi-people fs-1 text-warning mb-3"></i>
                            <h5>Customer Report</h5>
                            <p class="text-muted">Segmentation and behavior</p>
                            <button class="btn btn-outline-warning">Generate</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <a href="/" class="btn btn-link mt-3"><i class="bi bi-arrow-left"></i> Back to Dashboard</a>
    '''
    return render_template_string(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', html),
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M'),
        current_month=datetime.now().strftime('%B %Y')
    )

@app.route('/settings')
def settings():
    """Settings page"""
    html = '''
    <div class="row justify-content-center">
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header">
                    <h4><i class="bi bi-gear me-2"></i>Settings</h4>
                </div>
                <div class="card-body">
                    <form>
                        <div class="mb-3">
                            <label class="form-label">Company Name</label>
                            <input type="text" class="form-control" value="BizInsight AI Demo">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Data Refresh Interval</label>
                            <select class="form-select">
                                <option>15 minutes</option>
                                <option selected>30 minutes</option>
                                <option>1 hour</option>
                                <option>4 hours</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Notification Preferences</label>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" checked>
                                <label class="form-check-label">Email alerts for anomalies</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" checked>
                                <label class="form-check-label">Weekly summary reports</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox">
                                <label class="form-check-label">Real-time mobile notifications</label>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">AI Analysis Level</label>
                            <div class="form-range" min="1" max="3" step="1">
                                <span class="badge bg-light text-dark me-2">Basic</span>
                                <span class="badge bg-primary me-2">Standard</span>
                                <span class="badge bg-dark">Advanced</span>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">Save Settings</button>
                    </form>
                </div>
            </div>
            <div class="card mt-3">
                <div class="card-body">
                    <h5><i class="bi bi-shield-check me-2"></i>Data Management</h5>
                    <p class="text-muted small">All data is stored locally in your browser and SQLite database.</p>
                    <button class="btn btn-outline-danger me-2"><i class="bi bi-trash"></i> Clear Cache</button>
                    <button class="btn btn-outline-secondary"><i class="bi bi-download"></i> Export Data</button>
                </div>
            </div>
        </div>
    </div>
    <a href="/" class="btn btn-link mt-3"><i class="bi bi-arrow-left"></i> Back to Dashboard</a>
    '''
    return render_template_string(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', html),
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M')
    )

# ========== MAIN EXECUTION ==========
if __name__ == '__main__':
    # Initialize database with sample data
    init_db()
    
    # Print startup information
    print("\n" + "="*50)
    print("🚀 AI Business Insight Dashboard")
    print("="*50)
    print(f"Local:   http://127.0.0.1:5000")
    print(f"Network: http://{os.environ.get('HOST', '0.0.0.0')}:{os.environ.get('PORT', 5000)}")
    print("\n📊 Features:")
    print("  • Real-time business metrics")
    print("  • AI-generated insights")
    print("  • Interactive revenue charts")
    print("  • SQLite database with sample data")
    print("  • Fully responsive design")
    print("="*50 + "\n")
    
    # Run the app
    app.run(
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 5000)),
        debug=True
    )
