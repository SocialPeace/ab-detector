from tinydb import TinyDB, Query

class UserModel:

    def __init__(self, path='db.json'):
        self.db = TinyDB(path)

    def upsert_user(self, user):
        if not self.db.search(Query().id == user.id):
            self.db.insert(user.serialize())
            return 1
        return 0 

    def get_user(self, user_id):
        user = self.db.search(Query().id == user_id)
        return UserData.deserialize(user[0])

    def remove_user(self, user_id):
        self.db.remove(Query().id == user_id)

class UserData:
    
    def __init__(self, user=None):
        if user:
            user_info = user['kakao_account']['profile']
            self.id = user['id']
            self.nickname = user_info['nickname']  
            self.location = user['location']
            self.friend = user['friend']
        else:
            self.id = None
            self.nickname = None 
            self.location = None
            self.friend = None

    def __str__(self):
        return "<UserData>(id:%s, nickname:%s)" \
                % (self.id, self.nickname)

    def serialize(self):
        return {
            "id": self.id,
            "nickname": self.nickname, 
            "location": self.location,
            "friend": self.friend
        }

    @staticmethod
    def deserialize(user_data):
        user = UserData()
        user.id = user_data['id']
        user.nickname = user_data['nickname'] 
        user.location = user['location']
        user.friend = user['friend']
        return user