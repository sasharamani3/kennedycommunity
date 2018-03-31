import random
import pymysql
import pymysql.cursors

from helpers import rundbquery
from application import getDBsize
from werkzeug.security import generate_password_hash


for currentuser in range(2, getDBsize()+1):
    pw = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
    hash = generate_password_hash(pw)

    print('User ' + str(currentuser) + ' gets default pw ' + str(pw))

    query = "Update innodb.alumni set defaultpass = %(pw)s, password = %(hash)s where id = %(id)s"
    params = {}
    params['pw'] = pw
    params['hash'] = hash
    params['id'] = currentuser
    rundbquery(query,params)