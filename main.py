import mysql.connector as ms
from datetime import date

mycon = ms.connect(user = "root", password = "mysql", host = "localhost", database = "WMS", use_pure="True")
mycursor = mycon.cursor()

def create_init_db():
    init_tables=["CREATE TABLE IF NOT EXISTS USER(UserId int PRIMARY KEY AUTO_INCREMENT, Name varchar(25), Department varchar(10), Salary int)",
                        "CREATE TABLE IF NOT EXISTS PRODUCTS(ProductID int PRIMARY KEY AUTO_INCREMENT, Product_Name varchar(30), Cost_Price float, MRP float, Quantity int)",
                        "CREATE TABLE IF NOT EXISTS SALES(BillNo int PRIMARY KEY AUTO_INCREMENT, Customer_Name varchar(25), Products varchar(255), QTY int, Sale_Amount float, Date_Of_Sale date)",
                        "CREATE TABLE IF NOT EXISTS TRANSPORT(ShipmentID int PRIMARY KEY AUTO_INCREMENT, BillNo int, Address varchar(100), FOREIGN KEY (BillNo) REFERENCES SALES(BillNo))"]

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
    print(mrp, product)
    qty = int(input("Enter Quantity : "))
    sale_amt = mrp*qty
    mycursor.execute("INSERT INTO SALES (Customer_Name, Products, QTY, Sale_Amount, Date_Of_Sale) VALUES(%s, %s, %s, %s, %s)",(custm_name, product, qty, sale_amt, today))
    print(f"Sale of {product} with qty : {qty} @ {mrp} recorded")
    mycon.commit()
