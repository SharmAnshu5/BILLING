import streamlit as st
import pandas as pd
from datetime import datetime
import pdfkit
import base64
import os
import streamlit.components.v1 as components

st.set_page_config(page_title="Jewellery Billing System", layout="wide")

# -----------------------------
# FILES
# -----------------------------

ledger_file = "ledger.xlsx"
sales_file = "sales.xlsx"

# -----------------------------
# LOAD LEDGER
# -----------------------------

@st.cache_data
def load_ledger():
    try:
        return pd.read_excel(ledger_file)
    except:
        return pd.DataFrame()

ledger_df = load_ledger()

# -----------------------------
# LOAD SALES
# -----------------------------

def load_sales():
    required_columns = [
        "Bill No", "Date", "Customer", "Mobile", "Address",
        "Grand Total", "Previous Balance", "Total Payable",
        "Cash Paid", "Gold Paid (g)", "Gold Value",
        "Silver Paid (g)", "Silver Value", "Total Paid",
        "Balance Remaining", "Gold Rate", "Silver Rate",
        "Payment Type", "Remarks",
        "Gold Booked (g)", "Gold Booking Amount",
        "Silver Booked (g)", "Silver Booking Amount"
    ]
    
    try:
        if os.path.exists(sales_file):
            df = pd.read_excel(sales_file)
            # Ensure all columns exist
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None
            return df
        else:
            return pd.DataFrame(columns=required_columns)
    except:
        return pd.DataFrame(columns=required_columns)

sales_df = load_sales()

bill_number = len(sales_df) + 1

# -----------------------------
# SAVE CUSTOMER
# -----------------------------

def save_customer_to_ledger(name, mobile, address, balance, gold, silver):

    required_columns = [
        "Name", "Mobile Number", "Address",
        "Balance Remaning", "Gold Deposit ( gms)", "Silver",
        "Balance Status", "Last Updated"
    ]

    try:

        if os.path.exists(ledger_file):
            ledger = pd.read_excel(ledger_file)
        else:
            ledger = pd.DataFrame(columns=required_columns)

        # Ensure all columns exist
        for c in required_columns:
            if c not in ledger.columns:
                ledger[c] = None

        # Enforce stable dtypes before updates to avoid pandas incompatible dtype warnings
        text_columns = ["Name", "Mobile Number", "Address", "Balance Status", "Last Updated"]
        numeric_columns = ["Balance Remaning", "Gold Deposit ( gms)", "Silver"]

        for col in text_columns:
            ledger[col] = ledger[col].astype("string")

        for col in numeric_columns:
            ledger[col] = pd.to_numeric(ledger[col], errors="coerce")

        # Determine balance status
        if balance > 0:
            balance_status = "जमा"  # Jama (Credit/Positive)
        elif balance < 0:
            balance_status = "नाम"  # Naam (Debit/Negative)
        else:
            balance_status = "Nil"

        mobile_key = str(mobile).strip() if mobile else ""
        if not mobile_key:
            return False, "Mobile Number is required (unique id)."

        last_updated = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # Fill defaults: N/A for text, 0 for numbers
        record = {
            "Name": str(name).strip() if name else "N/A",
            "Mobile Number": mobile_key,
            "Address": str(address).strip() if address else "N/A",
            "Balance Remaning": float(balance) if balance else 0.0,
            "Gold Deposit ( gms)": float(gold) if gold else 0.0,
            "Silver": float(silver) if silver else 0.0,
            "Balance Status": balance_status,
            "Last Updated": last_updated
        }

        # Mobile Number is unique id for ledger row updates
        existing_mask = ledger["Mobile Number"].astype(str).str.strip() == mobile_key

        if existing_mask.any():
            # Update existing customer by mobile; latest bill name overwrites old name
            mask = existing_mask
            for col in required_columns:
                ledger.loc[mask, col] = record[col]
        else:
            # Add new customer
            ledger = pd.concat([ledger, pd.DataFrame([record])], ignore_index=True)

        # Fill any remaining NaN values with defaults
        for col in ledger.columns:
            if ledger[col].dtype in ['float64', 'int64']:
                ledger[col] = ledger[col].fillna(0)
            else:
                ledger[col] = ledger[col].fillna("N/A")

        ledger.to_excel(ledger_file, index=False)
        load_ledger.clear()

        return True, "Customer saved/updated by Mobile Number"

    except Exception as e:
        return False, str(e)

# -----------------------------
# TITLE
# -----------------------------

st.title("💎 Shri Hari Jewellers Billing Software")
st.info(f"Bill Number : {bill_number}")

# -----------------------------
# METAL RATES
# -----------------------------

st.sidebar.header("Metal Rates")

gold_rate = st.sidebar.number_input("Gold Rate ₹ / g", value=16000)
silver_rate = st.sidebar.number_input("Silver Rate ₹ /g", value=2700)
silver_rate_10 = silver_rate * 10

# -----------------------------
# CUSTOMER SECTION
# -----------------------------

st.sidebar.header("Customer Details")

customer_names = []

if not ledger_df.empty:
    customer_names = ledger_df["Name"].dropna().unique().tolist()

customer = st.sidebar.selectbox(
    "Select Customer",
    ["New Customer"] + sorted(customer_names)
)

mobile=""
Address=""
ledger_balance=0
ledger_gold=0
ledger_silver=0

if customer!="New Customer":

    row = ledger_df[ledger_df["Name"]==customer].iloc[0]

    mobile=row["Mobile Number"]
    Address=row["Address"]

    ledger_balance = float(row["Balance Remaning"]) if pd.notna(row["Balance Remaning"]) else 0
    ledger_gold = float(row["Gold Deposit ( gms)"]) if pd.notna(row["Gold Deposit ( gms)"]) else 0
    ledger_silver = float(row["Silver"]) if pd.notna(row["Silver"]) else 0

else:

    customer = st.sidebar.text_input("Customer Name")
    mobile = st.sidebar.text_input("Mobile Number")
    Address = st.sidebar.text_input("Address")

    ledger_balance = st.sidebar.number_input("Existing Balance ₹",value=0.0)
    ledger_gold = st.sidebar.number_input("Gold Deposit g",value=0.0)
    ledger_silver = st.sidebar.number_input("Silver Deposit g",value=0.0)

# save customer

if st.sidebar.button("Save Customer"):

    ok,msg = save_customer_to_ledger(
        customer,mobile,Address,
        ledger_balance,ledger_gold,ledger_silver
    )

    if ok:
        st.sidebar.success(msg)
        st.rerun()
    else:
        st.sidebar.error(msg)

# -----------------------------
# SHOW LEDGER INFO
# -----------------------------

st.subheader("Customer Ledger Info")

c1,c2,c3 = st.columns(3)

c1.metric("Balance Remaining ₹",ledger_balance)
c2.metric("Gold Deposit g",ledger_gold)
c3.metric("Silver Deposit g",ledger_silver)

# -----------------------------
# METAL BOOKING
# -----------------------------

st.subheader("🥇 Metal Booking")
st.caption("Customer pays ₹ to book gold/silver — grams auto-calculated at current rates and credited to their account")

bk1, bk2 = st.columns(2)

with bk1:
    st.markdown("**Gold Booking**")
    gold_booking_amount = st.number_input(
        "Gold Booking Amount ₹", value=0.0, step=100.0, min_value=0.0, key="gold_booking_amt"
    )
    gold_booked_grams = round(gold_booking_amount / gold_rate, 3) if gold_rate > 0 and gold_booking_amount > 0 else 0.0
    if gold_booking_amount > 0:
        st.info(f"Grams to be credited: **{gold_booked_grams} g**  (@ ₹{gold_rate}/g)")

with bk2:
    st.markdown("**Silver Booking**")
    silver_booking_amount = st.number_input(
        "Silver Booking Amount ₹", value=0.0, step=100.0, min_value=0.0, key="silver_booking_amt"
    )
    silver_booked_grams = round(silver_booking_amount / silver_rate, 3) if silver_rate > 0 and silver_booking_amount > 0 else 0.0
    if silver_booking_amount > 0:
        st.info(f"Grams to be credited: **{silver_booked_grams} g**  (@ ₹{round(silver_rate,2)}/g)")

total_booking_amount = gold_booking_amount + silver_booking_amount

if total_booking_amount > 0:
    booking_rows = []
    if gold_booking_amount > 0:
        booking_rows.append({
            "Metal": "Gold",
            "Current Rate (₹/g)": gold_rate,
            "Amount Booked (₹)": gold_booking_amount,
            "Grams Credited": gold_booked_grams
        })
    if silver_booking_amount > 0:
        booking_rows.append({
            "Metal": "Silver",
            "Current Rate (₹/g)": round(silver_rate, 2),
            "Amount Booked (₹)": silver_booking_amount,
            "Grams Credited": silver_booked_grams
        })
    st.dataframe(pd.DataFrame(booking_rows), use_container_width=True)
    st.success(f"Total Booking Cash Received: ₹ {round(total_booking_amount, 2)}")

st.divider()

# -----------------------------
# SESSION STATE INITIALIZATION
# -----------------------------

if "items" not in st.session_state:
    st.session_state["items"] = []

if "bill_saved" not in st.session_state:
    st.session_state["bill_saved"] = False

if "item_history" not in st.session_state:
    st.session_state["item_history"] = [
        "Necklace","Pajeb","Ladies Ring","Gents Ring","Chain",
        "Pendant","Mangal Sutra","Kada","Bracelet","Earrings",
        "Glass","Plate"
    ]

# -----------------------------
# ADD ITEM
# -----------------------------

st.subheader("Add Item")

col1,col2,col3,col4,col5,col6,col7 = st.columns(7)

with col1:
    serial = st.number_input("S.No",step=1)

with col2:

    options = ["Search item..."] + st.session_state.item_history + ["Other..."]

    selected = st.selectbox("Item",options)

    if selected=="Other...":

        new_item = st.text_input("Enter item")

        if new_item:
            item=new_item
            if new_item not in st.session_state.item_history:
                st.session_state.item_history.append(new_item)

    elif selected=="Search item...":
        item=""
    else:
        item=selected

with col3:
    metal = st.selectbox("Metal",["Gold","Silver"])

with col4:
    weight = st.number_input("Weight g",format="%.3f")

with col5:
    minus = st.number_input("Less Weight g",format="%.3f")

with col6:
    labour = st.number_input("Other Charges ₹")

with col7:
    less = st.number_input("Less ₹")

# add item

if st.button("Add Item"):

    total_weight = weight - minus

    rate = gold_rate if metal=="Gold" else silver_rate

    amount = (total_weight*rate)+labour-less

    st.session_state["items"].append({
        "S.No":serial,
        "Item":item,
        "Metal":metal,
        "Weight":weight,
        "Less":minus,
        "Total Weight":total_weight,
        "Rate":rate,
        "Labour":labour,
        "Less ₹":less,
        "Amount ₹":amount
    })

# clear bill

if st.button("🗑️ Clear Bill"):
    st.session_state["items"] = []
    st.session_state["bill_saved"] = False
    st.rerun()

# -----------------------------
# BILL TABLE
# -----------------------------

st.subheader("Bill Items")

if len(st.session_state["items"])>0:

    df = pd.DataFrame(st.session_state["items"])

    st.dataframe(df, width='stretch')

    grand_total = df["Amount ₹"].sum()

    st.success(f"Grand Total ₹ {round(grand_total,2)}")

else:

    df = pd.DataFrame()
    grand_total = 0.0
    st.info("No items added")

# -----------------------------
# PAYMENT
# -----------------------------

if not df.empty or total_booking_amount > 0:

    st.subheader("Payment")

    # Previous balance option
    col_prev1, col_prev2 = st.columns([1, 3])
    with col_prev1:
        include_previous = st.checkbox("Include Previous Balance", value=True)
    with col_prev2:
        if include_previous:
            st.info(f"Previous Balance: ₹ {ledger_balance}")

    # Calculate total with/without previous balance
    if include_previous:
        total_payable = grand_total + ledger_balance
    else:
        total_payable = grand_total

    st.metric("Total Payable", f"₹ {round(total_payable, 2)}")

    # Payment details
    p1, p2 = st.columns(2)

    payment_type = p1.selectbox("Payment Type", ["Cash", "UPI", "Credit", "RTGS", "Mixed"])
    cash_deposit = p2.number_input("Cash Amount Paid ₹", value=0.0, step=0.01)

    # Gold and Silver payment
    st.markdown("#### Payment in Gold/Silver")
    ps1, ps2, ps3, ps4 = st.columns(4)

    gold_paid_grams = ps1.number_input("Gold Paid (g)", value=0.0, step=0.001, format="%.3f")
    gold_paid_value = gold_paid_grams * gold_rate
    ps2.metric("Gold Value ₹", round(gold_paid_value, 2))

    silver_paid_grams = ps3.number_input("Silver Paid (g)", value=0.0, step=0.001, format="%.3f")
    silver_paid_value = silver_paid_grams * silver_rate
    ps4.metric("Silver Value ₹", round(silver_paid_value, 2))

    # Total payment
    total_payment = cash_deposit + gold_paid_value + silver_paid_value

    st.success(f"Total Payment Received: ₹ {round(total_payment, 2)}")

    # Calculate remaining balance and gold/silver deposits
    previous_balance = ledger_balance
    balance_remaining = total_payable - total_payment

    # Balance status for display
    if balance_remaining > 0:
        balance_status = "नाम"
    elif balance_remaining < 0:
        balance_status = "जमा"
    else:
        balance_status = "Nil"

    # Update gold and silver deposits (customer's remaining deposits + newly booked grams)
    new_gold_deposit = ledger_gold - gold_paid_grams + gold_booked_grams
    new_silver_deposit = ledger_silver - silver_paid_grams + silver_booked_grams

    # Show final balances
    fb1, fb2, fb3 = st.columns(3)
    fb1.metric(f"Balance Remaining ₹ ({balance_status})", round(balance_remaining, 2))
    fb2.metric("Gold Deposit (g)", round(new_gold_deposit, 3))
    fb3.metric("Silver Deposit (g)", round(new_silver_deposit, 3))

    # Remarks
    remarks = st.text_area("Remarks (Optional)", placeholder="Add any notes or remarks for this bill...")

# -----------------------------
# SAVE BILL
# -----------------------------

    if st.button("💾 Save Bill", disabled=st.session_state["bill_saved"]):

        # Save to sales file
        record = {
            "Bill No": bill_number,
            "Date": datetime.now(),
            "Customer": customer,
            "Mobile": mobile,
            "Address": Address,
            "Grand Total": grand_total,
            "Previous Balance": previous_balance if include_previous else 0,
            "Total Payable": total_payable,
            "Cash Paid": cash_deposit,
            "Gold Paid (g)": gold_paid_grams,
            "Gold Value": gold_paid_value,
            "Silver Paid (g)": silver_paid_grams,
            "Silver Value": silver_paid_value,
            "Total Paid": total_payment,
            "Balance Remaining": balance_remaining,
            "Gold Rate": gold_rate,
            "Silver Rate": silver_rate,
            "Payment Type": payment_type,
            "Remarks": remarks,
            "Gold Booked (g)": gold_booked_grams,
            "Gold Booking Amount": gold_booking_amount,
            "Silver Booked (g)": silver_booked_grams,
            "Silver Booking Amount": silver_booking_amount
        }
        
        # Create DataFrame from record and concat, handling empty df case
        new_record_df = pd.DataFrame([record])
        if sales_df.empty:
            sales_df2 = new_record_df
        else:
            sales_df2 = pd.concat([sales_df, new_record_df], ignore_index=True)
        sales_df2.to_excel(sales_file, index=False)

        # Update ledger with new balance and deposits
        save_customer_to_ledger(
            customer, mobile, Address,
            balance_remaining,
            new_gold_deposit,
            new_silver_deposit
        )

        st.success("✅ Bill saved and ledger updated successfully!")
        st.balloons()

# -----------------------------
# BILL HTML
# -----------------------------

    def build_bill_html():

        table_html = df.to_html(index=False) if not df.empty else ""

        # Build booking section HTML
        booking_section = ""
        if total_booking_amount > 0:
            booking_rows_html = ""
            if gold_booking_amount > 0:
                booking_rows_html += f"""<tr><td>Gold</td><td>₹ {gold_rate}/g</td><td>₹ {round(gold_booking_amount, 2)}</td><td>{gold_booked_grams} g</td></tr>"""
            if silver_booking_amount > 0:
                booking_rows_html += f"""<tr><td>Silver</td><td>₹ {round(silver_rate,2)}/g</td><td>₹ {round(silver_booking_amount, 2)}</td><td>{silver_booked_grams} g</td></tr>"""
            booking_section = f"""
            <h3>Metal Booking</h3>
            <table class='booking-table'>
                <thead><tr><th>Metal</th><th>Current Rate</th><th>Amount Booked (₹)</th><th>Grams Credited</th></tr></thead>
                <tbody>{booking_rows_html}</tbody>
            </table>
            <div class='booking-box'>
                <b>Total Booking Cash Received: ₹ {round(total_booking_amount, 2)}</b>
            </div>
            """

        # Build items section HTML (only if there are items)
        items_section = ""
        if not df.empty:
            items_section = f"""
            <h3>Items</h3>
            {table_html}
            <div class='total-box'>
            <h3 style='margin:0;border:none'>Bill Total: ₹ {round(grand_total, 2)}</h3>
            </div>
            """

        # Build payment details
        payment_details = f"""
        <div class='payment-section'>
            <h3>Payment Details</h3>
            <table class='payment-table'>
                <tr><td><b>Payment Type:</b></td><td>{payment_type}</td></tr>
                <tr><td><b>Cash Paid:</b></td><td>₹ {round(cash_deposit, 2)}</td></tr>
        """

        if gold_paid_grams > 0:
            payment_details += f"""<tr><td><b>Gold Paid:</b></td><td>{round(gold_paid_grams, 3)} g (₹ {round(gold_paid_value, 2)})</td></tr>"""

        if silver_paid_grams > 0:
            payment_details += f"""<tr><td><b>Silver Paid:</b></td><td>{round(silver_paid_grams, 3)} g (₹ {round(silver_paid_value, 2)})</td></tr>"""

        payment_details += f"""
                <tr><td><b>Total Payment:</b></td><td>₹ {round(total_payment, 2)}</td></tr>
            </table>
        </div>
        """

        # Show deposit lines only when values are not zero
        deposit_lines = ""
        if round(new_gold_deposit, 3) != 0:
            deposit_lines += f"<b>Gold Deposit:</b> {round(new_gold_deposit, 3)} g <br>"
        if round(new_silver_deposit, 3) != 0:
            deposit_lines += f"<b>Silver Deposit:</b> {round(new_silver_deposit, 3)} g"

        html = f"""
        <html>
        <head>
        <style>
        body {{font-family:Arial;padding:25px;background:#fff}}
        h2 {{color:#b8860b;margin-bottom:5px}}
        h3 {{color:#333;border-bottom:2px solid #d4af37;padding-bottom:5px}}
        table {{width:100%;border-collapse:collapse;margin:15px 0}}
        th,td {{border:1px solid #ccc;padding:8px;text-align:left}}
        th {{background:#f8f5e6}}
        .header-info {{margin:15px 0;line-height:1.8}}
        .rates {{background:#f0f0f0;padding:10px;margin:10px 0;border-radius:5px}}
        .payment-section {{margin:20px 0}}
        .payment-table {{width:50%;border:none}}
        .payment-table td {{border:none;padding:5px}}
        .total-box {{background:#fff3cd;padding:15px;margin:15px 0;border:2px solid #d4af37;border-radius:5px}}
        .balance-box {{background:#d1ecf1;padding:15px;margin:15px 0;border-radius:5px}}
        .booking-box {{background:#fff8e1;padding:10px;margin:10px 0;border:1px solid #f9a825;border-radius:5px}}
        .booking-table th {{background:#fff8e1}}
        .remarks {{margin:15px 0;padding:10px;background:#f9f9f9;border-left:4px solid #b8860b}}
        </style>
        </head>

        <body>

        <h2>Shri Hari Jewellers</h2>
        <h4 style='color:#666;margin-top:0'>Rough Bill</h4>

        <div class='header-info'>
        <b>Date:</b> {datetime.now().strftime("%d-%m-%Y %H:%M")} <br>
        <b>Customer:</b> {customer} <br>
        <b>Mobile:</b> {mobile} <br>
        <b>Address:</b> {Address}
        </div>

        <div class='rates'>
        <b>Current Rates:</b> Gold = ₹ {gold_rate}/g | Silver = ₹ {round(silver_rate, 2)}/g
        </div>

        {booking_section}

        {items_section}

        <div class='balance-box'>
        <b>Previous Balance:</b> ₹ {round(previous_balance if include_previous else 0, 2)} <br>
        <b>Total Payable:</b> ₹ {round(total_payable, 2)}
        </div>

        {payment_details}

        <div class='balance-box'>
        <b>Balance Remaining ({balance_status}):</b> ₹ {round(balance_remaining, 2)} <br>
        {deposit_lines}
        <b>Gold Remaining in Deposit:</b> {round(new_gold_deposit, 3)} g <br>
        <b>Silver Remaining in Deposit:</b> {round(new_silver_deposit, 3)} g
        </div>

        <div style='margin-top:40px;font-size:11px;color:#666;text-align:center'>
        This is a computer generated bill | Thank you for your business | Visit Again!
        </div>

        </body>
        </html>
        """

        return html

    bill_html = build_bill_html()

# -----------------------------
# PRINT BILL
# -----------------------------

    if st.button("Print Bill"):

         components.html(
            bill_html+"<script>window.print()</script>",
            height=700
        )

# -----------------------------
# DOWNLOAD PDF
# -----------------------------

    if st.button("Download PDF"):

        try:

            pdf_bytes = pdfkit.from_string(bill_html,False)

            st.download_button(
                "Download",
                pdf_bytes,
                file_name=f"{customer}_{datetime.now().strftime('%d-%m-%Y')}_bill.pdf",
                mime="application/pdf"
            )

        except:

            st.download_button(
                "Download HTML Bill",
                bill_html,
                file_name=f"{customer}_{datetime.now().strftime('%d-%m-%Y')}_bill.html"
            )