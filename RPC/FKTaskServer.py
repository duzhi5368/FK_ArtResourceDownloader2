import logging
import json
from threading import Thread
from flask import Flask, jsonify, request

from RPC.FKBrowserRequester import FKBrowserRequester

#================================================================

__TEST_ART_STATION_URL__ = "https://www.artstation.com/users/freeknight/projects.json?page=1"

class FKTaskServer:
    def __init__(self):
        self.requester = FKBrowserRequester()
        self.thread = None

    def Request(self, url):
        return self.requester.SendAndWait(url)
    
    def Telnet(self):
        while True:
            resp = self.Request(__TEST_ART_STATION_URL__)
            print("telnet ArtStation successed.")
            # todo: other web page
        
    def StartTelnetask(self):
        thread = Thread(target=self.Telnet)
        thread.setDaemon(True)
        thread.start()
    
    def IsRunning(self):
        if self.thread is None:
            return False
        if self.thread.is_alive():
            return True
        return False
    
    def Start(self):
        if self.IsRunning():
            return False
        
        def Run():
            app.run(debug=True, port=2333, use_reloader=False)
            app.logger.setLevel(logging.WRANING)
        
        self.thread = Thread(target=Run)
        self.thread.setDaemon(True)
        self.thread.start()
    
#================================================================

FKServer = FKTaskServer()

__all__ = ("FKServer")

app = Flask(__name__)

#================================================================

@app.route("/tasks/")
def GetTask():
    task = FKServer.requester.GetRequest(10)
    if task is None:
        return jsonify([])
    else:
        return jsonify([task, 1])

@app.route("/tasks/submit/", methods=["POST", "GET"])
def TaskSumbit():
    resp = request.data
    FKServer.requester.SubmitResponse(resp)
    return jsonify({})

#================================================================
# only for test
if __name__ == '__main__':
    FKServer.Start()
    FKServer.StartTelnetask()