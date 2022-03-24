import urllib3
import json
import firebase_admin
from firebase_admin import credentials, db

try:
    with open("credentials.json", "r") as cr:
        CREDENTIALS = json.load(cr)
except:
    print("Can't open credentials.json")
    exit()

cred = credentials.Certificate(CREDENTIALS["firebase"]["credentials_file"])
firebase_admin.initialize_app(cred, {
	"databaseURL": CREDENTIALS["firebase"]["db_url"]
})

class TG_bot:
    def __init__(self, token):
        self.T = token
        self.ID = None
        self.updateTimeout = 0
        self.link = "https://api.telegram.org/bot" + token
        self.offset = 0
        self.http = urllib3.PoolManager()
        
        self.getMe()

        self.menuMessges = {
            "root": {
                "levels": 2,
                "messages": [
                    "Этот бот поможет тебе закинуть однотипные посты в разные группы. Для начала, предлагаю добавить пару групп: /add_new",
                    "Теперь можно создать свой первый пост: /create_post",
                    "А теперь можешь полюбоваться своей работой))"
                ]
            },
            "addNew": {
               "levels": 2, 
               "messages": [
                   "Введи ссылку на чат в Telegram, можно ввести несколько, как закончишь введи /next",
                   "Отлично! Как группы кончатся, введи /next",
                   "Группы сохранены"
               ]
            },
            "createPost": {
                "levels": 2,
                "messages": [
                    "Просто введи сообщение и отправь его мне",
                    "Шикарно! Можешь создать еше один пост или выйти: /next",
                    "Обращайся и не забудь задонатить разработчику))"
                ]
            }
        }

        self.menuName = lambda num: list(self.menuMessges.keys())[num]
        self.WTN = lambda key: list(self.menuMessges.keys()).index(key)

    def getMe(self):
        data = self.__query("/getMe", {})
        if data["ok"]:
            self.ID = data["result"]["id"]

    def getUpdates(self):
        body = {
            "offset": self.offset,
            "timeout": self.updateTimeout
        }
        data = self.__query("/getUpdates", body)

        for upd in data["result"]:
            self.offset = int(upd["update_id"]) + 1
            
            if "my_chat_member" in upd: continue  
            uID = upd["message"]["from"]["id"]
            cID = upd["message"]["chat"]["id"]

            if "text" in upd["message"]:
                text = upd["message"]["text"]

            if "entities" in upd["message"]:
                for ent in upd["message"]["entities"]:
                    if ent["type"] == "bot_command":
                        self.__execCommand(text, cID, uID)
                    if ent["type"] == "url":
                        self.__execText(text, cID, uID)
            else:
                if self.__getMenuPlace(uID)["name"] == self.menuName(2):
                    self.__execText("", cID, uID, upd)
                else:
                    self.sendMessage(cID, "Принимаю только ссылки или команды")

    def setMyCommands(self):
        body = {
            "commands": json.dumps([
                {
                    "command": "/start",
                    "description": "Стартуем"
                },
                {
                    "command": "/about",
                    "description": "Что вообще происходит"
                },
                {
                    "command": "/add_new",
                    "description": "Добавить"
                },
                {
                    "command": "/create_post",
                    "description": "Создать пост"
                },
                {
                    "command": "/next",
                    "description": "Дальше по меню"
                }
            ])
        }

        self.__query("/deleteMyCommands", {})
        self.__query("/setMyCommands", body)

    def sendMessage(self, chatID, text):
        self.__query(
            "/sendMessage", 
            {
                "chat_id": chatID,
                "text": text
            }
        )

    def forwardMessage(self, chatID, fromID, messageID):
        data = self.__query(
            "/forwardMessage", 
            {
                "chat_id": chatID,
                "from_chat_id": fromID,
                "message_id": messageID
            }
        )

    def __getChatID(self, chatLink):
        chatLink = chatLink.replace("https://t.me/", "@")
        
        data = self.__query(
            "/getChat",
            {"chat_id": chatLink}
        )

        if data["ok"]:
            return data["result"]["id"]
        else:
            return False

    def __isAdmin(self, chatID):
        data = self.__query(
            "/getChatMember",
            {
                "chat_id": chatID,
                "user_id": self.ID
            }
        )

        return data["result"]["status"] == "administrator"

    def __query(self, method, fields):
        request = self.http.request(
            "GET", 
            self.link + method,
            fields=fields
        )

        return json.loads(request.data.decode('utf-8'))
    
    def __addUser(self, userID):
        ref = db.reference("/" + str(userID))
        if ref.get() is not None: return False

        ref.set({
            "groups": [],
            "actions": {
                "name": "root",
                "level": 0
            }
        })

    def __getMenuPlace(self, userID):
        ref = db.reference("/" + str(userID))
        if ref.get() is None: return False
        
        return ref.child("actions").get()

    def __pushGroup(self, userID, groupID):
        ref = db.reference("/" + str(userID))
        if ref.get() is None: return False

        ref.child("groups").push(groupID)

    def __menuNav(self, chatID, userID, menu, onNext, onMsg):
        ref = db.reference("/" + str(userID))
        if ref.get() is None: return False

        level = 0
        menu = menu if menu != "" else ref.child("actions/name").get()
        onExit = False

        if onNext:
            level = ref.child("actions/level").get()

            level += 1
            onExit = level == self.menuMessges[menu]["levels"]

        if onMsg:
            if onExit:
                self.sendMessage(chatID, self.menuMessges[menu]["messages"][level])
                level = self.WTN(menu)
                menu = "root"
                
            self.sendMessage(chatID, self.menuMessges[menu]["messages"][level])

        ref.child("actions/level").set(level)
        ref.child("actions/name").set(menu)
            
        return level

    def __getGroupList(self, userID):
        ref = db.reference("/" + str(userID))
        if ref.get() is None: return False

        data = ref.child("groups").get()
        out = []
        for g in data: out.append(data[g])

        return out

    def __execCommand(self, cmd, chatID, userID):
        if cmd == "/start":
            self.setMyCommands()
            self.__addUser(userID)
            self.sendMessage(chatID, "Hi!")
        if cmd == "/about":
            self.sendMessage(chatID, "Some strings about")
        if cmd == "/add_new":
            self.__menuNav(chatID, userID, self.menuName(1), False, True)
        if cmd == "/create_post":
            self.__menuNav(chatID, userID, self.menuName(2), False, True)
        if cmd == "/next":
            self.__menuNav(chatID, userID, "", True, True)

    def __execText(self, text, chatID, userID, fullMsg=None):
        mp = self.__getMenuPlace(userID)
        
        if mp["name"] == self.menuName(1) and mp["level"] < 2:
            if mp["level"] == 0: self.__menuNav(chatID, userID, "", True, False)

            groupID = self.__getChatID(text)
            if groupID and self.__isAdmin(groupID):
                self.sendMessage(chatID, self.menuMessges[mp["name"]]["messages"][1])
                self.__pushGroup(chatID, groupID)
            else:
                self.sendMessage(chatID, "Бот не является администратором канала! Или канал приватный")

        if mp["name"] == self.menuName(2) and mp["level"] < 2:
            if mp["level"] == 0: self.__menuNav(chatID, userID, "", True, False)

            messageID = fullMsg["message"]["message_id"]
            for groupID in self.__getGroupList(userID):
                self.forwardMessage(groupID, userID, messageID)

            self.sendMessage(chatID, self.menuMessges[mp["name"]]["messages"][1])
