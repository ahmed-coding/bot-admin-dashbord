import requests
import json

class BaseSettings:
    
    for_futuer = False
    for_spot = False
    testent = False
    data = []
    endpoint = 'http://127.0.0.1:8000/'
    url = endpoint + 'api/settings/?'
    headers = {
    "Content-Type": "application/json"
}
    def __init__(self, for_futuer = False, for_spot=False, testent= False):
        self.for_futuer = for_futuer
        self.for_spot = for_spot
        self.testent = testent
        if for_futuer:
            self.url = self.url + "&for_futer=true"
        if for_spot:
            self.url = self.url + "&for_spot=true"
        
        request = requests.get(self.url, headers=self.headers)
        
        self.data = request.json()
        
    def update(self):
        
        request = requests.get(self.url, headers=self.headers)
        
        self.data = request.json()
    
    def api_key(self):
        
        if self.testent:
            for item in self.data:
                if item['key'] == 'api_test_key':
                    return item['value']
        
        
        for item in self.data:
            if item['key'] == 'api_key':
                return item['value']
            
        return None

    

    def api_secret(self):
        
        if self.testent:
            for item in self.data:
                if item['key'] == 'api_test_secret':
                    return item['value']
        
        
        for item in self.data:
            if item['key'] == 'api_secret':
                return item['value']
        return None


    def bot_status(self):
        
        for item in self.data:
            if item['key'] == 'bot_status':
                return item['value'] == '1' 
    
    
        return None


    def max_trad(self):
        
        for item in self.data:
            if item['key'] == 'max_trad':
                return int(item['value'])
        return None




    def can_trad(self):
        
        for item in self.data:
            if item['key'] == 'can_trad':
                return item['value'] == '1'
        return None



    def investment(self):
        
        for item in self.data:
            if item['key'] == 'investment':
                return float(item['value'])
        return None
    
    
    
    
    def leverage(self):
        
        for item in self.data:
            if item['key'] == 'leverage':
                return int(item['value'])
        return None
    
    
    
    def profit_target(self):
        
        for item in self.data:
            if item['key'] == 'profit_target':
                return float(item['value'])
        return None



    def stop_loss(self):
        
        for item in self.data:
            if item['key'] == 'stop_loss':
                return float(item['value'])
            
        return None
    

    def klines_interval(self):
        
        for item in self.data:
            if item['key'] == 'klines_interval':
                return item['value']
        return None


    def klines_limit(self):
        
        for item in self.data:
            if item['key'] == 'klines_limit':
                return int(item['value'])
        return None

    def count_top_symbols(self):
        
        for item in self.data:
            if item['key'] == 'count_top_symbols':
                return item['value']
        return None
    
    

    def active_buy(self):
        
        for item in self.data:
            if item['key'] == 'active_buy':
                return item['value']
        return None
    
    
    def active_sell(self):
        
        for item in self.data:
            if item['key'] == 'active_sell':
                return item['value']
        return None
    


setting= BaseSettings(False,True)


print(setting.profit_target())
