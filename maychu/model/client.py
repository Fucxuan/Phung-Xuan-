import sqlite3

class Client:
    def __init__(self, name, age, CCCD):
        self.name = name
        self.age = age
        self.CCCD = CCCD

    def save_to_db(self):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute('INSERT INTO client VALUES (?, ?, ?)', (self.name,self.age, self.CCCD))
        conn.commit()
        conn.close()
   
    

    def check_if_account_exists(self):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute('SELECT * FROM clients WHERE username = ?', (self.name,))
        if c.fetchone() is None:
            return False
        else:
            return True
        
    def check_CCCD(self):
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        if self.check_if_account_exists():
            c.execute('SELECT * FROM clients WHERE username = ?', (self.name,))
            result = c.fetchone()
            if result[1] == self.CCCD:
                return True
            else:
                return False
        else:
            return False

    @staticmethod
    def get_all_client():
        conn = sqlite3.connect('database.sqlite')
        c = conn.cursor()
        c.execute('SELECT * FROM clients')
        client_data = c.fetchall()
        clients = []
        for data in client_data:
            name, age,CCCD = data
            client = Client(name, age, CCCD)
            clients.append(client)
        print("CLIENT-DB", clients)
        conn.close()
        return clients
