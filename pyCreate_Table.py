import pymysql.cursors
 
conn = pymysql.connect(host='localhost',
        user='root',
        password='1969',
        db='python',
        charset='utf8mb4')
 
try:
    with conn.cursor() as cursor:
        sql = '''
            CREATE TABLE datatable (
                id int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
                Temp varchar(255) NOT NULL,
                value varchar(255) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8
'''        
        cursor.execute(sql)
    conn.commit()
finally:
    conn.close()
