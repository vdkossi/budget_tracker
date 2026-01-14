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
import os

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
# HELPER: Rerun function (compatible with all Streamlit versions)
# =============================================================================
def rerun_app():
    """Rerun the app - compatible with both old and new Streamlit versions."""
    # Try new API first (Streamlit >= 1.27.0)
    if hasattr(st, 'rerun'):
        st.rerun()
    # Fall back to experimental API (older Streamlit versions)
    elif hasattr(st, 'experimental_rerun'):
        st.experimental_rerun()
    else:
        # Last resort: raise an error with helpful message
        raise RuntimeError("Streamlit rerun function not available. Please update Streamlit.")


# =============================================================================
# SIMPLE AUTHENTICATION
# =============================================================================
# Simple password-based authentication
# For deployment (Streamlit Cloud): Set in Streamlit secrets (see .streamlit/secrets.toml.example)
# For local: Set APP_PASSWORD environment variable

def get_app_password():
    """Get password from Streamlit secrets (deployment) or environment variable (local)."""
    # Try Streamlit secrets first (for Streamlit Cloud deployment)
    try:
        if hasattr(st, 'secrets'):
            # Try different access methods
            if hasattr(st.secrets, 'get'):
                # Access as dictionary
                pwd = st.secrets.get('password')
                if pwd:
                    return str(pwd).strip()  # Ensure it's a string and strip whitespace
            # Try direct attribute access
            if hasattr(st.secrets, 'password'):
                return str(st.secrets.password).strip()
            # Try dictionary-style access
            if 'password' in st.secrets:
                return str(st.secrets['password']).strip()
    except Exception as e:
        # Silently continue to try other methods
        pass
    
    # Fall back to environment variable (for local development)
    env_password = os.getenv("APP_PASSWORD")
    if env_password:
        return str(env_password).strip()
    
    # No password configured - return None
    return None

APP_PASSWORD = get_app_password()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Show login form if not authenticated
if not st.session_state.authenticated:
    st.title("🔒 Budget Tracker Login")
    st.markdown("---")
    
    # Check if password is configured
    if APP_PASSWORD is None:
        st.error("""
        ⚠️ **Password not configured!**
        
        Please set a password using one of these methods:
        
        **For Streamlit Cloud deployment:**
        1. Go to https://share.streamlit.io/
        2. Click on your app
        3. Click the "⋮" (three dots) menu in the top right
        4. Select "Settings" → "Secrets"
        5. In the secrets editor, add:
           ```toml
           password = "your-secure-password-here"
           ```
        6. Click "Save" and wait for the app to redeploy
        
        **For local development:**
        - Set environment variable: `export APP_PASSWORD="your-password"`
        - Or create `.streamlit/secrets.toml` with: `password = "your-password"`
        """)
        st.stop()
    
    # Debug: Show if password was found (remove this after debugging)
    with st.expander("🔍 Debug Info (remove after testing)"):
        st.write(f"Password configured: {APP_PASSWORD is not None}")
        if APP_PASSWORD:
            st.write(f"Password length: {len(APP_PASSWORD)}")
            st.write(f"First char: {APP_PASSWORD[0] if len(APP_PASSWORD) > 0 else 'N/A'}")
            st.write(f"Last char: {APP_PASSWORD[-1] if len(APP_PASSWORD) > 0 else 'N/A'}")
        # Try to show what secrets are available
        try:
            if hasattr(st, 'secrets'):
                st.write("Available secrets keys:", list(st.secrets.keys()) if hasattr(st.secrets, 'keys') else "N/A")
        except:
            st.write("Could not access secrets")
    
    # Automation markers - hidden divs for test identification
    st.markdown(
        '<div data-testid="login-form" data-automation="login-page" style="display: none;"></div>',
        unsafe_allow_html=True
    )
    
    # Password input with automation-friendly key
    # Streamlit creates element ID from key: input with key "login_password" becomes accessible
    password = st.text_input(
        "Enter password", 
        type="password", 
        key="login_password",  # Automation: use key "login_password" or selector '[data-testid="stTextInput"]'
        help="Enter your password to access the budget tracker"
    )
    
    # Add marker for password field
    st.markdown(
        '<div data-automation="password-field" data-field-key="login_password" style="display: none;"></div>',
        unsafe_allow_html=True
    )
    
    # Login button with automation-friendly key
    login_button = st.button(
        "Login", 
        use_container_width=True,
        key="login_button",  # Automation: use key "login_button" or button text "Login"
        help="Click to login with your password"
    )
    
    # Add marker for login button
    st.markdown(
        '<div data-automation="login-button" data-button-key="login_button" style="display: none;"></div>',
        unsafe_allow_html=True
    )
    
    if login_button:
        if password == APP_PASSWORD:
            st.session_state.authenticated = True
            rerun_app()
        else:
            st.error("❌ Incorrect password. Please try again.")
            # Debug: Show what we're comparing (only in development - remove in production)
            # Uncomment the line below for debugging:
            # st.caption(f"Debug: Expected password length: {len(APP_PASSWORD) if APP_PASSWORD else 0}, Entered length: {len(password)}")
    
    st.markdown("---")
    st.caption("💡 For deployment: Set password in Streamlit secrets. For local: Set APP_PASSWORD environment variable")
    st.stop()  # Stop execution here - don't show the app until authenticated


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
    
    # Logout button
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        rerun_app()
    
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
    
    # Check if we have users first
    users = db.get_all_users()
    if not users:
        st.info("👋 Welcome! Let's get started by adding users. Go to **Settings** in the sidebar.")
        return
    
    # Date selection for the month to view
    col1, col2 = st.columns([2, 1])
    with col1:
        today = date.today()
        selected_month = st.date_input(
            "Select Month",
            value=today.replace(day=1),
            key="dashboard_month"
        )
    
    year = selected_month.year
    month = selected_month.month
    month_name = selected_month.strftime("%B %Y")
    
    st.markdown(f"### 📅 {month_name} Overview")
    
    # Get monthly summary
    summary = db.get_monthly_summary(year, month)
    
    # Calculate totals by user and type
    total_expenses = 0
    total_income = 0
    expenses_by_user = {}
    income_by_user = {}
    
    for row in summary["by_user"]:
        user_name = row["user_name"]
        amount = row["total"] or 0
        
        if row["transaction_type"] == "expense":
            total_expenses += amount
            expenses_by_user[user_name] = expenses_by_user.get(user_name, 0) + amount
        elif row["transaction_type"] == "income":
            total_income += amount
            income_by_user[user_name] = income_by_user.get(user_name, 0) + amount
    
    net = total_income - total_expenses
    savings_rate = (net / total_income * 100) if total_income > 0 else 0
    
    # ==========================================================================
    # SECTION 1: HOUSEHOLD SUMMARY (Top Cards)
    # ==========================================================================
    st.markdown("---")
    
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric(
            label="💵 Total Income",
            value=format_currency(total_income),
            help="All income received this month"
        )
    
    with metric_col2:
        st.metric(
            label="💸 Total Expenses",
            value=format_currency(total_expenses),
            help="All expenses this month (not reduced by income)"
        )
    
    with metric_col3:
        delta_color = "normal" if net >= 0 else "inverse"
        st.metric(
            label="📊 Net (Income - Expenses)",
            value=format_currency(abs(net)),
            delta=f"{'✅ Surplus' if net >= 0 else '⚠️ Deficit'}",
            delta_color=delta_color
        )
    
    with metric_col4:
        st.metric(
            label="🎯 Savings Rate",
            value=f"{savings_rate:.1f}%",
            help="Percentage of income saved"
        )
    
    # ==========================================================================
    # SECTION 2: MONTH-OVER-MONTH COMPARISON
    # ==========================================================================
    st.markdown("---")
    st.markdown("### 📊 Month-over-Month Expense Trend")
    st.caption("Are your expenses going down? Let's find out!")
    
    # Get monthly comparison data
    monthly_data = db.get_monthly_comparison(6)  # Last 6 months
    
    if len(monthly_data) >= 2:
        # Get current and previous month data
        current_month_data = monthly_data[-1] if monthly_data else None
        previous_month_data = monthly_data[-2] if len(monthly_data) >= 2 else None
        
        if current_month_data and previous_month_data:
            current_expenses = current_month_data["expenses"]
            previous_expenses = previous_month_data["expenses"]
            
            # Calculate change
            if previous_expenses > 0:
                expense_change = current_expenses - previous_expenses
                expense_change_pct = (expense_change / previous_expenses) * 100
            else:
                expense_change = current_expenses
                expense_change_pct = 100 if current_expenses > 0 else 0
            
            expenses_down = expense_change < 0
            
            # Display comparison cards
            comp_col1, comp_col2, comp_col3 = st.columns(3)
            
            with comp_col1:
                # Parse month string for display
                prev_month_display = datetime.strptime(previous_month_data["month"], "%Y-%m").strftime("%B %Y")
                st.metric(
                    label=f"📅 {prev_month_display}",
                    value=format_currency(previous_expenses),
                    help="Previous month expenses"
                )
            
            with comp_col2:
                curr_month_display = datetime.strptime(current_month_data["month"], "%Y-%m").strftime("%B %Y")
                st.metric(
                    label=f"📅 {curr_month_display}",
                    value=format_currency(current_expenses),
                    help="Current month expenses"
                )
            
            with comp_col3:
                if expenses_down:
                    st.metric(
                        label="📉 Change",
                        value=format_currency(abs(expense_change)),
                        delta=f"⬇️ {abs(expense_change_pct):.1f}% LESS",
                        delta_color="normal"
                    )
                else:
                    st.metric(
                        label="📈 Change",
                        value=format_currency(abs(expense_change)),
                        delta=f"⬆️ {abs(expense_change_pct):.1f}% MORE",
                        delta_color="inverse"
                    )
            
            # Status message
            if expenses_down:
                st.success(f"🎉 Great job! You spent **{format_currency(abs(expense_change))}** less than last month ({abs(expense_change_pct):.1f}% decrease)")
            elif expense_change == 0:
                st.info("📊 Your expenses are the same as last month")
            else:
                st.warning(f"⚠️ Heads up! You spent **{format_currency(expense_change)}** more than last month ({expense_change_pct:.1f}% increase)")
        
        # Trend chart - last 6 months
        if len(monthly_data) >= 2:
            st.markdown("#### 📈 6-Month Expense Trend")
            
            # Prepare data for chart
            trend_df = pd.DataFrame(monthly_data)
            trend_df["month_display"] = trend_df["month"].apply(
                lambda x: datetime.strptime(x, "%Y-%m").strftime("%b '%y")
            )
            
            # Create line chart for expenses
            fig_trend = go.Figure()
            
            # Expense line
            fig_trend.add_trace(go.Scatter(
                x=trend_df["month_display"],
                y=trend_df["expenses"],
                mode='lines+markers+text',
                name='Expenses',
                line=dict(color='#C62828', width=3),
                marker=dict(size=10),
                text=[f"${x:,.0f}" for x in trend_df["expenses"]],
                textposition="top center"
            ))
            
            # Income line (for reference)
            fig_trend.add_trace(go.Scatter(
                x=trend_df["month_display"],
                y=trend_df["income"],
                mode='lines+markers',
                name='Income',
                line=dict(color='#2E7D32', width=2, dash='dash'),
                marker=dict(size=8)
            ))
            
            # Add trend line for expenses
            if len(trend_df) >= 3:
                # Simple linear regression for trend
                x_vals = list(range(len(trend_df)))
                y_vals = trend_df["expenses"].tolist()
                
                # Calculate trend (simple slope)
                n = len(x_vals)
                sum_x = sum(x_vals)
                sum_y = sum(y_vals)
                sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
                sum_x2 = sum(x ** 2 for x in x_vals)
                
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2) if (n * sum_x2 - sum_x ** 2) != 0 else 0
                intercept = (sum_y - slope * sum_x) / n
                
                trend_y = [slope * x + intercept for x in x_vals]
                
                trend_color = '#4CAF50' if slope < 0 else '#FF5722'  # Green if going down, orange if up
                
                fig_trend.add_trace(go.Scatter(
                    x=trend_df["month_display"],
                    y=trend_y,
                    mode='lines',
                    name='Trend',
                    line=dict(color=trend_color, width=2, dash='dot')
                ))
            
            fig_trend.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                yaxis_title="Amount ($)",
                xaxis_title="",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="x unified"
            )
            
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # Show trend interpretation
            if len(monthly_data) >= 3:
                first_expense = monthly_data[0]["expenses"]
                last_expense = monthly_data[-1]["expenses"]
                overall_change = last_expense - first_expense
                
                if first_expense > 0:
                    overall_pct = (overall_change / first_expense) * 100
                    
                    if overall_change < 0:
                        st.success(f"📉 **Overall trend:** Expenses are **DOWN** {abs(overall_pct):.1f}% over the last {len(monthly_data)} months!")
                    else:
                        st.warning(f"📈 **Overall trend:** Expenses are **UP** {overall_pct:.1f}% over the last {len(monthly_data)} months")
    else:
        st.info("📊 Need at least 2 months of data to show comparison. Keep tracking your expenses!")
    
    # ==========================================================================
    # SECTION 3: INCOME vs EXPENSES CHART
    # ==========================================================================
    st.markdown("---")
    st.markdown("### 📈 Income vs Expenses Comparison")
    
    # Create comparison bar chart
    comparison_data = pd.DataFrame({
        "Category": ["Income", "Expenses"],
        "Amount": [total_income, total_expenses],
        "Color": ["#2E7D32", "#C62828"]  # Green for income, Red for expenses
    })
    
    fig_compare = px.bar(
        comparison_data,
        x="Category",
        y="Amount",
        color="Category",
        color_discrete_map={"Income": "#2E7D32", "Expenses": "#C62828"},
        text="Amount"
    )
    fig_compare.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig_compare.update_layout(
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
        yaxis_title="Amount ($)",
        xaxis_title=""
    )
    st.plotly_chart(fig_compare, use_container_width=True)
    
    # ==========================================================================
    # SECTION 3: BREAKDOWN BY PERSON
    # ==========================================================================
    st.markdown("---")
    st.markdown("### 👥 Breakdown by Person")
    
    # Get all user names
    all_user_names = list(set(list(expenses_by_user.keys()) + list(income_by_user.keys())))
    
    if all_user_names:
        # Create tabs for each view
        tab1, tab2 = st.tabs(["📊 Side by Side", "📋 Details"])
        
        with tab1:
            # Grouped bar chart: Income vs Expenses by person
            person_data = []
            for name in all_user_names:
                person_data.append({"Person": name, "Type": "Income", "Amount": income_by_user.get(name, 0)})
                person_data.append({"Person": name, "Type": "Expenses", "Amount": expenses_by_user.get(name, 0)})
            
            df_person = pd.DataFrame(person_data)
            
            fig_person = px.bar(
                df_person,
                x="Person",
                y="Amount",
                color="Type",
                barmode="group",
                color_discrete_map={"Income": "#2E7D32", "Expenses": "#C62828"},
                text="Amount"
            )
            fig_person.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            fig_person.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                yaxis_title="Amount ($)",
                xaxis_title="",
                legend_title="Type"
            )
            st.plotly_chart(fig_person, use_container_width=True)
        
        with tab2:
            # Detailed metrics per person
            person_cols = st.columns(len(all_user_names))
            for idx, name in enumerate(all_user_names):
                with person_cols[idx]:
                    inc = income_by_user.get(name, 0)
                    exp = expenses_by_user.get(name, 0)
                    person_net = inc - exp
                    
                    st.markdown(f"#### 🧑 {name}")
                    st.metric("Income", format_currency(inc))
                    st.metric("Expenses", format_currency(exp))
                    st.metric(
                        "Net", 
                        format_currency(abs(person_net)),
                        delta=f"{'Surplus' if person_net >= 0 else 'Deficit'}"
                    )
                    if total_expenses > 0:
                        st.caption(f"📊 {(exp/total_expenses*100):.1f}% of household expenses")
    else:
        st.info("No data for this month yet.")
    
    # ==========================================================================
    # SECTION 4: EXPENSE BREAKDOWN BY CATEGORY
    # ==========================================================================
    st.markdown("---")
    st.markdown("### 🏷️ Expense Categories")
    
    category_data = []
    for row in summary["by_category"]:
        if row["transaction_type"] == "expense":
            category_data.append({
                "Category": row["category_name"],
                "Amount": row["total"]
            })
    
    if category_data:
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Donut chart
            df_cat = pd.DataFrame(category_data)
            df_cat = df_cat.sort_values("Amount", ascending=False)
            
            fig_pie = px.pie(
                df_cat,
                values="Amount",
                names="Category",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(
                showlegend=False,
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with chart_col2:
            # Horizontal bar chart (top categories)
            fig_bar = px.bar(
                df_cat.head(10),  # Top 10 categories
                y="Category",
                x="Amount",
                orientation="h",
                color="Amount",
                color_continuous_scale="Reds",
                text="Amount"
            )
            fig_bar.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            fig_bar.update_layout(
                showlegend=False,
                margin=dict(t=20, b=20, l=20, r=20),
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title="Amount ($)",
                yaxis_title="",
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No expense data to display.")
    
    # ==========================================================================
    # SECTION 5: RECENT TRANSACTIONS (Color-coded)
    # ==========================================================================
    st.markdown("---")
    st.markdown("### 📝 Recent Transactions")
    
    transactions = db.get_transactions()[:15]  # Last 15
    
    if transactions:
        # Show with visual distinction between income and expense
        for t in transactions:
            is_income = t["transaction_type"] == "income"
            icon = "💵" if is_income else "💸"
            color = "green" if is_income else "red"
            sign = "+" if is_income else "-"
            
            col1, col2, col3, col4 = st.columns([2, 2, 3, 2])
            with col1:
                st.markdown(f"**{t['transaction_date']}**")
            with col2:
                st.markdown(f"🧑 {t['user_name']}")
            with col3:
                st.markdown(f"{t['category_name']}")
                if t['description']:
                    st.caption(t['description'])
            with col4:
                st.markdown(f"{icon} :{color}[**{sign}{format_currency(t['amount'])}**]")
        
        st.markdown("---")
        st.caption("💵 = Income | 💸 = Expense")
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
    
    # ==========================================================================
    # DATE SELECTION (Outside form for validation)
    # ==========================================================================
    st.markdown("### 📅 Step 1: Select Date")
    st.markdown("*Accurate dates are important for month-to-month comparisons!*")
    
    date_col1, date_col2 = st.columns([1, 2])
    
    with date_col1:
        # Default to None to force selection
        expense_date = st.date_input(
            "When did this expense occur?",
            value=None,
            key="expense_date_input",
            help="Select the actual date of the expense"
        )
    
    with date_col2:
        if expense_date is None:
            st.warning("⚠️ Please select a date to continue")
            date_confirmed = False
        elif expense_date == date.today():
            st.info("📅 You selected **today's date**. Is this correct?")
            date_confirmed = st.checkbox(
                "Yes, this expense is from today",
                key="expense_date_confirm"
            )
            if not date_confirmed:
                st.caption("Check the box to confirm, or select a different date")
        else:
            # Past or future date - show what they selected
            days_diff = (date.today() - expense_date).days
            if days_diff > 0:
                st.success(f"✅ Date: **{expense_date.strftime('%B %d, %Y')}** ({days_diff} days ago)")
            else:
                st.success(f"✅ Date: **{expense_date.strftime('%B %d, %Y')}** (future date)")
            date_confirmed = True
    
    # Only show form if date is confirmed
    if not expense_date or (expense_date == date.today() and not date_confirmed):
        st.info("👆 Please select and confirm the date above to continue")
        return
    
    st.markdown("---")
    st.markdown("### 💸 Step 2: Enter Expense Details")
    
    # ==========================================================================
    # EXPENSE FORM
    # ==========================================================================
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
        
        with col2:
            # Amount
            amount = st.number_input(
                "Amount ($)",
                min_value=0.01,
                value=0.01,
                step=0.01,
                format="%.2f"
            )
            
            # Description
            description = st.text_input(
                "Description (optional)",
                placeholder="e.g., Weekly groceries at Trader Joe's"
            )
        
        # Show selected date
        st.info(f"📅 Recording for: **{expense_date.strftime('%B %d, %Y')}**")
        
        # Submit button
        submitted = st.form_submit_button("💾 Save Expense", use_container_width=True)
        
        if submitted:
            if amount <= 0.01:
                st.error("Please enter a valid amount")
            else:
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
                
                st.success(f"✅ Expense of {format_currency(amount)} saved for {selected_user} on {expense_date.strftime('%b %d, %Y')}!")
                st.balloons()
    
    # Show recent expenses below the form with CRUD operations
    st.markdown("---")
    st.markdown("### 💸 Recent Expenses")
    st.caption("Click on any entry to edit or delete it")
    
    recent = db.get_transactions(transaction_type="expense")[:10]
    
    if recent:
        # Calculate total
        total_recent = sum(t["amount"] for t in recent)
        st.metric("Total (shown below)", format_currency(total_recent))
        
        st.markdown("---")
        
        for t in recent:
            with st.expander(
                f"💸 {t['transaction_date']} | {t['user_name']} | "
                f"{t['category_name']} | -{format_currency(t['amount'])}"
            ):
                if t['description']:
                    st.markdown(f"**Description:** {t['description']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### ✏️ Edit")
                    with st.form(f"edit_expense_{t['id']}"):
                        # Get fresh user/category lists
                        all_users = db.get_all_users()
                        all_categories = db.get_categories_by_type("expense")
                        
                        user_names = [u["name"] for u in all_users]
                        category_names = [c["name"] for c in all_categories]
                        
                        # Find current indices
                        current_user_idx = user_names.index(t['user_name']) if t['user_name'] in user_names else 0
                        current_cat_idx = category_names.index(t['category_name']) if t['category_name'] in category_names else 0
                        
                        new_user = st.selectbox("Person", user_names, index=current_user_idx, key=f"exp_edit_user_{t['id']}")
                        new_category = st.selectbox("Category", category_names, index=current_cat_idx, key=f"exp_edit_cat_{t['id']}")
                        new_amount = st.number_input("Amount", value=float(t['amount']), min_value=0.01, key=f"exp_edit_amt_{t['id']}")
                        new_desc = st.text_input("Description", value=t['description'] or "", key=f"exp_edit_desc_{t['id']}")
                        new_date = st.date_input("Date", value=date.fromisoformat(t['transaction_date']), key=f"exp_edit_date_{t['id']}")
                        
                        if st.form_submit_button("💾 Save Changes"):
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
                            st.success("✅ Expense updated!")
                            rerun_app()
                
                with col2:
                    st.markdown("#### 🗑️ Delete")
                    st.warning("This cannot be undone!")
                    if st.button(f"Delete this expense", key=f"del_expense_{t['id']}"):
                        db.delete_transaction(t['id'])
                        st.success("✅ Expense deleted!")
                        rerun_app()
    else:
        st.info("No expenses recorded yet. Add your first expense above!")


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
    
    # ==========================================================================
    # DATE SELECTION (Outside form for validation)
    # ==========================================================================
    st.markdown("### 📅 Step 1: Select Date")
    st.markdown("*Accurate dates are important for month-to-month comparisons!*")
    
    date_col1, date_col2 = st.columns([1, 2])
    
    with date_col1:
        # Default to None to force selection
        income_date = st.date_input(
            "When was this income received?",
            value=None,
            key="income_date_input",
            help="Select the actual date of the income"
        )
    
    with date_col2:
        if income_date is None:
            st.warning("⚠️ Please select a date to continue")
            date_confirmed = False
        elif income_date == date.today():
            st.info("📅 You selected **today's date**. Is this correct?")
            date_confirmed = st.checkbox(
                "Yes, this income is from today",
                key="income_date_confirm"
            )
            if not date_confirmed:
                st.caption("Check the box to confirm, or select a different date")
        else:
            # Past or future date - show what they selected
            days_diff = (date.today() - income_date).days
            if days_diff > 0:
                st.success(f"✅ Date: **{income_date.strftime('%B %d, %Y')}** ({days_diff} days ago)")
            else:
                st.success(f"✅ Date: **{income_date.strftime('%B %d, %Y')}** (future date)")
            date_confirmed = True
    
    # Only show form if date is confirmed
    if not income_date or (income_date == date.today() and not date_confirmed):
        st.info("👆 Please select and confirm the date above to continue")
        return
    
    st.markdown("---")
    st.markdown("### 💵 Step 2: Enter Income Details")
    
    # ==========================================================================
    # INCOME FORM
    # ==========================================================================
    with st.form("income_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            user_names = [u["name"] for u in users]
            selected_user = st.selectbox("Who received this income?", user_names)
            
            categories = db.get_categories_by_type("income")
            category_names = [c["name"] for c in categories]
            selected_category = st.selectbox("Category", category_names)
        
        with col2:
            amount = st.number_input(
                "Amount ($)",
                min_value=0.01,
                value=0.01,
                step=0.01,
                format="%.2f"
            )
            
            description = st.text_input(
                "Description (optional)",
                placeholder="e.g., January paycheck"
            )
        
        # Show selected date
        st.info(f"📅 Recording for: **{income_date.strftime('%B %d, %Y')}**")
        
        submitted = st.form_submit_button("💾 Save Income", use_container_width=True)
        
        if submitted:
            if amount <= 0.01:
                st.error("Please enter a valid amount")
            else:
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
                
                st.success(f"✅ Income of {format_currency(amount)} recorded for {selected_user} on {income_date.strftime('%b %d, %Y')}!")
                st.balloons()
    
    # Show recent income below the form with CRUD operations
    st.markdown("---")
    st.markdown("### 💵 Recent Income")
    st.caption("Click on any entry to edit or delete it")
    
    recent_income = db.get_transactions(transaction_type="income")[:10]
    
    if recent_income:
        # Calculate total
        total_recent = sum(t["amount"] for t in recent_income)
        st.metric("Total (shown below)", format_currency(total_recent))
        
        st.markdown("---")
        
        for t in recent_income:
            with st.expander(
                f"💵 {t['transaction_date']} | {t['user_name']} | "
                f"{t['category_name']} | +{format_currency(t['amount'])}"
            ):
                if t['description']:
                    st.markdown(f"**Description:** {t['description']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### ✏️ Edit")
                    with st.form(f"edit_income_{t['id']}"):
                        # Get fresh user/category lists
                        all_users = db.get_all_users()
                        all_categories = db.get_categories_by_type("income")
                        
                        user_names = [u["name"] for u in all_users]
                        category_names = [c["name"] for c in all_categories]
                        
                        # Find current indices
                        current_user_idx = user_names.index(t['user_name']) if t['user_name'] in user_names else 0
                        current_cat_idx = category_names.index(t['category_name']) if t['category_name'] in category_names else 0
                        
                        new_user = st.selectbox("Person", user_names, index=current_user_idx, key=f"inc_edit_user_{t['id']}")
                        new_category = st.selectbox("Category", category_names, index=current_cat_idx, key=f"inc_edit_cat_{t['id']}")
                        new_amount = st.number_input("Amount", value=float(t['amount']), min_value=0.01, key=f"inc_edit_amt_{t['id']}")
                        new_desc = st.text_input("Description", value=t['description'] or "", key=f"inc_edit_desc_{t['id']}")
                        new_date = st.date_input("Date", value=date.fromisoformat(t['transaction_date']), key=f"inc_edit_date_{t['id']}")
                        
                        if st.form_submit_button("💾 Save Changes"):
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
                            st.success("✅ Income updated!")
                            rerun_app()
                
                with col2:
                    st.markdown("#### 🗑️ Delete")
                    st.warning("This cannot be undone!")
                    if st.button(f"Delete this income", key=f"del_income_{t['id']}"):
                        db.delete_transaction(t['id'])
                        st.success("✅ Income deleted!")
                        rerun_app()
    else:
        st.info("No income recorded yet. Add your first income above!")


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
                                rerun_app()
                
                with action_col2:
                    with st.expander("🗑️ Delete this goal"):
                        st.warning(f"Are you sure you want to delete '{goal['name']}'?")
                        if st.button(f"Yes, delete", key=f"del_goal_{goal['id']}"):
                            db.delete_savings_goal(goal["id"])
                            st.success("Goal deleted!")
                            rerun_app()
                
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
                rerun_app()


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
                                rerun_app()
                
                with action_col2:
                    with st.expander("🗑️ Delete this debt"):
                        st.warning(f"Are you sure you want to delete '{debt['name']}'?")
                        if st.button(f"Yes, delete", key=f"del_debt_{debt['id']}"):
                            db.delete_debt(debt["id"])
                            st.success("Debt deleted!")
                            rerun_app()
                
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
                rerun_app()


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
                        rerun_app()
            
            with col2:
                st.markdown("#### 🗑️ Delete Transaction")
                st.warning("This cannot be undone!")
                if st.button(f"Delete this transaction", key=f"del_trans_{t['id']}"):
                    db.delete_transaction(t['id'])
                    st.success("Transaction deleted!")
                    rerun_app()


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
            # Use a container to group user elements for easier automation
            with st.container():
                # Add hidden marker with user info for automation
                st.markdown(
                    f'<div data-user-id="{user["id"]}" data-user-name="{user["name"]}" style="display: none;"></div>',
                    unsafe_allow_html=True
                )
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    # User name with data attribute
                    st.markdown(f"🧑 **{user['name']}**")
                with col2:
                    # Delete expander - add data attribute via markdown for automation
                    st.markdown(
                        f'<div data-delete-expander-user="{user["name"]}" style="display: none;"></div>',
                        unsafe_allow_html=True
                    )
                    with st.expander("🗑️"):
                        st.caption("User must have no transactions to delete.")
                        # Delete button with clear identifier
                        if st.button(
                            "Delete", 
                            key=f"del_user_{user['id']}",
                            use_container_width=True
                        ):
                            try:
                                db.delete_user(user["id"])
                                st.success("User deleted!")
                                rerun_app()
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
                    rerun_app()
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
                rerun_app()
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
                            rerun_app()
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

