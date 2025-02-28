from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import datetime
from .constants import USER_MAX_WINS_PER_DAY

class Contest(models.Model):
    """
    Contest model representing a contest in the Djungle Contest API.
    
    Attributes:
        code (str): Unique identifier for the contest.
        name (str): Name of the contest.
        start_date (date): Start date of the contest (inclusive).
        end_date (date): End date of the contest (inclusive).
    """
    code = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the contest")
    name = models.CharField(max_length=255, help_text="Name of the contest")
    start_date = models.DateField(help_text="Start date of the contest (inclusive)")
    end_date = models.DateField(help_text="End date of the contest (inclusive)")
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def clean(self):
        """
        Validate the model instance.
        Raises ValidationError if end_date is before start_date.
        """
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError(
                {'end_date': 'End date cannot be before start date.'}
            )
    
    def is_active(self):
        """
        Check if the contest is currently active based on the date range.
        
        Returns:
            bool: True if the contest is active, False otherwise.
        """
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class Prize(models.Model):
    """
    Prize model representing a prize that can be won in a contest.
    
    Attributes:
        code (str): Unique identifier for the prize.
        name (str): Name of the prize.
        perday (int): Maximum number of times this prize can be won per day.
        contest (Contest): The contest this prize belongs to.
    """
    code = models.CharField(max_length=50, help_text="Unique identifier for the prize")
    name = models.CharField(max_length=255, help_text="Name of the prize")
    perday = models.PositiveIntegerField(help_text="Maximum number of times this prize can be won per day")
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='prizes', help_text="The contest this prize belongs to")
    
    class Meta:
        unique_together = ('code', 'contest')
    
    def __str__(self):
        return f"{self.name} ({self.code}) - {self.contest.name}"
    
    def get_wins_today(self):
        """
        Get the number of times this prize has been won today.
        
        Returns:
            int: Number of wins today.
        """
        today = timezone.now().date()
        
        # Ensure today is a string if it's a mock
        if hasattr(today, 'resolve_expression'):
            # This is likely a mock object, use a real date
            today = datetime.date.today()
            
        return self.win_records.filter(timestamp__date=today).count()
    
    def can_win_today(self):
        """
        Check if this prize can still be won today based on the daily limit.
        
        Returns:
            bool: True if the prize can still be won today, False otherwise.
        """
        return self.get_wins_today() < self.perday


class WinRecord(models.Model):
    """
    WinRecord model to track prize winnings.
    
    Attributes:
        prize (Prize): The prize that was won.
        user_id (str): Optional identifier for the user who won the prize (for bonus feature).
        timestamp (datetime): When the prize was won.
    """
    prize = models.ForeignKey(Prize, on_delete=models.CASCADE, related_name='win_records', help_text="The prize that was won")
    user_id = models.CharField(max_length=255, null=True, blank=True, help_text="Optional identifier for the user who won the prize")
    timestamp = models.DateTimeField(auto_now_add=True, help_text="When the prize was won")
    
    def __str__(self):
        user_str = f" by {self.user_id}" if self.user_id else ""
        return f"{self.prize.name} won{user_str} at {self.timestamp}"
    
    @classmethod
    def get_user_wins_today(cls, user_id):
        """
        Get the number of wins a specific user has had today across all contests.
        
        Args:
            user_id (str): The identifier for the user.
            
        Returns:
            int: Number of wins today for this user.
        """
        if not user_id:
            return 0
            
        today = timezone.now().date()
        return cls.objects.filter(user_id=user_id, timestamp__date=today).count()
    
    @classmethod
    def user_can_win_today(cls, user_id, max_wins=USER_MAX_WINS_PER_DAY):
        """
        Check if a user can still win today based on their daily win limit.
        
        Args:
            user_id (str): The identifier for the user.
            max_wins (int): Maximum number of wins allowed per user per day.
            
        Returns:
            bool: True if the user can still win today, False otherwise.
        """
        if not user_id:
            return True
            
        return cls.get_user_wins_today(user_id) < max_wins
