import MySQLdb
import discord
import asyncio
from datetime import datetime

class DB_Wrapper:

    def __init__(self, user, passwd, host, db):
        self.user = user
        self.passwd = passwd
        self.host = host
        self.db = db
        return

    async def execute(self, client, member, sql_command, args=None, notify=False):
        try:
            db_connection = MySQLdb.connect(user=self.user, passwd=self.passwd, host=self.host, db=self.db, charset="utf8mb4")
            cursor = db_connection.cursor()
            cursor.execute(sql_command, args)
            result = cursor.fetchall()
            db_connection.commit()
            cursor.close()
            db_connection.close()
        except Exception as e:
            time = str(datetime.now())
            print(time+": failed to properly execute DB command: "+sql_command)
            print("The exception that occurred was: "+str(e))
            if notify:
                await client.send_message(member, "I had some trouble with a database query. Please ask Chish#2578 to check the logs at time "+time)
            return
        return result
