import urllib3
import json
import firebase_admin
from firebase_admin import credentials, db

try:
    with open("./src/credentials.json", "r") as f:
        CREDENTIALS = json.load(f)
    with open("./src/dialogs.json", "r") as f:
        DIALOGS = json.load(f)
    with open("./src/TG_commands.json", "r") as f:
        COMMANDS = json.load(f)
except:
    print("Can't open credentials.json")
    exit()

cred = credentials.Certificate(CREDENTIALS["firebase"]["credentials_file"])
firebase_admin.initialize_app(cred, {
	"databaseURL": CREDENTIALS["firebase"]["db_url"]
})

def dialog(fullPath=""):
    path = fullPath.split("/")
    cmd = path.pop()
    
    def search(i, obj):
        for d in obj:
            if path[i] == d["name"]:
                if i == len(path) - 1:
                    return d["dialog"][cmd]
                else:
                    return search(i+1, d["inner"])
        
        return False

    return search(0, DIALOGS)

dialog("root/add_new/good")
    
class TG_bot:
    def __init__(self, token):
        self.T = token
        self.ID = None
        self.updateTimeout = 0
        self.link = "https://api.telegram.org/bot" + token
        self.offset = 0
        self.http = urllib3.PoolManager()
        
        if not self.getMe():
            print("api problem, check token")
            exit()

    def getMe(self):
        data = self.__query("/getMe", {})
        if data["ok"]:
            self.ID = data["result"]["id"]
        else:
            return False

        return True

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

            action = self.__menuNav(cID)

            if action != "root":
                if "add_new" in action:
                    self.__addNew(upd["message"], cID, uID)
                if "create_post" in action:
                    self.__createPost(upd["message"], cID, uID)
                    print("create_post")
                
                continue

            if "entities" in upd["message"]:
                onCommand = False
                for ent in upd["message"]["entities"]:
                    if ent["type"] == "bot_command":
                        onCommand = True
                        self.__execCommand(upd["message"]["text"], cID, uID)
                
                if not onCommand:
                    self.sendMessage(cID, self.__msg("root/error"))
            else:
                self.sendMessage(cID, self.__msg("root/error"))

    def setMyCommands(self):
        self.__query("/deleteMyCommands", {})
        self.__query("/setMyCommands", {"commands": json.dumps(COMMANDS)})

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

    def __msg(self, fullPath="", dialog=True):
        path = fullPath.split("/")
        if dialog: cmd = path.pop()
        
        def search(i, obj):
            for d in obj:
                if path[i] == d["name"]:
                    if i == len(path) - 1:
                        if dialog:
                            return d["dialog"][cmd]
                        else:
                            return d["message"]
                    else:
                        return search(i+1, d["inner"])
            
            return False

        return search(0, DIALOGS)
        
    def __isAdmin(self, chatID):
        data = self.__query(
            "/getChatMember",
            {
                "chat_id": chatID,
                "user_id": self.ID
            }
        )

        return data["result"]["status"] == "administrator"

    def __query(self, method, fields, timeout=None):
        request = self.http.request(
            "GET", 
            self.link + method,
            fields=fields,
            timeout=timeout
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

    def __pushGroup(self, userID, groupID):
        ref = db.reference("/" + str(userID))
        if ref.get() is None: return False

        groups = ref.child("groups").get()

        for g in groups:
            if groupID == groups[g]: return False
        
        ref.child("groups").push(groupID)
        return True

    def __menuNav(self, userID, menu=None):
        ref = db.reference("/" + str(userID))
        if ref.get() is None: return False

        current = ref.child("actions/name").get()

        if menu == "back":
            if current != "root":
                current = "/".join(current.split("/")[:-1])
                ref.child("actions/name").set(current)
            
            return current
        elif menu != None:
            current = menu

        ref.child("actions/name").set(current)

        return current 

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
            self.sendMessage(chatID, self.__msg("root", False))
        if cmd == "/about":
            self.sendMessage(chatID, self.__msg("about", False))
        if cmd == "/add_new":
            self.sendMessage(chatID, self.__msg("root/add_new", False))
            self.__menuNav(userID, "root/add_new")
        if cmd == "/create_post":
            self.sendMessage(chatID, self.__msg("root/create_post", False))
            self.__menuNav(userID, "root/create_post")
        if cmd == "/exit":
            self.__menuNav(userID, "back")
            self.sendMessage(chatID, self.__msg("root/back"))

    def __addNew(self, message, chatID, userID):
        url = None
        if "entities" in message:
            for ent in message["entities"]:
                if ent["type"] == "bot_command":
                    if message["text"] == "/exit":
                        self.__menuNav(userID, "back")
                        self.sendMessage(chatID, self.__msg("root/add_new/exit"))
                        return True
                if ent["type"] == "url":
                    url = message["text"]
            if url is None:
                self.sendMessage(chatID, self.__msg("root/add_new/bad"))
                return False
        else:
            self.sendMessage(chatID, self.__msg("root/add_new/bad"))
            return False

        groupID = self.__getChatID(url)
        if groupID and self.__isAdmin(groupID):
            if not self.__pushGroup(userID, groupID):
                self.sendMessage(chatID, self.__msg("root/add_new/exists"))
            else:
                self.sendMessage(chatID, self.__msg("root/add_new/good"))
        else:
            self.sendMessage(chatID, self.__msg("root/add_new/bad"))

    def __createPost(self, message, chatID, userID):
        if "entities" in message:
            for ent in message["entities"]:
                if ent["type"] == "bot_command":
                    if message["text"] == "/exit":
                        self.__menuNav(userID, "back")
                        self.sendMessage(chatID, self.__msg("root/create_post/exit"))
                        return True

        for groupID in self.__getGroupList(userID):
            self.forwardMessage(groupID, userID, message["message_id"])

        self.sendMessage(chatID, self.__msg("root/create_post/good"))

        return True
