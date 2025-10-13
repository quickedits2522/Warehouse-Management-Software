import mysql.connector as ms
from datetime import date
from prettytable import from_db_cursor
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image, HRFlowable
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import qrcode
import io
from flask import Flask, render_template, request, redirect, url_for, flash

# Establish connection to MySQL database
mycon = ms.connect(user = "root", password = "mysql", host = "localhost", database = "WMS", use_pure="True")
mycursor = mycon.cursor()

def create_init_db():
    # Create all required tables if they do not exist
    init_tables=["CREATE DATABASE IF NOT EXISTS WMS",
                "CREATE TABLE IF NOT EXISTS USER(UserID int PRIMARY KEY, Name varchar(25), Department varchar(10), Salary int)",
                "CREATE TABLE IF NOT EXISTS PRODUCTS(ProductID int PRIMARY KEY, Product_Name varchar(30), Cost_Price float, MRP float, Quantity int)",
                "CREATE TABLE IF NOT EXISTS SALES(BillNo int PRIMARY KEY, Customer_Name varchar(25), Products varchar(255), QTY int, Sale_Amount float, Date_Of_Sale date)",
                "CREATE TABLE IF NOT EXISTS TRANSPORT(ShipmentID int PRIMARY KEY, BillNo int, Address varchar(100), Status varchar(25), FOREIGN KEY (BillNo) REFERENCES SALES(BillNo) ON DELETE CASCADE)",
                "CREATE TABLE IF NOT EXISTS PROFIT_AND_LOSS(BillNo int, ProductID int, Net_Profit float)",
                "CREATE TABLE IF NOT EXISTS SETTINGS(CompanyName varchar(40), CompanyID int, GSTIN char(15), State varchar(25), UPI varchar(25), IGST float, CGST float, SGST float)"]

    for i in init_tables:
        mycursor.execute(i)
    mycon.commit()

def delete_db():
    # Delete all tables from the database (irreversible)
    print("WARNING! : This process is irreversible, All your data will be deleted permanently!!")
    usr_confirm = input("Do you want to continue (Y/N) : ")
    if usr_confirm in "Yy":
        mycursor.execute("DROP TABLE IF EXISTS USER")
        mycursor.execute("DROP TABLE IF EXISTS PRODUCTS")
        mycursor.execute("DROP TABLE IF EXISTS SALES")
        mycursor.execute("DROP TABLE IF EXISTS TRANSPORT")
        print("Deleted all the tables")

    elif usr_confirm in "Nn" : 
        print("Operation Canceled")
    
    else :
        print("Invalid Choice")

def record_sale(custm_name, address, product, qty, today, status):
    # Record a sale, update inventory, generate bill, and record shipment
    mycursor.execute("SELECT MRP, Quantity from PRODUCTS where Product_Name = %s",(product,))
    output = mycursor.fetchall()
    mrp = output[0][0]
    qty_avl = output[0][1]
    print(f"MRP of {product} : ₹{mrp}")

    if qty <= qty_avl:
        sale_amt = mrp*qty*1.18  # Calculate sale amount with GST
        mycursor.execute("INSERT INTO SALES (Customer_Name, Products, QTY, Sale_Amount, Date_Of_Sale) VALUES (%s, %s, %s, %s, %s)",(custm_name, product, qty, sale_amt, today))
        mycon.commit()
        mycursor.execute("SELECT BillNo FROM SALES WHERE Sale_Amount = %s", (sale_amt,))
        bill_no = mycursor.fetchall()[0][0]
        print(f"Sale of {product} with qty : {qty} @ ₹{mrp} recorded")
        items = (product, qty)
        gen_bill(bill_no, custm_name, address, items)  # Generate PDF invoice
        record_shipment(bill_no, address, status)      # Record shipment info
        mycursor.execute("UPDATE PRODUCTS SET Quantity = Quantity - %s WHERE Product_Name = %s", (qty, product))
        mycon.commit()

    else :
        print("Purchase quantity exceed available quantity")

def record_shipment(billno, address, status): # This function is auto handled by the record_sale function. (Not to be included in the menu)
    # Record shipment details for an order
    mycursor.execute("INSERT INTO TRANSPORT (BillNo, Address, Status) VALUES (%s, %s, %s)",(billno, address, status))
    mycon.commit()
    print("Recorded Shipment info for the order")

def shipping_info(): # View all shipment info
    # Display all shipment records
    mycursor.execute("SELECT * FROM TRANSPORT")
    table = from_db_cursor(mycursor)
    print(table)

def search_ship(): # Search shipment by ShipmentID
    # Search for a shipment using ShipmentID
    shipID = input("Enter the ShipmentID to be searched : ")

    try:
        mycursor.execute("SELECT * from TRANSPORT where ShipmentID = %s", (shipID,))
        print(f"Found Record for the ShipmentID : {shipID}")
        table = from_db_cursor(mycursor)
        print(table)

    except:
        print(f"No records found for the ShipmentID : {shipID}")

def manual_update(): # Manual Update of any table
    # Update any record in any table manually
    table_name = input("Enter the name of the table to be updated : ")
    column_name = input("Enter the column name to be updated : ")
    value = input("Enter value to be updated : ")
    row = input("Enter row identifier (Primary Key) : ")
    row_value = int(input("Enter row identifier value (Primary Key Value) : "))

    try : 
        mycursor.execute(f"UPDATE {table_name} SET {column_name} = {value} WHERE {row} = {row_value}")
        mycon.commit()
        print("Successfully Updated the Record")
    
    except :
        print("Error Encountered")

def manual_select(): # Manual Select Details of any table
    # Select and display records from any table
    table_name = input("Enter the name of the table to be updated : ")
    column_name = input("Enter the column name to be updated (Enter '*' to display all records) : ")

    try : 
        mycursor.execute(f"SELECT {column_name} FROM {table_name}")
        table = from_db_cursor(mycursor)
        print(table)
    
    except :
        print("Error Encountered")

def set_settings(): # Should be used only once to set the company details
    # Set company details and GST settings
    Company_Name = input("Enter Company Name : ")
    Company_ID = int(input("Enter Company ID : "))
    GST_No = input("Enter GST Registration Number : ")
    state = input("Enter GST Registration State : ")
    igst = float(input("Enter IGST Rate : "))
    cgst = sgst = float(input("Enter CGST/SGST Rate : "))
    upi = input("Enter UPI ID : ")
    mycursor.execute("INSERT INTO SETTINGS VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",(Company_Name, Company_ID, GST_No, state, upi, igst, cgst, sgst))
    mycon.commit()
    print("Settings Saved Successfully")

def gen_bill(bill_no, customer_name, customer_address, items):
    # Generate a GST invoice PDF for a sale

    mycursor.execute("SELECT CompanyName, GSTIN, UPI fROM SETTINGS")
    data = mycursor.fetchall()
    company_name = data[0][0]
    gstin = data[0][1]
    upi = data[0][2]
    mycursor.execute("SELECT MRP FROM PRODUCTS WHERE Product_Name = %s",(items[0],))
    mrp = mycursor.fetchall()[0][0]
    filename = f"GST_Invoice_{customer_name}_{bill_no}.pdf"
    logo_path = "logo.png"

    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)
    styles = getSampleStyleSheet()
    elements = []

    # --- Custom Styles ---
    title_style = ParagraphStyle('title_style', parent=styles['Title'], alignment=0, fontSize=18, leading=22)
    header_style = ParagraphStyle('header_style', parent=styles['Normal'], fontSize=10, leading=14)
    bold_style = ParagraphStyle('bold_style', parent=styles['Normal'], fontSize=10, leading=14, fontName='Helvetica-Bold')
    cell_style = ParagraphStyle('cell_style', parent=styles['Normal'], fontSize=9, leading=12, alignment=1)
    footer_style = ParagraphStyle('footer_style', parent=styles['Italic'], alignment=1, fontSize=9, textColor=colors.grey)

    # --- Header / Company Info ---
    try:
        logo = Image(logo_path, width=75, height=75)
        logo.hAlign = 'RIGHT'
        elements.append(logo)
    except Exception:
        pass

    elements.append(Paragraph(f"<b>{company_name}</b>", title_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"{company_name}", header_style))
    elements.append(Paragraph("Phone: +91-9876543210 | Email: contact@abcstores.com", header_style))
    elements.append(Paragraph(f"{gstin}", header_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Spacer(1, 10))

    # --- Invoice + Customer Info ---
    now = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    customer_block = f"""
    <b>Bill No:</b> {bill_no}<br/>
    <b>Date:</b> {now}<br/><br/>
    <b>Billed To:</b><br/>
    {customer_name}<br/>
    {customer_address}
    """

    elements.append(Paragraph(customer_block, header_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 10))

    # --- Table Header ---
    data = [
        [
            Paragraph("<b>SL.No</b>", cell_style),
            Paragraph("<b>Description</b>", cell_style),
            Paragraph("<b>Qty</b>", cell_style),
            Paragraph("<b>Unit Price (Rs.)</b>", cell_style),
            Paragraph("<b>Amount (Rs.)</b>", cell_style)
        ]
    ]

    # --- Item Rows ---
    subtotal = 0
    total = int(items[1])*mrp
    subtotal += total
    data.append([
            Paragraph("1.", cell_style),
            Paragraph(str(items[0]), cell_style),
            Paragraph(str(items[1]), cell_style),
            Paragraph(str(mrp), cell_style),
            Paragraph(str(total), cell_style)
    ])

    # --- GST Calculations ---
    gst_rate = 18
    gst_amount = subtotal * gst_rate / 100
    grand_total = subtotal + gst_amount

    data.append(["", "", "", Paragraph("Subtotal", cell_style),
                 Paragraph(f"{subtotal:.2f}", cell_style)])
    data.append(["", "", "", Paragraph(f"GST ({gst_rate}%)", cell_style),
                 Paragraph(f"{gst_amount:.2f}", cell_style)])
    data.append(["", "", "", Paragraph("<b>Grand Total</b>", cell_style),
                 Paragraph(f"<b>{grand_total:.2f}</b>", cell_style)])

    # --- Table Styling ---
    table = Table(data, colWidths=[40, 220, 60, 80, 80])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#5388BD")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -3), [colors.whitesmoke, colors.lightgrey]),
    ])
    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 20))

    # --- QR Code Payment ---
    qr_data = f"upi://pay?pa={upi}&am={grand_total:.2f}&cu=INR"
    qr = qrcode.make(qr_data)
    qr_buffer = io.BytesIO()
    qr.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_img = Image(qr_buffer, width=100, height=100)
    qr_img.hAlign = 'LEFT'

    elements.append(Paragraph("<b>Scan to Pay (UPI)</b>", bold_style))
    elements.append(qr_img)
    elements.append(Spacer(1, 15))

    # --- Terms & Footer ---
    elements.append(Paragraph("<b>Terms & Conditions:</b>", bold_style))
    elements.append(Paragraph(
        "1. Goods once sold will not be taken back.<br/>"
        "2. Warranty as per manufacturer's terms only.<br/>"
        "3. Please retain this invoice for future reference.",
        header_style
    ))
    elements.append(Spacer(1, 15))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Thank you for your business!", footer_style))
    elements.append(Paragraph("This is a computer-generated invoice.", footer_style))

    # --- Build PDF ---
    doc.build(elements)
    print(f"GST Invoice generated successfully: {filename}")

# This part is Flask related : 

app = Flask(__name__)
app.secret_key = "328bh23jh5bh25h5j2j5jh21bj14jk1b5j"

@app.route("/")
def index():
    # Render the home page
    cursor = mycon.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(ProductID) FROM PRODUCTS")
    no_of_items = cursor.fetchall()
    cursor.execute("SELECT COUNT(UserID) FROM USER")
    no_of_users = cursor.fetchall()
    cursor.execute("SELECT COUNT(ShipmentID) FROM TRANSPORT")
    no_of_ships = cursor.fetchall()
    cursor.execute("SELECT SUM(Sale_Amount) FROM SALES")
    revenue = cursor.fetchall()

    return render_template("index.html", no_of_items=no_of_items[0]['COUNT(ProductID)'], 
                           no_of_users=no_of_users[0]['COUNT(UserID)'],
                           no_of_ships=no_of_ships[0]['COUNT(ShipmentID)'],
                           revenue=int(revenue[0]['SUM(Sale_Amount)']))

@app.route("/add_order", methods=["GET", "POST"])
def add_order():
    # Handle adding a new order via web form
    cursor = mycon.cursor(dictionary=True)
    cursor.execute("SELECT Product_Name FROM PRODUCTS")
    products = cursor.fetchall()
    print(products)

    if request.method == "POST":
        order_id = int(request.form["orderId"])
        customer_name = request.form["customerName"]
        customer_address = request.form["customerAddress"]
        product_name = request.form["productName"]
        quantity = int(request.form["quantity"])
        status = request.form["status"]
        order_date = request.form["date"]
        record_sale(customer_name, customer_address, product_name, quantity, order_date, status)
        flash("✅ Order added successfully!", "success")
        return redirect(url_for("add_order"))
    
    return render_template("add_stock.html", products=products)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    cursor = mycon.cursor(dictionary=True)
    cursor.execute("SELECT * FROM SETTINGS")
    current_settings = cursor.fetchall()
    print(current_settings)
    return render_template("settings.html", settings=current_settings[0]) 
    
app.run(host="localhost", port = 81, debug=True)
