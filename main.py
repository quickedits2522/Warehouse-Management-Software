import mysql.connector as ms
mycon = ms.connect(user = "root", password = "mysql", host = "localhost", database = "WMS", use_pure="True")
mycursor = mycon.cursor()

def create_init_db():
    init_tables=["CREATE TABLE IF NOT EXISTS USER(UserId int PRIMARY KEY, Name varchar(25), Department varchar(10), Salary int)",
                        "CREATE TABLE IF NOT EXISTS PRODUCTS(ProductID int PRIMARY KEY, Product_Name varchar(30), Cost_Price float, MRP float, Quantity int)",
                        "CREATE TABLE IF NOT EXISTS SALES(BillNo int PRIMARY KEY, Customer_Name varchar(25), Sale_Amount float, Date_Of_Sale date)",
                        "CREATE TABLE IF NOT EXISTS TRANSPORT(ShipmentID int PRIMARY KEY, BillNo int, Address varchar(100), FOREIGN KEY (BillNo) REFERENCES SALES(BillNo))"]

    for i in init_tables:
        mycursor.execute(i)
    mycon.commit()

def delete_db():
    print("!WARNING! : This process is irreversible, All your data will be deleted permanently!!")
    usr_confirm = input("Do you want to continue (Y/N) : ")
    if usr_confirm in "Yy":
        mycursor.execute("DROP TABLE IF EXISTS USER")
        mycursor.execute("DROP TABLE IF EXISTS PRODUCTS")
        mycursor.execute("DROP TABLE IF EXISTS SALES")
        mycursor.execute("DROP TABLE IF EXISTS TRANSPORT")
        print("Deleted all the tables")

    elif usr_confirm in "Nn" : 
        print("Operation Canceled")