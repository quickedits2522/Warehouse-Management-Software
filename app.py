import logging
import os
import sys
import mysql.connector as ms
from datetime import date
import pandas as pd
from prettytable import from_db_cursor
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import qrcode
import io
import webbrowser
from flask import Flask, jsonify, render_template, request, redirect, send_file, url_for, flash, session
import bcrypt
from functools import wraps

# Establish connection to MySQL database
# Ensure user and password are correct for your MySQL setup
mycon = ms.connect(user = "root", passwd = "mysql", host = "localhost", use_pure=True)
# Cursor is initialized as a dictionary cursor for easy column access
mycursor = mycon.cursor(dictionary=True, buffered=True)
mycursor.execute("CREATE DATABASE IF NOT EXISTS WMS")
mycursor.execute("USE WMS")
company_name = None

LOG_FILE = "activity_log.txt"

def new_cursor():
    return mycon.cursor(dictionary=True, buffered=True)

# Initialize company_name globally for Flask routes to prevent error
# This value will be updated in the main block after check_settings_filled()
company_name = "WMS App" 
try:
    mycursor.execute("SELECT CompanyName FROM SETTINGS LIMIT 1")
    setting_result = mycursor.fetchone()
    if setting_result:
        company_name = setting_result['CompanyName']
except ms.Error as e:
    # This handles the case where SETTINGS table might not exist yet
    if 'Table' not in str(e) and 'exist' not in str(e):
        print(f"Database error during initial company name fetch: {e}")


# Function to log activities to console and file
def log_activity(message, level="INFO"):
    """Log activities with timestamp and level to a log file and print to console."""
    try:
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}\n"

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_message)

        print(log_message.strip())

    except Exception as e:
        print(f"Failed to log activity: {e}")

# CLI user management function wrapper for the main menu, as it calls add_user()
def add_user():
    add_user_cli()

#--------------- User Management ----------------

def add_user_cli():
    """CLI function to add a new user to the USER table."""
    try : 
        # UserID is now AUTO_INCREMENT, so we only need Name, Dept, and Sal
        # The database schema for USER table has (UserID int PRIMARY KEY AUTO_INCREMENT, Name varchar(50), username varchar(50) UNIQUE,  Department varchar(30), Salary int)
        # However, the CLI only asks for UserID, Name, Dept, Sal. To match the schema, 
        # we'll add 'username' in the database (which is used for LOGIN) but it's missing in CLI.
        # For simplicity, since UserID is AUTO_INCREMENT, we'll ask for username in CLI too.
        # The original code only took UserID, Name, Dept, Sal.
        
        # Original: userid = input("Enter UserID: ") 
        # Modified to use AUTO_INCREMENT and add a placeholder 'username'
        name = input("Enter Username (Real Name): ")
        username_login = input("Enter Login Username (Unique): ")
        dept = input("Enter Department: ")
        sal = int(input("Enter Salary: "))
    
        # Insert into USER table (UserID is auto-generated)
        mycursor.execute("INSERT INTO USER (Name, username, Department, Salary) VALUES (%s, %s, %s, %s)", (name, username_login, dept, sal))
        mycon.commit()
        log_activity(f"User '{name}' successfully added to the table with username '{username_login}'")

    except ms.IntegrityError:
        # UserID is AUTO_INCREMENT, so this error is likely for the UNIQUE 'username' column
        log_activity(f"Username : {username_login} already exists. Please use a unique username.")

    except ValueError: 
        log_activity("Invalid input. Please enter the correct data types for salary.")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def remove_user_cli():
    """CLI function to delete a user by UserID."""
    try :
        delete_id = input("Enter UserID of the entry to be deleted : ")
        # Using parameterized query for better security
        mycursor.execute("DELETE FROM USER WHERE UserID = %s", (delete_id,))
        mycon.commit()
        if mycursor.rowcount == 0:
            log_activity(f"No user found with UserID: {delete_id}. No entry deleted.")
        else:
            log_activity(f"Entry successfully deleted from the table for userID : {delete_id}")
        
    except Exception as e:
        log_activity(f"An error occurred: {e}")

def search_user_cli():
    """CLI function to search and display a user by UserID."""
    try : 
        user = input("Enter UserID of the user to be found: ")
        mycursor.execute("select * from user where UserID = %s", (user,))
        table = from_db_cursor(mycursor)
        if not table._rows :
            log_activity(f"No records found for UserID : {user}")
        else :
            log_activity(table)

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def update_user_cli():
    """CLI function to update a specific column for a user by UserID."""
    try :
        column = input("Enter Column where the value is to be changed: ")
        value1 = input("Enter UserID of the entry to be updated: ")
        value2 = input("Enter Updated value: ")
        # Warning: Direct string formatting for column name can be an SQL injection risk.
        # For a simple CLI, we proceed, but for production, this should be validated.
        mycursor.execute(f"UPDATE USER SET {column} = %s WHERE UserID = %s", (value2, value1))
        mycon.commit()
        log_activity(f"Value of column : {column} updated to {value2} successfully updated for UserID : {value1}")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

#--------------- Product Management ----------------

def add_stock_cli():
    """CLI function to add a new product to the PRODUCTS table."""
    try : 
        # ProductID is AUTO_INCREMENT, but the original code asks for it. 
        # We will keep it as AUTO_INCREMENT and remove the input.
        # Original: pdtid = input("Enter ProductID: ") 
        name = input("Enter product name: ")
        cost = float(input("Enter cost price of product: "))
        mrp = float(input("Enter MRP of product: "))
        qty = int(input("Enter quantity of product: "))
    
        # Insert, letting ProductID be auto-generated
        mycursor.execute("INSERT INTO PRODUCTS (Product_Name, Cost_Price, MRP, Quantity) VALUES (%s, %s, %s, %s)", (name, cost, mrp, qty))
        mycon.commit()
        log_activity(f"Record successfully added for Product Name : {name}, Cost Price : {cost}, MRP : {mrp}, Quantity : {qty}")

    except ms.IntegrityError as e:
        # ProductID is AUTO_INCREMENT, so integrity error is unlikely here unless product name is unique (not enforced by schema)
        log_activity(f"An Integrity Error occurred: {e}")

    except ValueError: 
        log_activity("Invalid input. Please enter the correct data types (numbers for cost, mrp, qty).")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def remove_stock_cli():
    """CLI function to delete a product by ProductID."""
    try :
        value = input("Enter the ProductID of the entry to be deleted: ")
        mycursor.execute("delete from Products where ProductID = %s",(value,))
        mycon.commit()
        if mycursor.rowcount == 0:
            log_activity(f"No product found with ProductID: {value}. No entry deleted.")
        else:
            log_activity(f"ProductID : {value} successfully deleted from the table Products")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def search_stock_cli():
    """CLI function to search and display a product by ProductID."""
    try:
        product = input("Enter the ProductID of the entry to be dislayed: ")
        mycursor.execute("SELECT * FROM Products WHERE ProductID = %s", (product,))
        table = from_db_cursor(mycursor)
        if not table._rows :
            log_activity(f"No records found for ProductID: {product}")
        else :
            log_activity(table)

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def update_stock_cli():
    """CLI function to update a specific column for a product by ProductID."""
    try :
        column = input("Enter Column where the value is to be changed: ")
        value1 = input("Enter ProductID of the entry to be updated: ")
        value2 = input("Enter updated value: ")
        # Warning: Direct string formatting for column name can be an SQL injection risk.
        # For a simple CLI, we proceed, but for production, this should be validated.
        mycursor.execute(f"update Products set {column} = %s where ProductID = %s", (value2, value1))
        mycon.commit()
        log_activity(f"Value of {column} updated to {value2} for the ProductID : {value1} successfully")

    except Exception as e:
        log_activity(f"An error occurred: {e}")


def check_settings_filled():
    """Checks if company settings are present and returns the company name or an error message."""
    cursor = mycon.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM SETTINGS")
    result = cursor.fetchone()
    
    if result and result['count'] == 0:
        return "ADD COMPANY NAME IN SETTINGS"
    
    cursor.execute("SELECT CompanyName from SETTINGS LIMIT 1")
    company_name = cursor.fetchone()
    return company_name['CompanyName']

def create_init_db():
    """Creates all required tables if they do not exist."""
    try : 
        # Ensure Foreign Key is only used when the referenced table is created
        init_tables=[
            "CREATE TABLE IF NOT EXISTS USER(UserID int PRIMARY KEY AUTO_INCREMENT, Name varchar(50), username varchar(50) UNIQUE,  Department varchar(30), Salary int)",
            "CREATE TABLE IF NOT EXISTS PRODUCTS(ProductID int PRIMARY KEY AUTO_INCREMENT, Product_Name varchar(50), Cost_Price float, MRP float, Quantity int)",
            "CREATE TABLE IF NOT EXISTS SALES(BillNo int PRIMARY KEY AUTO_INCREMENT, Customer_Name varchar(50), Products varchar(300), QTY int, Sale_Amount float, Date_Of_Sale date)",
            # TRANSPORT references SALES, so it must be created after SALES
            "CREATE TABLE IF NOT EXISTS TRANSPORT(ShipmentID int PRIMARY KEY AUTO_INCREMENT, BillNo int, Address varchar(300), Status varchar(30), FOREIGN KEY (BillNo) REFERENCES SALES(BillNo) ON DELETE CASCADE)",
            "CREATE TABLE IF NOT EXISTS PROFIT_AND_LOSS(BillNo int, Product_Name varchar(50), Net_Profit float)",
            "CREATE TABLE IF NOT EXISTS SETTINGS(CompanyName varchar(255), CompanyID VARCHAR(255), GSTIN char(30), Company_Address varchar(255), State varchar(255), Mobile_No BIGINT, Email varchar(255), UPI varchar(40), IGST float, CGST float, SGST float)",
            # LOGIN references USER, so it must be created after USER
            "CREATE TABLE IF NOT EXISTS LOGIN(UserID int, Username varchar(255), Password varchar(255), Department varchar(30), FOREIGN KEY (UserID) REFERENCES USER(UserID) ON DELETE CASCADE)"
        ]
        for i in init_tables:
            mycursor.execute(i)
        mycon.commit()
        log_activity("Initialized USER, PRODUCTS, SALES, TRANSPORT, PROFIT_AND_LOSS, SETTINGS and LOGIN tables in the database")

    except Exception as e:
        log_activity(f"An error occurred during initialization: {e}")

def delete_db_cli():
    """Deletes all tables from the database (irreversible)."""
    try : 
        log_activity("WARNING! : This process is irreversible, All your data will be deleted permanently!!")
        usr_confirm = input("Do you want to continue (Y/N) : ")
        # Drop tables in an order that avoids foreign key constraint issues (children before parents)
        tables = ["TRANSPORT", "LOGIN", "PROFIT_AND_LOSS", "SALES", "PRODUCTS", "USER", "SETTINGS"]
        if usr_confirm in "Yy":
            for i in tables:
                mycursor.execute(f"DROP TABLE IF EXISTS {i}")
            mycon.commit()
            log_activity("Deleted TRANSPORT, LOGIN, PROFIT_AND_LOSS, SALES, PRODUCTS, USER and SETTINGS tables from the database")

        elif usr_confirm in "Nn" : 
            log_activity("Operation Canceled by the user")
    
        else :
            log_activity("Invalid Choice entered by the user")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def record_sale(custm_name, address, product, qty, today, status, discount = 0.0):
    """Record a sale, update inventory, generate bill, and record shipment."""
    
    # Convert discount percentage to a decimal rate
    discount_rate = discount / 100.0 if discount > 0.0 else 0.0

    try:
        # Fetch MRP, Cost Price, and Quantity available
        mycursor.execute("SELECT MRP, Cost_Price, Quantity FROM PRODUCTS WHERE Product_Name = %s", (product,))
        output = mycursor.fetchall()
        
        if not output:
             log_activity(f"\nProduct '{product}' not found in inventory.")
             return # Exit function

        mrp = float(output[0]['MRP'])
        qty_avl = int(output[0]['Quantity'])
        cost_price = float(output[0]['Cost_Price'])

        log_activity(f"MRP of {product} : ₹{mrp}")

        if qty <= qty_avl:
            log_activity('NO ERROR - SUFFICIENT STOCK AVAILABLE')

            # Calculate pre-tax amount
            base_amount = mrp * qty
            discounted_amount = base_amount * (1 - discount_rate)
            
            # --- Fetch GST Rates for Sale Amount Calculation ---
            mycursor.execute("SELECT State, IGST, CGST, SGST FROM SETTINGS LIMIT 1")
            gst_settings = mycursor.fetchone()
            company_state = gst_settings['State'].lower()
            igst_rate = gst_settings['IGST']
            cgst_rate = gst_settings['CGST']
            sgst_rate = gst_settings['SGST']
            
            # Simple check for inter/intra state for Sale_Amount calculation
            # Note: A more robust system would check the state of the *customer* address vs company state.
            # Here, we use the simple state match as implemented in gen_bill (company_state vs customer_address content).
            if company_state in address.lower():
                # Intra-state: CGST + SGST
                total_tax_rate = cgst_rate + sgst_rate
            else:
                # Inter-state: IGST
                total_tax_rate = igst_rate
            
            sale_amt = discounted_amount * (1 + total_tax_rate) # Calculate sale amount with GST
            sale_amt = round(sale_amt, 2)

            # Record the sale in the SALES table
            mycursor.execute("INSERT INTO SALES (Customer_Name, Products, QTY, Sale_Amount, Date_Of_Sale) VALUES (%s, %s, %s, %s, %s)", 
                             (custm_name, product, qty, sale_amt, today))
            mycon.commit()
            log_activity('NO ERROR - SALE RECORDED IN DATABASE with values : ' + f"Customer_Name : {custm_name}, Products : {product}, QTY : {qty}, Sale_Amount : ₹{sale_amt}, Date_Of_Sale : {today}")

            # Retrieve the BillNo for the newly created sale
            mycursor.execute(f"SELECT BillNo FROM SALES WHERE Customer_Name = %s AND Products = %s AND QTY = %s AND Sale_Amount = %s AND Date_Of_Sale = %s",
                             (custm_name, product, qty, sale_amt, today))
            bill_no = mycursor.fetchone()['BillNo']
            log_activity(f"BillNo for the sale recorded : {bill_no}")

            # Record profit
            profit = (discounted_amount / qty - cost_price) * qty
            profit = round(profit, 2)
            mycursor.execute("INSERT INTO PROFIT_AND_LOSS (BillNo, Product_Name, Net_Profit) VALUES (%s, %s, %s)", (bill_no, product, profit))
            log_activity(f"Recorded Net Profit of ₹{profit} for BillNo : {bill_no}")
            mycon.commit()

            gen_bill(bill_no, custm_name, address, product, qty, discount_rate)  # Generate PDF invoice
            log_activity("GST Invoice generated successfully for BillNo : " + str(bill_no))
            filename = f"GST_Invoice_{custm_name}_{bill_no}.pdf"

            # Open in default PDF viewer
            # Need to ensure the file path is correct for the OS
            filepath = os.path.abspath(filename)
            webbrowser.open(f"file:///{filepath}") 

            record_shipment_cli(bill_no, address, status)      # Record shipment info
            log_activity(f"Recorded Shipment info for BillNo : {bill_no}")

            # Update inventory
            mycursor.execute("UPDATE PRODUCTS SET Quantity = Quantity - %s WHERE Product_Name = %s",(qty, product))
            mycon.commit()
            log_activity(f"Inventory updated: {qty} units of '{product}' deducted.")
        else:
            log_activity("\nPurchase quantity exceeds available stock!")
            log_activity(f"Available quantity for '{product}': {qty_avl}")

    except Exception as e:
        log_activity(f"An error occurred in record_sale: {e}")

def record_shipment_cli(billno, address, status):
    """Internal function to record shipment data."""
    try:
        mycursor.execute("INSERT INTO TRANSPORT (BillNo, Address, Status) VALUES (%s, %s, %s)",(billno, address, status))
        mycon.commit()
        log_activity("Recorded Shipment info for the order with BillNo : " + str(billno))

    except Exception as e:
        log_activity(f"An error occurred while recording shipment: {e}")

def delete_sale_cli():
    """CLI function to delete a sale record by BillNo."""
    try :
        bill = input("Enter the BillNo of the sale record to be deleted : ")
        # Deleting from SALES will automatically delete from TRANSPORT due to ON DELETE CASCADE
        mycursor.execute("DELETE FROM SALES WHERE BillNo = %s", (bill,))
        # Also need to delete from PROFIT_AND_LOSS as it has BillNo but no cascade constraint defined in this script
        mycursor.execute("DELETE FROM PROFIT_AND_LOSS WHERE BillNo = %s", (bill,))
        mycon.commit()
        log_activity(f"Sale record with BillNo : {bill} successfully deleted from the table and associated tables.")
        
    except Exception as e:
        log_activity(f"An error occurred: {e}")

def search_sale_cli():
    """CLI function to search sale by BillNo."""
    try:
        billno = input("Enter the BillNo of the sale record to be searched : ")
        mycursor.execute("SELECT * FROM SALES WHERE BillNo = %s", (billno,))
        table = from_db_cursor(mycursor)
        if not table._rows :
            log_activity(f"No records found for BillNo : {billno}")
        else :
            log_activity(table)
            log_activity(f"Displayed record for BillNo : {billno}")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def sale_info_cli():
    """CLI function to view all sales info."""
    try:
        mycursor.execute("SELECT * FROM SALES")
        table = from_db_cursor(mycursor)
        if not table._rows :
            log_activity("No Sales Records Found")
        else :
            log_activity(table)
            log_activity("Displayed all sales records")

    except Exception as e:
        log_activity(f"An error occurred: {e}")
    
def shipping_info_cli():
    """CLI function to view all shipment info."""
    try:
        mycursor.execute("SELECT * FROM TRANSPORT")
        table = from_db_cursor(mycursor)
        if not table._rows :
            log_activity("No Shipment Records Found")
        else :
            log_activity(table)
            log_activity("Displayed all shipment records")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def user_info_cli():
    """CLI function to view all users info."""
    try:
        # Note: Added 'username' to the query to match updated schema
        mycursor.execute("SELECT UserID, Name, Department, Salary, username FROM USER")
        table = from_db_cursor(mycursor)
        log_activity(table)
        log_activity("Displayed all user records")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def product_info_cli():
    """CLI function to view all products info."""
    try:
        mycursor.execute("SELECT * FROM PRODUCTS")
        table = from_db_cursor(mycursor)
        log_activity(table)
        log_activity("Displayed all product records")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def search_ship_cli():
    """CLI function to search shipment by ShipmentID."""
    shipID = input("Enter the ShipmentID to be searched : ")

    try:
        mycursor.execute("SELECT * FROM TRANSPORT WHERE ShipmentID = %s", (shipID,))
        table = from_db_cursor(mycursor)
        if not table._rows:
            log_activity(f"No records found for the ShipmentID : {shipID}")
        else:
            log_activity(f"Found Record for the ShipmentID : {shipID}")
            log_activity(table)
            log_activity(f"Displayed record for ShipmentID : {shipID}")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def set_settings_cli(): 
    """CLI function to set the company details (to be used once)."""
    
    try:
        Company_Name = input("Enter Company Name : ")
        Company_ID = input("Enter Company ID : ") # Changed to string input as per DB schema
        GST_No = input("Enter GST Registration Number : ")
        Company_Address = input("Enter Company Address : ")
        state = input("Enter GST Registration State : ")
        mobno = input("Enter Company Mobile Number : ")
        email = input("Enter Company Email ID : ")
        igst = float(input("Enter IGST Rate (e.g., 0.18 for 18%): "))
        cgst = sgst = float(input("Enter CGST/SGST Rate (e.g., 0.09 for 9%): "))
        upi = input("Enter UPI ID : ")
        
        # Check if settings already exist
        mycursor.execute("SELECT COUNT(*) FROM SETTINGS")
        if mycursor.fetchone()['COUNT(*)'] > 0:
            log_activity("Settings already exist. Use the GUI or SQL UPDATE to modify.")
            return

        # Using parameterized query
        mycursor.execute("""
            INSERT INTO SETTINGS (CompanyName, CompanyID, GSTIN, Company_Address, State, Mobile_No, Email, UPI, IGST, CGST, SGST) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (Company_Name, Company_ID, GST_No, Company_Address, state, mobno, email, upi, igst, cgst, sgst))
        
        mycon.commit()
        log_activity("Settings Saved Successfully with values : " + f"Company Name : {Company_Name}, Company ID : {Company_ID}, GST Registration Number : {GST_No}, Company Address : {Company_Address}, GST Registration State : {state}, Company Mobile Number : {mobno}, Company Email ID : {email}, IGST Rate : {igst}, CGST/SGST Rate : {cgst}, UPI ID : {upi}")

    except ValueError:
        log_activity("Invalid input. Please enter numbers for ID/rates and check mobile number format.")
    except Exception as e:
        log_activity(f"An error occurred during setting settings: {e}")


def export_table_to_csv(table_name):
    """Exports data from a specified database table to a CSV file."""
    try:
        query = f"SELECT * FROM {table_name}"
        # pandas.read_sql is used to fetch data directly into a DataFrame
        df = pd.read_sql(query, mycon) 
        filename = f"{table_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        # Get the absolute path for clean logging
        filepath = os.path.abspath(filename)
        log_activity(f"Exported {table_name} data to {filepath}")
        return filename
    except Exception as e:
        log_activity(f"Error exporting data: {e}")
        return None
        
def gen_bill(bill_no, customer_name, customer_address, product, qty, discount_rate = 0.0):
    """Generate a GST invoice PDF for a sale."""
    
    try:
        # --- Fetch Company Info ---
        mycursor.execute("SELECT CompanyName, GSTIN, UPI, Company_Address, Mobile_No, Email FROM SETTINGS LIMIT 1")
        data = mycursor.fetchone()
        if not data:
            log_activity("Company settings not found. Cannot generate bill.")
            return

        company_name = data['CompanyName']
        gstin = data['GSTIN']
        upi = data['UPI']
        company_address = data['Company_Address']
        mobile_no = data['Mobile_No']
        email = data['Email']

        # --- Fetch Product Info ---
        mycursor.execute("SELECT MRP FROM PRODUCTS WHERE Product_Name = %s", (product,))
        mrp_data = mycursor.fetchone()
        if not mrp_data:
            log_activity(f"Product '{product}' not found. Cannot generate bill.")
            return
            
        mrp = mrp_data['MRP']
        log_activity(f"Product MRP fetched: ₹{mrp}")
        filename = f"GST_Invoice_{customer_name}_{bill_no}.pdf"
        logo_path = "logo.png"

        doc = SimpleDocTemplate(
            filename, pagesize=A4,
            rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20
        )
        styles = getSampleStyleSheet()
        elements = []

        # --- Custom Styles (as in original code) ---
        title_style = ParagraphStyle(
            'title_style', parent=styles['Title'],
            alignment=1, fontSize=22, leading=26, textColor=colors.HexColor("#1A237E")
        )
        header_style = ParagraphStyle(
            'header_style', parent=styles['Normal'],
            fontSize=11, leading=15, textColor=colors.HexColor("#263238")
        )
        bold_style = ParagraphStyle(
            'bold_style', parent=styles['Normal'],
            fontSize=11, leading=15, fontName='Helvetica-Bold', textColor=colors.HexColor("#1A237E")
        )
        cell_style = ParagraphStyle(
            'cell_style', parent=styles['Normal'],
            fontSize=10, leading=13, alignment=1
        )
        footer_style = ParagraphStyle(
            'footer_style', parent=styles['Italic'],
            alignment=1, fontSize=10, textColor=colors.HexColor("#607D8B")
        )

        # --- Header / Company Info ---
        header_table_data = []
        try:
            # Check if logo exists and add it
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=60, height=60)
                logo.hAlign = 'LEFT'
                header_table_data.append([logo, Paragraph(f"<b>{company_name}</b>", title_style)])
            else:
                header_table_data.append(["", Paragraph(f"<b>{company_name}</b>", title_style)])
        except Exception as e:
             # Fallback if image loading fails for other reasons
             log_activity(f"Error loading logo: {e}")
             header_table_data.append(["", Paragraph(f"<b>{company_name}</b>", title_style)])

        header_table = Table(header_table_data, colWidths=[70, 400])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ]))
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#1A237E")))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"GSTIN: <b>{gstin}</b>", header_style))
        elements.append(Paragraph(f"Address: {company_address}", header_style))
        elements.append(Paragraph(f"Phone: +91-{mobile_no} | Email: {email}", header_style))
        elements.append(Spacer(1, 10))

        # --- Invoice + Customer Info ---
        now = datetime.now().strftime("%d-%m-%Y %I:%M %p")
        info_table_data = [
            [Paragraph(f"<b>Bill No:</b> {bill_no}", header_style),
             Paragraph(f"<b>Date:</b> {now}", header_style)],
            [Paragraph(f"<b>Billed To:</b><br/>{customer_name}<br/>{customer_address}", header_style),
             Paragraph(f"<b>Payment Mode:</b> UPI", header_style)]
        ]
        info_table = Table(info_table_data, colWidths=[270, 200])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(info_table)
        elements.append(HRFlowable(width="100%", thickness=0.7, color=colors.HexColor("#1A237E")))
        elements.append(Spacer(1, 10))

        # --- Table Header ---
        data = [
            [
            Paragraph("<b>SL.No</b>", ParagraphStyle('cell_style', parent=cell_style, alignment=0)),
            Paragraph("<b>Description</b>", cell_style),
            Paragraph("<b>Qty</b>", cell_style),
            Paragraph("<b>Unit Price (Rs.)</b>", cell_style),
            Paragraph("<b>Amount (Rs.)</b>", cell_style)
            ]
        ]

        # --- Item Rows ---
        total = mrp * qty
        subtotal_before_discount = total

        # Single product row
        data.append([
        Paragraph("1.", cell_style),
        Paragraph(str(product), cell_style),
        Paragraph(str(qty), cell_style),
        Paragraph(f"{mrp:.2f}", cell_style),
        Paragraph(f"{total:.2f}", cell_style)
        ])

        # --- Discount Calculation ---
        discount_amount = subtotal_before_discount * discount_rate
        subtotal_after_discount = subtotal_before_discount - discount_amount

        data.append(["", "", "", Paragraph("Discount", cell_style),
                     Paragraph(f"{discount_amount:.2f}", cell_style)])
        
        data.append(["", "", "", Paragraph("Subtotal", cell_style),
                     Paragraph(f"{subtotal_after_discount:.2f}", cell_style)])
        
        # --- GST Calculation based on State ---
        mycursor.execute("SELECT State, IGST, CGST, SGST FROM SETTINGS LIMIT 1")
        gst_settings = mycursor.fetchone()
        company_state = gst_settings['State'].lower() # Convert to lower for case-insensitive check
        igst_rate = gst_settings['IGST']
        cgst_rate = gst_settings['CGST']
        sgst_rate = gst_settings['SGST']
        
        gst_amount = 0.0

        # Check if customer address contains the company's state (Intra-state)
        if company_state in customer_address.lower():
            # Intra-state: CGST + SGST
            cgst_amount = subtotal_after_discount * cgst_rate
            sgst_amount = subtotal_after_discount * sgst_rate
            gst_amount = cgst_amount + sgst_amount
            gst_label = f"CGST ({cgst_rate*100:.2f}%)"
            gst_label2 = f"SGST ({sgst_rate*100:.2f}%)"
            data.append(["", "", "", Paragraph(gst_label, cell_style),
                 Paragraph(f"{cgst_amount:.2f}", cell_style)])
            data.append(["", "", "", Paragraph(gst_label2, cell_style),
                 Paragraph(f"{sgst_amount:.2f}", cell_style)])
        else:
            # Inter-state: IGST
            gst_amount = subtotal_after_discount * igst_rate
            gst_label = f"IGST ({igst_rate*100:.2f}%)"
            data.append(["", "", "", Paragraph(gst_label, cell_style),
                 Paragraph(f"{gst_amount:.2f}", cell_style)])
                 
        grand_total = subtotal_after_discount + gst_amount
        # Final amount, rounded to 2 decimal places
        grand_total = round(grand_total, 2) 

        data.append(["", "", "", Paragraph("<b>Grand Total</b>", cell_style),
                     Paragraph(f"<b>{grand_total:.2f}</b>", cell_style)])

        # --- Table Styling (as in original code) ---
        table = Table(data, colWidths=[40, 220, 60, 80, 80])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1976D2")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#B0BEC5")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -3), [colors.whitesmoke, colors.HexColor("#E3F2FD")]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            # Bold for Grand Total Row
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#BBDEFB")),
        ])
        table.setStyle(style)
        elements.append(table)
        elements.append(Spacer(1, 18))

        # --- QR Code Payment ---
        qr_data = f"upi://pay?pa={upi}&am={grand_total:.2f}&cu=INR"
        qr = qrcode.make(qr_data)
        qr_buffer = io.BytesIO()
        qr.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        qr_img = Image(qr_buffer, width=90, height=90)
        qr_img.hAlign = 'LEFT'

        qr_table = Table([
            [qr_img, Paragraph(
                "<b>Scan to Pay (UPI)</b><br/>"
                f"Payee: {company_name}<br/>"
                f"UPI ID: <b>{upi}</b><br/>"
                f"Amount: <b>Rs.{grand_total:.2f}</b>", header_style
            )]
        ], colWidths=[100, 370])
        qr_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ]))
        elements.append(qr_table)
        elements.append(Spacer(1, 15))

        # --- Terms & Footer (as in original code) ---
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#B0BEC5")))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph("<b>Terms & Conditions:</b>", bold_style))
        elements.append(Paragraph(
            "1. Goods once sold will not be taken back.<br/>"
            "2. Warranty as per manufacturer's terms only.<br/>"
            "3. Please retain this invoice for future reference.",
            header_style
        ))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#B0BEC5")))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph("Thank you for your business!", footer_style))
        elements.append(Paragraph("This is a computer-generated invoice.", footer_style))

        # --- Build PDF ---
        doc.build(elements)
        log_activity(f"GST Invoice generated successfully: {filename}")

    except Exception as e:
        log_activity(f"Error generating invoice: {e}")

def remove_sale_cli():
    """CLI function to delete a sale record by BillNo."""
    try:
        bill = input("Enter the BillNo of the sale record to be deleted : ")
        # Deleting from SALES will cascade to TRANSPORT. Need to delete from PROFIT_AND_LOSS manually.
        mycursor.execute("DELETE FROM SALES WHERE BillNo = %s", (bill,))
        mycursor.execute("DELETE FROM PROFIT_AND_LOSS WHERE BillNo = %s", (bill,))
        mycon.commit()
        log_activity("Sale record and associated profit/shipment successfully deleted from the table for BillNo : " + str(bill))

    except Exception as e:
        log_activity(f"An error occurred: {e}")
    
def update_shipment_status_cli():
    """CLI function to update shipment status by ShipmentID."""
    try:
        ship_id = int(input("Enter ShipmentID to update status: "))
        new_status = input("Enter new status (e.g., In Transit, Delivered): ")
        mycursor.execute("UPDATE TRANSPORT SET Status = %s WHERE ShipmentID = %s", (new_status, ship_id))
        mycon.commit()
        log_activity("Shipment status updated successfully for ShipmentID : " + str(ship_id))

    except ValueError:
        log_activity("Invalid input. Please enter the correct data types (integer for ShipmentID).")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

# ---------- MANDATORY CHECKS BEFORE MAIN MENU ----------

def low_stock_alert_cli():
    """CLI function to alert for products with low stock (less than 10 units)."""
    mycursor.execute("SELECT Product_Name, Quantity FROM PRODUCTS WHERE Quantity < 10")
    # FIX: Using dictionary access instead of tuple indexing
    low_stock = mycursor.fetchall() 
    if low_stock:
        log_activity("\n Low Stock Alert:")
        for p in low_stock:
            # FIX: Use column names for dictionary cursor output
            log_activity(f"   - {p['Product_Name']}: {p['Quantity']} units left") 
        print()
    else:
        log_activity("No low stock items found.")

def checks_cli():
    """Ensure database and tables exist, and prompt for initial setup if needed."""
    
    # Must run before any settings checks
    create_init_db()

    low_stock_alert_cli()
    
    # Check settings
    mycursor.execute("SELECT COUNT(*) FROM SETTINGS")
    if mycursor.fetchone()['COUNT(*)'] == 0:
        print("No company settings found. Please set up your company details.")
        set_settings_cli()
        # Re-fetch company name after setup
        global company_name
        company_name = check_settings_filled()


    mycursor.execute("SELECT CompanyName FROM SETTINGS LIMIT 1")
    settings = mycursor.fetchone()
    # Check if settings were fetched (should be if set_settings_cli was called)
    if settings:
        print("="*70)
        print(f"\nWelcome to {settings['CompanyName']} Warehouse Management System (WMS)\n")
        print("="*70)
    else:
        print("="*70)
        print("\nWelcome to Warehouse Management System (WMS)\n")
        print("="*70)

    # Check for initial data
    mycursor.execute("SELECT COUNT(*) FROM USER")
    if mycursor.fetchone()['COUNT(*)'] == 0:
        print("No users found in the system. Please add a user to proceed.\n")
        # FIX: Call the wrapper function or the CLI function directly
        add_user_cli() 

    mycursor.execute("SELECT COUNT(*) FROM PRODUCTS")
    if mycursor.fetchone()['COUNT(*)'] == 0:
        print("No products found in the inventory. Please add products to proceed.\n")
        add_stock_cli()

def print_divider():
    print("\n" + "="*60)

def main_menu():
    """Main CLI menu loop."""

    while True:
        print("Main Menu:")
        print("1. User Management")
        print("2. Stock Management")
        print("3. Sales Management")
        print("4. Shipment Management")
        print("5. Database Management")
        # print("6. Analytics Dashboard") # CLI Analytics not fully implemented/used
        print("6. Exit") # Changed exit from 7 to 6 after removing analytics option

        try :
            choice = input("Enter your choice (1-6): ")

        except KeyboardInterrupt:
            print("\nExiting the program. Goodbye!")
            break

        if choice == '1':
            # --- USER MANAGEMENT ---
            while True:
                print("\nUser Management:")
                print("a. Add User")
                print("b. Remove User")
                print("c. Search User")
                print("d. Update User Info")
                print("e. View All Users")
                print("f. Back to Main Menu")

                ch = input("Enter your choice: ").lower()

                if ch == 'a':
                    # FIX: Call the correct function
                    add_user_cli()
                    print_divider()

                elif ch == 'b':
                    remove_user_cli()
                    print_divider()

                elif ch == 'c':
                    search_user_cli()
                    print_divider()

                elif ch == 'd':
                    update_user_cli()
                    print_divider()

                elif ch == 'e':
                    user_info_cli()
                    print_divider()

                elif ch == 'f':
                    break

                else:
                    print("Invalid Choice. Please try again.")
                    print_divider()
                    continue

                cont = input("Do you want to continue in User Management? (y/n): ")

                if cont.lower() != 'y':
                    print_divider()
                    break

        elif choice == '2':
            # --- PRODUCT MANAGEMENT ---
            while True:
                print("\nStock Management:")
                print("a. Add Product")
                print("b. Remove Product")
                print("c. Search Product")
                print("d. Update Product Info")
                print("e. View All Products")
                print("f. Low Stock Alert")
                print("g. Back to Main Menu")

                try : 
                    ch = input("Enter your choice: ").lower()
                except KeyboardInterrupt:
                    print("\nExiting the program. Goodbye!")
                    sys.exit(0)

                if ch == 'a':
                    add_stock_cli()
                    print_divider()

                elif ch == 'b':
                    remove_stock_cli()
                    print_divider()

                elif ch == 'c':
                    search_stock_cli()
                    print_divider()

                elif ch == 'd':
                    update_stock_cli()
                    print_divider()

                elif ch == 'e':
                    product_info_cli()
                    print_divider()
                
                elif ch == 'f':
                    low_stock_alert_cli()
                    print_divider()
                
                elif ch == 'g':
                    break

                else:
                    print("Invalid Choice. Please try again.")
                    print_divider()
                    continue

                cont = input("Do you want to continue in Stock Management? (y/n): ")
                if cont.lower() != 'y':
                    print_divider()
                    break

        elif choice == '3':
            # --- SALES MANAGEMENT ---
            while True:
                print("\nSales Management:")
                print("a. Record Sale")
                print("b. Delete Sale")
                print("c. View All Sales")
                print("d. Search Sale")
                print("e. Back to Main Menu")

                try : 
                    ch = input("Enter your choice: ").lower()
                except KeyboardInterrupt:
                    print("\nExiting the program. Goodbye!")
                    sys.exit(0)

                if ch == 'a':
                    try:
                        custm_name = input("Enter Customer Name: ")
                        address = input("Enter Customer Address: ")
                        product = input("Enter Product Name: ")
                        qty = int(input("Enter Quantity: "))
                        today = date.today()
                        status = input("Enter Shipment Status: ")
                        discount = float(input("Enter Discount Percentage (0-100, default 0): ") or 0.0) # Added optional discount input
                        record_sale(custm_name, address, product, qty, today, status, discount)
                    except ValueError:
                        log_activity("Invalid input for Quantity or Discount. Please enter numbers.")
                    except Exception as e:
                        log_activity(f"An error occurred during sale recording: {e}")

                    print_divider()

                elif ch == 'b':
                    delete_sale_cli()
                    print_divider()
                
                elif ch == 'c':
                    sale_info_cli()
                    print_divider()
                
                elif ch == 'd':
                    search_sale_cli()
                    print_divider()
                
                elif ch == 'e':
                    break

                else:
                    print("Invalid Choice. Please try again.")
                    print_divider()

                cont = input("Do you want to continue in Sales Management? (y/n): ")
                if cont.lower() != 'y':
                    print_divider()
                    break

        elif choice == '4':
            # --- SHIPMENT MANAGEMENT ---
            while True:
                print("\nShipment Management:")
                print("a. View all Shipments")
                print("b. Search Shipment")
                print("c. Update Shipment Status")
                print("d. Delete Shipment Record (Deletes Sale/Profit too)") # Clarified the action
                print("e. Back to Main Menu")


                try : 
                    ch = input("Enter your choice: ").lower()
                except KeyboardInterrupt:
                    print("\nExiting the program. Goodbye!")
                    sys.exit(0)

                if ch == 'a':
                    shipping_info_cli()
                    print_divider()

                elif ch == 'b':
                    search_ship_cli()
                    print_divider()

                elif ch == 'c':
                    update_shipment_status_cli()
                    print_divider()
                
                elif ch == 'd':
                    # Deleting sale will also delete shipment due to foreign key constraint
                    remove_sale_cli()
                    print_divider()
                
                elif ch == 'e':
                    break

                else:
                    print("Invalid Choice. Please try again.")
                    print_divider()
                    continue

                cont = input("Do you want to continue in Shipment Management? (y/n): ")
                if cont.lower() != 'y':
                    print_divider()
                    break

        elif choice == '5':
            # ---- DATABASE MANAGEMENT ---- 
            while True:
                print("\nDatabase Management:")
                print("a. Delete Entire Database (All Tables)")
                print("b. Export Table to CSV")
                print("c. Back to Main Menu")

                try : 
                    ch = input("Enter your choice: ").lower()
                except KeyboardInterrupt:
                    print("\nExiting the program. Goodbye!")
                    sys.exit(0)

                if ch == 'a':
                    delete_db_cli()
                    print_divider()
                    print("Exiting the program as the database has been deleted.")
                    sys.exit(0)

                elif ch == 'b':
                    table_name = input("Enter the table name to export: ")
                    export_table_to_csv(table_name)
                    print_divider()

                elif ch == 'c':
                    break

                else:
                    print("Invalid Choice. Please try again.")
                    print_divider()
                    continue

                cont = input("Do you want to continue in Database Management? (y/n): ")
                if cont.lower() != 'y':
                    print_divider()
                    break
        
        elif choice == '6':
            print("Exiting the program. Goodbye!")
            print("=" * 60)
            break
        
        # elif choice == '6': # Original '6. Analytics Dashboard' - currently removed
        #    print("Analytics Dashboard not yet implemented in CLI.")
        #    print_divider()
        #    continue

        else:
            print("Invalid choice. Please try again.")
            print_divider()

# ---------- FLASK APP (GUI) ----------

app = Flask(__name__)
app.secret_key = "egweg4h4r4h654re65j465er562rb11rg6465w" 

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/register', methods=["GET", "POST"])
def register():
    """Route for user registration (for login table)."""
    # FIX: Use the global company_name
    global company_name
    if request.method == "POST":
        usrname = request.form.get('username').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        department = "Default" # Default department for new registrations (can be changed later)

        if not usrname or not password or not confirm_password:
            return render_template("register.html", error="Please fill in all fields", company_name=company_name)
        
        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match", company_name=company_name)

        mycursor.execute('SELECT * FROM LOGIN WHERE Username = %s', (usrname,))
        existing_user = mycursor.fetchone()
        if existing_user:
            return render_template("register.html", error="Username already exists. Try a different one.", company_name=company_name)

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert a placeholder into the USER table first to get a UserID
        mycursor.execute("INSERT INTO USER (Name, username, Department, Salary) VALUES (%s, %s, %s, %s)", 
                         (usrname, usrname, department, 0))
        mycon.commit()
        
        # Retrieve the generated UserID
        mycursor.execute("SELECT UserID FROM USER WHERE username = %s", (usrname,))
        user_id = mycursor.fetchone()['UserID']

        # Insert into LOGIN table, linking to the new UserID
        mycursor.execute('INSERT INTO LOGIN (UserID, Username, Password, Department) VALUES (%s, %s, %s, %s)', 
                         (user_id, usrname, hashed_pw, department))
        mycon.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template("register.html", company_name=company_name)

@app.route('/login', methods=["GET", "POST"])
def login():
    """Route for user login."""
    # FIX: Use the global company_name
    global company_name
    if request.method == "POST":
        usrname = request.form.get('username')
        password = request.form.get('password')

        mycursor.execute('SELECT Password, UserID, Department FROM LOGIN WHERE Username = %s', (usrname,))
        record = mycursor.fetchone()

        if record:
            stored_hash = record['Password'].encode('utf-8') if isinstance(record['Password'], str) else record['Password']
            
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                session['username'] = usrname
                session['user_id'] = record['UserID'] # Store UserID in session
                session['department'] = record['Department'] # Store Department in session
                return redirect(url_for("home"))
            else:
                return render_template("login.html", error="Invalid password", company_name=company_name)
        else:
            return render_template("login.html", error="User not found", company_name=company_name)

    return render_template("login.html", company_name=company_name)

@app.route('/logout')
def logout():
    """Route to log out and clear session."""
    session.pop('username', None)
    session.pop('user_id', None)
    session.pop('department', None)
    return redirect(url_for('login'))

def login_required(f):
    """Decorator to ensure user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def home():
    """Home dashboard route."""
    global company_name
    create_init_db()
    check = check_settings_filled()
    if check == "ADD COMPANY NAME IN SETTINGS":
        # Redirect to settings if company name is not set
        flash("Please complete your company settings first.", "warning")
        return redirect(url_for('settings')) 
    
    # Update global company_name after check
    company_name = check
    
    mycursor.execute("SELECT COUNT(UserID) FROM USER")
    no_of_users = mycursor.fetchone()['COUNT(UserID)']
    mycursor.execute("SELECT COUNT(ProductID) FROM PRODUCTS")
    no_of_items = mycursor.fetchone()['COUNT(ProductID)']
    mycursor.execute("SELECT SUM(Sale_Amount) FROM SALES")
    revenue = mycursor.fetchone()['SUM(Sale_Amount)'] or 0
    mycursor.execute("SELECT COUNT(ShipmentID) FROM TRANSPORT")
    no_of_ships = mycursor.fetchone()['COUNT(ShipmentID)'] or 0
    mycursor.execute("show tables")
    tables = mycursor.fetchall()
    mycursor.execute("SELECT SUM(Net_Profit) FROM PROFIT_AND_LOSS")
    profit = mycursor.fetchone()['SUM(Net_Profit)'] or 0
    return render_template('index.html', no_of_users=no_of_users, no_of_items=no_of_items, revenue=revenue, no_of_ships=no_of_ships, company_name=company_name, db_data=tables,no_of_tables=len(tables), profit=profit, username=session.get('username'))

@app.route('/sales', methods=['GET', 'POST'])
@login_required
def sales():
    """Sales view route."""
    global company_name
    mycursor.execute("SELECT SUM(Sale_Amount) FROM SALES")
    total_sale_amount = mycursor.fetchone()['SUM(Sale_Amount)'] or 0
    mycursor.execute("SELECT * FROM SALES ORDER BY BillNo DESC")
    sales_data = mycursor.fetchall()
    count = len(sales_data)
    return render_template('sales.html', company_name=company_name, total_sale_amount=total_sale_amount, sales_data=sales_data, count=count, username=session.get('username'))

@app.route('/add_order', methods=['GET', 'POST'])
@login_required
def add_order():
    """Route to add a new sale order."""
    global company_name
    today = date.today().strftime("%Y-%m-%d")
    mycursor.execute("SELECT Product_Name FROM PRODUCTS")
    products = mycursor.fetchall()
    success = False

    if request.method == 'POST':
        try:
            custm_name = request.form['customerName']
            address = request.form['customerAddress']
            product = request.form['productName']
            qty = int(request.form['quantity'])
            status = request.form['status']
            sale_date = request.form['date']
            discount = float(request.form['discount'] or 0.0) # Ensure discount is handled correctly
            
            # Check stock availability
            mycursor.execute("SELECT Quantity FROM PRODUCTS WHERE Product_Name = %s", (product,))
            stock = mycursor.fetchone()
            if stock and qty > stock['Quantity']:
                flash(f"❌ Error: Purchase quantity ({qty}) exceeds available stock ({stock['Quantity']}) for {product}.", "error")
                return render_template('add_order.html', products=products, success=False, company_name=company_name, today=sale_date, username=session.get('username'))
            
            if not stock:
                flash(f"❌ Error: Product '{product}' not found in inventory.", "error")
                return render_template('add_order.html', products=products, success=False, company_name=company_name, today=sale_date, username=session.get('username'))
            
            # Record the sale using the existing function
            record_sale(custm_name, address, product, qty, sale_date, status, discount)
            flash("✅ Sale recorded and Invoice generated successfully!", "success")
            success = True
        
        except ValueError:
            flash("❌ Error: Invalid input for Quantity or Discount. Please ensure they are numbers.", "error")
        except Exception as e:
            flash(f"❌ An unexpected error occurred: {e}", "error")

        # Return a clean GET redirect after POST to prevent resubmission
        return redirect(url_for('add_order')) 

    # For GET request
    return render_template('add_order.html', products=products, success=success, company_name=company_name, company_logo="/static/logo.png", today=today, username=session.get('username'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Route for viewing and updating company settings."""
    global company_name
    mycursor.execute("SELECT COUNT(*) AS count FROM SETTINGS")
    result = mycursor.fetchone()
    has_settings = result['count'] > 0

    if request.method == 'POST':
        try:
            company_name = request.form['CompanyName']
            company_id = request.form['CompanyID']
            gstin = request.form['GSTIN']
            company_address = request.form['Company_Address']
            state = request.form['State']
            mobile_no = request.form['Mobile_No']
            email = request.form['Email']
            upi = request.form['UPI']
            igst = float(request.form['IGST'])
            cgst = float(request.form['CGST'])
            sgst = float(request.form['SGST'])
        
        except ValueError:
            flash("❌ Error: GST rates must be valid numbers.", "error")
            return redirect(url_for('settings'))

        if has_settings:
            mycursor.execute("""
                UPDATE SETTINGS 
                SET CompanyName=%s, CompanyID=%s, GSTIN=%s, Company_Address=%s, 
                    State=%s, Mobile_No=%s, Email=%s, UPI=%s, IGST=%s, CGST=%s, SGST=%s
            """, (company_name, company_id, gstin, company_address, state, mobile_no, email, upi, igst, cgst, sgst))
        else:
            mycursor.execute("""
                INSERT INTO SETTINGS (CompanyName, CompanyID, GSTIN, Company_Address, State, Mobile_No, Email, UPI, IGST, CGST, SGST)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (company_name, company_id, gstin, company_address, state, mobile_no, email, upi, igst, cgst, sgst))
            log_activity("Inserted values into settings")

        mycon.commit()
        # Update global variable after successful save
        company_name = check_settings_filled()
        flash("✅ Settings saved successfully!", "success")
        return redirect(url_for('home'))

    if has_settings:
        mycursor.execute("SELECT * FROM SETTINGS LIMIT 1")
        settings = mycursor.fetchone()
        return render_template('settings.html', settings=settings, company_name=company_name, username=session.get('username'))
    
    else:
        # Initial setup page
        return render_template('settings_setup.html', company_name="WMS Setup", username=session.get('username'))

@app.route("/profit_loss")
@login_required
def p_and_l():
    """Profit and Loss report route."""
    global company_name
    mycursor.execute("SELECT * FROM PROFIT_AND_LOSS ORDER BY BillNo DESC")
    data = mycursor.fetchall()
    total_net_profit = sum(row['Net_Profit'] for row in data)
    # Using BillNo (int) and Product_Name (string) for unique counts
    total_bills = len(set(row['BillNo'] for row in data))
    total_products = len(set(row['Product_Name'] for row in data))
    return render_template(
        'Profit_and_loss.html',
        company_name=company_name,
        profit_loss_data=data,
        total_net_profit=total_net_profit,
        total_bills=total_bills,
        total_products=total_products, 
        username=session.get('username')
        )

@app.route('/inventory')
@login_required
def inventory():
    """Inventory/Products management route."""
    global company_name
    mycursor.execute("SELECT * FROM PRODUCTS ORDER BY ProductID DESC")
    products_data = mycursor.fetchall()
    count = len(products_data)
    total_products = sum(p['Quantity'] for p in products_data)
    total_value = int(sum((p['MRP'] or 0) * (p['Quantity'] or 0) for p in products_data)) # Handle potential None/null values
    return render_template('inventory.html', company_name=company_name, products_data=products_data, count=count, total_products=total_products, total_value=total_value, username=session.get('username'))

@app.route("/add_product", methods=["POST"])
@login_required
def add_product():
    """Route to add a new product."""
    if request.method == "POST":
        try:
            name = request.form['product_name']
            cp = float(request.form['cost_price'])
            mrp = float(request.form['mrp'])
            qty = int(request.form["quantity"])
            # ProductID is AUTO_INCREMENT
            mycursor.execute("INSERT INTO PRODUCTS (Product_Name, Cost_Price, MRP, Quantity) VALUES (%s, %s, %s, %s)", (name, cp, mrp, qty))
            mycon.commit()
            log_activity(f"Added new product : Product Name : {name}, Cost_price : {cp}, MRP : {mrp}, Quantity : {qty}")
            flash("✅ Product added successfully!", "success")
        except ValueError:
             flash("❌ Error: Please ensure Cost Price, MRP, and Quantity are valid numbers.", "error")
        except Exception as e:
            flash(f"❌ Error adding product: {e}", "error")
            
        return redirect(url_for("inventory"))
    
@app.route('/export_inventory')
@login_required
def export_inventory(): 
    """Route to export products table to CSV."""
    filename = export_table_to_csv("PRODUCTS")
    if filename:
        log_activity("Exported Products Info")
        return send_file(filename, as_attachment=True)
        
    else:
        return redirect(url_for('inventory'))

@app.route('/delete_product/<int:id>')
@login_required
def delete_product(id):
    """Route to delete a product by ProductID."""
    mycursor.execute("DELETE FROM PRODUCTS WHERE PRODUCTID=%s", (id,))
    mycon.commit()
    flash("✅ Product deleted successfully!", "success")
    return redirect(url_for('inventory'))

@app.route('/edit_product', methods=['POST'])
@login_required
def edit_inventory():
    """Route to edit a product's details."""
    try:
        productid = request.form['product_id']
        product_name = request.form['product_name']
        cost_price = float(request.form['cost_price'])
        mrp = float(request.form['mrp'])
        quantity = int(request.form['quantity'])
        mycursor.execute("""
            UPDATE PRODUCTS
            SET product_name=%s, cost_price=%s, mrp=%s, quantity=%s
            WHERE productid=%s
        """, (product_name, cost_price, mrp, quantity, productid))

        mycon.commit()
        flash("✅ Product updated successfully!", "success")
    except ValueError:
        flash("❌ Error: Please ensure Cost Price, MRP, and Quantity are valid numbers.", "error")
    except Exception as e:
        flash(f"❌ Error updating product: {e}", "error")
        
    return redirect(url_for('inventory'))

@app.route('/export_profit_loss')
@login_required
def export_profit_loss():
    """Route to export profit and loss table to CSV."""
    filename = export_table_to_csv("PROFIT_AND_LOSS")
    if filename:
        return send_file(filename, as_attachment=True)
    else:
        flash("❌ Error exporting profit & loss data.", "error")
        return redirect(url_for('p_and_l'))

@app.route('/edit_shipment', methods=['POST'])
@login_required
def edit_shipment():
    """Route to edit shipment details."""
    try:
        shipment_id = request.form['shipment_id']
        bill_no = request.form['bill_no']
        address = request.form['address']
        status = request.form['status']

        mycursor.execute("""
            UPDATE TRANSPORT
            SET BillNo=%s, Address=%s, Status=%s
            WHERE ShipmentID=%s
        """, (bill_no, address, status, shipment_id))

        mycon.commit()
        flash("✅ Shipment updated successfully!", "success")
    except Exception as e:
        flash(f"❌ Error updating shipment: {e}", "error")
        
    return redirect(url_for('shipments'))

@app.route('/delete_shipment/<int:id>')
@login_required
def delete_shipment(id):
    """Route to delete a shipment by ShipmentID. (Also deletes Sale/Profit)."""
    try:
        mycursor.execute("SELECT BillNo FROM TRANSPORT WHERE ShipmentID=%s", (id,))
        billno_data = mycursor.fetchone()
        
        if billno_data:
            billno = int(billno_data['BillNo'])
            # Since TRANSPORT has ON DELETE CASCADE from SALES, we only need to delete the SALE.
            # But the original code deletes TRANSPORT first, then PROFIT_AND_LOSS. Let's stick to the original intent:
            # Delete from TRANSPORT (which might fail if other constraints exist, but here it's fine)
            mycursor.execute("DELETE FROM TRANSPORT WHERE ShipmentID=%s", (id,))
            # Manually delete from PROFIT_AND_LOSS
            mycursor.execute("DELETE FROM PROFIT_AND_LOSS WHERE BillNo=%s", (billno,))
            # Manually delete from SALES (if not auto-cascaded, safer to delete the parent)
            mycursor.execute("DELETE FROM SALES WHERE BillNo=%s", (billno,))
            mycon.commit()
            flash("✅ Shipment, Sale, and Profit record deleted successfully!", "success")
        else:
            flash("❌ Error: Shipment not found.", "error")

    except Exception as e:
        flash(f"❌ Error deleting shipment: {e}", "error")

    return redirect(url_for('shipments'))

@app.route('/export_shipments')
@login_required
def export_shipments():
    """Route to export transport table to CSV."""
    filename = export_table_to_csv("TRANSPORT")
    if filename:
        return send_file(filename, as_attachment=True)
    else:
        flash("❌ Error exporting shipments data.", "error")
        return "Error exporting shipments", 500
    
@app.route("/add_user", methods=["POST"])
@login_required
def add_user():
    """Route to add a new user (for USER table)."""
    if request.method == "POST":
        try:
            name = request.form['name']
            dept = request.form['department']
            sal = int(request.form['salary'])
            username = name.lower().replace(" ", "") # Generate a default username

            # Insert into USER table. UserID is auto-generated.
            mycursor.execute("INSERT INTO USER (Name, username, Department, Salary) VALUES (%s, %s, %s, %s)", (name, username, dept, sal))
            mycon.commit()
            log_activity(f"Added new user: Name : {name}, Department : {dept}, Salary : {sal}")
            flash("✅ User added successfully!", "success")
        except ValueError:
            flash("❌ Error: Salary must be a number.", "error")
        except ms.IntegrityError:
            flash("❌ Error: Username already exists. Please update the user manually.", "error")
        except Exception as e:
             flash(f"❌ Error adding user: {e}", "error")
             
        return redirect(url_for("users_webpage"))

@app.route('/shipments')
@login_required
def shipments():
    """Shipments tracking route."""
    global company_name
    mycursor.execute("SELECT * FROM TRANSPORT ORDER BY ShipmentID DESC")
    shipments_data = mycursor.fetchall()
    # Summary cards
    total_shipments = len(shipments_data)
    # FIX: Use .lower() for robust status comparison
    pending = len([s for s in shipments_data if s['Status'] and s['Status'].lower() == 'pending'])
    delivered = len([s for s in shipments_data if s['Status'] and s['Status'].lower() == 'delivered'])
    
    return render_template(
        'shipments.html',
        company_name=company_name,
        shipments_data=shipments_data,
        total_shipments=total_shipments,
        pending=pending,
        delivered=delivered, username=session.get('username'))

# The get_bill_details route seems to refer to non-existent tables 'bills' and 'bill_items'
# I'll keep the function signature but comment out the inner logic as it cannot be fixed 
# without knowing the actual schema or intent to refactor the database.
# @app.route('/get_bill_details/<int:bill_no>')
# def get_bill_details(bill_no):
#     try:
#         # This logic seems to refer to non-existent 'bills' and 'bill_items' tables.
#         # Assuming the intent was to fetch from SALES and PROFIT_AND_LOSS
#         mycursor.execute("SELECT * FROM SALES WHERE BillNo = %s", (bill_no,))
#         bill = mycursor.fetchone()
        
#         mycursor.execute("SELECT Net_Profit FROM PROFIT_AND_LOSS WHERE BillNo = %s", (bill_no,))
#         profit_data = mycursor.fetchone()

#         if not bill:
#             return jsonify({"error": "Bill not found"}), 404

#         details = {
#             "Bill No": bill["BillNo"],
#             "Customer Name": bill["Customer_Name"],
#             "Date": str(bill["Date_Of_Sale"]),
#             "Total Amount": f"₹ {bill['Sale_Amount']:.2f}",
#             "Net Profit": f"₹ {profit_data['Net_Profit']:.2f}" if profit_data else "N/A",
#             "Product": bill["Products"],
#             "Quantity": bill["QTY"]
#         }

#         return jsonify(details)

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
    
@app.route('/users')
@login_required
def users_webpage():
    """Users management route."""
    global company_name
    mycursor.execute("SELECT * FROM USER ORDER BY UserID DESC")
    users_data = mycursor.fetchall()
    count = len(users_data)
    return render_template('users.html', company_name=company_name, users_data=users_data, count=count, username=session.get('username'))

@app.route('/edit_users', methods=['POST'])
@login_required
def edit_users():
    """Route to edit user details."""
    try:
        user_id = request.form['user_id']
        name = request.form['name']
        department = request.form['department']
        salary = int(request.form['salary'])
        username = request.form.get('username') # Added username to update logic

        mycursor.execute("""
            UPDATE USER
            SET Name=%s, username=%s, Department=%s, Salary=%s
            WHERE UserID=%s
        """, (name, username, department, salary, user_id))
        
        # Also update the LOGIN table's Department and Username if they match
        mycursor.execute("""
            UPDATE LOGIN
            SET Department=%s, Username=%s
            WHERE UserID=%s
        """, (department, username, user_id))

        log_activity(f"Updated UserID : {user_id} with Name : {name}, Username : {username}, Department : {department}, Salary : {salary}")
        mycon.commit()
        flash("✅ User updated successfully!", "success")
    except ValueError:
        flash("❌ Error: Salary must be a valid number.", "error")
    except Exception as e:
        flash(f"❌ Error updating user: {e}", "error")
        
    return redirect(url_for('users_webpage'))

@app.route('/delete_user/<int:id>')
@login_required
def delete_user(id):
    """Route to delete a user by UserID. (Also deletes LOGIN record via CASCADE)."""
    # Delete from USER will cascade to LOGIN (ON DELETE CASCADE)
    mycursor.execute("DELETE FROM USER WHERE UserID=%s", (id,))
    mycon.commit()
    flash("✅ User and associated login record deleted successfully!", "success")
    return redirect(url_for('users_webpage'))

@app.route('/dbm', methods=['GET', 'POST'])
@login_required
def dbms():
    """Database management route."""
    global company_name
    mycursor.execute("show tables")
    tables = [t[f'Tables_in_{mycon.database}'] for t in mycursor.fetchall()] # Extract table names
    # Convert list of table names back to list of dicts for template compatibility if needed
    db_data = [{'table_name': t} for t in tables] 
    return render_template('dbms.html', db_data=db_data, company_name=company_name, no_of_tables=len(tables), username=session.get('username'))

@app.route('/delete_table/<table_name>')
@login_required
def delete_table(table_name):
    cursor = new_cursor()
    """Safely drop a table and refresh the DB list without crashing the app."""
    try:

        # Temporarily disable FK constraints to avoid dependency crashes
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

        # Use backticks to handle reserved names
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        mycon.commit()

        log_activity(f"Deleted table: {table_name}")

    except Exception as e:
        mycon.rollback()
        log_activity(f"Error deleting table {table_name}: {e}")

    finally:
        cursor.close()

    # Use redirect AFTER cursor is safely closed
    return redirect(url_for('dbms'))

@app.route('/view_invoice/<int:bill_no>')
@login_required
def view_invoice(bill_no):
    """Open the saved PDF invoice for a specific BillNo."""
    try:
        # Fetch customer name for filename
        mycursor.execute("SELECT Customer_Name FROM SALES WHERE BillNo = %s", (bill_no,))
        record = mycursor.fetchone()

        if not record:
            flash("❌ Invoice not found for this BillNo.", "error")
            return redirect(url_for('sales'))

        customer_name = record['Customer_Name']
        filename = f"GST_Invoice_{customer_name}_{bill_no}.pdf"
        file_path = os.path.abspath(filename)

        if not os.path.exists(file_path):
            flash("❌ PDF not found. It may not have been generated yet.", "error")
            return redirect(url_for('sales'))

        # Send the file to the browser to view/download
        return send_file(file_path, as_attachment=False)

    except Exception as e:
        flash(f"❌ Error opening invoice: {e}", "error")
        return redirect(url_for('sales'))
    
if __name__ == '__main__':
    # Initial setup to ensure database/tables/settings are ready
    create_init_db()
    # FIX: Update global company_name before Flask runs
    company_name = check_settings_filled()

    # The original CLI/GUI choice logic is commented out, so it defaults to GUI.
    # To run CLI instead, uncomment the following block and comment out the app.run(debug=True)
    
    # userinput = 2 # Default to GUI for the provided code
    # try:
    #     userinput = int(input('Enter 1 for CLI or 2 for GUI: '))
    # except ValueError:
    #     print("Invalid choice. Defaulting to GUI.")
    # except KeyboardInterrupt:
    #     print("\nExiting.")
    #     sys.exit(0)
    
    # if userinput == 1:
    #     checks_cli() # Run CLI checks/setup
    #     main_menu()
    # elif userinput == 2:
    #     webbrowser.open("http://127.0.0.1:5000/login") # Open login page
    app.run(debug=True)
    # else:
    #     print("Invalid Choice Entered")