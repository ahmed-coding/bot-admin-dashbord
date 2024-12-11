from django.db import models
# Create your models here.

class Symbol(models.Model):
    symbol = models.CharField(max_length=100,unique=True)
    return_value = models.FloatField()  # Avoid naming it 'return', as it's a reserved keyword
    trades = models.IntegerField()
    win_rate = models.FloatField()
    best_trade = models.FloatField()
    worst_trade = models.FloatField()
    max_duration = models.CharField(max_length=100)  # Use CharField if duration is a string like "2h30m"
    avg_duration = models.CharField(max_length=100)
    created_time= models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.symbol
    

class FSymbol(models.Model):
    symbol = models.CharField(max_length=100,unique=True)
    return_value = models.FloatField()  # Avoid naming it 'return', as it's a reserved keyword
    trades = models.IntegerField()
    win_rate = models.FloatField()
    best_trade = models.FloatField()
    worst_trade = models.FloatField()
    max_duration = models.CharField(max_length=100)  # Use CharField if duration is a string like "2h30m"
    avg_duration = models.CharField(max_length=100)
    created_time= models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.symbol



class Trade(models.Model):
    symbol= models.CharField(max_length=100)
    quantity= models.FloatField()
    initial_price= models.FloatField()
    target_price= models.FloatField()
    stop_price= models.FloatField()
    start_time = models.DateTimeField(verbose_name="Start time", auto_now=False, auto_now_add=False)
    timeout = models.CharField(max_length=50)
    investment = models.FloatField()
    is_open= models.BooleanField(default= True)
    created_time= models.DateTimeField(auto_now_add=True)
    updated_time= models.DateTimeField(auto_now=True)
    is_futuer= models.BooleanField(default= False)
    def __str__(self):
        return self.symbol
    
    

class BotSettings(models.Model):
    key= models.CharField(max_length=100)
    value= models.CharField(max_length=100)
    
    def __str__(self):
        return self.key
    
