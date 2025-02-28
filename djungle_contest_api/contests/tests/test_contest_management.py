"""
Tests for Contest Management functionality.

This module contains tests for Contest CRUD operations and model methods.
"""
import datetime
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from contests.models import Contest, Prize, WinRecord


class ContestModelTests(TestCase):
    """Tests for Contest model functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create a contest that is currently active
        self.active_contest = Contest.objects.create(
            code="ACTIVE",
            name="Active Contest",
            start_date=timezone.now().date() - datetime.timedelta(days=1),
            end_date=timezone.now().date() + datetime.timedelta(days=1)
        )
        
        # Create a contest that has ended
        self.past_contest = Contest.objects.create(
            code="PAST",
            name="Past Contest",
            start_date=timezone.now().date() - datetime.timedelta(days=10),
            end_date=timezone.now().date() - datetime.timedelta(days=2)
        )
        
        # Create a contest that will start in the future
        self.future_contest = Contest.objects.create(
            code="FUTURE",
            name="Future Contest",
            start_date=timezone.now().date() + datetime.timedelta(days=2),
            end_date=timezone.now().date() + datetime.timedelta(days=10)
        )
    
    def test_create_contest(self):
        """Test that contests can be created correctly."""
        contest = Contest.objects.create(
            code="TEST",
            name="Test Contest",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + datetime.timedelta(days=30)
        )
        
        # Verify contest was created
        self.assertEqual(contest.code, "TEST")
        self.assertEqual(contest.name, "Test Contest")
        self.assertEqual(contest.start_date, timezone.now().date())
        self.assertEqual(contest.end_date, timezone.now().date() + datetime.timedelta(days=30))
        
        # Verify we can retrieve the contest from the database
        retrieved_contest = Contest.objects.get(code="TEST")
        self.assertEqual(retrieved_contest.name, "Test Contest")
    
    def test_string_representation(self):
        """Test the string representation of Contest objects."""
        self.assertEqual(
            str(self.active_contest), 
            f"Active Contest (ACTIVE)"
        )
    
    def test_is_active_method(self):
        """Test the is_active method of Contest objects."""
        # Test an active contest
        self.assertTrue(self.active_contest.is_active())
        
        # Test a past contest
        self.assertFalse(self.past_contest.is_active())
        
        # Test a future contest
        self.assertFalse(self.future_contest.is_active())
    
    def test_update_contest(self):
        """Test updating contest fields."""
        # Update the active contest
        self.active_contest.name = "Updated Contest Name"
        self.active_contest.end_date = timezone.now().date() + datetime.timedelta(days=5)
        self.active_contest.save()
        
        # Retrieve the contest again and verify updates
        updated_contest = Contest.objects.get(code="ACTIVE")
        self.assertEqual(updated_contest.name, "Updated Contest Name")
        self.assertEqual(updated_contest.end_date, timezone.now().date() + datetime.timedelta(days=5))
    
    def test_delete_contest(self):
        """Test deleting a contest."""
        # Create a temporary contest
        temp_contest = Contest.objects.create(
            code="TEMP",
            name="Temporary Contest",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + datetime.timedelta(days=1)
        )
        
        # Verify it exists
        self.assertTrue(Contest.objects.filter(code="TEMP").exists())
        
        # Delete it
        temp_contest.delete()
        
        # Verify it's gone
        self.assertFalse(Contest.objects.filter(code="TEMP").exists())
    
    def test_invalid_date_range(self):
        """Test validation for contests with end_date before start_date."""
        # Create a contest with an invalid date range
        with self.assertRaises(ValidationError):
            contest = Contest(
                code="INVALID",
                name="Invalid Date Contest",
                start_date=timezone.now().date() + datetime.timedelta(days=5),
                end_date=timezone.now().date()
            )
            contest.full_clean()  # This should raise a ValidationError
    
    def test_duplicate_code(self):
        """Test that contest codes must be unique."""
        # Try to create a contest with a duplicate code
        with self.assertRaises(Exception):  # Could be IntegrityError or ValidationError depending on implementation
            Contest.objects.create(
                code="ACTIVE",  # This code already exists
                name="Another Active Contest",
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + datetime.timedelta(days=1)
            )


class PrizeModelTests(TestCase):
    """Tests for Prize model functionality related to contests."""
    
    def setUp(self):
        """Set up test data."""
        # Create a contest
        self.contest = Contest.objects.create(
            code="TEST",
            name="Test Contest",
            start_date=timezone.now().date() - datetime.timedelta(days=1),
            end_date=timezone.now().date() + datetime.timedelta(days=1)
        )
    
    def test_create_prize(self):
        """Test that prizes can be created and associated with contests."""
        prize = Prize.objects.create(
            code="PRIZE1",
            name="Test Prize",
            perday=10,
            contest=self.contest
        )
        
        # Verify prize was created
        self.assertEqual(prize.code, "PRIZE1")
        self.assertEqual(prize.name, "Test Prize")
        self.assertEqual(prize.perday, 10)
        self.assertEqual(prize.contest, self.contest)
        
        # Verify we can retrieve the prize from the database
        retrieved_prize = Prize.objects.get(code="PRIZE1", contest=self.contest)
        self.assertEqual(retrieved_prize.name, "Test Prize")
        
        # Verify we can access prizes from the contest
        self.assertEqual(self.contest.prizes.count(), 1)
        self.assertEqual(self.contest.prizes.first().code, "PRIZE1")
    
    def test_update_prize(self):
        """Test updating prize fields."""
        # Create a prize
        prize = Prize.objects.create(
            code="PRIZE2",
            name="Original Prize Name",
            perday=5,
            contest=self.contest
        )
        
        # Update the prize
        prize.name = "Updated Prize Name"
        prize.perday = 20
        prize.save()
        
        # Retrieve the prize again and verify updates
        updated_prize = Prize.objects.get(code="PRIZE2", contest=self.contest)
        self.assertEqual(updated_prize.name, "Updated Prize Name")
        self.assertEqual(updated_prize.perday, 20)
    
    def test_delete_prize(self):
        """Test deleting a prize."""
        # Create a temporary prize
        temp_prize = Prize.objects.create(
            code="TEMP",
            name="Temporary Prize",
            perday=10,
            contest=self.contest
        )
        
        # Verify it exists
        self.assertTrue(Prize.objects.filter(code="TEMP", contest=self.contest).exists())
        
        # Delete it
        temp_prize.delete()
        
        # Verify it's gone
        self.assertFalse(Prize.objects.filter(code="TEMP", contest=self.contest).exists())
    
    def test_contest_cascading_delete(self):
        """Test that deleting a contest also deletes associated prizes."""
        # Create a temporary contest
        temp_contest = Contest.objects.create(
            code="TEMP_CONTEST",
            name="Temporary Contest",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + datetime.timedelta(days=1)
        )
        
        # Create a prize associated with the temporary contest
        Prize.objects.create(
            code="PRIZE_TEMP",
            name="Temporary Prize",
            perday=10,
            contest=temp_contest
        )
        
        # Verify the prize exists
        self.assertTrue(Prize.objects.filter(code="PRIZE_TEMP", contest=temp_contest).exists())
        
        # Delete the contest
        temp_contest.delete()
        
        # Verify the contest and associated prize are gone
        self.assertFalse(Contest.objects.filter(code="TEMP_CONTEST").exists())
        self.assertFalse(Prize.objects.filter(code="PRIZE_TEMP").exists()) 