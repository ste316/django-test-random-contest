"""
Tests for WinRecord model and user win limits.

This module contains tests for tracking wins and enforcing user-specific limits.
"""
import datetime
from django.test import TestCase
from django.utils import timezone
from contests.models import Contest, Prize, WinRecord


class WinRecordTests(TestCase):
    """Tests for the WinRecord model and win tracking."""
    
    def setUp(self):
        """Set up test data."""
        # Create a contest
        self.contest = Contest.objects.create(
            code="WIN_TEST",
            name="Win Record Test Contest",
            start_date=timezone.now().date() - datetime.timedelta(days=1),
            end_date=timezone.now().date() + datetime.timedelta(days=1)
        )
        
        # Create a prize for the contest
        self.prize = Prize.objects.create(
            code="WIN_PRIZE",
            name="Win Record Test Prize",
            perday=10,
            contest=self.contest
        )
    
    def test_create_win_record(self):
        """Test creating a win record."""
        # Create a win record
        win_record = WinRecord.objects.create(
            prize=self.prize,
            user_id="test_user"
        )
        
        # Verify the win record was created
        self.assertIsNotNone(win_record.id)
        self.assertEqual(win_record.prize, self.prize)
        self.assertEqual(win_record.user_id, "test_user")
        self.assertIsNotNone(win_record.timestamp)
    
    def test_win_record_string_representation(self):
        """Test the string representation of a WinRecord."""
        # Create a win record
        win_record = WinRecord.objects.create(
            prize=self.prize,
            user_id="test_user"
        )
        
        # Check the string representation
        self.assertIn(self.prize.name, str(win_record))
        self.assertIn("test_user", str(win_record))
    
    def test_win_record_with_null_user(self):
        """Test creating a win record without a user ID."""
        # Create a win record without a user_id
        win_record = WinRecord.objects.create(
            prize=self.prize
        )
        
        # Verify the win record was created
        self.assertIsNotNone(win_record.id)
        self.assertEqual(win_record.prize, self.prize)
        self.assertIsNone(win_record.user_id)
        
        # Check the string representation
        self.assertIn(self.prize.name, str(win_record))
        self.assertNotIn("by", str(win_record))  # Should not include "by" since there's no user
    
    def test_get_wins_today(self):
        """Test the get_wins_today method of the Prize model."""
        # Initially there should be no wins
        self.assertEqual(self.prize.get_wins_today(), 0)
        
        # Create 5 win records for today
        for i in range(5):
            WinRecord.objects.create(
                prize=self.prize,
                user_id=f"user_{i}"
            )
        
        # Verify the count is correct
        self.assertEqual(self.prize.get_wins_today(), 5)
    
    def test_can_win_today(self):
        """Test the can_win_today method of the Prize model."""
        # Initially the prize should be winnable
        self.assertTrue(self.prize.can_win_today())
        
        # Create win records up to the daily limit
        for i in range(self.prize.perday):
            WinRecord.objects.create(
                prize=self.prize,
                user_id=f"user_{i}"
            )
        
        # Now the prize should not be winnable
        self.assertFalse(self.prize.can_win_today())
    
    def test_win_record_related_name(self):
        """Test accessing win records from a prize using the related_name."""
        # Create some win records
        for i in range(3):
            WinRecord.objects.create(
                prize=self.prize,
                user_id=f"user_{i}"
            )
        
        # Access win records using the related_name
        win_records = self.prize.win_records.all()
        self.assertEqual(win_records.count(), 3)
        
        # Verify the win records belong to the prize
        for record in win_records:
            self.assertEqual(record.prize, self.prize)


class UserWinLimitsTests(TestCase):
    """Tests for user-specific win limits (Bonus Feature)."""
    
    def setUp(self):
        """Set up test data."""
        # Create a contest
        self.contest = Contest.objects.create(
            code="USER_LIMIT",
            name="User Limit Test Contest",
            start_date=timezone.now().date() - datetime.timedelta(days=1),
            end_date=timezone.now().date() + datetime.timedelta(days=1)
        )
        
        # Create a prize for the contest
        self.prize = Prize.objects.create(
            code="USER_PRIZE",
            name="User Limit Test Prize",
            perday=10,
            contest=self.contest
        )
        
        # Define a user ID for testing
        self.test_user_id = "limit_test_user"
    
    def test_get_user_wins_today(self):
        """Test counting wins for a specific user today."""
        # Initially there should be no wins for this user
        user_wins = WinRecord.objects.filter(
            prize__contest=self.contest,
            user_id=self.test_user_id,
            timestamp__date=timezone.now().date()
        ).count()
        self.assertEqual(user_wins, 0)
        
        # Create 3 win records for this user
        for i in range(3):
            WinRecord.objects.create(
                prize=self.prize,
                user_id=self.test_user_id
            )
        
        # Verify the count is correct
        user_wins = WinRecord.objects.filter(
            prize__contest=self.contest,
            user_id=self.test_user_id,
            timestamp__date=timezone.now().date()
        ).count()
        self.assertEqual(user_wins, 3)
    
    def test_user_win_limit_enforcement(self):
        """Test enforcing a maximum number of wins per user per day."""
        # Define a maximum number of wins per user per day
        MAX_WINS_PER_USER = 2
        
        # Create win records up to the limit
        for i in range(MAX_WINS_PER_USER):
            WinRecord.objects.create(
                prize=self.prize,
                user_id=self.test_user_id
            )
        
        # Check if user has reached the limit
        user_wins_today = WinRecord.objects.filter(
            prize__contest=self.contest,
            user_id=self.test_user_id,
            timestamp__date=timezone.now().date()
        ).count()
        
        user_can_win = user_wins_today < MAX_WINS_PER_USER
        
        # User should not be able to win more
        self.assertFalse(user_can_win)
    
    def test_different_users_separate_limits(self):
        """Test that win limits are tracked separately for different users."""
        # Define a maximum number of wins per user per day
        MAX_WINS_PER_USER = 2
        
        # Create win records for first user up to the limit
        for i in range(MAX_WINS_PER_USER):
            WinRecord.objects.create(
                prize=self.prize,
                user_id="user_1"
            )
        
        # User 1 should have reached the limit
        user1_wins_today = WinRecord.objects.filter(
            prize__contest=self.contest,
            user_id="user_1",
            timestamp__date=timezone.now().date()
        ).count()
        self.assertEqual(user1_wins_today, MAX_WINS_PER_USER)
        
        # Create a win record for a different user
        WinRecord.objects.create(
            prize=self.prize,
            user_id="user_2"
        )
        
        # User 2 should have one win and be under the limit
        user2_wins_today = WinRecord.objects.filter(
            prize__contest=self.contest,
            user_id="user_2",
            timestamp__date=timezone.now().date()
        ).count()
        self.assertEqual(user2_wins_today, 1)
        user2_can_win = user2_wins_today < MAX_WINS_PER_USER
        self.assertTrue(user2_can_win)
    
    def test_win_limits_across_contests(self):
        """Test that win limits are tracked separately across different contests."""
        # Create another contest
        second_contest = Contest.objects.create(
            code="SECOND_LIMIT",
            name="Second User Limit Test Contest",
            start_date=timezone.now().date() - datetime.timedelta(days=1),
            end_date=timezone.now().date() + datetime.timedelta(days=1)
        )
        
        # Create a prize for the second contest
        second_prize = Prize.objects.create(
            code="SECOND_PRIZE",
            name="Second User Limit Test Prize",
            perday=10,
            contest=second_contest
        )
        
        # Define a maximum number of wins per user per day per contest
        MAX_WINS_PER_USER = 2
        
        # Create win records for the first contest up to the limit
        for i in range(MAX_WINS_PER_USER):
            WinRecord.objects.create(
                prize=self.prize,
                user_id=self.test_user_id
            )
        
        # User should have reached the limit for the first contest
        user_wins_contest1 = WinRecord.objects.filter(
            prize__contest=self.contest,
            user_id=self.test_user_id,
            timestamp__date=timezone.now().date()
        ).count()
        self.assertEqual(user_wins_contest1, MAX_WINS_PER_USER)
        
        # User should still be able to win in the second contest
        user_wins_contest2 = WinRecord.objects.filter(
            prize__contest=second_contest,
            user_id=self.test_user_id,
            timestamp__date=timezone.now().date()
        ).count()
        self.assertEqual(user_wins_contest2, 0)
        
        # Create a win in the second contest
        WinRecord.objects.create(
            prize=second_prize,
            user_id=self.test_user_id
        )
        
        # Verify the count is correct for both contests
        user_wins_contest1 = WinRecord.objects.filter(
            prize__contest=self.contest,
            user_id=self.test_user_id,
            timestamp__date=timezone.now().date()
        ).count()
        self.assertEqual(user_wins_contest1, MAX_WINS_PER_USER)
        
        user_wins_contest2 = WinRecord.objects.filter(
            prize__contest=second_contest,
            user_id=self.test_user_id,
            timestamp__date=timezone.now().date()
        ).count()
        self.assertEqual(user_wins_contest2, 1)
        
        # User can still win in second contest
        user_can_win_contest2 = user_wins_contest2 < MAX_WINS_PER_USER
        self.assertTrue(user_can_win_contest2) 