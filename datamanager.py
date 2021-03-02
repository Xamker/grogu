import psycopg2


class Datamanager:
    """
    This class is used to communicate with a PostgresSQL database
    Attributes:
        -self.connection, that is the connection to the database;
        -self.cursors, that allows us to move in the database;
    Methods:
        -add_faction(self, name_faction): it adds to the table factions a new row under the key name_faction;

        -remove_faction(self, name_faction): remove name_faction from factions table;

        -add_user(user_id, name_faction, captain, daily_points,
                points, daily_time, total_time, warnings): adds a user to "users" table;

        -remove_user(user_id): remove a user with id = user_id from table "users";

        -update_user(user_id, daily_points, points, daily_time, total_time, warnings): update user values in table "users";

        -get_all_users(): get all users from table "users";

        -get_all_factions(): get all factions from table "factions";

        -get_ranks(): return a  list made by rank of faction(sum of point of users in a faction) for all faction;

        -get_players_from_faction(name_faction): return a list made by all users in the faction "name_faction";

        -get_user(user_id): get user from table "users" where id = user_id;
    """
    def __init__(self, dbname, user, password, host, port):
        self.connection = psycopg2.connect(dbname=dbname, user=user, password=password,
                                           host = host, port = port,  sslmode='require')
        self.cursor = self.connection.cursor()
        #self.teams = dict()

    def add_faction(self, namefaction, id_channel):
        self.cursor.execute("INSERT INTO factions (name, id_channel) VALUES (%s, %s);", (namefaction, id_channel))
        self.connection.commit()

    def remove_faction(self, namefaction):
        self.cursor.execute("DELETE FROM factions WHERE name = %s;", (namefaction,))
        self.connection.commit()

    def get_id_channel(self, namefaction):
        self.cursor.execute("SELECT id_channel FROM factions WHERE name = %s;", (namefaction,))
        return self.cursor.fetchone()[0]

    def add_user(self, user_id, namefaction, captain, daily_points=0.0, points=0.0, daily_time=0.0, total_time=0.0, warnings=0):
        print(user_id, namefaction, captain)
        self.cursor.execute("INSERT INTO users (id, namefaction_fk, captain, daily_points, points, daily_time, total_time, warnings) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
                                                 (user_id, namefaction, captain, daily_points, points, daily_time, total_time, warnings))
        self.connection.commit()

    def remove_user(self, user_id):
        self.cursor.execute("DELETE FROM users WHERE id=%s;", (user_id,))
        self.connection.commit()

    def update_user(self, user_id, daily_points, points, daily_time, total_time, warnings):
        # self.cursor.execute("SELECT  daily_points, points, daily_time,
        #                       total_time, warnings FROM users WHERE id = %s;", (user_id,))
        self.cursor.execute(
            "UPDATE users SET daily_points = %s, points = %s, daily_time = %s, total_time = %s, warnings = %s WHERE id = %s;",
            (daily_points, points, daily_time, total_time, warnings, user_id))
        print("In updateUser")
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()

    def get_all_users(self):
        self.cursor.execute("SELECT * FROM users;")
        return self.cursor.fetchall()

    def query_all_users(self):
        self.cursor.execute("SELECT id, captain, namefaction_fk, daily_points, points, daily_time, total_time, warnings FROM users;")
        return self.cursor.fetchall()

    def get_all_factions(self):
        self.cursor.execute("SELECT * FROM factions;")
        return self.cursor.fetchall()

    def get_rank_factions(self):
        factions = self.get_all_factions()
        name_factions = [faction[0] for faction in factions]
        scores = dict()
        for name_faction in name_factions:
            self.cursor.execute("SELECT SUM(points) AS score FROM users where namefaction_fk = %s;", (name_faction,))
            scores[name_faction] = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE namefaction_fk = %s;", (name_faction,))
            number_members = self.cursor.fetchone()[0]
            scores[name_faction] = scores[name_faction]/number_members
        rank_list = sorted(scores.items(), key = lambda score: score[1], reverse = True)
        return rank_list

    def get_rank_users(self):
        users = self.get_all_users()
        user_ids = [user[0] for user in users]
        scores = dict()
        for user_id in user_ids:
            self.cursor.execute("SELECT points, total_time FROM users WHERE id = %s;", (user_id,))
            datas = self.cursor.fetchone()
            scores[user_id] = (datas[0], datas[1])
        rank_list = sorted(scores.items(), key = lambda score: score[1][0], reverse = True)
        return rank_list

    def get_players_from_faction(self, name_faction):
        self.cursor.execute("SELECT id FROM users where namefaction_fk = %s;", (name_faction,))
        return self.cursor.fetchall()

    def get_faction_from_id(self, user_id):
        #self.cursor.execute("SELECT EXISTS ( SELECT 1 FROM users WHERE id = %s);", (user_id,))
        #if self.cursor.fetchone()[0]:
        self.cursor.execute("SELECT namefaction_fk FROM users WHERE id = %s;", (user_id,))
        return self.cursor.fetchone()[0]
        #return None

    def get_faction_name(self, name_faction):
        self.cursor.execute("SELECT name FROM factions WHERE name= %s;", (name_faction,))
    def get_user(self, user_id):
        self.cursor.execute("SELECT daily_points, points, daily_time, total_time, warnings FROM users WHERE id = %s;",
                            (user_id,))
        return self.cursor.fetchone()

    def is_captain(self, user_id):
        self.cursor.execute("SELECT captain FROM users WHERE id = %s;",
                            (user_id,))
        return self.cursor.fetchone()