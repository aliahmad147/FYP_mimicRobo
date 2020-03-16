import threading
from time import sleep
from threading import Timer
import pyttsx3
class mythread(threading.Thread):
    def __init__(self, i):
        threading.Thread.__init__(self)
        self.line = i
    def run(self):
        print ("Value send", self.line)
        engine = pyttsx3.init()
        try:
            print (self.line)
            engine.say(self.line)
            engine.runAndWait()
        except:
            engine.endLoop()
            print("Error--")
            self.run()
            #raise Exception('exception in code')

        finally:
            pyttsx3.engine.Engine.stop(engine)
            #pyttsx3.driver.DriverProxy.setBusy(engine, busy=False)