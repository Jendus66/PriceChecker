# PriceChecker

PriceChecker is a Python script, which checks products urls saved in a database and scrapes their prices. If the scrapped price is lower than set price (limit price for buying) then the script sends email or notification to smartphone via Pushover app.

![Screenshot](notification2.jpg)

**Database**

There need to be 3 tables in the database for the python script. SQL queries for tables create are in file sql.txt<br />

**1) pc_min_price**<br />
Table pc_min_price contains all the products for which prices will be scrapped. Columns:<br />
a) product_id - unique product id (integer - auto increase)<br />
b) product - product name<br />
c) price - limit price when I want to buy (E.g. if the price is set to 1500 then I get a notification when a product price on a website is lower than 1500)<br />
d) datum - date of record insertion to the database<br />
e) email - email address for notification<br />
f) active - 1 - active (price will be scrapped), 0 - not active (price wont be scrapped)

![Screenshot](pc_min_price.png)


**2) pc_records**<br />
Table pc_records contains product urls for individual eshop and their current price on the websites. Columns:<br />
a) record_id - unique record id<br />
b) product_id - product id, foreign key from pc_min_price<br />
c) url - product url for the particular eshop<br />
d) actual_price - the last scrapped price from the website<br />
f) datum - the last scrapping date<br />

![Screenshot](pc_records.png)

**3) pc_mail_sent**<br />
Table pc_mail_sent contains records of all sent emails and notifications. Columns:<br />
a) receiver - receivers email address<br />
b) datum - notification/email sent date<br />
c) shop - eshop for which was notification sent<br />
d) product - product for which was notification sent<br />
f) price - product price on the eshop for which was notification sent<br />

![Screenshot](pc_mail_sent.png)

**price_check_db_gt.py**<br />
The python script for the prices scrapping from the individual eshops websites. The script has these steps:
1) Gets active products and their urls from the database<br />
2) Gets the current product price from the urls<br />
3) Update the current price in the database (table pc_records)<br />
4) Check if current price is lower than limit price for buying and if a notification has been already sent<br />
5) Send notification via Pushover app if the current price is lower then the limit price and a notification has not been sent yet<br />
