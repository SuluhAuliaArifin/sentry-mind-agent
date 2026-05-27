import requests

class Executor:
    def execute(self, action):
        if action["type"] == "webhook":
            return requests.post(
                action["url"],
                json=action["payload"]
            ).json()

        if action["type"] == "log":
            print(action["message"])
            return {"status": "logged"}

        return {"status": "unknown_action"}