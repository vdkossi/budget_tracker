"""
app.py - Budget Tracker Main Application
=========================================

This is the main entry point for our Streamlit app!

STREAMLIT CONCEPT: How It Works
-------------------------------
Streamlit runs your Python script from top to bottom every time:
- User clicks a button? Script reruns.
- User types in a field? Script reruns.

This means we need to be smart about when to load data and save state.
We use st.session_state to remember things between reruns.

TO RUN THIS APP:
    cd /Users/dodzi/python/budget_tracker
    streamlit run app.py

The app will open in your browser at http://localhost:8501
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# Import our database functions
import database as db

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
# This MUST be the first Streamlit command!
st.set_page_config(
    page_title="Family Budget Tracker",
    page_icon="💰",
    layout="wide",  # Use full width of the browser
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM STYLING
# =============================================================================
# STREAMLIT CONCEPT: Custom CSS
# You can inject custom CSS to style your app beyond the defaults

st.markdown("""
<style>
    /* Main color scheme - warm, inviting tones */
    :root {
        --primary-color: #2E7D32;
        --secondary-color: #1565C0;
        --accent-color: #F57C00;
    }
    
    /* Style metric cards */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Style the sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f1f5f9;
    }
    
    /* Style success/info messages */
    .stSuccess, .stInfo {
        border-radius: 10px;
    }
    
    /* Better form styling */
    .stForm {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# DATABASE INITIALIZATION & AUTO-BACKUP
# =============================================================================
# PYTHON CONCEPT: Caching with Decorators
# The @st.cache_resource decorator runs this only ONCE, not on every rerun.
# Perfect for database setup and auto-backup!

@st.cache_resource
def initialize_app():
    """Initialize the database and create auto-backup when app starts."""
    db.init_database()
    
    # Auto-backup: Create a backup each time the app starts
    # This runs only once per session (thanks to @st.cache_resource)
    backup_path = db.create_backup()
    if backup_path:
        print(f"✓ Auto-backup created: {backup_path}")
    
    return True

# Run initialization
initialize_app()


# =============================================================================
# SESSION STATE SETUP
# =============================================================================
# STREAMLIT CONCEPT: Session State
# st.session_state is a dictionary that persists across reruns.
# Use it to store user selections, form data, etc.

if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================

with st.sidebar:
    st.title("💰 Family Budget")
    st.markdown("---")
    
    # Navigation buttons
    # STREAMLIT CONCEPT: Buttons return True when clicked
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.current_page = "Dashboard"
    
    if st.button("💸 Add Expense", use_container_width=True):
        st.session_state.current_page = "Add Expense"
    
    if st.button("💵 Add Income", use_container_width=True):
        st.session_state.current_page = "Add Income"
    
    if st.button("🏦 Savings Goals", use_container_width=True):
        st.session_state.current_page = "Savings"
    
    if st.button("💳 Debt Tracker", use_container_width=True):
        st.session_state.current_page = "Debt"
    
    if st.button("📈 Reports", use_container_width=True):
        st.session_state.current_page = "Reports"
    
    if st.button("⚙️ Settings", use_container_width=True):
        st.session_state.current_page = "Settings"
    
    st.markdown("---")
    
    # Quick user selector (always visible)
    users = db.get_all_users()
    if users:
        user_names = [u["name"] for u in users]
        st.selectbox(
            "Current User",
            user_names,
            key="current_user",
            help="Select who is entering data"
        )
    else:
        st.warning("No users yet! Go to Settings to add users.")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_current_user_id():
    """Get the ID of the currently selected user."""
    if "current_user" in st.session_state:
        users = db.get_all_users()
        for user in users:
            if user["name"] == st.session_state.current_user:
                return user["id"]
    return None


def format_currency(amount):
    """Format a number as currency."""
    return f"${amount:,.2f}"


# =============================================================================
# PAGE: DASHBOARD
# =============================================================================

def show_dashboard():
    """Display the main dashboard with overview stats."""
    st.title("📊 Dashboard")
    st.markdown("### Your Financial Overview")
    
    # Check if we have users first
    users = db.get_all_users()
    if not users:
        st.info("👋 Welcome! Let's get started by adding users. Go to **Settings** in the sidebar.")
        return
    
    # Date selection for the month to view
    col1, col2 = st.columns([2, 1])
    with col1:
        # PYTHON CONCEPT: datetime
        # We use datetime to work with dates and times
        today = date.today()
        selected_month = st.date_input(
            "Select Month",
            value=today.replace(day=1),
            key="dashboard_month"
        )
    
    year = selected_month.year
    month = selected_month.month
    
    # Get monthly summary
    summary = db.get_monthly_summary(year, month)
    
    # Calculate totals
    total_expenses = 0
    total_income = 0
    expenses_by_user = {}
    income_by_user = {}
    
    for row in summary["by_user"]:
        user_name = row["user_name"]
        amount = row["total"] or 0
        
        if row["transaction_type"] == "expense":
            total_expenses += amount
            expenses_by_user[user_name] = amount
        elif row["transaction_type"] == "income":
            total_income += amount
            income_by_user[user_name] = amount
    
    net = total_income - total_expenses
    
    # Display main metrics
    st.markdown("---")
    
    # STREAMLIT CONCEPT: Columns
    # st.columns() creates side-by-side containers
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric(
            label="💰 Total Income",
            value=format_currency(total_income),
        )
    
    with metric_col2:
        st.metric(
            label="💸 Total Expenses",
            value=format_currency(total_expenses),
        )
    
    with metric_col3:
        st.metric(
            label="📈 Net",
            value=format_currency(net),
            delta=f"{'Surplus' if net >= 0 else 'Deficit'}"
        )
    
    with metric_col4:
        savings_rate = (net / total_income * 100) if total_income > 0 else 0
        st.metric(
            label="🎯 Savings Rate",
            value=f"{savings_rate:.1f}%",
        )
    
    st.markdown("---")
    
    # Spending by person
    st.markdown("### 👥 Spending by Person")
    
    if expenses_by_user:
        person_cols = st.columns(len(expenses_by_user))
        for idx, (name, amount) in enumerate(expenses_by_user.items()):
            with person_cols[idx]:
                st.metric(
                    label=f"🧑 {name}",
                    value=format_currency(amount),
                    delta=f"{(amount/total_expenses*100):.1f}% of total" if total_expenses > 0 else "0%"
                )
    else:
        st.info("No expenses recorded for this month yet.")
    
    st.markdown("---")
    
    # Charts section
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("### 📊 Expenses by Category")
        category_data = []
        for row in summary["by_category"]:
            if row["transaction_type"] == "expense":
                category_data.append({
                    "Category": row["category_name"],
                    "Amount": row["total"]
                })
        
        if category_data:
            df = pd.DataFrame(category_data)
            fig = px.pie(
                df, 
                values="Amount", 
                names="Category",
                hole=0.4,  # Makes it a donut chart
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data to display.")
    
    with chart_col2:
        st.markdown("### 👤 Spending by Person")
        if expenses_by_user:
            df = pd.DataFrame([
                {"Person": name, "Amount": amount} 
                for name, amount in expenses_by_user.items()
            ])
            fig = px.bar(
                df,
                x="Person",
                y="Amount",
                color="Person",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data to display.")
    
    # Recent transactions
    st.markdown("---")
    st.markdown("### 📝 Recent Transactions")
    
    transactions = db.get_transactions()[:10]  # Last 10
    
    if transactions:
        # PYTHON CONCEPT: List Comprehension
        # A compact way to create lists from other lists
        trans_data = [{
            "Date": t["transaction_date"],
            "Person": t["user_name"],
            "Category": t["category_name"],
            "Type": t["transaction_type"].title(),
            "Amount": format_currency(t["amount"]),
            "Description": t["description"] or "-"
        } for t in transactions]
        
        # PANDAS CONCEPT: DataFrame
        # DataFrames are like spreadsheets in Python
        df = pd.DataFrame(trans_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions yet. Start by adding an expense or income!")


# =============================================================================
# PAGE: ADD EXPENSE
# =============================================================================

def show_add_expense():
    """Form to add a new expense."""
    st.title("💸 Add Expense")
    st.markdown("Record a new expense")
    
    # Check for users
    users = db.get_all_users()
    if not users:
        st.warning("⚠️ Please add users first in Settings!")
        return
    
    # STREAMLIT CONCEPT: Forms
    # Forms group inputs together and only submit when button is clicked
    # This prevents the page from rerunning on every keystroke!
    
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # User selection
            user_names = [u["name"] for u in users]
            selected_user = st.selectbox(
                "Who made this expense?",
                user_names,
                index=0
            )
            
            # Category selection
            categories = db.get_categories_by_type("expense")
            category_names = [c["name"] for c in categories]
            selected_category = st.selectbox(
                "Category",
                category_names
            )
            
            # Amount
            amount = st.number_input(
                "Amount ($)",
                min_value=0.01,
                value=0.01,
                step=0.01,
                format="%.2f"
            )
        
        with col2:
            # Date
            expense_date = st.date_input(
                "Date",
                value=date.today()
            )
            
            # Description
            description = st.text_input(
                "Description (optional)",
                placeholder="e.g., Weekly groceries at Trader Joe's"
            )
        
        # Submit button
        submitted = st.form_submit_button("💾 Save Expense", use_container_width=True)
        
        if submitted:
            # Get IDs from names
            user_id = next(u["id"] for u in users if u["name"] == selected_user)
            category_id = next(c["id"] for c in categories if c["name"] == selected_category)
            
            # Save to database
            db.add_transaction(
                user_id=user_id,
                category_id=category_id,
                amount=amount,
                description=description,
                transaction_type="expense",
                transaction_date=expense_date.isoformat()
            )
            
            st.success(f"✅ Expense of {format_currency(amount)} saved for {selected_user}!")
            st.balloons()  # Fun celebration animation!
    
    # Show recent expenses below the form
    st.markdown("---")
    st.markdown("### Recent Expenses")
    
    recent = db.get_transactions(transaction_type="expense")[:5]
    if recent:
        for t in recent:
            st.markdown(
                f"**{t['transaction_date']}** - {t['user_name']} spent "
                f"**{format_currency(t['amount'])}** on {t['category_name']}"
                f"{' - ' + t['description'] if t['description'] else ''}"
            )
    else:
        st.info("No expenses recorded yet.")


# =============================================================================
# PAGE: ADD INCOME
# =============================================================================

def show_add_income():
    """Form to add new income."""
    st.title("💵 Add Income")
    st.markdown("Record income (salary, side hustle, gifts, etc.)")
    
    users = db.get_all_users()
    if not users:
        st.warning("⚠️ Please add users first in Settings!")
        return
    
    with st.form("income_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            user_names = [u["name"] for u in users]
            selected_user = st.selectbox("Who received this income?", user_names)
            
            categories = db.get_categories_by_type("income")
            category_names = [c["name"] for c in categories]
            selected_category = st.selectbox("Category", category_names)
            
            amount = st.number_input(
                "Amount ($)",
                min_value=0.01,
                value=0.01,
                step=0.01,
                format="%.2f"
            )
        
        with col2:
            income_date = st.date_input("Date", value=date.today())
            description = st.text_input(
                "Description (optional)",
                placeholder="e.g., January paycheck"
            )
        
        submitted = st.form_submit_button("💾 Save Income", use_container_width=True)
        
        if submitted:
            user_id = next(u["id"] for u in users if u["name"] == selected_user)
            category_id = next(c["id"] for c in categories if c["name"] == selected_category)
            
            db.add_transaction(
                user_id=user_id,
                category_id=category_id,
                amount=amount,
                description=description,
                transaction_type="income",
                transaction_date=income_date.isoformat()
            )
            
            st.success(f"✅ Income of {format_currency(amount)} recorded for {selected_user}!")
            st.balloons()


# =============================================================================
# PAGE: SAVINGS GOALS
# =============================================================================

def show_savings():
    """Manage savings goals."""
    st.title("🏦 Savings Goals")
    
    tab1, tab2 = st.tabs(["📊 View Goals", "➕ Add New Goal"])
    
    with tab1:
        goals = db.get_all_savings_goals()
        
        if goals:
            for goal in goals:
                progress = (goal["current_amount"] / goal["target_amount"]) * 100 if goal["target_amount"] > 0 else 0
                
                st.markdown(f"### 🎯 {goal['name']}")
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.progress(min(progress / 100, 1.0))
                with col2:
                    st.metric("Progress", f"{progress:.1f}%")
                with col3:
                    remaining = goal["target_amount"] - goal["current_amount"]
                    st.metric("Remaining", format_currency(remaining))
                
                st.markdown(
                    f"**{format_currency(goal['current_amount'])}** of "
                    f"**{format_currency(goal['target_amount'])}**"
                )
                
                if goal["target_date"]:
                    st.caption(f"Target date: {goal['target_date']}")
                
                # Actions: Add contribution or Delete
                action_col1, action_col2 = st.columns(2)
                
                with action_col1:
                    with st.expander("💵 Add contribution"):
                        with st.form(f"contrib_{goal['id']}"):
                            contrib = st.number_input(
                                "Amount", 
                                min_value=0.01, 
                                key=f"contrib_amt_{goal['id']}"
                            )
                            if st.form_submit_button("Add"):
                                new_amount = goal["current_amount"] + contrib
                                db.update_savings_goal_amount(goal["id"], new_amount)
                                st.success("Contribution added!")
                                st.experimental_rerun()
                
                with action_col2:
                    with st.expander("🗑️ Delete this goal"):
                        st.warning(f"Are you sure you want to delete '{goal['name']}'?")
                        if st.button(f"Yes, delete", key=f"del_goal_{goal['id']}"):
                            db.delete_savings_goal(goal["id"])
                            st.success("Goal deleted!")
                            st.experimental_rerun()
                
                st.markdown("---")
        else:
            st.info("No savings goals yet. Create one in the 'Add New Goal' tab!")
    
    with tab2:
        with st.form("savings_goal_form", clear_on_submit=True):
            name = st.text_input("Goal Name", placeholder="e.g., Emergency Fund, Vacation")
            target = st.number_input("Target Amount ($)", min_value=1.0, value=1000.0)
            target_date = st.date_input("Target Date (optional)", value=None)
            
            if st.form_submit_button("Create Goal"):
                db.add_savings_goal(
                    name=name,
                    target_amount=target,
                    target_date=target_date.isoformat() if target_date else None
                )
                st.success(f"✅ Goal '{name}' created!")
                st.experimental_rerun()


# =============================================================================
# PAGE: DEBT TRACKER
# =============================================================================

def show_debt():
    """Manage and track debts."""
    st.title("💳 Debt Tracker")
    
    tab1, tab2 = st.tabs(["📊 View Debts", "➕ Add New Debt"])
    
    with tab1:
        debts = db.get_all_debts()
        
        if debts:
            # Summary metrics
            total_debt = sum(d["current_balance"] for d in debts)
            total_original = sum(d["original_amount"] for d in debts)
            paid_off = total_original - total_debt
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Debt", format_currency(total_debt))
            with col2:
                st.metric("Paid Off", format_currency(paid_off))
            with col3:
                pct = (paid_off / total_original * 100) if total_original > 0 else 0
                st.metric("Progress", f"{pct:.1f}%")
            
            st.markdown("---")
            
            # Individual debts
            for debt in debts:
                paid_pct = ((debt["original_amount"] - debt["current_balance"]) / debt["original_amount"] * 100) if debt["original_amount"] > 0 else 0
                
                st.markdown(f"### 💳 {debt['name']}")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.progress(min(paid_pct / 100, 1.0))
                    st.markdown(
                        f"**{format_currency(debt['current_balance'])}** remaining "
                        f"of **{format_currency(debt['original_amount'])}**"
                    )
                with col2:
                    if debt["interest_rate"]:
                        st.caption(f"APR: {debt['interest_rate']}%")
                    if debt["minimum_payment"]:
                        st.caption(f"Min Payment: {format_currency(debt['minimum_payment'])}")
                
                # Actions: Make payment or Delete
                action_col1, action_col2 = st.columns(2)
                
                with action_col1:
                    with st.expander("💵 Make a payment"):
                        with st.form(f"payment_{debt['id']}"):
                            payment = st.number_input(
                                "Payment Amount",
                                min_value=0.01,
                                key=f"payment_amt_{debt['id']}"
                            )
                            if st.form_submit_button("Record Payment"):
                                new_balance = max(0, debt["current_balance"] - payment)
                                db.update_debt_balance(debt["id"], new_balance)
                                st.success("Payment recorded!")
                                st.experimental_rerun()
                
                with action_col2:
                    with st.expander("🗑️ Delete this debt"):
                        st.warning(f"Are you sure you want to delete '{debt['name']}'?")
                        if st.button(f"Yes, delete", key=f"del_debt_{debt['id']}"):
                            db.delete_debt(debt["id"])
                            st.success("Debt deleted!")
                            st.experimental_rerun()
                
                st.markdown("---")
        else:
            st.info("No debts tracked. Add one in the 'Add New Debt' tab!")
    
    with tab2:
        with st.form("debt_form", clear_on_submit=True):
            name = st.text_input("Debt Name", placeholder="e.g., Chase Credit Card, Car Loan")
            
            col1, col2 = st.columns(2)
            with col1:
                original = st.number_input("Original Amount ($)", min_value=0.01, value=1000.0)
                current = st.number_input("Current Balance ($)", min_value=0.0, value=1000.0)
            with col2:
                rate = st.number_input("Interest Rate (%)", min_value=0.0, value=0.0)
                min_payment = st.number_input("Minimum Payment ($)", min_value=0.0, value=0.0)
            
            due_day = st.number_input(
                "Due Date (day of month)", 
                min_value=1, 
                max_value=31, 
                value=1
            )
            
            if st.form_submit_button("Add Debt"):
                db.add_debt(
                    name=name,
                    original_amount=original,
                    current_balance=current,
                    interest_rate=rate,
                    minimum_payment=min_payment,
                    due_date=due_day
                )
                st.success(f"✅ Debt '{name}' added!")
                st.experimental_rerun()


# =============================================================================
# PAGE: REPORTS
# =============================================================================

def show_reports():
    """Detailed financial reports."""
    st.title("📈 Reports")
    
    users = db.get_all_users()
    if not users:
        st.warning("Add users first to see reports!")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # User filter
        user_options = ["All (Household)"] + [u["name"] for u in users]
        selected_user = st.selectbox("Filter by Person", user_options)
    
    with col2:
        # Date range
        today = date.today()
        start_date = st.date_input(
            "Start Date",
            value=today.replace(day=1)
        )
    
    with col3:
        end_date = st.date_input(
            "End Date",
            value=today
        )
    
    # Get filtered transactions
    user_id = None
    if selected_user != "All (Household)":
        user_id = next(u["id"] for u in users if u["name"] == selected_user)
    
    transactions = db.get_transactions(
        user_id=user_id,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )
    
    if not transactions:
        st.info("No transactions found for the selected filters.")
        return
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame([dict(t) for t in transactions])
    
    # Summary stats
    expenses = df[df["transaction_type"] == "expense"]["amount"].sum()
    income = df[df["transaction_type"] == "income"]["amount"].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Expenses", format_currency(expenses))
    with col2:
        st.metric("Total Income", format_currency(income))
    with col3:
        st.metric("Net", format_currency(income - expenses))
    
    st.markdown("---")
    
    # Charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("### Expenses by Category")
        expense_df = df[df["transaction_type"] == "expense"]
        if not expense_df.empty:
            cat_totals = expense_df.groupby("category_name")["amount"].sum().reset_index()
            fig = px.pie(
                cat_totals,
                values="amount",
                names="category_name",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        if selected_user == "All (Household)":
            st.markdown("### Expenses by Person")
            if not expense_df.empty:
                user_totals = expense_df.groupby("user_name")["amount"].sum().reset_index()
                fig = px.bar(
                    user_totals,
                    x="user_name",
                    y="amount",
                    color="user_name",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
    
    # Transaction table with edit/delete
    st.markdown("---")
    st.markdown("### All Transactions")
    st.caption("Click on a transaction to edit or delete it")
    
    # Show transactions as expandable items for edit/delete
    for t in transactions:
        with st.expander(
            f"**{t['transaction_date']}** | {t['user_name']} | "
            f"{t['category_name']} | {format_currency(t['amount'])} | "
            f"{t['transaction_type'].title()}"
        ):
            st.markdown(f"**Description:** {t['description'] or 'No description'}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### ✏️ Edit Transaction")
                with st.form(f"edit_trans_{t['id']}"):
                    # Get fresh user/category lists
                    all_users = db.get_all_users()
                    all_categories = db.get_categories_by_type(t['transaction_type'])
                    
                    user_names = [u["name"] for u in all_users]
                    category_names = [c["name"] for c in all_categories]
                    
                    # Find current indices
                    current_user_idx = user_names.index(t['user_name']) if t['user_name'] in user_names else 0
                    current_cat_idx = category_names.index(t['category_name']) if t['category_name'] in category_names else 0
                    
                    new_user = st.selectbox("Person", user_names, index=current_user_idx, key=f"edit_user_{t['id']}")
                    new_category = st.selectbox("Category", category_names, index=current_cat_idx, key=f"edit_cat_{t['id']}")
                    new_amount = st.number_input("Amount", value=float(t['amount']), min_value=0.01, key=f"edit_amt_{t['id']}")
                    new_desc = st.text_input("Description", value=t['description'] or "", key=f"edit_desc_{t['id']}")
                    new_date = st.date_input("Date", value=date.fromisoformat(t['transaction_date']), key=f"edit_date_{t['id']}")
                    
                    if st.form_submit_button("Save Changes"):
                        new_user_id = next(u["id"] for u in all_users if u["name"] == new_user)
                        new_cat_id = next(c["id"] for c in all_categories if c["name"] == new_category)
                        
                        db.update_transaction(
                            transaction_id=t['id'],
                            user_id=new_user_id,
                            category_id=new_cat_id,
                            amount=new_amount,
                            description=new_desc,
                            transaction_date=new_date.isoformat()
                        )
                        st.success("Transaction updated!")
                        st.experimental_rerun()
            
            with col2:
                st.markdown("#### 🗑️ Delete Transaction")
                st.warning("This cannot be undone!")
                if st.button(f"Delete this transaction", key=f"del_trans_{t['id']}"):
                    db.delete_transaction(t['id'])
                    st.success("Transaction deleted!")
                    st.experimental_rerun()


# =============================================================================
# PAGE: SETTINGS
# =============================================================================

def show_settings():
    """App settings and user management."""
    st.title("⚙️ Settings")
    
    # User management
    st.markdown("### 👥 Manage Users")
    
    users = db.get_all_users()
    
    if users:
        for user in users:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"🧑 **{user['name']}**")
            with col2:
                with st.expander("🗑️"):
                    st.caption("User must have no transactions to delete.")
                    if st.button("Delete", key=f"del_user_{user['id']}"):
                        try:
                            db.delete_user(user["id"])
                            st.success("User deleted!")
                            st.experimental_rerun()
                        except ValueError as e:
                            st.error(str(e))
    else:
        st.info("No users added yet.")
    
    # Add new user
    st.markdown("---")
    st.markdown("### ➕ Add New User")
    
    with st.form("add_user_form", clear_on_submit=True):
        new_user_name = st.text_input(
            "Name",
            placeholder="Enter name (e.g., John, Jane)"
        )
        
        if st.form_submit_button("Add User"):
            if new_user_name.strip():
                try:
                    db.add_user(new_user_name.strip())
                    st.success(f"✅ User '{new_user_name}' added!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Could not add user: {e}")
            else:
                st.warning("Please enter a name.")
    
    # Backup section
    st.markdown("---")
    st.markdown("### 💾 Data Backup")
    
    # Database info
    db_info = db.get_database_info()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Database Size", f"{db_info['size_kb']:.1f} KB")
    with col2:
        st.metric("Transactions", db_info['transaction_count'])
    with col3:
        st.metric("Users", db_info['user_count'])
    
    if db_info['last_modified']:
        st.caption(f"Last modified: {db_info['last_modified'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Manual backup button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Create Backup Now", use_container_width=True):
            backup_path = db.create_backup()
            if backup_path:
                st.success(f"✅ Backup created!")
                st.experimental_rerun()
            else:
                st.warning("No database to backup yet.")
    
    with col2:
        # Download database file
        if db_info['exists']:
            with open(db_info['path'], 'rb') as f:
                st.download_button(
                    "⬇️ Download Database",
                    data=f,
                    file_name=f"budget_tracker_{datetime.now().strftime('%Y%m%d')}.db",
                    mime="application/octet-stream",
                    use_container_width=True
                )
    
    # Show existing backups
    backups = db.get_all_backups()
    
    if backups:
        with st.expander(f"📁 View Backups ({len(backups)} files)"):
            st.caption("Auto-backups are created each time you open the app. Last 30 are kept.")
            
            for backup in backups:
                bcol1, bcol2, bcol3 = st.columns([3, 1, 1])
                with bcol1:
                    st.text(backup['date'].strftime('%Y-%m-%d %H:%M:%S'))
                with bcol2:
                    st.text(f"{backup['size_kb']:.1f} KB")
                with bcol3:
                    if st.button("Restore", key=f"restore_{backup['filename']}"):
                        try:
                            db.restore_from_backup(backup['path'])
                            st.success("Database restored! Refresh the page.")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
    else:
        st.info("No backups yet. They'll be created automatically when you use the app.")
    
    # About section
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    **Family Budget Tracker** v1.0
    
    A simple app to track household finances together.
    
    Built with:
    - 🐍 Python
    - 📊 Streamlit
    - 🗄️ SQLite
    - 📈 Plotly
    
    **Auto-Backup:** Your data is automatically backed up each time you open the app.
    Last 30 backups are kept in the `backups/` folder.
    """)


# =============================================================================
# MAIN APP ROUTING
# =============================================================================
# PYTHON CONCEPT: Dictionary Dispatch
# Instead of a long if/elif chain, we use a dictionary to map pages to functions.
# This is cleaner and more Pythonic!

PAGES = {
    "Dashboard": show_dashboard,
    "Add Expense": show_add_expense,
    "Add Income": show_add_income,
    "Savings": show_savings,
    "Debt": show_debt,
    "Reports": show_reports,
    "Settings": show_settings,
}

# Run the selected page
current_page = st.session_state.current_page
if current_page in PAGES:
    PAGES[current_page]()  # Call the function!
else:
    show_dashboard()  # Default fallback

