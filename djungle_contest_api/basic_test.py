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

    # Test Case 2: Invalid contest code
    print("\nTest Case 2: Invalid contest code")
    response = requests.get(f"{play_url}?contest=invalid_contest_code")
    
    if response.status_code == 404:
        print(f"✅ Success - Correctly returned {response.status_code} for invalid contest")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Failed! Expected 404, got {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test Case 3: Missing contest parameter
    print("\nTest Case 3: Missing contest parameter")
    response = requests.get(f"{play_url}")
    
    if response.status_code == 400:
        print(f"✅ Success - Correctly returned {response.status_code} for missing contest parameter")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Failed! Expected 400, got {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test Case 4: Debug mode
    print("\nTest Case 4: Debug mode")
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

def setup_multiple_test_data(num_contests=3, force_cleanup=False):
    """
    Create multiple test contests and prizes for testing.
    
    Args:
        num_contests (int): Number of contests to create
        force_cleanup (bool): Whether to force cleanup of existing test data
    
    Returns:
        list: List of tuples containing (contest, prize) for each contest
    """
    # Generate a unique base code for this test run
    base_test_code = f"test_{int(time.time())}"
    
    # Create date range (today and 7 days from now)
    today = timezone.now().date()
    end_date = today + timedelta(days=7)
    
    # Delete any existing test contests to avoid conflicts
    if force_cleanup:
        cleanup_test_data()
    
    # List to store created contests and prizes
    contest_prize_list = []
    
    # Create multiple contests
    for i in range(num_contests):
        # Create unique codes for each contest
        test_code = f"{base_test_code}_contest_{i+1}"
        
        # Create a new test contest
        contest = Contest.objects.create(
            code=test_code,
            name=f"Test Contest {test_code}",
            start_date=today,
            end_date=end_date
        )
        
        # Create a prize for the contest with 100 available per day
        prize = Prize.objects.create(
            code=f"{test_code}_prize",
            name=f"Test Prize for {test_code}",
            perday=100,
            contest=contest
        )

        print(f"Created test contest: {contest.name} ({contest.code})")
        print(f"Created test prize: {prize.name} ({prize.code})")
        print(f"Prize perday: {prize.perday}")
        
        contest_prize_list.append((contest, prize))
    
    return contest_prize_list

def test_multiple_contests_with_users(contest_prize_list, max_attempts=250):
    """
    Test multiple contests with multiple users.
    
    Args:
        contest_prize_list (list): List of (contest, prize) tuples
        max_attempts (int): Maximum number of attempts per user per contest
    """
    # Base URL - assuming the server is running locally
    base_url = "http://127.0.0.1:8000"
    play_url = f"{base_url}/play"
    
    # Generate 5 unique users
    users = [f"test_user_{random.randint(1000, 9999)}" for _ in range(3)]+['', '']
    
    # Detailed results tracking
    results = {
        'total_contests': len(contest_prize_list),
        'users': {}
    }
    
    # Iterate through each contest
    for contest_idx, (contest, prize) in enumerate(contest_prize_list, 1):
        print(f"\n=== Testing Contest {contest_idx}: {contest.code} ===")
        
        # Track results for this contest
        contest_results = {
            'contest_code': contest.code,
            'user_wins': {}
        }
        
        # Test each user
        for user in users:
            print(f"\nTesting user {user if user else 'anonymous'} on contest {contest.code}")
            
            # Track wins for this user on this contest
            user_wins = 0
            user_win_details = []
            
            # Make attempts for this user
            for attempt in range(max_attempts):
                response = requests.get(f"{play_url}?contest={contest.code}&user={user}")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('win') == True:
                        user_wins += 1
                        # Log detailed win information
                        win_info = {
                            'attempt': attempt + 1,
                            'response': result
                        }
                        user_win_details.append(win_info)
                        print(f"  Attempt {attempt+1}: '🎉 WIN!'")
            
            # Store user's wins
            contest_results['user_wins'][user] = {
                'total_wins': user_wins,
                'win_details': user_win_details
            }
            print(f"User {user} wins: {user_wins}/{max_attempts}")
        
        # Store contest results
        results['users'][contest.code] = contest_results
    
    # Print summary
    print("\n=== Test Summary ===")
    for contest_code, contest_data in results['users'].items():
        print(f"\nContest: {contest_code}")
        for user, user_results in contest_data['user_wins'].items():
            print(f"  {user if user else 'anonymous'}: {user_results['total_wins']} wins")
    
    return results

def main(only_cleanup=False):
    """
    Main test function.
    """
    print("=== Djungle Contest API Multi-Contest Test ===")
    print(f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if only_cleanup:
        cleanup_test_data()
        print("\n✅ Tests completed successfully!")
        return
    
    try:
        # Set up multiple test contests
        contest_prize_list = setup_multiple_test_data(num_contests=2, force_cleanup=True)
        time.sleep(3)
        
        # Run tests on multiple contests with multiple users
        test_results = test_multiple_contests_with_users(contest_prize_list)
        
        # Test play endpoint for each contest
        contest, prize = contest_prize_list[0]
        print(f"\nTesting play endpoint for contest: {contest.code}")
        test_play_endpoint(contest, prize)
        
        # Optional: Check win records for each contest
        for contest, prize in contest_prize_list:
            check_win_records(prize)
        
        print('\nSleeping for 300 seconds, to check if the win records are correct, then cleanup')
        # Optional delay to allow for processing
        time.sleep(300)
        
        print('Cleaning up test data...')
        time.sleep(0.07)
        # Cleanup
        cleanup_test_data()
        print("\n✅ Tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_test_data()
        print("\nDB cleared, exiting...")

if __name__ == "__main__":
    main(only_cleanup=False)