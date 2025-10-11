import mysql.connector as ms
from datetime import date
from prettytable import from_db_cursor

mycon = ms.connect(user = "root", password = "mysql", host = "localhost", database = "WMS", use_pure="True")
mycursor = mycon.cursor()

def create_init_db():
    init_tables=["CREATE TABLE IF NOT EXISTS USER(UserId int PRIMARY KEY AUTO_INCREMENT, Name varchar(25), Department varchar(10), Salary int)",
                "CREATE TABLE IF NOT EXISTS PRODUCTS(ProductID int PRIMARY KEY AUTO_INCREMENT, Product_Name varchar(30), Cost_Price float, MRP float, Quantity int)",
                "CREATE TABLE IF NOT EXISTS SALES(BillNo int PRIMARY KEY AUTO_INCREMENT, Customer_Name varchar(25), Products varchar(255), QTY int, Sale_Amount float, Date_Of_Sale date)",
                "CREATE TABLE IF NOT EXISTS TRANSPORT(ShipmentID int PRIMARY KEY AUTO_INCREMENT, BillNo int, Address varchar(100), Status varchar(25), FOREIGN KEY (BillNo) REFERENCES SALES(BillNo) ON DELETE CASCADE)",
                "CREATE TABLE IF NOT EXISTS SETTINGS(CompanyName varchar(40), CompanyID int, GST_No char(15), State varchar(25), IGST float, CGST float, SGST float)"]

    for i in init_tables:
        mycursor.execute(i)
    mycon.commit()

def delete_db():
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

def record_sale():
    today = date.today()
    custm_name = input("Enter Customer Name : ")
    pid = input("Enter Product ID : ")
    mycursor.execute("SELECT MRP, Product_Name, Quantity from PRODUCTS where ProductId = %s",(pid,))
    output = mycursor.fetchall()
    mrp = output[0][0]
    product = output[0][1]
    qty_avl = output[0][2]
    print(f"MRP of {product} : ₹{mrp}")

    qty = int(input("Enter Quantity : "))

    if qty <= qty_avl:
        sale_amt = mrp*qty
        mycursor.execute("INSERT INTO SALES (Customer_Name, Products, QTY, Sale_Amount, Date_Of_Sale) VALUES(%s, %s, %s, %s, %s)",(custm_name, product, qty, sale_amt, today))
        mycon.commit()
        print(f"Sale of {product} with qty : {qty} @ ₹{mrp} recorded")
        record_shipment()

    else :
        print("Purchase quantity exceed available quantity")

def record_shipment(): # This function is auto handled by the record_sale function. (Not to be included in the menu)

    ship_prd = input("Do you want to record shipment information for this order? (Y/N) : ")

    if ship_prd in "Yy":
        address = input("Enter shipment address : ")
        status = "Processing"
        mycursor.execute("INSERT INTO TRANSPORT (Address, Status) VALUES (%s, %s)",(address, status))
        mycon.commit()
        print("Recorded Shipment info for the order")
    
    elif ship_prd in "Nn":
        mycursor.execute("INSERT INTO TRANSPORT (Address, Status) VALUES (NA, NA)")
        mycon.commit()
        print("Shipment info for the order is not recorded")
    
    else :
        print("Invalid Choice")

def shipping_info():
    mycursor.execute("SELECT * FROM TRANSPORT")
    table = from_db_cursor(mycursor)
    print(table)

def search_ship():
    shipID = input("Enter the ShipmentID to be searched : ")

    try:
        mycursor.execute("SELECT * from TRANSPORT where ShipmentID = %s", (shipID,))
        print(f"Found Record for the ShipmentID : {shipID}")
        table = from_db_cursor(mycursor)
        print(table)

    except:
        print(f"No records found for the ShipmentID : {shipID}")

def manual_update():
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

def manual_select():
    table_name = input("Enter the name of the table to be updated : ")
    column_name = input("Enter the column name to be updated (Enter '*' to display all records) : ")

    try : 
        mycursor.execute(f"SELECT {column_name} FROM {table_name}")
        table = from_db_cursor(mycursor)
        print(table)
    
    except :
        print("Error Encountered")

def set_settings():
    Company_Name = input("Enter Company Name : ")
    Company_ID = int(input("Enter Company ID : "))
    GST_No = input("Enter GST Registration Number : ")
    state = input("Enter GST Registration State : ")
    igst = float(input("Enter IGST Rate : "))
    cgst = sgst = float(input("Enter CGST/SGST Rate : "))
    mycursor.execute("INSERT INTO SETTINGS VALUES (%s, %s, %s, %s, %s, %s, %s)",(Company_Name, Company_ID, GST_No, state, igst, cgst, sgst))
    mycon.commit()
    print("Settings Saved Successfully")

def gen_bill():
    print("Under Progress")