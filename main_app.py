import sys
import mysql.connector as ms
from datetime import date
from prettytable import from_db_cursor
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import qrcode
import io
import webbrowser

# Establish connection to MySQL database

mycon = ms.connect(user = "root", passwd = "mysql", host = "localhost", database = "WMS", use_pure=True)
mycursor = mycon.cursor()

#--------------- User Management ----------------

def add_user():
    
    try : 
        userid = input("Enter userID: ")
        name = input("Enter username: ")
        dept = input("Enter department: ")
        sal = int(input("Enter salary: "))
    
        mycursor.execute("insert into user (UserId, Name, Department, Salary) values(%s, %s, %s, %s)",(userid, name, dept,sal))
        mycon.commit()
        print("Entry successfully added to the table")

    except ms.IntegrityError:
        print("UserID already exists. Please use a unique UserID.")
    except ValueError: 
        print("Invalid input. Please enter the correct data types.")
    except Exception as e:
        print(f"An error occurred: {e}")

def remove_user():
    
    try :
        delete = input("Enter userID of the entry to be deleted : ")
        mycursor.execute("delete from user where UserID = %s",(delete,))
        mycon.commit()
        print("Entry successfully deleted from the table")
        
    except Exception as e:
        print(f"An error occurred: {e}")

def search_user():
    
    try : 
        user = input("Enter userID of the user to be found: ")
        mycursor.execute("select * from user where UserID = %s",(user,))
        data = mycursor.fetchall()
        if not data:
            print("NO RECORD FOUND")
        else:
            table = from_db_cursor(mycursor)
            print(table)

    except Exception as e:
        print(f"An error occurred: {e}")

def update_user():
    
    try :
        column = input("Enter column where the value is to be changed: ")
        value1 = input("Enter userID of the entry to be updated: ")
        value2 = input("Enter updated value: ")
        mycursor.execute(f"update user set {column} = %s where UserID=%s",(value2,value1))
        mycon.commit()
        print("Value successfully updated")

    except Exception as e:
        print(f"An error occurred: {e}")

#-----------Stock Management---------------------------

def add_stock():

    try : 
        pdtid = input("Enter productID: ")
        name = input("Enter product name: ")
        cost = int(input("Enter cost price of product: "))
        mrp = int(input("Enter MRP of product: "))
        qty = int(input("Enter quantity of product: "))
    
        mycursor.execute("insert into Products values(%s, %s, %s, %s, %s)",(pdtid, name, cost, mrp,qty))
        mycon.commit()
        print("Record successfully added")

    except ms.IntegrityError:
        print("ProductID already exists. Please use a unique ProductID.")

    except ValueError: 
        print("Invalid input. Please enter the correct data types.")

    except Exception as e:
        print(f"An error occurred: {e}")

def remove_stock():
    
    try :
        value = input("Enter the productID of the entry to be deleted: ")
        mycursor.execute("delete from Products where ProductID = %s",(value,))
        mycon.commit()
        print("Entry successfully deleted from the table")

    except Exception as e:
        print(f"An error occurred: {e}")

def search_stock():
    
    try:
        product = input("Enter the productID of the entry to be dislayed: ")
        mycursor.execute("Select * from Products where ProductID = %s",(product,))
        table = from_db_cursor(mycursor)
        print(table)

    except Exception as e:
        print(f"An error occurred: {e}")

def update_stock():
    
    try :
        column = input("Enter column where the value is to be changed: ")
        value1 = input("Enter productID of the entry to be updated: ")
        value2 = input("Enter updated value: ")
        mycursor.execute(f"update Products set {column} = %s where ProductID = %s",(value2,value1))
        mycon.commit()
        print("Value successfully updated")

    except Exception as e:
        print(f"An error occurred: {e}")

def create_init_db():
    
    # Create all required tables if they do not exist
    try : 
        mycursor.execute("CREATE DATABASE IF NOT EXISTS WMS")
        init_tables=["CREATE TABLE IF NOT EXISTS USER(UserID int PRIMARY KEY, Name varchar(25), Department varchar(10), Salary int)",
                    "CREATE TABLE IF NOT EXISTS PRODUCTS(ProductID int PRIMARY KEY, Product_Name varchar(30), Cost_Price float, MRP float, Quantity int)",
                    "CREATE TABLE IF NOT EXISTS SALES(BillNo int PRIMARY KEY AUTO_INCREMENT, Customer_Name varchar(25), Products varchar(255), QTY int, Sale_Amount float, Date_Of_Sale date)",
                    "CREATE TABLE IF NOT EXISTS TRANSPORT(ShipmentID int PRIMARY KEY, BillNo int, Address varchar(100), Status varchar(25), FOREIGN KEY (BillNo) REFERENCES SALES(BillNo) ON DELETE CASCADE)",
                    "CREATE TABLE IF NOT EXISTS PROFIT_AND_LOSS(BillNo int, ProductID int, Net_Profit float)",
                    "CREATE TABLE IF NOT EXISTS SETTINGS(CompanyName varchar(40), CompanyID int, GSTIN char(15), Company_Address varchar(255), State varchar(25), Mobile_No. BIGINT, Email varchar(50), UPI varchar(25), IGST float, CGST float, SGST float)"]

        for i in init_tables:
            mycursor.execute(i)
        mycon.commit()
        print("Initialized Database and Tables")

    except Exception as e:
        print(f"An error occurred during initialization: {e}")

def delete_db():
    
    # Delete all tables from the database (irreversible)
    
    try : 
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

    except Exception as e:
        print(f"An error occurred: {e}")

def record_sale(custm_name, address, product, qty, today, status):
    
    # Record a sale, update inventory, generate bill, and record shipment
    
    try:
        mycursor.execute("SELECT MRP, Quantity from PRODUCTS where Product_Name = %s",(product,))
        output = mycursor.fetchall()
        mrp = output[0][0]
        qty_avl = output[0][1]
        print(f"MRP of {product} : ₹{mrp}")

        if qty <= qty_avl:
            sale_amt = mrp * qty * 1.18  # Calculate sale amount with GST
            sale_amt = round(sale_amt, 2)

            # Record the sale in the SALES table

            mycursor.execute(f"INSERT INTO SALES (Customer_Name, Products, QTY, Sale_Amount, Date_Of_Sale) VALUES ('{custm_name}', '{product}', {qty}, {sale_amt}, '{today}')")
            mycon.commit()

            # Retrieve the BillNo for the newly created sale
            mycursor.execute(f"SELECT BillNo FROM SALES WHERE Customer_Name = '{custm_name}' AND Products = '{product}' AND QTY = {qty} AND Sale_Amount = {sale_amt} AND Date_Of_Sale = '{today}'")
            bill_no = mycursor.fetchone()[0]
            print("\n" + "="*50)
            print(f"Sale Recorded!")
            print(f"Bill No      : {bill_no}")
            print(f"Customer Name: {custm_name}")
            print(f"Address      : {address}")
            print(f"Product      : {product}")
            print(f"Quantity     : {qty}")
            print(f"Unit Price   : ₹{mrp}")
            print(f"Total Amount : ₹{sale_amt:.2f} (incl. GST)")
            print("="*50 + "\n")

            gen_bill(bill_no, custm_name, address, product, qty)  # Generate PDF invoice
            filename = f"GST_Invoice_{custm_name}_{bill_no}.pdf"
            webbrowser.open(filename)

            record_shipment(bill_no, address, status)      # Record shipment info

            # Update inventory
            mycursor.execute("UPDATE PRODUCTS SET Quantity = Quantity - %s WHERE Product_Name = %s",(qty, product))
            mycon.commit()
            print(f"Inventory updated: {qty} units of '{product}' deducted.")
        else:
            print("\nPurchase quantity exceeds available stock!")
            print(f"Available quantity for '{product}': {qty_avl}")

    except IndexError:
        print(f"\nProduct '{product}' not found in inventory.")

    except Exception as e:
        print(f"An error occurred: {e}")

def record_shipment(billno, address, status): # This function is auto handled by the record_sale function. (Not to be included in the menu)
    try:
        mycursor.execute("INSERT INTO TRANSPORT (BillNo, Address, Status) VALUES (%s, %s, %s)",(billno, address, status))
        mycon.commit()
        print("Recorded Shipment info for the order")

    except Exception as e:
        print(f"An error occurred while recording shipment: {e}")

def shipping_info(): # View all shipment info

    try:
        mycursor.execute("SELECT * FROM TRANSPORT")
        table = from_db_cursor(mycursor)
        print(table)

    except Exception as e:
        print(f"An error occurred: {e}")

def search_ship(): # Search shipment by ShipmentID
    
    shipID = input("Enter the ShipmentID to be searched : ")

    try:
        mycursor.execute("SELECT * from TRANSPORT where ShipmentID = %s", (shipID,))
        print(f"Found Record for the ShipmentID : {shipID}")
        table = from_db_cursor(mycursor)
        print(table)

    except:
        print(f"No records found for the ShipmentID : {shipID}")

def manual_update(): # Manual Update of any table
    
    try :
        table_name = input("Enter the name of the table to be updated : ")
        column_name = input("Enter the column name to be updated : ")
        value = input("Enter value to be updated : ")
        row = input("Enter row identifier (Primary Key) : ")
        row_value = int(input("Enter row identifier value (Primary Key Value) : "))
        mycursor.execute(f"UPDATE {table_name} SET {column_name} = {value} WHERE {row} = {row_value}")
        mycon.commit()
        print("Successfully Updated the Record")
    
    except ValueError:
        print("Invalid input. Please enter the correct data types.")

    except Exception as e:
        print(f"An error occurred: {e}")
    
def manual_select(): # Manual Select Details of any table
    
    try :
        table_name = input("Enter the name of the table to be updated : ")
        column_name = input("Enter the column name to be updated (Enter '*' to display all records) : ")
        mycursor.execute(f"SELECT {column_name} FROM {table_name}")
        table = from_db_cursor(mycursor)
        print(table)
    
    except Exception as e:
        print(f"An error occurred: {e}")

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
    mycursor.execute("INSERT INTO SETTINGS VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",(Company_Name, Company_ID, GST_No, Company_Address, state, mobno, email, upi, igst, cgst, sgst))
    mycon.commit()
    print("Settings Saved Successfully")

def gen_bill(bill_no, customer_name, customer_address, product, qty):
    
    # Generate a GST invoice PDF for a sale
    
    try:
        # --- Fetch Company Info ---
        mycursor.execute("SELECT CompanyName, GSTIN, UPI, Company_Address FROM SETTINGS")
        data = mycursor.fetchall()
        company_name = data[0][0]
        gstin = data[0][1]
        upi = data[0][2]
        company_address = data[0][3]

        # --- Fetch Product Info ---
        mycursor.execute("SELECT MRP FROM PRODUCTS WHERE Product_Name = %s", (product,))
        mrp = mycursor.fetchall()[0][0]
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
        elements.append(Paragraph("Phone: +91-9886601823 | Email: vibhaBala@gmail.com", header_style))
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
                mycursor.execute("SELECT MRP FROM PRODUCTS WHERE Product_Name = %s", (prod,))
                prod_mrp = mycursor.fetchall()[0][0]
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
        company_state = gst_settings[0]
        igst_rate = gst_settings[1]
        cgst_rate = gst_settings[2]
        sgst_rate = gst_settings[3]

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
        print(f"GST Invoice generated successfully: {filename}")

    except Exception as e:
        print(f"Error generating invoice: {e}")

# ---------- MANDATORY CHECKS BEFORE MAIN MENU ----------

def checks():

    # Ensure database and tables exist, and prompt for initial setup if needed

    mycursor.execute("SELECT COUNT(*) FROM SETTINGS")
    if mycursor.fetchone()[0] == 0:
        print("No company settings found. Please set up your company details.")
        set_settings()

    mycursor.execute("SELECT * FROM SETTINGS")
    settings = mycursor.fetchall()
    print(f"\nWelcome to {settings[0][0]} Warehouse Management System (WMS)\n")

    mycursor.execute("SELECT * FROM USER")
    users = mycursor.fetchall()
    if not users:
        print("No users found in the system. Please add users to proceed.\n")
        add_user()

    mycursor.execute("SELECT * FROM PRODUCTS")
    products = mycursor.fetchall()
    if not products:
        print("No products found in the inventory. Please add products to proceed.\n")
        add_stock()

# ---------- MAIN MENU ----------

def print_divider():
    print("\n" + "="*60 + "\n")

def main_menu():
    checks()
    print("\n" + "="*60)
    print("      Welcome to Warehouse Management System (WMS)      ")
    print("="*60 + "\n")

    while True:
        print("""
        Main Menu:
        1. User Management
        2. Stock Management
        3. Sales Management
        4. Shipment Management
        5. Database Management
        6. Exit
        """)
        try :
            choice = input("Enter your choice (1-6): ")

        except KeyboardInterrupt:
            print("\nExiting the program. Goodbye!")
            break

        if choice == '1':

            # --- USER MANAGEMENT ---
            
            while True:
                print("""
                User Management:
                a. Add User
                b. Remove User
                c. Search User
                d. Update User Info
                e. Back to Main Menu
                """)
                ch = input("Enter your choice: ").lower()

                if ch == 'a':
                    add_user()
                    print_divider()
                elif ch == 'b':
                    remove_user()
                    print_divider()
                elif ch == 'c':
                    search_user()
                    print_divider()
                elif ch == 'd':
                    update_user()
                    print_divider()
                elif ch == 'e':
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
                print("""
                Stock Management:
                a. Add Product
                b. Remove Product
                c. Search Product
                d. Update Product Info
                e. Back to Main Menu
                """)
                try : 
                    ch = input("Enter your choice: ").lower()
                except KeyboardInterrupt:
                    print("\nExiting the program. Goodbye!")
                    sys.exit(0)

                if ch == 'a':
                    add_stock()
                    print_divider()
                elif ch == 'b':
                    remove_stock()
                    print_divider()
                elif ch == 'c':
                    search_stock()
                    print_divider()
                elif ch == 'd':
                    update_stock()
                    print_divider()
                elif ch == 'e':
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
                print("""
                Sales Management:
                a. Record Sale
                b. Back to Main Menu
                """)
                try : 
                    ch = input("Enter your choice: ").lower()
                except KeyboardInterrupt:
                    print("\nExiting the program. Goodbye!")
                    sys.exit(0)

                if ch == 'a':
                    custm_name = input("Enter Customer Name: ")
                    address = input("Enter Customer Address: ")
                    product = input("Enter Product Name: ")
                    qty = int(input("Enter Quantity: "))
                    today = date.today()
                    status = input("Enter Shipment Status: ")
                    record_sale(custm_name, address, product, qty, today, status)
                    print_divider()
                elif ch == 'b':
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
                print("""
                Shipment Management:
                a. List of Shipments
                b. Search Shipment
                c. Back to Main Menu
                """)

                try : 
                    ch = input("Enter your choice: ").lower()
                except KeyboardInterrupt:
                    print("\nExiting the program. Goodbye!")
                    sys.exit(0)

                if ch == 'a':
                    shipping_info()
                    print_divider()
                elif ch == 'b':
                    search_ship()
                    print_divider()
                elif ch == 'c':
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
                print("""
                Database Management:
                a. Delete Entire Database
                b. Update Rows/Columns
                c. Select Custom Records
                d. Back to Main Menu
                """)
                try : 
                    ch = input("Enter your choice: ").lower()
                except KeyboardInterrupt:
                    print("\nExiting the program. Goodbye!")
                    sys.exit(0)

                if ch == 'a':
                    delete_db()
                    print_divider()
                elif ch == 'b':
                    manual_update()
                    print_divider()
                elif ch == 'c':
                    manual_select()
                    print_divider()
                elif ch == 'd':
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
            print("\nThank you for using the Warehouse Management System! Goodbye.")
            print("="*60)
            break

        else:
            print("Invalid choice. Please try again.")
            print_divider()

# Run the main menu

if __name__ == "__main__":
    create_init_db()
    checks()
    main_menu()