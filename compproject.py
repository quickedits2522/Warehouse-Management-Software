import mysql.connector as ms
con = ms.connect(host="localhost", user="root", passwd="mysql", database="db1")
cursor = con.cursor()
n = y
m = y

while True:
    a = input("Enter  userID: ")
    b =  input("Enter username: ")
    c = input("Enter  department: ")
    d = int(input("Enter  salary: "))
    cursor.execute("insert into users values =%(s)"(a,b,c,d))
    m = input("Do you wish to continue?(y/n) ")
    if m=='y' or m=='Y':
        break
    
while True:
    e = input("Enter  productID: ")
    f = input("Enter product name: ")
    g = input("Enter cost price of product: ")
    h = int(input("Enter MRP of product: "))
    i = int(input("Enter  quantity of product: "))
    cursor.execute("insert into products values%(s)" %(e,f,g,h,i))
    n = input("Do you wish to continue?(y/n) ")
    if n=='y' or n=='Y':
        break
    
def add_user():
    values = eval(input("Enter the entry to be inserted into the table: "))
    cursor.execute("insert into users values(%s)"%(values,))
    con.commit()
    print("Entry successfully added to the table")

def remove_user():
    delete = input("Enter userID of the entry to be deleted: ")
    cursor.execute("delete from users where userID = '%s'"%(delete))
    con.commit()
    print("Entry successfully deleted from the table")

def search_user():
    user = input("Enter userID of the user to be found: ")
    cursor.execute("select * from users where userID = '%s'"%(user,))
    data = cursor.fetchall()
    for row in data:
        print(row)

def update_user():
    column = input("Enter column where the value is to be changed: ")
    value1 = input("Enter userID of the entry to be updated: ")
    value2 = input("Enter updated value: ")
    cursor.execute("update users set %s = %s where userID='%s'"%(column,value2,value1))
    con.commit()
    print("Value successfully updated")
    

def add_stock():
    value = eval(input("Enter entry to be added to 'Products': "))
    cursor.execute("insert into Products values(%s)"%(value,))
    con.commit()
    print("Record successfully added")


def premove_product():
    value = input("Enter the productID of the entry to be deleted: ")
    cursor.execute("delete from Products where %s = %s"%(ProductID, value))
    con.commit()
    print("Entry successfully deleted from the table")


def search_product():
    product = input("Enter the productID of the entry to be dislayed: ")
    cursor.execute("Select * from Products where %s = %s"%(ProductID, product))
    data = cursor.fetchall()
    for row in data:
        print(row)

def  update_product():
    column = input("Enter column where the value is to be changed: ")
    value1 = input("Enter productID of the entry to be updated: ")
    value2 = input("Enter updated value: ")
    cursor.execute("update Products set %s = %s where userID='%s'"%(column,value2,value1))
    con.commit()
    print("Value successfully updated")

