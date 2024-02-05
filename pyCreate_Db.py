import pymysql.cursors
conn = pymysql.connect(host='localhost',
                       user='root',
                       password='1969',
                       charset='utf8mb4')

try:
    with conn.cursor() as cursor:
        sql = 'CREATE DATABASE rs485db'         #data base name :python
        cursor.execute(sql)
    conn.commit()

finally:
    conn.close()
    
