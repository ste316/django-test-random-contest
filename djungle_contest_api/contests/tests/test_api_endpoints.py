"""
Tests for API endpoints.

This module contains tests for all API endpoints and expected status codes.
"""
import datetime
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from contests.models import Contest, Prize, WinRecord


class PlayEndpointTests(TestCase):
    """Tests for the /play/ endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create an active contest
        self.active_contest = Contest.objects.create(
            code="ACTIVE_API",
            name="Active API Test Contest",
            start_date=timezone.now().date() - datetime.timedelta(days=1),
            end_date=timezone.now().date() + datetime.timedelta(days=1)
        )
        
        # Create a prize for the active contest
        self.prize = Prize.objects.create(
            code="PRIZE_API",
            name="API Test Prize",
            perday=10,
            contest=self.active_contest
        )
        
        # Create a past contest (not active)
        self.past_contest = Contest.objects.create(
            code="PAST_API",
            name="Past API Test Contest",
            start_date=timezone.now().date() - datetime.timedelta(days=10),
            end_date=timezone.now().date() - datetime.timedelta(days=2)
        )
        
        # Create a future contest (not active yet)
        self.future_contest = Contest.objects.create(
            code="FUTURE_API",
            name="Future API Test Contest",
            start_date=timezone.now().date() + datetime.timedelta(days=2),
            end_date=timezone.now().date() + datetime.timedelta(days=10)
        )
        
        # URL for the play endpoint - using namespace
        self.play_url = reverse('contests:play')
    
    def test_missing_contest_parameter(self):
        """Test the /play/ endpoint with missing contest parameter (400 Bad Request)."""
        response = self.client.get(self.play_url)
        
        # Check status code
        self.assertEqual(response.status_code, 400)
        
        # Check response content
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Missing required parameter', data['error'])
    
    def test_nonexistent_contest(self):
        """Test the /play/ endpoint with a non-existent contest code (404 Not Found)."""
        response = self.client.get(f"{self.play_url}?contest=NONEXISTENT")
        
        # Check status code
        self.assertEqual(response.status_code, 404)
        
        # Check response content
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Contest not found', data['error'])
    
    def test_inactive_past_contest(self):
        """Test the /play/ endpoint with a past contest (422 Unprocessable Entity)."""
        response = self.client.get(f"{self.play_url}?contest={self.past_contest.code}")
        
        # Check status code
        self.assertEqual(response.status_code, 422)
        
        # Check response content
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('not active', data['error'])
    
    def test_inactive_future_contest(self):
        """Test the /play/ endpoint with a future contest (422 Unprocessable Entity)."""
        response = self.client.get(f"{self.play_url}?contest={self.future_contest.code}")
        
        # Check status code
        self.assertEqual(response.status_code, 422)
        
        # Check response content
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('not active', data['error'])
    
    def test_valid_contest(self):
        """Test the /play/ endpoint with a valid, active contest (200 OK)."""
        response = self.client.get(f"{self.play_url}?contest={self.active_contest.code}")
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check response structure
        data = json.loads(response.content)
        self.assertIn('win', data)
        self.assertIn('contest', data)
        self.assertEqual(data['contest'], self.active_contest.code)
        
        # The 'prize' field might be null (loss) or an object (win)
        if data['win']:
            self.assertIsNotNone(data['prize'])
            self.assertIn('code', data['prize'])
            self.assertIn('name', data['prize'])
        else:
            self.assertIsNone(data['prize'])
    
    def test_valid_contest_with_user(self):
        """Test the /play/ endpoint with a valid contest and user parameter (200 OK)."""
        response = self.client.get(f"{self.play_url}?contest={self.active_contest.code}&user=test_user123")
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check response structure
        data = json.loads(response.content)
        self.assertIn('win', data)
        self.assertIn('contest', data)
        self.assertEqual(data['contest'], self.active_contest.code)
        
        # The 'prize' field might be null (loss) or an object (win)
        if data['win']:
            self.assertIsNotNone(data['prize'])
            self.assertIn('code', data['prize'])
            self.assertIn('name', data['prize'])
            
            # Verify a win record was created with the correct user_id
            win_record = WinRecord.objects.filter(
                prize__contest__code=self.active_contest.code,
                user_id='test_user123'
            ).first()
            
            if win_record:
                self.assertEqual(win_record.user_id, 'test_user123')
        else:
            self.assertIsNone(data['prize'])
    
    def test_max_daily_limit_reached(self):
        """Test the /play/ endpoint when the prize daily limit is reached."""
        # Create WinRecord entries to reach the daily limit
        for i in range(self.prize.perday):
            WinRecord.objects.create(
                prize=self.prize,
                user_id=f"test_user_{i}"
            )
        
        # Make a request
        response = self.client.get(f"{self.play_url}?contest={self.active_contest.code}")
        
        # Check status code (should still be 200 even when no win is possible)
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = json.loads(response.content)
        self.assertIn('win', data)
        self.assertFalse(data['win'])  # Should not win
        self.assertIsNone(data['prize'])  # Prize should be null
    
    def test_debug_mode(self):
        """Test the /play/ endpoint with debug mode enabled."""
        response = self.client.get(f"{self.play_url}?contest={self.active_contest.code}&debug=true")
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check for debug information in the response
        data = json.loads(response.content)
        self.assertIn('debug_info', data)
        
        # Debug info should contain relevant information
        debug_info = data['debug_info']
        self.assertIn('timestamp', debug_info)
        self.assertIn('contest_status', debug_info)
        self.assertIn('daily_limit', debug_info)
        self.assertIn('wins_today', debug_info)
    
    def test_multiple_requests_same_user(self):
        """Test multiple requests from the same user."""
        user_id = "repeat_user"
        
        # Make 20 requests with the same user
        results = []
        for i in range(20):
            response = self.client.get(f"{self.play_url}?contest={self.active_contest.code}&user={user_id}")
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            if data['win']:
                results.append(True)
            else:
                results.append(False)
        
        # Count how many wins the user got
        win_count = results.count(True)
        
        # Get actual win records from the database
        db_win_count = WinRecord.objects.filter(
            prize__contest=self.active_contest,
            user_id=user_id
        ).count()
        
        # Verify consistency between response and database
        self.assertEqual(win_count, db_win_count)
        
        # Daily limit should not be exceeded
        self.assertLessEqual(win_count, self.prize.perday)


class IndexEndpointTests(TestCase):
    """Tests for the / (index) endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create an active contest
        self.active_contest = Contest.objects.create(
            code="ACTIVE_INDEX",
            name="Active Index Test Contest",
            start_date=timezone.now().date() - datetime.timedelta(days=1),
            end_date=timezone.now().date() + datetime.timedelta(days=1)
        )
        
        # URL for the index endpoint - using namespace
        self.index_url = reverse('contests:index')
    
    def test_index_json_response(self):
        """Test the index endpoint JSON response."""
        # Set Accept header to prefer JSON
        response = self.client.get(self.index_url, HTTP_ACCEPT='application/json')
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = json.loads(response.content)
        self.assertIn('name', data)
        self.assertIn('version', data)
        self.assertIn('active_contests', data)
        self.assertIn('endpoints', data)
        
        # Validate endpoints information
        endpoints = data['endpoints']
        self.assertTrue(any(e['path'] == '/' for e in endpoints))
        self.assertTrue(any(e['path'] == '/play/' for e in endpoints))
    
    def test_index_html_response(self):
        """Test the index endpoint HTML response."""
        # Set Accept header to prefer HTML
        response = self.client.get(self.index_url, HTTP_ACCEPT='text/html')
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check response content type
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')


class StatsEndpointTests(TestCase):
    """Tests for the /stats/ endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create an active contest
        self.active_contest = Contest.objects.create(
            code="ACTIVE_STATS",
            name="Active Stats Test Contest",
            start_date=timezone.now().date() - datetime.timedelta(days=1),
            end_date=timezone.now().date() + datetime.timedelta(days=1)
        )
        
        # Create a prize for the active contest
        self.prize = Prize.objects.create(
            code="PRIZE_STATS",
            name="Stats Test Prize",
            perday=10,
            contest=self.active_contest
        )
        
        # Create some win records
        for i in range(5):
            WinRecord.objects.create(
                prize=self.prize,
                user_id=f"stats_user_{i}"
            )
        
        # URL for the stats endpoint - using namespace
        self.stats_url = reverse('contests:stats')
    
    def test_missing_contest_parameter(self):
        """Test the /stats/ endpoint with missing contest parameter (400 Bad Request)."""
        response = self.client.get(self.stats_url)
        
        # Check status code
        self.assertEqual(response.status_code, 400)
        
        # Check response content
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_nonexistent_contest(self):
        """Test the /stats/ endpoint with a non-existent contest code (404 Not Found)."""
        response = self.client.get(f"{self.stats_url}?contest=NONEXISTENT")
        
        # Check status code
        self.assertEqual(response.status_code, 404)
        
        # Check response content
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_valid_contest_stats(self):
        """Test the /stats/ endpoint with a valid contest (200 OK)."""
        response = self.client.get(f"{self.stats_url}?contest={self.active_contest.code}")
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check response structure
        data = json.loads(response.content)
        self.assertIn('contest', data)
        self.assertIn('prizes', data)
        self.assertIn('wins_today', data)
        
        # Validate contest information
        self.assertEqual(data['contest']['code'], self.active_contest.code)
        self.assertEqual(data['contest']['name'], self.active_contest.name)
        
        # Validate prize information
        prizes = data['prizes']
        self.assertEqual(len(prizes), 1)
        self.assertEqual(prizes[0]['code'], self.prize.code)
        self.assertEqual(prizes[0]['name'], self.prize.name)
        self.assertEqual(prizes[0]['perday'], self.prize.perday)
        
        # Validate win information
        self.assertEqual(data['wins_today'], 5)
    
    def test_valid_contest_stats_with_debug(self):
        """Test the /stats/ endpoint with debug mode (200 OK)."""
        response = self.client.get(f"{self.stats_url}?contest={self.active_contest.code}&debug=true")
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check for debug information
        data = json.loads(response.content)
        self.assertIn('debug_info', data)
        
        # Debug info should contain distribution information
        debug_info = data['debug_info']
        self.assertIn('daily_stats', debug_info) 