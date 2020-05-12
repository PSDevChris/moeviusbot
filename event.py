#Event-Class

import json
from myfunc import log

class Event:    
    def __init__ (self, eventType):
        self.eventType = eventType
        self.eventTime = ''
        self.eventGame = ''
        self.eventMembers = {}

        self.load()
        
    def updateEvent(self, eventTime, eventGame):
        self.eventTime = eventTime
        self.eventGame = eventGame
        self.save()

    def addMember(self, newMember):
        if newMember.id not in self.eventMembers.keys():
            self.eventMembers[newMember.id] = newMember.display_name
            self.save()
        
    def reset(self):
        self.eventTime = ''
        self.eventGame = ''
        self.eventMembers = {}
        
        self.save()
            
    def save(self):
        with open(self.eventType + '.json', 'w') as f:
            json.dump(self.__dict__, f)
            
    def load(self):
        try:
            with open(self.eventType + '.json', 'r') as f:
                data = f.read()

                self.eventTime = json.loads(data)['eventTime']
                log(f'Event-Zeit für {self.eventType} wurde geladen: {self.eventTime}')

                self.eventGame = json.loads(data)['eventGame']
                log(f'Event-Game für {self.eventType} wurde geladen: {self.eventGame}')

                self.eventMembers = json.loads(data)['eventMembers']
                log(f'Event-Members für {self.eventType} wurden geladen: {self.eventMembers}')
        except:
            pass
            log(f'Event {self.eventType} konnte nicht geladen werden!')