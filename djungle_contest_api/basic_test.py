'''
Basic test for the Djungle Contest API /play endpoint

This test script:
1. Creates a test Contest and Prize in the database
2. Tests the /play endpoint with different user scenarios
3. Verifies proper API responses
'''
import os
import django
import requests
import json
from datetime import datetime, timedelta
import random
import time

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djungle_contest_api.settings')
django.setup()

# Now we can import Django models
from contests.models import Contest, Prize, WinRecord
from django.utils import timezone
from django.db import connection

def cleanup_test_data():
    Contest.objects.filter(code__startswith='test_').delete()

def setup_test_data(force_cleanup=False):
    """
    Create test contest and prize data for testing.
    
    Returns:
        tuple: (contest, prize) objects created for testing
    """
    # Generate a unique code for this test run
    test_code = f"test_{int(time.time())}"
    
    # Create date range (today and 7 days from now)
    today = timezone.now().date()
    end_date = today + timedelta(days=7)
    
    # Delete any existing test contests to avoid conflicts
    if force_cleanup:
        cleanup_test_data()
    # Create a new test contest
    contest = Contest.objects.create(
        code=test_code,
        name=f"Test Contest {test_code}",
        start_date=today,
        end_date=end_date
    )
    
    # Create a prize for the contest with 10 available per day
    prize = Prize.objects.create(
        code=f"{test_code}_prize",
        name=f"Test Prize for {test_code}",
        perday=100,
        contest=contest
    )

    print(f"Created test contest: {contest.name} ({contest.code})")
    print(f"Created test prize: {prize.name} ({prize.code})")
    print(f"Prize perday: {prize.perday}")
    
    return contest, prize

def test_play_endpoint(contest, prize):
    """
    Test the /play endpoint with various scenarios.
    
    Args:
        contest: The Contest model instance to test with
        prize: The Prize model instance to test with
    """
    # Base URL - assuming the server is running locally
    base_url = "http://127.0.0.1:8000"
    play_url = f"{base_url}/play"
    
    # Test Case 1: Valid contest with anonymous user
    print("\nTest Case 1: Valid contest with anonymous user")
    response = requests.get(f"{play_url}?contest={contest.code}")
    
    if response.status_code == 200:
        print(f"✅ Success! Status code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        print(f"Win result: {'🎉 WIN!' if result.get('win') else '❌ No win'}")
    else:
        print(f"❌ Failed! Status code: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test Case 2: Multiple requests with same user
    user_id = f"test_user_{random.randint(1000, 9999)}"
    max_attempts = 250
    print(f"\nTest Case 2: Multiple requests with same user (user_id: {user_id}), total attempts: {max_attempts}")
    
    tot_wins = 0
    # Make 5 attempts with the same user
    for i in range(max_attempts):
        response = requests.get(f"{play_url}?contest={contest.code}&user={user_id}")
        
        if response.status_code == 200:
            result: dict = response.json()
            if result.get('win') == True:
                print(f"  Attempt {i+1}: '🎉 WIN!'")
                tot_wins += 1

        else:
            print(f"  Attempt {i+1}: ❌ Failed with status code {response.status_code}")
    
    print(f"\nTotal wins: {tot_wins}/{max_attempts}")

    # Test Case 6: Multiple requests without specifying user
    print(f"\nTest Case 3: Multiple requests without specifying user, total attempts: {max_attempts}")
    
    tot_wins_anonymous = 0
    # Make 500 attempts without a specific user
    for i in range(max_attempts):
        response = requests.get(f"{play_url}?contest={contest.code}")
        
        if response.status_code == 200:
            result: dict = response.json()
            if result.get('win') == True:
                print(f"  Attempt {i+1}: '🎉 WIN!'")
                tot_wins_anonymous += 1

        else:
            print(f"  Attempt {i+1}: ❌ Failed with status code {response.status_code}")
    
    print(f"\nTotal anonymous wins: {tot_wins_anonymous}/{max_attempts}")

    # Test Case 3: Invalid contest code
    print("\nTest Case 4: Invalid contest code")
    response = requests.get(f"{play_url}?contest=invalid_contest_code")
    
    if response.status_code == 404:
        print(f"✅ Success - Correctly returned {response.status_code} for invalid contest")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Failed! Expected 404, got {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test Case 4: Missing contest parameter
    print("\nTest Case 5: Missing contest parameter")
    response = requests.get(f"{play_url}")
    
    if response.status_code == 400:
        print(f"✅ Success - Correctly returned {response.status_code} for missing contest parameter")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Failed! Expected 400, got {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test Case 5: Debug mode
    print("\nTest Case 6: Debug mode")
    response = requests.get(f"{play_url}?contest={contest.code}&debug=true")
    
    if response.status_code == 200:
        print(f"✅ Success! Status code: {response.status_code}")
        result = response.json()
        has_debug_info = 'debug_info' in result
        print(f"Contains debug info: {'✅ Yes' if has_debug_info else '❌ No'}")
        if has_debug_info:
            print(f"Debug info: {json.dumps(result['debug_info'], indent=2)}")
    else:
        print(f"❌ Failed! Status code: {response.status_code}")
        print(f"Response: {response.text}")

def check_win_records(prize):
    """
    Check the win records for the test prize.
    
    Args:
        prize: The Prize model instance to check
    """
    # Get today's win records for this prize
    today = timezone.now().date()
    win_records = WinRecord.objects.filter(
        prize=prize,
        timestamp__date=today
    )
    
    print(f"\nWin Records for {prize.name} today:")
    print(f"Total wins: {win_records.count()}")
    
    # Group by user_id
    wins_by_user = {}
    for record in win_records:
        user_id = record.user_id or 'anonymous'
        if user_id not in wins_by_user:
            wins_by_user[user_id] = 0
        wins_by_user[user_id] += 1
    
    print("\nWins by user:")
    for user_id, count in wins_by_user.items():
        print(f"  {user_id}: {count} wins")

def main(only_cleanup=False):
    """
    Main test function.
    """
    print("=== Djungle Contest API Test ===")
    print(f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if only_cleanup:
        cleanup_test_data()
        print("\n✅ Tests completed successfully!")
        return
    
    try:
        # Set up test data
        contest, prize = setup_test_data(force_cleanup=True)
        time.sleep(3)
        # Run tests
        test_play_endpoint(contest, prize)
        
        # Check win records
        check_win_records(prize)
        time.sleep(300)
        
        cleanup_test_data()
        print("\n✅ Tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up test data if needed
        # Contest.objects.filter(code__startswith='test_').delete()
        print("\nTest data has been kept in the database for review.")
        print("You can delete test contests with: Contest.objects.filter(code__startswith='test_').delete()")

if __name__ == "__main__":
    main(only_cleanup=False)