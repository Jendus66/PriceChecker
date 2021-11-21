import requests
from lxml import html
import sys
import mysql.connector
from datetime import datetime
from pushover import Client


#Alza
def Alza(link):
    """Input: product url on alza.cz, return: price of the product on alza.cz"""
    link = link.strip()
    r = requests.get(link, headers=headers)
    xpath_pre = html.fromstring(r.content)
    price_raw = xpath_pre.cssselect(".bigPrice")
    
    # If price was not found try this one:
    if not price_raw:
        price_raw = xpath_pre.cssselect(".price_withVat")
    price_raw2 = ""
    
    # If price still was not found try this (product is probably on sale)
    if not price_raw:
        price_raw = xpath_pre.cssselect(".pricenormal > td:nth-child(2) > span:nth-child(1)")
    for i in price_raw:
        price_raw2 = i.text_content()
    # Remove some characters to be able to convert string to int
    price = price_raw2.replace(",-", "").replace(chr(160), "")
    # Convert string to int and insert product price to database
    try:
        price = int(price)
        InsertPrice(price, link)
        return price
    except ValueError:
        return -1
        

#CZC
def CZC(link):
    """Input: product url on czc.cz, return: price of the product on czc.cz"""
    link = link.strip()
    r = requests.get(link, headers=headers)
    xpath_pre = html.fromstring(r.content)
    # Get price element
    price_raw_list = xpath_pre.cssselect("span.price:nth-child(1) > span:nth-child(2)")
    
    if not price_raw_list:
        price_raw_list = xpath_pre.cssselect(".action > span:nth-child(2)")
    
    price_raw = ""
    for i in price_raw_list:
        price_raw = i.text_content()
    price = price_raw.replace("Kč", "").replace(chr(160),"")

    # Convert string to int and insert product price to database
    try:
        price = int(price)
        InsertPrice(price, link)
        return price
    except ValueError:
        return -1


#Mall
def Mall(link):
    """Input: product url on mall.cz, return: price of the product on mall.cz"""
    link = link.strip()
    r = requests.get(link, headers=headers)
    xpath_pre = html.fromstring(r.content)
    price_raw = ""
    price_raw_list = xpath_pre.cssselect(".final-price")
    if not price_raw_list:
        price_raw_list = xpath_pre.cssselect(".price__wrap__box__final")
    for x in price_raw_list:
        price_raw = x.text_content()
    price = price_raw.strip()[:-3].replace(chr(32), "")
    # Convert string to int and insert product price to database
    try:
        price = int(price)
        InsertPrice(price, link)
        return price
    except ValueError:
        return -1


#Mironet
def Mironet(link):
    """Input: product url on mironet.cz, return: price of the product on mironet.cz"""
    link = link.strip()
    r = requests.get(link, headers=headers)
    xpath_pre = html.fromstring(r.content)
    price_raw_list = xpath_pre.cssselect(".product_cena_box > span:nth-child(1)")
    price_raw = ""
    for i in price_raw_list:
        price_raw = i.text_content()

    price = price_raw.strip()[:-3].replace(chr(160), "")
    # Convert string to int and insert product price to database
    try:
        price = int(price)
        InsertPrice(price, link)
        return price
    except ValueError:
        return -1


def SendMail(receive, message, shop, product, price):
    """This function sends email.
    Input: receivers email, message, shop and product."""
    import smtplib, ssl
    global cursor

    # Senders gmail adress and password
    sender = "xxx@gmail.com"
    password = "password"

    context = ssl.create_default_context()
    time = str(datetime.now().strftime("%d.%m.%Y"))
    with smtplib.SMTP_SSL("smtp.gmail.com", port=465, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, receive, message)

    # Insert a timestamp of the sent email to the database
    query_send_mail = f"""INSERT INTO pc_mail_sent(receiver, datum, shop, product, price) 
VALUES('{receive}', STR_TO_DATE('{time}', '%d.%m.%Y'), '{shop}', '{product}', {price});"""
    cursor.execute(query_send_mail)
    print("Email odeslán")


def InsertPrice(price, link):
    """Insert a current price of product to the database. Input: price (integer), link (product url as string), no return."""
    global cursor

    today = datetime.now().strftime("%d.%m.%Y")
    query = f"""UPDATE pc_records SET actual_price={price}, datum=STR_TO_DATE('{today}', '%d.%m.%Y')
WHERE url='{link}'"""
    cursor.execute(query)


def SentMailCheck(mail, shop, price, product):
    """Function for checking if the email has been already sent. Input: mail (receivers email adress,
shop (name of the eshop), price (price of the product), product (name of the product). Return: False (email has not been sent yet),
True (email has been already sent - record exists in the database)
"""
    global cursor
    today = datetime.now().strftime("%d.%m.%Y")

    query = f"""SELECT * FROM pc_mail_sent
    WHERE receiver = '{mail}'
    AND shop = '{shop}'
    AND price = {price}
    AND product = '{product}'
    AND datum = STR_TO_DATE('{today}', '%d.%m.%Y')
    """
    cursor.execute(query)
    result = cursor.fetchone()

    if result:
        return True
    else:
        return False

def notify(api, key, message, title):
    """Function for sending a notification to smartphone via Pushover app."""
    client = Client(key,api_token = api)
    client.send_message(message,title=title)

##### PROGRAM #####

# Headers for request library
headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'}

# SQL query to get active products and their urls. Price will be got for these products/urls. The SQL query also
# returns Pushover api code and Pushover api key
query = """select pmp.product, pmp.price, pr.url, pmp.email, u.pushover_api, u.pushover_key from pc_min_price pmp
left join pc_records pr on pmp.product_id = pr.product_id
left join users u on pmp.email = u.email
where pmp.active = 1
order by pmp.product"""

# Connection to DB settings
db_conn = mysql.connector.connect(host="localhost", user="user", passwd="password", database="database")
cursor = db_conn.cursor()
cursor.execute(query)

results = cursor.fetchall()

# Loop for all the products for which price will be got
for row in results:
    produkt = row[0]
    price_min = row[1]
    link = row[2]
    email = row[3]
    api = row[4]
    key = row[5]

# If for Alza.cz eshop
    if "alza" in link:
        # Get product price on eshop website
        price_alza = Alza(link)
        if price_alza <= price_min and price_alza != -1:
            # If price is lower than limit price and price was found on the website then send notification/email
            sent_mail = SentMailCheck(email, "Alza", price_alza, produkt)

            # If notification/email has not been already sent than send it
            if not sent_mail:
                message = f"""Subject: {produkt} - Alza snizila cenu! \n
Cena na Alze je nyni {price_alza} Kc.\n
                """
                SendMail(email, message, "Alza", produkt, price_alza)
                msg_notify = f"Cena na Alze je nyní {price_alza} Kč.\n {link}"
                notify(api,key,msg_notify,f"Alza - {produkt}")

# If for CZC.cz eshop
    elif "czc" in link:
        # Get product price on eshop website
        price_czc = CZC(link)
        if price_czc <= price_min and price_czc != -1:
            # If price is lower than limit price and price was found on the website then send notification/email
            sent_mail = SentMailCheck(email, "CZC", price_czc, produkt)

            # If notification/email has not been already sent than send it
            if not sent_mail:
                message = f"""Subject: {produkt} - CZC snizilo cenu! \n
Cena na CZC je nyni {price_czc} Kc.\n
            """
                SendMail(email, message, "CZC", produkt, price_czc)
                msg_notify = f"Cena na CZC je nyní {price_czc} Kč.\n {link}"
                notify(api,key,msg_notify,f"CZC - {produkt}")

# If for Mall.cz eshop
    elif "mall" in link:
        # Get product price on eshop website
        price_mall = Mall(link)
        if price_mall <= price_min and price_mall != -1:
            # If price is lower than limit price and price was found on the website then send notification/email
            sent_mail = SentMailCheck(email, "Mall", price_mall, produkt)

            # If notification/email has not been already sent than send it
            if not sent_mail:
                message = f"""Subject: {produkt} - Mall snizil cenu! \n
Cena na Mall je nyni {price_mall} Kc.\n
            """
                SendMail(email, message, "Mall", produkt, price_mall)
                msg_notify = f"Cena na Mall.cz je nyní {price_mall} Kč.\n {link}"
                notify(api,key,msg_notify,f"Mall - {produkt}")

# If for Mironet.cz eshop
    elif "mironet" in link:
        # Get product price on eshop website
        price_mironet = Mironet(link)
        if price_mironet <= price_min and price_mironet != -1:
            # If price is lower than limit price and price was found on the website then send notification/email
            sent_mail = SentMailCheck(email, "Mironet", price_mironet, produkt)

            # If notification/email has not been already sent than send it
            if not sent_mail:
                message = f"""Subject: {produkt} - Mironet snizil cenu! \n
Cena na Mironet je nyni {price_mironet} Kc.\n
            """
                SendMail(email, message, "Mironet", produkt, price_mironet)
                msg_notify = f"Cena na Mironet je nyní {price_mironet} Kč.\n {link}"
                notify(api,key,msg_notify,f"Mironet - {produkt}")

    else:
        # Eshop was not found (eshop supported: Alza.cz, CZC.cz, Mall.cz, Mironet.cz)
        print("Nenalezen eshop.")

db_conn.commit()
db_conn.close()
print("Hotovo")
