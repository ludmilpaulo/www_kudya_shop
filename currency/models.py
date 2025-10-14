# currency/models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta

class ExchangeRate(models.Model):
    """Store daily exchange rates for currency conversion"""
    
    base_currency = models.CharField(max_length=3, default='AOA')  # Base currency (Angolan Kwanza)
    target_currency = models.CharField(max_length=3, db_index=True)  # Target currency code
    rate = models.DecimalField(max_digits=18, decimal_places=6)  # Exchange rate
    date = models.DateField(auto_now_add=True, db_index=True)  # Rate date
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('base_currency', 'target_currency', 'date')
        ordering = ['-date', 'target_currency']
        indexes = [
            models.Index(fields=['base_currency', 'target_currency', '-date']),
        ]
    
    def __str__(self):
        return f"{self.base_currency}/{self.target_currency}: {self.rate} ({self.date})"
    
    @classmethod
    def get_latest_rate(cls, from_currency='AOA', to_currency='USD'):
        """Get the latest exchange rate between two currencies"""
        if from_currency == to_currency:
            return 1.0
        
        # Try to get today's rate
        today = timezone.now().date()
        rate = cls.objects.filter(
            base_currency=from_currency,
            target_currency=to_currency,
            date=today
        ).first()
        
        if rate:
            return float(rate.rate)
        
        # Fallback to most recent rate (within last 7 days)
        week_ago = today - timedelta(days=7)
        rate = cls.objects.filter(
            base_currency=from_currency,
            target_currency=to_currency,
            date__gte=week_ago
        ).order_by('-date').first()
        
        if rate:
            return float(rate.rate)
        
        # Return 1.0 as ultimate fallback
        return 1.0
    
    @classmethod
    def needs_update(cls, base_currency='AOA'):
        """Check if rates need updating (older than 12 hours)"""
        today = timezone.now().date()
        twelve_hours_ago = timezone.now() - timedelta(hours=12)
        
        recent_rate = cls.objects.filter(
            base_currency=base_currency,
            date=today,
            last_updated__gte=twelve_hours_ago
        ).first()
        
        return recent_rate is None

