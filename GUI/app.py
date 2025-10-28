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
from flask import Flask, render_template, request, redirect, send_file, url_for, flash

# Establish connection to MySQL database

mycon = ms.connect(user = "root", passwd = "mysql", host = "localhost", use_pure=True)
mycursor = mycon.cursor(dictionary=True, buffered=True)
mycursor.execute("CREATE DATABASE IF NOT EXISTS WMS")
mycursor.execute("USE WMS")
LOG_FILE = "activity_log.txt"
mycursor.execute("SELECT CompanyName FROM SETTINGS")
company_name = mycursor.fetchone()['CompanyName']

#--------------- User Management ----------------

def add_user():
    
    try : 
        userid = input("Enter UserID: ")
        name = input("Enter Username: ")
        dept = input("Enter Department: ")
        sal = int(input("Enter Salary: "))
    
        mycursor.execute(f"INSERT INTO USER (UserID, Name, Department, Salary) VALUES ({userid}, '{name}', '{dept}', {sal})")
        mycon.commit()
        log_activity("Entry successfully added to the table")

    except ms.IntegrityError:
        log_activity(f"UserID : {userid} already exists. Please use a unique UserID.")

    except ValueError: 
        log_activity("Invalid input. Please enter the correct data types.")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def remove_user():
    
    try :
        delete = input("Enter UserID of the entry to be deleted : ")
        mycursor.execute(f"DELETE FROM USER WHERE UserID = {delete}")
        mycon.commit()
        log_activity(f"Entry successfully deleted from the table for userID : {delete}")
        
    except Exception as e:
        log_activity(f"An error occurred: {e}")

def search_user():
    
    try : 
        user = input("Enter UserID of the user to be found: ")
        mycursor.execute(f"select * from user where UserID = {user}")
        table = from_db_cursor(mycursor)
        if not table._rows :
            log_activity(f"No records found for UserID : {user}")
        else :
            log_activity(table)

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def update_user():
    
    try :
        column = input("Enter Column where the value is to be changed: ")
        value1 = input("Enter UserID of the entry to be updated: ")
        value2 = input("Enter Updated value: ")
        mycursor.execute(f"UPDATE USER SET {column} = '{value2}' WHERE UserID = {value1}")
        mycon.commit()
        log_activity(f"Value of column : {column} updated to {value2} successfully updated for UserID : {value1}")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

#--------------- Product Management ----------------

def add_stock():

    try : 
        pdtid = input("Enter ProductID: ")
        name = input("Enter product name: ")
        cost = int(input("Enter cost price of product: "))
        mrp = int(input("Enter MRP of product: "))
        qty = int(input("Enter quantity of product: "))
    
        mycursor.execute(f"INSERT INTO PRODUCTS (ProductID, Product_Name, Cost_Price, MRP, Quantity) VALUES ({pdtid}, '{name}', {cost}, {mrp}, {qty})")
        mycon.commit()
        log_activity(f"Record successfully added for ProductID : {pdtid}, Product Name : {name}, Cost Price : {cost}, MRP : {mrp}, Quantity : {qty}")

    except ms.IntegrityError:
        log_activity(f"ProductID : {pdtid} already exists. Please use a unique ProductID.")

    except ValueError: 
        log_activity("Invalid input. Please enter the correct data types.")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def remove_stock():
    
    try :
        value = input("Enter the ProductID of the entry to be deleted: ")
        mycursor.execute("delete from Products where ProductID = %s",(value,))
        mycon.commit()
        log_activity(f"ProductID : {value} successfully deleted from the table Products")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def search_stock():
    
    try:
        product = input("Enter the ProductID of the entry to be dislayed: ")
        mycursor.execute(f"SELECT * FROM Products WHERE ProductID = {product}")
        table = from_db_cursor(mycursor)
        if not table._rows :
            log_activity(f"No records found for ProductID: {product}")
        else :
            log_activity(table)

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def update_stock():
    
    try :
        column = input("Enter Column where the value is to be changed: ")
        value1 = input("Enter ProductID of the entry to be updated: ")
        value2 = input("Enter updated value: ")
        mycursor.execute(f"update Products set {column} = {value2} where ProductID = {value1}")
        mycon.commit()
        log_activity(f"Value of {column} updated to {value2} for the ProductID : {value1} successfully")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def create_init_db():
    
    # Create all required tables if they do not exist
    try : 
        init_tables=["CREATE TABLE IF NOT EXISTS USER(UserID int PRIMARY KEY AUTO_INCREMENT, Name varchar(50), Department varchar(30), Salary int)",
                    "CREATE TABLE IF NOT EXISTS PRODUCTS(ProductID int PRIMARY KEY AUTO_INCREMENT, Product_Name varchar(50), Cost_Price float, MRP float, Quantity int)",
                    "CREATE TABLE IF NOT EXISTS SALES(BillNo int PRIMARY KEY AUTO_INCREMENT, Customer_Name varchar(50), Products varchar(300), QTY int, Sale_Amount float, Date_Of_Sale date)",
                    "CREATE TABLE IF NOT EXISTS TRANSPORT(ShipmentID int PRIMARY KEY AUTO_INCREMENT, BillNo int, Address varchar(300), Status varchar(30), FOREIGN KEY (BillNo) REFERENCES SALES(BillNo) ON DELETE CASCADE)",
                    "CREATE TABLE IF NOT EXISTS PROFIT_AND_LOSS(BillNo int, Product_Name varchar(50), Net_Profit float)",
                    "CREATE TABLE IF NOT EXISTS SETTINGS(CompanyName varchar(255), CompanyID int, GSTIN char(30), Company_Address varchar(255), State varchar(255), Mobile_No BIGINT, Email varchar(255), UPI varchar(40), IGST float, CGST float, SGST float)"]
        for i in init_tables:
            mycursor.execute(i)
        mycon.commit()
        log_activity("Initialized USER, PRODUCTS, SALES, TRANSPORT, PROFIT_AND_LOSS and SETTINGS tables in the database")

    except Exception as e:
        log_activity(f"An error occurred during initialization: {e}")

def delete_db():
    
    # Delete all tables from the database (irreversible)
    
    try : 
        log_activity("WARNING! : This process is irreversible, All your data will be deleted permanently!!")
        usr_confirm = input("Do you want to continue (Y/N) : ")
        tables = ["TRANSPORT", "SALES", "PRODUCTS", "USER", "PROFIT_AND_LOSS", "SETTINGS"]
        if usr_confirm in "Yy":
            for i in tables:
                mycursor.execute(f"DROP TABLE IF EXISTS {i}")
            log_activity("Deleted TRANSPORT, SALES, PRODUCTS, USER, PROFIT_AND_LOSS and SETTINGS tables from the database")

        elif usr_confirm in "Nn" : 
            log_activity("Operation Canceled by the user")
    
        else :
            log_activity("Invalid Choice entered by the user")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def record_sale(custm_name, address, product, qty, today, status):
    
    # Record a sale, update inventory, generate bill, and record shipment
    
    try:
        mycursor.execute(f"SELECT MRP, Quantity FROM PRODUCTS WHERE Product_Name = '{product}'")
        output = mycursor.fetchall()
        mrp = float(output[0]['MRP'])
        qty_avl = float(output[0]['Quantity'])
        log_activity(f"MRP of {product} : ₹{mrp}")

        if qty <= qty_avl:
            log_activity('NO ERROR - SUFFICIENT STOCK AVAILABLE')
            sale_amt = mrp * qty * 1.18  # Calculate sale amount with GST
            sale_amt = round(sale_amt, 2)

            # Record the sale in the SALES table

            mycursor.execute(f"INSERT INTO SALES (Customer_Name, Products, QTY, Sale_Amount, Date_Of_Sale) VALUES ('{custm_name}', '{product}', {qty}, {sale_amt}, '{today}')")
            mycon.commit()
            log_activity('NO ERROR - SALE RECORDED IN DATABASE with values : ' + f"Customer_Name : {custm_name}, Products : {product}, QTY : {qty}, Sale_Amount : ₹{sale_amt}, Date_Of_Sale : {today}")

            # Retrieve the BillNo for the newly created sale
            mycursor.execute(f"SELECT BillNo FROM SALES WHERE Customer_Name = '{custm_name}' AND Products = '{product}' AND QTY = {qty} AND Sale_Amount = {sale_amt} AND Date_Of_Sale = '{today}'")
            bill_no = mycursor.fetchone()['BillNo']
            log_activity(f"BillNo for the sale recorded : {bill_no}")

            # Record profit
            mycursor.execute("SELECT Cost_Price FROM PRODUCTS WHERE Product_Name = %s", (product,))
            cost_price = mycursor.fetchone()['Cost_Price']
            profit = (mrp - cost_price) * qty
            mycursor.execute("INSERT INTO PROFIT_AND_LOSS VALUES (%s, %s, %s)", (bill_no, product, profit))
            log_activity(f"Recorded Profit of ₹{profit} for BillNo : {bill_no}")
            mycon.commit()

            gen_bill(bill_no, custm_name, address, product, qty)  # Generate PDF invoice
            log_activity("GST Invoice generated successfully for BillNo : " + str(bill_no))
            filename = f"GST_Invoice_{custm_name}_{bill_no}.pdf"

            # Ensure the file is saved in the current working directory
            filepath = os.path.abspath(filename)

            # Open in default PDF viewer
            webbrowser.open(f"file://{filepath}")

            record_shipment(bill_no, address, status)      # Record shipment info
            log_activity(f"Recorded Shipment info for BillNo : {bill_no}")

            # Update inventory
            mycursor.execute("UPDATE PRODUCTS SET Quantity = Quantity - %s WHERE Product_Name = %s",(qty, product))
            mycon.commit()
            log_activity(f"Inventory updated: {qty} units of '{product}' deducted.")
        else:
            log_activity("\nPurchase quantity exceeds available stock!")
            log_activity(f"Available quantity for '{product}': {qty_avl}")

    except IndexError:
        log_activity(f"\nProduct '{product}' not found in inventory.")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def record_shipment(billno, address, status): # This function is auto handled by the record_sale function. (Not to be included in the menu)
    try:
        mycursor.execute("INSERT INTO TRANSPORT (BillNo, Address, Status) VALUES (%s, %s, %s)",(billno, address, status))
        mycon.commit()
        log_activity("Recorded Shipment info for the order with BillNo : " + str(billno))

    except Exception as e:
        log_activity(f"An error occurred while recording shipment: {e}")

def delete_sale(): # Delete a sale record by BillNo
    
    try :
        bill = input("Enter the BillNo of the sale record to be deleted : ")
        mycursor.execute(f"DELETE FROM SALES WHERE BillNo = {bill}")
        mycon.commit()
        log_activity(f"Sale record with BillNo : {bill} successfully deleted from the table")
        
    except Exception as e:
        log_activity(f"An error occurred: {e}")

def search_sale(): # Search sale by BillNo
    
    try:
        billno = input("Enter the BillNo of the sale record to be searched : ")
        mycursor.execute(f"SELECT * FROM SALES WHERE BillNo = {billno}")
        table = from_db_cursor(mycursor)
        if not table._rows :
            log_activity(f"No records found for BillNo : {billno}")
        else :
            log_activity(table)
            log_activity(f"Displayed record for BillNo : {billno}")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def sale_info(): # View all sales info

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
    
def shipping_info(): # View all shipment info

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

def user_info(): # View all users info

    try:
        mycursor.execute("SELECT * FROM USER")
        table = from_db_cursor(mycursor)
        log_activity(table)
        log_activity("Displayed all user records")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def product_info(): # View all products info

    try:
        mycursor.execute("SELECT * FROM PRODUCTS")
        table = from_db_cursor(mycursor)
        log_activity(table)
        log_activity("Displayed all product records")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

def search_ship(): # Search shipment by ShipmentID
    
    shipID = input("Enter the ShipmentID to be searched : ")

    try:
        mycursor.execute(f"SELECT * FROM TRANSPORT WHERE ShipmentID = {shipID}")
        log_activity(f"Found Record for the ShipmentID : {shipID}")
        table = from_db_cursor(mycursor)
        log_activity(table)
        log_activity(f"Displayed record for ShipmentID : {shipID}")

    except:
        log_activity(f"No records found for the ShipmentID : {shipID}")

def set_settings(): 

    # Should be used only once to set the company details
    
    Company_Name = input("Enter Company Name : ")
    Company_ID = int(input("Enter Company ID : "))
    GST_No = input("Enter GST Registration Number : ")
    Company_Address = input("Enter Company Address : ")
    state = input("Enter GST Registration State : ")
    mobno = input("Enter Company Mobile Number : ")
    email = input("Enter Company Email ID : ")
    igst = float(input("Enter IGST Rate : "))
    cgst = sgst = float(input("Enter CGST/SGST Rate : "))
    upi = input("Enter UPI ID : ")
    mycursor.execute(f"INSERT INTO SETTINGS VALUES ('{Company_Name}', {Company_ID}, '{GST_No}', '{Company_Address}', '{state}', {mobno}, '{email}', '{upi}', {igst}, {cgst}, {sgst})")
    mycon.commit()
    log_activity("Settings Saved Successfully with values : " + f"Company Name : {Company_Name}, Company ID : {Company_ID}, GST Registration Number : {GST_No}, Company Address : {Company_Address}, GST Registration State : {state}, Company Mobile Number : {mobno}, Company Email ID : {email}, IGST Rate : {igst}, CGST/SGST Rate : {cgst}, UPI ID : {upi}")

def log_activity(message, level="INFO"):

    # Log activities with timestamp and level to a log file

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

def export_table_to_csv(table_name):
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, mycon)  # Make sure mycon is your MySQL connection
        filename = f"{table_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        log_activity(f"Exported {table_name} data to {filename}")
        return filename  # Return the file path so Flask can send it
    except Exception as e:
        log_activity(f"Error exporting data: {e}")
        return None
        
def gen_bill(bill_no, customer_name, customer_address, product, qty):
    
    # Generate a GST invoice PDF for a sale
    
    try:
        # --- Fetch Company Info ---
        mycursor.execute("SELECT CompanyName, GSTIN, UPI, Company_Address, Mobile_No, Email FROM SETTINGS")
        data = mycursor.fetchone()
        company_name = data['CompanyName']
        gstin = data['GSTIN']
        upi = data['UPI']
        company_address = data['Company_Address']
        mobile_no = data['Mobile_No']
        email = data['Email']
        log_activity(data)

        # --- Fetch Product Info ---
        mycursor.execute(f"SELECT MRP FROM PRODUCTS WHERE Product_Name = '{product}'")
        mrp = mycursor.fetchone()['MRP']
        log_activity(f"Product MRP fetched: ₹{mrp}")
        filename = f"GST_Invoice_{customer_name}_{bill_no}.pdf"
        logo_path = "logo.png"

        doc = SimpleDocTemplate(
            filename, pagesize=A4,
            rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20
        )
        styles = getSampleStyleSheet()
        elements = []

        # --- Custom Styles ---
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
            logo = Image(logo_path, width=60, height=60)
            logo.hAlign = 'LEFT'
            header_table_data.append([logo, Paragraph(f"<b>{company_name}</b>", title_style)])
        except Exception:
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

        subtotal = 0

        # If product and qty are lists, handle multiple products

        if isinstance(product, list) and isinstance(qty, list):
            for idx, (prod, q) in enumerate(zip(product, qty), start=1):
                mycursor.execute(f"SELECT MRP FROM PRODUCTS WHERE Product_Name = '{prod}'")
                prod_mrp = mycursor.fetchone()['MRP']
                total = int(q) * prod_mrp
                subtotal += total
                data.append([
                Paragraph(str(idx), cell_style),
                Paragraph(str(prod), cell_style),
                Paragraph(str(q), cell_style),
                Paragraph(f"{prod_mrp:.2f}", cell_style),
                Paragraph(f"{total:.2f}", cell_style)
                ])
        else:
            # Single product fallback
            total = int(qty) * mrp
            subtotal += total
            data.append([
            Paragraph("1.", cell_style),
            Paragraph(str(product), cell_style),
            Paragraph(str(qty), cell_style),
            Paragraph(f"{mrp:.2f}", cell_style),
            Paragraph(f"{total:.2f}", cell_style)
            ])

        # --- GST Calculations ---
        gst_rate = 18
        gst_amount = subtotal * gst_rate / 100
        grand_total = subtotal + gst_amount

        data.append(["", "", "", Paragraph("Subtotal", cell_style),
                     Paragraph(f"{subtotal:.2f}", cell_style)])
        
        # --- GST Calculation based on State ---
        mycursor.execute("SELECT State, IGST, CGST, SGST FROM SETTINGS")
        gst_settings = mycursor.fetchone()
        company_state = gst_settings['State']
        igst_rate = gst_settings['IGST']
        cgst_rate = gst_settings['CGST']
        sgst_rate = gst_settings['SGST']

        if company_state.lower() in customer_address.lower():
            # Intra-state: CGST + SGST
            cgst_amount = subtotal * cgst_rate
            sgst_amount = subtotal * sgst_rate
            gst_amount = cgst_amount + sgst_amount
            gst_label = f"CGST ({cgst_rate*100}%)"
            gst_label2 = f"SGST ({sgst_rate*100}%)"
            data.append(["", "", "", Paragraph(gst_label, cell_style),
                 Paragraph(f"{cgst_amount:.2f}", cell_style)])
            data.append(["", "", "", Paragraph(gst_label2, cell_style),
                 Paragraph(f"{sgst_amount:.2f}", cell_style)])
        else:
            # Inter-state: IGST
            gst_amount = subtotal * igst_rate
            gst_label = f"IGST ({igst_rate*100}%)"
            data.append(["", "", "", Paragraph(gst_label, cell_style),
                 Paragraph(f"{gst_amount:.2f}", cell_style)])
        data.append(["", "", "", Paragraph("<b>Grand Total</b>", cell_style),
                     Paragraph(f"<b>{grand_total:.2f}</b>", cell_style)])

        # --- Table Styling ---
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

        # --- Terms & Footer ---
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

def remove_sale():
    try:
        bill = input("Enter the BillNo of the sale record to be deleted : ")
        mycursor.execute("DELETE FROM SALES WHERE BillNo = %s", (bill,))
        mycon.commit()
        log_activity("Sale record and associated shipment successfully deleted from the table for BillNo : " + str(bill))

    except Exception as e:
        log_activity(f"An error occurred: {e}")
    
def update_shipment_status():
    try:
        ship_id = int(input("Enter ShipmentID to update status: "))
        new_status = input("Enter new status (e.g., In Transit, Delivered): ")
        mycursor.execute("UPDATE TRANSPORT SET Status = %s WHERE ShipmentID = %s", (new_status, ship_id))
        mycon.commit()
        log_activity("Shipment status updated successfully for ShipmentID : " + str(ship_id))

    except ValueError:
        log_activity("Invalid input. Please enter the correct data types.")

    except Exception as e:
        log_activity(f"An error occurred: {e}")

# ---------- MANDATORY CHECKS BEFORE MAIN MENU ----------

def low_stock_alert():

    # Alert for products with low stock (less than 10 units)

    mycursor.execute("SELECT Product_Name, Quantity FROM PRODUCTS WHERE Quantity < 10")
    low_stock = mycursor.fetchall()
    if low_stock:
        log_activity("\n Low Stock Alert:")
        for p in low_stock:
            log_activity(f"   - {p[0]}: {p[1]} units left")
        print()

def checks():

    # Ensure database and tables exist, and prompt for initial setup if needed

    low_stock_alert()
    mycursor.execute("SELECT COUNT(*) FROM SETTINGS")
    if mycursor.fetchone()[0] == 0:
        log_activity("No company settings found. Please set up your company details.")
        set_settings()

    mycursor.execute("SELECT * FROM SETTINGS")
    settings = mycursor.fetchall()
    print("="*70)
    log_activity(f"\nWelcome to {settings[0][0]} Warehouse Management System (WMS)\n")
    print("="*70)

    mycursor.execute("SELECT * FROM USER")
    users = mycursor.fetchall()
    if not users:
        log_activity("No users found in the system. Please add users to proceed.\n")
        add_user()

    mycursor.execute("SELECT * FROM PRODUCTS")
    products = mycursor.fetchall()
    if not products:
        log_activity("No products found in the inventory. Please add products to proceed.\n")
        add_stock()

# ---------- FLASK APP (GUI) ----------

app = Flask(__name__)
app.secret_key = "egweg4h4r4h654re65j465er562rb11rg6465w" 

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def home():
    mycursor.execute("SELECT COUNT(*) FROM USER")
    no_of_users = mycursor.fetchone()['COUNT(*)']
    mycursor.execute("SELECT COUNT(*) FROM PRODUCTS")
    no_of_items = mycursor.fetchone()['COUNT(*)']
    mycursor.execute("SELECT SUM(Sale_Amount) FROM SALES")
    revenue = mycursor.fetchone()['SUM(Sale_Amount)'] or 0
    mycursor.execute("SELECT COUNT(*) FROM TRANSPORT")
    no_of_ships = mycursor.fetchone()['COUNT(*)']
    return render_template('index.html', no_of_users=no_of_users, no_of_items=no_of_items, revenue=revenue, no_of_ships=no_of_ships, company_name=company_name)

@app.route('/add_order', methods=['GET', 'POST'])
def add_order():
    today = date.today().strftime("%Y-%m-%d")
    mycursor.execute("SELECT Product_Name FROM PRODUCTS")
    products = mycursor.fetchall()

    success = False

    if request.method == 'POST':
        custm_name = request.form['customerName']
        address = request.form['customerAddress']
        product = request.form['productName']
        qty = int(request.form['quantity'])
        status = request.form['status']
        today = request.form['date']

        record_sale(custm_name, address, product, qty, today, status)
        success = True  # Only set after successful POST
        return render_template('add_order.html', products=products, success=success, company_name=company_name, company_logo="/static/logo.png", today=today)

    return render_template('add_order.html', products=products, success=success, company_name=company_name, company_logo="/static/logo.png", today=today)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    mycursor.execute("SELECT * FROM SETTINGS")
    settings = mycursor.fetchall()[0]
    return render_template('settings.html',settings=settings, company_name=company_name)

@app.route("/profit_loss")
def users():
    mycursor.execute("SELECT * FROM PROFIT_AND_LOSS")
    data = mycursor.fetchall()
    total_net_profit = sum(row['Net_Profit'] for row in data)
    total_bills = len(set(row['BillNo'] for row in data))
    total_products = len(set(row['Product_Name'] for row in data))
    return render_template(
        'Profit_and_loss.html',
        company_name=company_name,
        profit_loss_data=data,
        total_net_profit=total_net_profit,
        total_bills=total_bills,
        total_products=total_products
    )

@app.route('/export_profit_loss')
def export_profit_loss():
    # Export using your existing function
    filename = export_table_to_csv("PROFIT_AND_LOSS")  # Returns the file path

    # Send the file to the user
    return send_file(filename, as_attachment=True)

@app.route('/edit_shipment', methods=['POST'])
def edit_shipment():
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
    return redirect(url_for('shipments'))

@app.route('/delete_shipment/<int:id>')
def delete_shipment(id):

    mycursor.execute("DELETE FROM TRANSPORT WHERE ShipmentID=%s", (id,))
    mycon.commit()
    return redirect(url_for('shipments'))

@app.route('/export_shipments')
def export_shipments():
    # Use your existing export function
    filename = export_table_to_csv("TRANSPORT")  # Returns CSV file path
    if filename:
        return send_file(filename, as_attachment=True)
    else:
        return "Error exporting shipments", 500
    
@app.route("/users/add", methods=["GET","POST"])
def add_user():
    if request.method == "POST":
        name = request.form['name']
        dept = request.form['department']
        sal = int(request.form['salary'])
        mycursor.execute("INSERT INTO USER (Name, Department, Salary) VALUES (%s, %s, %s)", (name, dept, sal))
        mycon.commit()
        flash("User added successfully!")
        return redirect(url_for("users"))
    return render_template("add_user.html", company_name=company_name)

@app.route('/shipments')
def shipments():
    mycursor.execute("SELECT * FROM TRANSPORT")
    shipments_data = mycursor.fetchall()
    # Summary cards
    total_shipments = len(shipments_data)
    pending = len([s for s in shipments_data if s['Status'].lower() == 'pending'])
    delivered = len([s for s in shipments_data if s['Status'].lower() == 'delivered'])
    
    return render_template(
        'shipments.html',
        company_name=company_name,
        shipments_data=shipments_data,
        total_shipments=total_shipments,
        pending=pending,
        delivered=delivered
    )

@app.route('/users')
def users_webpage():
    mycursor.execute("SELECT * FROM USER")
    users_data = mycursor.fetchall()
    return render_template('users.html', company_name=company_name, users_data=users_data)

@app.route('/dbm', methods=['GET', 'POST'])
def dbms():
    mycursor.execute("show tables")
    tables = mycursor.fetchall()
    print(tables)
    return render_template('dbms.html', db_data=tables, company_name=company_name, no_of_tables=len(tables))

if __name__ == '__main__':
    create_init_db()
    app.run(debug=True)
