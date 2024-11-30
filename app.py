import streamlit as st
from auth import UserAuth
from main import ExpenseTracker  # Adjust import path if necessary
import pandas as pd
import datetime
import pymysql
from streamlit_option_menu import option_menu  # Make sure to install this if not already

# Create an instance of UserAuth
auth = UserAuth()

# Check if the user is already logged in
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.title("Login or Sign-Up")

    # Login form
    login_username = st.text_input("Username", key="login_username")
    login_password = st.text_input("Password", type="password", key="login_password")

    if st.button("Log In"):
        user_id = auth.authenticate_user(login_username, login_password)
        if user_id:
            st.session_state["authenticated"] = True
            st.session_state["username"] = login_username
            st.session_state["user_id"] = user_id  # Store user ID in session state
            st.success("Logged in successfully!")
            st.rerun()  # Refresh to show the walletnote content
        else:
            st.error("Invalid username or password!")

    # Sign-Up form
    st.subheader("Create an Account")
    signup_username = st.text_input("New Username", key="signup_username")
    signup_password = st.text_input("New Password", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

    if st.button("Sign Up"):
        if signup_username and signup_password and confirm_password:
            if signup_password != confirm_password:
                st.error("Passwords do not match!")
            else:
                if auth.register_user(signup_username, signup_password):
                    st.success("Account created successfully! You can now log in.")
        else:
            st.error("All fields are required!")

else:
    # If authenticated, show the walletnote content
    st.title("Welcome to Wallet Note")
    st.markdown(
        '<h5 style="text-align: left;">Jot down your daily expenses with just multiple clicks!</h5>',
        unsafe_allow_html=True,
    )

    # Navigation Menu
    selected = option_menu(
        menu_title=None,
        options=["Expenses Entry", "Expenses Overview", "Summary"],
        icons=["pencil-fill", "clipboard2-data", "bar-chart-fill"],
        orientation="horizontal",
    )

    # Create an instance of ExpenseTracker with the user ID from session state
    expense_tracker = ExpenseTracker(st.session_state["user_id"])

    if selected == "Expenses Entry":
        st.header("Add Expenses")
        with st.expander("Add Expenses"):
            category = st.selectbox(
                "Category",
                (
                    "Housing",
                    "Food",
                    "Transportation",
                    "Entertainment",
                    "School Tuition",
                    "Medical",
                    "Investment",
                ),
            )
            description = st.text_input("Description (optional)").title()
            value = st.number_input("Value", min_value=0.01)
            date = st.date_input("Date", value=datetime.date.today())

            if st.button("Add Expense"):
                try:
                    expense_tracker.add_expense(date, value, category, description)
                    st.success("Expense added successfully!")
                except pymysql.MySQLError as e:
                    st.error(f"Error adding expense: {e}")

    elif selected == "Expenses Overview":
        st.header("Expenses Overview")
        start_date = st.date_input("Start Date", value=datetime.date.today())
        end_date = st.date_input("End Date", value=datetime.date.today())

        if start_date > end_date:
            st.error("Start date cannot be after end date.")
        else:
            expenses = expense_tracker.get_expenses(start_date, end_date)
            if expenses:
                # Display expenses in a DataFrame
                df = pd.DataFrame(expenses, columns=["Date", "Amount", "Category", "Description"])
                st.write("### Expenses:")
                st.dataframe(df)

                # Add functionality to delete an expense
                st.write("### Delete an Expense")
                selected_index = st.number_input(
                    "Select the row index to delete (0-based index from the table above)",
                    min_value=0,
                    max_value=len(df) - 1 if len(df) > 0 else 0,
                    step=1,
                )

                if st.button("Delete Selected Expense"):
                    selected_row = df.iloc[selected_index]
                    try:
                        expense_tracker.delete_expense(
                            date=selected_row["Date"],
                            amount=selected_row["Amount"],
                            category=selected_row["Category"],
                            description=selected_row["Description"],
                        )
                        st.success("Expense deleted successfully!")
                        import time
                        time.sleep(1)
                        # Refresh the view
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting expense: {e}")
            else:
                st.info("No expenses found in the selected date range.")

    elif selected == "Summary":
        # Add buttons for choosing summary type
        summary_type = st.radio(
            "Select Summary View",
            options=["By Category", "By Month"],
            horizontal=True,
        )

        expenses = expense_tracker.get_expenses()
        if expenses:
            if summary_type == "By Category":
                # Create a dictionary to store total amounts by category
                category_totals = {}
                for date, amount, category, description in expenses:
                    if category in category_totals:
                        category_totals[category] += amount
                    else:
                        category_totals[category] = amount

                # Create a DataFrame for better visualization in Streamlit
                df = pd.DataFrame(list(category_totals.items()), columns=["Category", "Total Amount"])
                df = df.sort_values(by="Total Amount", ascending=False)

                st.write("### Expense Summary by Category")
                st.dataframe(df)  # Display the DataFrame as a table

            elif summary_type == "By Month":
                # Group expenses by month
                monthly_totals = {}
                for date, amount, category, description in expenses:
                    month_year = date.strftime("%Y-%m")  # Format as 'YYYY-MM'
                    if month_year in monthly_totals:
                        monthly_totals[month_year] += amount
                    else:
                        monthly_totals[month_year] = amount

                # Create a DataFrame for monthly totals
                df = pd.DataFrame(list(monthly_totals.items()), columns=["Month", "Total Amount"])
                df = df.sort_values(by="Month")

                st.write("### Expense Summary by Month")
                st.dataframe(df)  # Display the DataFrame as a table
        else:
            st.info("No expenses recorded yet.")

    # Ensure to close the connection at the end
    expense_tracker.close_connection()
