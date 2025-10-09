import mysql.connector as ms
con = ms.connect(host="localhost", user="root", passwd="mysql", database="users")
cursor = con.cursor()

"""rec01 = eval(input("Enter record 1 for table Users: "))
rec02 = eval(input("Enter record 2 for table Users: "))
rec03 = eval(input("Enter record 3 for table Users: "))
rec04 = eval(input("Enter record 3 for table Users: "))
rec05 = eval(input("Enter record 4 for table Users: "))

rec1 = eval(input("Enter record 1 for table Products: "))
rec2= eval(input("Enter record 2 for table Products: "))
rec3= eval(input("Enter record 3 for table Products: "))
rec4 = eval(input("Enter record 4 for table Products: "))
rec5 = eval(input("Enter record 5 for table Products: "))"""



def add_user():
    values = eval(input("Enter the entry to be inserted into the table: "))
    cursor.execute("insert into user1 values(%s)"%(values,))
    con.commit()
    print("Entry successfully added to the table")

def remove_user():
    delete = input("Enter userID of the entry to be deleted: ")
    cursor.execute("delete from %s where %s = '%s'"%(users, userID, delete))
    con.commit()
    print("Entry successfully deleted from the table")

def search_user():
    user = input("Enter userID of the user to be found: ")
    cursor.execute("select * from user1 where userID = '%s'"%(user,))
    data = cursor.fetchall()
    for row in data:
        print(row)

def update_user():
    column = input("Enter column where the value is to be changed: ")
    value1 = input("Enter userID of the entry to be updated: ")
    value2 = input("Enter updated value: ")
    cursor.execute("update %s set %s = %s where userID='%s'"%(column,value2,value1))
    con.commit()
    print("Value successfully updated")
    

def add_stock():
    value = eval(input("Enter entry to be added to 'Products': "))
    cursor.execute("insert into Products values(%s)"%(value,))
    con.commit()
    print("Record successfully added")


def premove_product():
    value = input("Enter the productID of the entry to be deleted: ")
    cursor.execute("delete from %s where %s = %s"%(Products, ProductID, value))
    con.commit()
    print("Entry successfully deleted from the table")


def search_product():
    product = input("Enter the productID of the entry to be dislayed: ")
    cursor.execute("Select * from %s where %s = %s"%(Products, ProductID, product))
    data = cursor.fetchall()
    for row in data:
        print(row)

def  update_product():
    column = input("Enter column where the value is to be changed: ")
    value1 = input("Enter productID of the entry to be updated: ")
    value2 = input("Enter updated value: ")
    cursor.execute("update %s set %s = %s where userID='%s'"%(column,value2,value1))
    con.commit()
    print("Value successfully updated")

    

    
    
 
