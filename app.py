"""
Smart Expense Splitter - Single File Flask App (No Database)
Perfect for 2026: Privacy-focused, social, and AI-enhanced
Deploy: python app.py
Access: http://localhost:5000
"""

# ========== IMPORTS ==========
import os
import json
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
import plotly.graph_objects as go
import plotly.utils
from typing import Dict, List, Tuple
import hashlib
import re

# ========== CONFIGURATION ==========
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "expense-splitter-2026-secure-key")
app.config['SESSION_TYPE'] = 'filesystem'

# In-memory storage (no database!)
# This is fine for a single-instance app with moderate traffic
expense_rooms = {}
user_sessions = {}

# ========== HTML TEMPLATES (Embedded) ==========
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Expense Splitter{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css">
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <style>
        :root {
            --primary: #3b82f6;
            --secondary: #8b5cf6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --dark: #1f2937;
            --light: #f9fafb;
        }
        body {
            background: linear-gradient(135deg, #f0f4ff 0%, #f8fafc 100%);
            min-height: 100vh;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        .navbar-brand {
            font-weight: 800;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .card-hover {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid #e5e7eb;
        }
        .card-hover:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.05) !important;
            border-color: var(--primary);
        }
        .btn-gradient {
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            color: white;
            border: none;
            font-weight: 600;
        }
        .btn-gradient:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 25px rgba(59, 130, 246, 0.3);
            color: white;
        }
        .pulse {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
            100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
        }
        .receipt-card {
            border-left: 4px solid var(--primary);
            background: linear-gradient(to right, #ffffff, #f8fafc);
        }
        .user-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
        }
        .amount-badge {
            font-size: 0.9em;
            font-weight: 600;
            padding: 0.5em 1em;
        }
        .split-method {
            background: #f0f9ff;
            border: 2px solid #3b82f6;
            color: #1d4ed8;
        }
        .currency-input {
            font-size: 1.5rem;
            font-weight: 600;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            padding: 10px 15px;
        }
        .currency-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        .qr-code {
            width: 120px;
            height: 120px;
            background: #f3f4f6;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
        }
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
        .receipt-line {
            border-bottom: 2px dashed #e5e7eb;
            margin: 10px 0;
        }
        .settle-btn {
            background: linear-gradient(90deg, var(--success), #34d399);
            color: white;
            font-weight: 600;
        }
        .copy-link {
            cursor: pointer;
            background: #f8fafc;
            border: 2px dashed #d1d5db;
            border-radius: 10px;
            padding: 10px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }
        .copy-link:hover {
            background: #f0f9ff;
            border-color: var(--primary);
        }
        .ai-suggestion {
            background: linear-gradient(to right, #f0f9ff, #fef3c7);
            border-left: 4px solid var(--warning);
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-white bg-white shadow-sm sticky-top">
        <div class="container">
            <a class="navbar-brand fs-3" href="/">
                <i class="bi bi-calculator-fill me-2"></i>SplitSmart
            </a>
            <div class="navbar-nav">
                <a class="nav-link fw-medium" href="/"><i class="bi bi-house me-1"></i>Home</a>
                <a class="nav-link fw-medium" href="/create"><i class="bi bi-plus-circle me-1"></i>New Split</a>
                <a class="nav-link fw-medium" href="/history"><i class="bi bi-clock-history me-1"></i>History</a>
                <div class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle fw-medium" href="#" role="button" data-bs-toggle="dropdown">
                        <i class="bi bi-person-circle me-1"></i>Account
                    </a>
                    <ul class="dropdown-menu">
                        <li><a class="dropdown-item" href="/profile"><i class="bi bi-person me-2"></i>Profile</a></li>
                        <li><a class="dropdown-item" href="/settings"><i class="bi bi-gear me-2"></i>Settings</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item text-danger" href="/logout"><i class="bi bi-box-arrow-right me-2"></i>Logout</a></li>
                    </ul>
                </div>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="container py-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show animate__animated animate__fadeIn">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    <footer class="mt-5 py-4 bg-white border-top">
        <div class="container text-center">
            <div class="row align-items-center">
                <div class="col-md-4">
                    <h6 class="fw-bold mb-2">SplitSmart</h6>
                    <p class="small text-muted mb-0">Smart expense splitting for friends & groups</p>
                </div>
                <div class="col-md-4">
                    <div class="d-flex justify-content-center gap-3 mb-3">
                        <a href="#" class="text-muted"><i class="bi bi-twitter fs-5"></i></a>
                        <a href="#" class="text-muted"><i class="bi bi-github fs-5"></i></a>
                        <a href="#" class="text-muted"><i class="bi bi-discord fs-5"></i></a>
                    </div>
                </div>
                <div class="col-md-4">
                    <p class="small text-muted mb-0">
                        <i class="bi bi-shield-check me-1"></i>No database • Privacy focused • 2026 Ready
                    </p>
                </div>
            </div>
            <hr class="my-3">
            <p class="small text-muted mb-0">
                © 2026 SplitSmart • All data stored locally in your session
            </p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/qrcode@1.5.3/build/qrcode.min.js"></script>
    
    <script>
        // Initialize QR Code
        function generateQR(elementId, text) {
            QRCode.toCanvas(document.getElementById(elementId), text, {
                width: 100,
                height: 100,
                margin: 1
            });
        }

        // Copy link to clipboard
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                alert('Link copied to clipboard!');
            });
        }

        // Format currency input
        document.addEventListener('input', function(e) {
            if (e.target.classList.contains('currency-format')) {
                let value = e.target.value.replace(/[^0-9.]/g, '');
                if (value) {
                    e.target.value = parseFloat(value).toFixed(2);
                }
            }
        });

        // Auto-calculate splits
        function calculateSplit() {
            const total = parseFloat(document.getElementById('totalAmount')?.value) || 0;
            const people = parseInt(document.getElementById('numPeople')?.value) || 1;
            if (total > 0 && people > 0) {
                const perPerson = total / people;
                document.getElementById('perPerson').innerText = `$${perPerson.toFixed(2)} each`;
            }
        }

        // Share functionality
        function shareExpense() {
            if (navigator.share) {
                navigator.share({
                    title: 'Split this expense with me!',
                    url: window.location.href
                });
            }
        }

        // Initialize tooltips
        document.addEventListener('DOMContentLoaded', function() {
            var tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltips.map(function (el) {
                return new bootstrap.Tooltip(el);
            });
        });
    </script>
</body>
</html>
'''

# ========== HELPER CLASSES ==========
class ExpenseCalculator:
    """Core expense calculation logic"""
    
    @staticmethod
    def calculate_splits(total: float, people: List[str], method: str = 'equal', 
                        custom_percentages: Dict[str, float] = None) -> Dict[str, float]:
        """
        Calculate splits based on method
        Methods: equal, percentage, exact, weighted
        """
        total = Decimal(str(total))
        
        if method == 'equal':
            share = total / Decimal(len(people))
            return {person: float(share.quantize(Decimal('0.01'), ROUND_HALF_UP)) 
                   for person in people}
        
        elif method == 'percentage':
            if not custom_percentages or sum(custom_percentages.values()) != 100:
                raise ValueError("Percentages must sum to 100")
            
            result = {}
            for person in people:
                percentage = Decimal(str(custom_percentages.get(person, 0))) / Decimal('100')
                result[person] = float((total * percentage).quantize(Decimal('0.01'), ROUND_HALF_UP))
            return result
        
        elif method == 'exact':
            if not custom_percentages:
                raise ValueError("Exact amounts required")
            
            if Decimal(str(sum(custom_percentages.values()))) != total:
                raise ValueError(f"Exact amounts must sum to {total}")
            
            return {person: float(Decimal(str(amount)).quantize(Decimal('0.01'), ROUND_HALF_UP))
                   for person, amount in custom_percentages.items()}
        
        return {}

    @staticmethod
    def optimize_settlements(debts: Dict[str, float]) -> List[Dict]:
        """
        Optimize debt settlements using minimum transactions
        Returns list of settlement instructions
        """
        # Group by debtor/creditor
        balances = defaultdict(float)
        for person, amount in debts.items():
            balances[person] += amount
        
        # Separate creditors and debtors
        creditors = {p: a for p, a in balances.items() if a > 0}
        debtors = {p: -a for p, a in balances.items() if a < 0}
        
        settlements = []
        for debtor, debt_amount in debtors.items():
            remaining_debt = debt_amount
            
            for creditor, credit_amount in list(creditors.items()):
                if remaining_debt == 0:
                    break
                    
                if credit_amount > 0:
                    payment = min(remaining_debt, credit_amount)
                    settlements.append({
                        'from': debtor,
                        'to': creditor,
                        'amount': float(payment)
                    })
                    
                    remaining_debt -= payment
                    creditors[creditor] -= payment
        
        return settlements

class AISuggestions:
    """AI-powered expense suggestions"""
    
    COLOR_MAP = {
        'food': '#f59e0b',
        'drinks': '#8b5cf6',
        'travel': '#3b82f6',
        'shopping': '#ec4899',
        'entertainment': '#10b981',
        'utilities': '#6366f6',
        'other': '#6b7280'
    }
    
    @staticmethod
    def categorize_expense(description: str) -> str:
        """Simple AI categorization based on keywords"""
        desc_lower = description.lower()
        
        categories = {
            'food': ['restaurant', 'food', 'dinner', 'lunch', 'breakfast', 'cafe', 'pizza', 'burger'],
            'drinks': ['bar', 'drinks', 'coffee', 'beer', 'wine', 'cocktail'],
            'travel': ['uber', 'lyft', 'taxi', 'train', 'flight', 'hotel', 'gas'],
            'shopping': ['store', 'shop', 'amazon', 'target', 'walmart', 'clothes'],
            'entertainment': ['movie', 'concert', 'ticket', 'netflix', 'spotify'],
            'utilities': ['electric', 'water', 'internet', 'phone', 'rent'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in desc_lower for keyword in keywords):
                return category
        
        return 'other'

    @staticmethod
    def generate_suggestions(expenses: List) -> List[Dict]:
        """Generate AI suggestions for expense optimization"""
        if not expenses:
            return []
        
        suggestions = []
        
        # Calculate totals by category
        category_totals = defaultdict(float)
        for exp in expenses:
            category = exp.get('category', 'other')
            category_totals[category] += exp.get('amount', 0)
        
        # Generate suggestions
        if len(category_totals) > 0:
            max_category = max(category_totals.items(), key=lambda x: x[1])
            if max_category[1] > sum(category_totals.values()) * 0.4:  # More than 40%
                suggestions.append({
                    'type': 'warning',
                    'title': 'High Spending Alert',
                    'message': f"You're spending {max_category[0].upper()} makes up {(max_category[1]/sum(category_totals.values())*100):.0f}% of total"
                })
        
        # Check for large individual expenses
        large_expenses = [e for e in expenses if e.get('amount', 0) > 100]
        if len(large_expenses) > 2:
            suggestions.append({
                'type': 'info',
                'title': 'Multiple Large Expenses',
                'message': 'Consider splitting large expenses over time'
            })
        
        # Default suggestion
        if not suggestions:
            suggestions.append({
                'type': 'success',
                'title': 'Spending Looks Good',
                'message': 'Your expenses are well-distributed across categories'
            })
        
        return suggestions

class ReceiptGenerator:
    """Generate beautiful receipt/PDF-like outputs"""
    
    @staticmethod
    def generate_receipt_data(expense_data: Dict) -> Dict:
        """Format expense data for receipt display"""
        receipt = {
            'id': expense_data.get('id', str(uuid.uuid4())[:8]),
            'date': expense_data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M')),
            'title': expense_data.get('title', 'Untitled Expense'),
            'total': expense_data.get('total', 0),
            'paid_by': expense_data.get('paid_by', 'Unknown'),
            'split_method': expense_data.get('method', 'equal'),
            'participants': expense_data.get('participants', []),
            'splits': expense_data.get('splits', {}),
            'category': expense_data.get('category', 'other'),
            'description': expense_data.get('description', ''),
            'settlements': expense_data.get('settlements', [])
        }
        
        # Generate share URL
        receipt['share_url'] = f"/room/{receipt['id']}"
        receipt['qr_data'] = f"{request.host_url.strip('/')}{receipt['share_url']}"
        
        return receipt

# ========== ROUTES ==========
@app.route('/')
def home():
    """Homepage with quick actions"""
    html = '''
    <div class="row justify-content-center">
        <div class="col-lg-10">
            <!-- Hero Section -->
            <div class="text-center mb-5 animate__animated animate__fadeIn">
                <h1 class="display-5 fw-bold mb-3">Split Expenses <span class="text-primary">Smartly</span></h1>
                <p class="lead text-muted mb-4">
                    Split bills with friends, track group expenses, and settle up instantly.
                    No sign-up required. Privacy focused.
                </p>
                <div class="d-flex justify-content-center gap-3">
                    <a href="/create" class="btn btn-gradient btn-lg px-4">
                        <i class="bi bi-plus-circle me-2"></i>Create New Split
                    </a>
                    <a href="/join" class="btn btn-outline-primary btn-lg px-4">
                        <i class="bi bi-arrow-right-circle me-2"></i>Join Room
                    </a>
                </div>
            </div>

            <!-- Features Grid -->
            <div class="row g-4 mb-5">
                <div class="col-md-4">
                    <div class="card card-hover h-100 border-0 shadow-sm">
                        <div class="card-body text-center p-4">
                            <div class="rounded-circle bg-primary bg-opacity-10 p-3 d-inline-block mb-3">
                                <i class="bi bi-lightning-charge-fill fs-2 text-primary"></i>
                            </div>
                            <h5 class="fw-bold">Instant Splits</h5>
                            <p class="text-muted">Split bills equally, by percentage, or custom amounts in seconds.</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card card-hover h-100 border-0 shadow-sm">
                        <div class="card-body text-center p-4">
                            <div class="rounded-circle bg-success bg-opacity-10 p-3 d-inline-block mb-3">
                                <i class="bi bi-share-fill fs-2 text-success"></i>
                            </div>
                            <h5 class="fw-bold">Share & Collaborate</h5>
                            <p class="text-muted">Generate shareable links or QR codes for friends to join.</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card card-hover h-100 border-0 shadow-sm">
                        <div class="card-body text-center p-4">
                            <div class="rounded-circle bg-warning bg-opacity-10 p-3 d-inline-block mb-3">
                                <i class="bi bi-robot fs-2 text-warning"></i>
                            </div>
                            <h5 class="fw-bold">AI Insights</h5>
                            <p class="text-muted">Get smart suggestions for expense optimization and settlements.</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Quick Stats -->
            <div class="card border-0 shadow-sm mb-5">
                <div class="card-body p-4">
                    <div class="row text-center">
                        <div class="col-md-3">
                            <h3 class="fw-bold text-primary">{{ stats.expenses }}</h3>
                            <p class="text-muted mb-0">Expenses Tracked</p>
                        </div>
                        <div class="col-md-3">
                            <h3 class="fw-bold text-success">${{ stats.total }}</h3>
                            <p class="text-muted mb-0">Total Amount</p>
                        </div>
                        <div class="col-md-3">
                            <h3 class="fw-bold text-warning">{{ stats.users }}</h3>
                            <p class="text-muted mb-0">Active Users</p>
                        </div>
                        <div class="col-md-3">
                            <h3 class="fw-bold text-secondary">{{ stats.rooms }}</h3>
                            <p class="text-muted mb-0">Active Rooms</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recent Activity -->
            <div class="card border-0 shadow-sm">
                <div class="card-header bg-white border-0">
                    <h5 class="fw-bold mb-0"><i class="bi bi-clock-history me-2"></i>Recent Activity</h5>
                </div>
                <div class="card-body">
                    {% if recent_activity %}
                    <div class="list-group list-group-flush">
                        {% for activity in recent_activity %}
                        <div class="list-group-item border-0 px-0">
                            <div class="d-flex align-items-center">
                                <div class="user-avatar me-3" style="background: {{ activity.color }};">
                                    {{ activity.initials }}
                                </div>
                                <div class="flex-grow-1">
                                    <h6 class="mb-1">{{ activity.title }}</h6>
                                    <p class="text-muted small mb-0">
                                        <i class="bi bi-calendar me-1"></i>{{ activity.time }}
                                        <i class="bi bi-people ms-3 me-1"></i>{{ activity.participants }} people
                                    </p>
                                </div>
                                <div>
                                    <span class="badge amount-badge bg-light text-dark">${{ activity.amount }}</span>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="text-center py-5">
                        <i class="bi bi-receipt fs-1 text-muted mb-3"></i>
                        <p class="text-muted">No recent activity. Create your first split!</p>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    '''
    
    # Generate sample stats
    stats = {
        'expenses': len(expense_rooms),
        'total': sum(room.get('total', 0) for room in expense_rooms.values()),
        'users': len(user_sessions),
        'rooms': len(expense_rooms)
    }
    
    # Recent activity from rooms
    recent_activity = []
    colors = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899']
    
    for room_id, room in list(expense_rooms.items())[:5]:  # Last 5 rooms
        recent_activity.append({
            'title': room.get('title', 'Untitled'),
            'time': room.get('created_at', 'Just now'),
            'participants': len(room.get('participants', [])),
            'amount': room.get('total', 0),
            'color': colors[len(recent_activity) % len(colors)],
            'initials': ''.join([name[0] for name in room.get('title', 'EX').split()[:2]]).upper()
        })
    
    return render_template_string(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', html),
        stats=stats,
        recent_activity=recent_activity
    )

@app.route('/create', methods=['GET', 'POST'])
def create_expense():
    """Create a new expense split"""
    if request.method == 'POST':
        try:
            # Get form data
            title = request.form.get('title', 'Untitled Expense')
            total = float(request.form.get('total', 0))
            paid_by = request.form.get('paid_by', 'You')
            method = request.form.get('method', 'equal')
            
            # Parse participants
            participants_str = request.form.get('participants', '')
            participants = [p.strip() for p in participants_str.split(',') if p.strip()]
            
            if not participants:
                participants = ['Person 1', 'Person 2', 'Person 3']
            
            # Create expense room
            room_id = str(uuid.uuid4())[:8]
            category = AISuggestions.categorize_expense(title)
            
            # Calculate splits
            splits = ExpenseCalculator.calculate_splits(total, participants, method)
            
            # Create room data
            expense_rooms[room_id] = {
                'id': room_id,
                'title': title,
                'total': total,
                'paid_by': paid_by,
                'method': method,
                'participants': participants,
                'splits': splits,
                'category': category,
                'description': request.form.get('description', ''),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'color': AISuggestions.COLOR_MAP.get(category, '#6b7280')
            }
            
            # Generate settlements
            debts = {p: -amount for p, amount in splits.items()}
            debts[paid_by] = total - splits.get(paid_by, 0)
            settlements = ExpenseCalculator.optimize_settlements(debts)
            expense_rooms[room_id]['settlements'] = settlements
            
            return redirect(f'/room/{room_id}')
        
        except Exception as e:
            return f"Error: {str(e)}", 400
    
    # GET request - show form
    html = '''
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <div class="card border-0 shadow-sm">
                <div class="card-header bg-white border-0 pb-0">
                    <h4 class="fw-bold"><i class="bi bi-plus-circle me-2"></i>Create New Expense Split</h4>
                    <p class="text-muted">Split bills, rent, trips, or any group expense</p>
                </div>
                <div class="card-body">
                    <form method="POST" id="expenseForm">
                        <!-- Basic Info -->
                        <div class="row mb-4">
                            <div class="col-md-8 mb-3">
                                <label class="form-label fw-medium">Expense Title</label>
                                <input type="text" class="form-control form-control-lg" name="title" 
                                       placeholder="Dinner at Italian Restaurant" required>
                                <div class="form-text">A descriptive name for this expense</div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label class="form-label fw-medium">Total Amount</label>
                                <div class="input-group input-group-lg">
                                    <span class="input-group-text">$</span>
                                    <input type="number" class="form-control currency-format" name="total" 
                                           step="0.01" min="0" placeholder="0.00" required oninput="calculateSplit()">
                                </div>
                            </div>
                        </div>

                        <!-- Paid By -->
                        <div class="row mb-4">
                            <div class="col-md-6 mb-3">
                                <label class="form-label fw-medium">Paid By</label>
                                <input type="text" class="form-control" name="paid_by" 
                                       placeholder="Your name" value="You">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label fw-medium">Split Method</label>
                                <select class="form-select" name="method" id="splitMethod" onchange="toggleCustomInputs()">
                                    <option value="equal">Equal Split</option>
                                    <option value="percentage">By Percentage</option>
                                    <option value="exact">Exact Amounts</option>
                                </select>
                            </div>
                        </div>

                        <!-- Participants -->
                        <div class="mb-4">
                            <label class="form-label fw-medium">Participants</label>
                            <textarea class="form-control" name="participants" rows="2" 
                                      placeholder="Enter names separated by commas: Alex, Taylor, Jordan"></textarea>
                            <div class="form-text">Leave empty for default: Person 1, Person 2, Person 3</div>
                        </div>

                        <!-- Split Preview -->
                        <div class="card bg-light border-0 mb-4" id="splitPreview">
                            <div class="card-body">
                                <h6 class="fw-medium mb-3"><i class="bi bi-eye me-2"></i>Split Preview</h6>
                                <div class="text-center py-3">
                                    <h3 id="perPerson" class="fw-bold text-primary">$0.00 each</h3>
                                    <p class="text-muted small mb-0" id="splitDetails">Calculated for 3 people</p>
                                </div>
                            </div>
                        </div>

                        <!-- Description -->
                        <div class="mb-4">
                            <label class="form-label fw-medium">Description (Optional)</label>
                            <textarea class="form-control" name="description" rows="2" 
                                      placeholder="Any additional details about this expense..."></textarea>
                        </div>

                        <!-- Submit -->
                        <div class="d-flex justify-content-between">
                            <a href="/" class="btn btn-outline-secondary">
                                <i class="bi bi-arrow-left me-2"></i>Cancel
                            </a>
                            <button type="submit" class="btn btn-gradient px-4">
                                <i class="bi bi-lightning-charge me-2"></i>Create Split
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- AI Suggestions -->
            <div class="card border-0 shadow-sm mt-4 ai-suggestion">
                <div class="card-body">
                    <div class="d-flex">
                        <div class="flex-shrink-0">
                            <i class="bi bi-robot fs-3 text-warning"></i>
                        </div>
                        <div class="flex-grow-1 ms-3">
                            <h6 class="fw-bold mb-1">AI Suggestion</h6>
                            <p class="mb-0">For dining expenses, consider adding tax and tip (usually 15-20%) before splitting.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function calculateSplit() {
            const total = parseFloat(document.querySelector('[name="total"]').value) || 0;
            const participants = document.querySelector('[name="participants"]').value;
            const people = participants ? participants.split(',').filter(p => p.trim()).length : 3;
            
            if (total > 0 && people > 0) {
                const perPerson = total / people;
                document.getElementById('perPerson').innerText = `$${perPerson.toFixed(2)} each`;
                document.getElementById('splitDetails').innerText = `Calculated for ${people} people`;
            }
        }

        function toggleCustomInputs() {
            const method = document.getElementById('splitMethod').value;
            // Implement custom input toggles for percentage/exact methods
        }

        // Initial calculation
        document.addEventListener('DOMContentLoaded', calculateSplit);
    </script>
    '''
    
    return render_template_string(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', html)
    )

@app.route('/room/<room_id>')
def view_room(room_id):
    """View expense room with calculations"""
    room = expense_rooms.get(room_id)
    if not room:
        return "Room not found", 404
    
    # Generate receipt data
    receipt = ReceiptGenerator.generate_receipt_data(room)
    
    # Generate chart data
    labels = list(room['splits'].keys())
    values = list(room['splits'].values())
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.3,
        marker=dict(colors=[room['color']] * len(labels))
    )])
    
    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    
    chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    html = f'''
    <div class="row justify-content-center">
        <div class="col-lg-10">
            <!-- Header -->
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h2 class="fw-bold mb-1">{room['title']}</h2>
                    <p class="text-muted mb-0">
                        <i class="bi bi-calendar me-1"></i>{room['created_at']}
                        <i class="bi bi-tag ms-3 me-1"></i>{room['category'].title()}
                    </p>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-primary" onclick="shareExpense()">
                        <i class="bi bi-share me-1"></i>Share
                    </button>
                    <a href="/create" class="btn btn-gradient">
                        <i class="bi bi-plus-circle me-1"></i>New Split
                    </a>
                </div>
            </div>

            <!-- Main Content -->
            <div class="row">
                <!-- Left Column: Receipt -->
                <div class="col-lg-8">
                    <div class="card border-0 shadow-sm mb-4">
                        <div class="card-body receipt-card">
                            <div class="text-center mb-4">
                                <div class="display-6 fw-bold text-primary mb-2">${room['total']:.2f}</div>
                                <span class="badge split-method">{room['method'].title()} Split</span>
                            </div>

                            <div class="receipt-line"></div>

                            <!-- Paid By -->
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <div>
                                    <h6 class="fw-medium mb-1">Paid By</h6>
                                    <div class="d-flex align-items-center">
                                        <div class="user-avatar me-2" style="background: {room['color']};">
                                            {room['paid_by'][0].upper()}
                                        </div>
                                        <span class="fw-medium">{room['paid_by']}</span>
                                    </div>
                                </div>
                                <div class="text-end">
                                    <div class="fw-bold">${room['total']:.2f}</div>
                                    <small class="text-muted">Total paid</small>
                                </div>
                            </div>

                            <!-- Splits -->
                            <h6 class="fw-medium mt-4 mb-3">Split Details</h6>
                            <div class="list-group list-group-flush">
                                {% for person, amount in room['splits'].items() %}
                                <div class="list-group-item border-0 px-0">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div class="d-flex align-items-center">
                                            <div class="user-avatar me-3" style="background: {room['color'] if loop.index % 2 else '#10b981'}};">
                                                {{ person[0].upper() }}
                                            </div>
                                            <div>
                                                <h6 class="mb-0 fw-medium">{{ person }}</h6>
                                                <small class="text-muted">Owes</small>
                                            </div>
                                        </div>
                                        <div class="text-end">
                                            <div class="fw-bold">${amount:.2f}</div>
                                            <small class="text-muted">{{ (amount/room['total']*100)|round(1) }}%</small>
                                        </div>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>

                            {% if room['description'] %}
                            <div class="mt-4">
                                <h6 class="fw-medium mb-2">Notes</h6>
                                <p class="text-muted mb-0">{room['description']}</p>
                            </div>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Settlements -->
                    <div class="card border-0 shadow-sm">
                        <div class="card-header bg-white border-0">
                            <h5 class="fw-bold mb-0"><i class="bi bi-arrow-left-right me-2"></i>Recommended Settlements</h5>
                        </div>
                        <div class="card-body">
                            {% if room['settlements'] %}
                            <div class="list-group list-group-flush">
                                {% for settle in room['settlements'] %}
                                <div class="list-group-item border-0 px-0">
                                    <div class="d-flex align-items-center">
                                        <div class="flex-shrink-0">
                                            <i class="bi bi-arrow-right-circle fs-4 text-primary"></i>
                                        </div>
                                        <div class="flex-grow-1 ms-3">
                                            <h6 class="fw-medium mb-1">{{ settle['from'] }} → {{ settle['to'] }}</h6>
                                            <p class="text-muted small mb-0">For exact balance settlement</p>
                                        </div>
                                        <div>
                                            <span class="badge amount-badge settle-btn">${settle['amount']:.2f}</span>
                                        </div>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                            {% else %}
                            <div class="text-center py-4">
                                <i class="bi bi-check-circle fs-1 text-success mb-3"></i>
                                <p class="text-muted">All settled up! No payments needed.</p>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                </div>

                <!-- Right Column: Share & Visuals -->
                <div class="col-lg-4">
                    <!-- Share Card -->
                    <div class="card border-0 shadow-sm mb-4">
                        <div class="card-body text-center">
                            <h5 class="fw-bold mb-3"><i class="bi bi-share me-2"></i>Share This Split</h5>
                            
                            <!-- QR Code -->
                            <div class="mb-3">
                                <div class="qr-code mb-2">
                                    <canvas id="qrCanvas"></canvas>
                                </div>
                                <p class="small text-muted">Scan to join this expense room</p>
                            </div>

                            <!-- Share Link -->
                            <div class="mb-3">
                                <label class="form-label fw-medium">Shareable Link</label>
                                <div class="copy-link mb-2" onclick="copyToClipboard('{receipt['qr_data']}')">
                                    {receipt['qr_data']}
                                </div>
                                <button class="btn btn-outline-primary btn-sm w-100" 
                                        onclick="copyToClipboard('{receipt['qr_data']}')">
                                    <i class="bi bi-clipboard me-1"></i>Copy Link
                                </button>
                            </div>

                            <!-- Social Share -->
                            <div class="d-grid gap-2">
                                <button class="btn btn-outline-success" onclick="shareExpense()">
                                    <i class="bi bi-whatsapp me-1"></i>Share on WhatsApp
                                </button>
                                <button class="btn btn-outline-dark">
                                    <i class="bi bi-envelope me-1"></i>Email Summary
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Chart -->
                    <div class="card border-0 shadow-sm mb-4">
                        <div class="card-body">
                            <h5 class="fw-bold mb-3"><i class="bi bi-pie-chart me-2"></i>Split Visualization</h5>
                            <div id="splitChart"></div>
                        </div>
                    </div>

                    <!-- Quick Actions -->
                    <div class="card border-0 shadow-sm">
                        <div class="card-body">
                            <h5 class="fw-bold mb-3"><i class="bi bi-lightning me-2"></i>Quick Actions</h5>
                            <div class="d-grid gap-2">
                                <a href="/create?clone={room_id}" class="btn btn-outline-primary">
                                    <i class="bi bi-copy me-1"></i>Duplicate Split
                                </a>
                                <button class="btn btn-outline-warning">
                                    <i class="bi bi-printer me-1"></i>Print Receipt
                                </button>
                                <button class="btn btn-outline-danger">
                                    <i class="bi bi-trash me-1"></i>Delete Room
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Generate QR code
        generateQR('qrCanvas', '{receipt['qr_data']}');
        
        // Render chart
        var chartData = {chart_json};
        Plotly.newPlot('splitChart', chartData.data, chartData.layout);
        
        // Share function
        function shareExpense() {{
            if (navigator.share) {{
                navigator.share({{
                    title: 'Split: {room['title']}',
                    text: 'Check out this expense split on SplitSmart',
                    url: window.location.href
                }});
            }}
        }}
    </script>
    '''
    
    return render_template_string(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', html),
        room=room,
        chart_json=chart_json,
        receipt=receipt
    )

@app.route('/history')
def history():
    """View expense history"""
    html = '''
    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2 class="fw-bold"><i class="bi bi-clock-history me-2"></i>Expense History</h2>
                <div>
                    <button class="btn btn-outline-primary" onclick="exportHistory()">
                        <i class="bi bi-download me-1"></i>Export
                    </button>
                </div>
            </div>

            {% if rooms %}
            <!-- Filter Controls -->
            <div class="card border-0 shadow-sm mb-4">
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-md-3">
                            <label class="form-label">Date Range</label>
                            <select class="form-select" onchange="filterHistory()">
                                <option>All Time</option>
                                <option>Last 7 Days</option>
                                <option>Last 30 Days</option>
                                <option>This Month</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Category</label>
                            <select class="form-select" onchange="filterHistory()">
                                <option>All Categories</option>
                                <option>Food & Dining</option>
                                <option>Travel</option>
                                <option>Shopping</option>
                                <option>Entertainment</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Sort By</label>
                            <select class="form-select" onchange="filterHistory()">
                                <option>Newest First</option>
                                <option>Amount (High to Low)</option>
                                <option>Amount (Low to High)</option>
                                <option>Participants</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Search</label>
                            <input type="text" class="form-control" placeholder="Search expenses..." oninput="filterHistory()">
                        </div>
                    </div>
                </div>
            </div>

            <!-- Expenses Grid -->
            <div class="row" id="expensesGrid">
                {% for room in rooms %}
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card card-hover h-100">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-3">
                                <div>
                                    <span class="badge rounded-pill" style="background: {{ room.color }}; color: white;">
                                        {{ room.category|upper }}
                                    </span>
                                    <h5 class="fw-bold mt-2 mb-1">{{ room.title }}</h5>
                                    <p class="text-muted small mb-0">
                                        <i class="bi bi-calendar me-1"></i>{{ room.created_at }}
                                    </p>
                                </div>
                                <div class="text-end">
                                    <div class="h4 fw-bold text-primary">${{ room.total }}</div>
                                    <small class="text-muted">{{ room.participants|length }} people</small>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <small class="text-muted d-block mb-1">
                                    <i class="bi bi-person-check me-1"></i>Paid by {{ room.paid_by }}
                                </small>
                                <small class="text-muted">
                                    <i class="bi bi-diagram-3 me-1"></i>{{ room.method|title }} split
                                </small>
                            </div>
                            
                            <div class="d-flex justify-content-between align-items-center">
                                <a href="/room/{{ room.id }}" class="btn btn-outline-primary btn-sm">
                                    <i class="bi bi-eye me-1"></i>View
                                </a>
                                <div class="text-muted small">
                                    Room ID: {{ room.id }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <!-- Empty State -->
            <div class="text-center py-5">
                <div class="mb-4">
                    <i class="bi bi-receipt-cutoff fs-1 text-muted"></i>
                </div>
                <h4 class="fw-bold mb-3">No Expense History</h4>
                <p class="text-muted mb-4">You haven't created any expense splits yet.</p>
                <a href="/create" class="btn btn-gradient">
                    <i class="bi bi-plus-circle me-2"></i>Create Your First Split
                </a>
            </div>
            {% endif %}
        </div>
    </div>

    <script>
        function filterHistory() {
            // Implement client-side filtering
            const search = document.querySelector('input[type="text"]').value.toLowerCase();
            const cards = document.querySelectorAll('#expensesGrid .col-md-6');
            
            cards.forEach(card => {
                const title = card.querySelector('h5').textContent.toLowerCase();
                const category = card.querySelector('.badge').textContent.toLowerCase();
                const shouldShow = title.includes(search) || category.includes(search);
                card.style.display = shouldShow ? 'block' : 'none';
            });
        }

        function exportHistory() {
            // Implement JSON/CSV export
            alert('Export feature coming soon!');
        }
    </script>
    '''
    
    # Get all rooms (in real app, would filter by user)
    rooms = list(expense_rooms.values())
    
    return render_template_string(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', html),
        rooms=rooms
    )

@app.route('/join', methods=['GET', 'POST'])
def join_room():
    """Join an existing room"""
    if request.method == 'POST':
        room_id = request.form.get('room_id', '').strip()
        if room_id in expense_rooms:
            return redirect(f'/room/{room_id}')
        else:
            return "Room not found", 404
    
    html = '''
    <div class="row justify-content-center">
        <div class="col-lg-6">
            <div class="card border-0 shadow-sm">
                <div class="card-body text-center p-5">
                    <div class="mb-4">
                        <i class="bi bi-arrow-right-circle fs-1 text-primary"></i>
                    </div>
                    <h2 class="fw-bold mb-3">Join Expense Room</h2>
                    <p class="text-muted mb-4">Enter the room ID or scan a QR code to join an existing expense split.</p>
                    
                    <form method="POST" class="mb-4">
                        <div class="input-group input-group-lg mb-3">
                            <span class="input-group-text">
                                <i class="bi bi-hash"></i>
                            </span>
                            <input type="text" class="form-control" name="room_id" 
                                   placeholder="Enter room ID (e.g., a1b2c3d4)" required>
                            <button class="btn btn-gradient" type="submit">
                                <i class="bi bi-arrow-right"></i>
                            </button>
                        </div>
                        <div class="form-text">The room ID is in the shareable link</div>
                    </form>
                    
                    <div class="mt-4">
                        <p class="text-muted mb-2">Don't have a room ID?</p>
                        <a href="/create" class="btn btn-outline-primary">
                            <i class="bi bi-plus-circle me-2"></i>Create New Split Instead
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    return render_template_string(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', html)
    )

@app.route('/api/split', methods=['POST'])
def api_split():
    """API endpoint for programmatic splits"""
    try:
        data = request.json
        total = float(data.get('total', 0))
        people = data.get('people', [])
        method = data.get('method', 'equal')
        
        splits = ExpenseCalculator.calculate_splits(total, people, method)
        
        return jsonify({
            'success': True,
            'total': total,
            'splits': splits,
            'per_person': total / len(people) if people else 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/ai-suggestions', methods=['POST'])
def api_ai_suggestions():
    """Get AI suggestions for expenses"""
    try:
        data = request.json
        expenses = data.get('expenses', [])
        
        suggestions = AISuggestions.generate_suggestions(expenses)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ========== MAIN EXECUTION ==========
if __name__ == '__main__':
    # Print startup information
    print("\n" + "="*60)
    print("💸 SPLITSMART - Smart Expense Splitter")
    print("="*60)
    print(f"📱 Local:   http://127.0.0.1:5000")
    print(f"🌐 Network: http://{os.environ.get('HOST', '0.0.0.0')}:{os.environ.get('PORT', 5000)}")
    print("\n✨ Features:")
    print("  • No database - all data in memory")
    print("  • QR code sharing")
    print("  • AI-powered expense categorization")
    print("  • Optimal settlement calculations")
    print("  • Beautiful visualizations")
    print("  • Mobile responsive design")
    print("="*60 + "\n")
    
    # Add some sample data for demo
    sample_room_id = 'demo123'
    expense_rooms[sample_room_id] = {
        'id': sample_room_id,
        'title': 'Weekend Trip to Mountains',
        'total': 1248.50,
        'paid_by': 'Alex',
        'method': 'equal',
        'participants': ['Alex', 'Taylor', 'Jordan', 'Casey'],
        'splits': {'Alex': 312.13, 'Taylor': 312.13, 'Jordan': 312.13, 'Casey': 312.13},
        'category': 'travel',
        'description': 'Airbnb, food, and activities for the weekend',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'color': '#3b82f6'
    }
    
    # Run the app
    app.run(
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 5000)),
        debug=True
    )
