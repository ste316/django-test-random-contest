# Phase 10: Implementing User Daily Win Limits (Bonus 2)

## Overview

This phase implements the second bonus feature: per-user daily win limits. The feature restricts the number of times a single user can win prizes per day across all contests, enhancing fairness and preventing abuse of the system.

## Implementation Details

### 1. Constants Definition

A new constants file was created to centralize configuration values related to the application. The user daily win limit (WMAX) was set to 3 as per requirements.

```python
# contests/constants.py
"""
Constants and configuration values for the Djungle Contest API.

This module contains constants used throughout the application.
"""

# User daily win limit (Bonus 2 feature)
USER_MAX_WINS_PER_DAY = 3  # WMAX value
```

### 2. Win Record Model Enhancement

The `WinRecord` model was extended with class methods to track and check user win limits:

```python
# From contests/models.py
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
```

### 3. Prize Distribution Logic Update

The `PrizeDistributor` class was modified to check for user daily win limits as part of the win determination process:

```python
# From contests/prize_distribution.py
def can_win(self, prize, user_id=None):
    # ... existing code ...
    
    # Check if the user has reached their daily win limit
    from .models import WinRecord
    
    if user_id and not WinRecord.user_can_win_today(user_id, USER_MAX_WINS_PER_DAY):
        if self.debug:
            self.logger.debug(
                f"User {user_id} has reached their daily win limit of {USER_MAX_WINS_PER_DAY}",
                extra=context
            )
        return False
    
    # Continue with the existing win determination logic
    # ... existing code ...
```

### 4. API Endpoint Update

The play endpoint in the views.py file was updated to check user win limits before processing the prize request, returning an HTTP 420 status code when a user has reached their daily win limit:

```python
# From contests/views.py
def play(request):
    # ... existing code ...
    
    # Check if user has reached their daily win limit
    if user_id:
        if not WinRecord.user_can_win_today(user_id, USER_MAX_WINS_PER_DAY):
            error_msg = f"User has reached the daily win limit of {USER_MAX_WINS_PER_DAY}"
            logger.warning(f"Win limit reached: {error_msg}", extra=log_context)
            return JsonResponse({'error': error_msg}, status=420)
    
    # ... continue with prize processing ...
```

Additionally, debug information was enhanced to include user win count data:

```python
# Add debug info if requested
if debug_mode:
    user_wins_today = 0
    if user_id:
        user_wins_today = WinRecord.get_user_wins_today(user_id)
    
    result['debug_info'] = {
        'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        'contest_status': 'active' if contest.is_active() else 'inactive',
        'daily_limit': prize.perday,
        'wins_today': wins_today,
        'user_id': user_id or 'anonymous',
        'user_wins_today': user_wins_today,
        'user_max_wins': USER_MAX_WINS_PER_DAY
    }
```

### 5. Test Cases

A comprehensive test case was added to verify the user daily win limit functionality:

```python
# From contests/tests/test_api_endpoints.py
def test_user_daily_win_limit(self):
    """Test that a user can't win more than the daily limit (WMAX = 3)."""
    # Create an active contest
    today = timezone.now().date()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)
    
    contest = Contest.objects.create(
        code='test_user_limit',
        name='Test User Limit Contest',
        start_date=yesterday,
        end_date=tomorrow
    )
    
    # Create a prize with a high daily limit (higher than user limit)
    prize = Prize.objects.create(
        code='prize_user_limit',
        name='User Limit Test Prize',
        perday=10,  # High daily limit to ensure it doesn't interfere with test
        contest=contest
    )
    
    # Same user_id for all requests
    user_id = 'test_user_123'
    
    # Create win records for this user today (reaching the WMAX limit)
    for _ in range(USER_MAX_WINS_PER_DAY):
        WinRecord.objects.create(
            prize=prize,
            user_id=user_id,
            timestamp=timezone.now()
        )
    
    # Verify the user has reached the win limit
    self.assertEqual(WinRecord.get_user_wins_today(user_id), USER_MAX_WINS_PER_DAY)
    
    # Try to play again - should get a 420 response
    response = self.client.get(
        reverse('play'), 
        {'contest': contest.code, 'user': user_id}
    )
    
    # Check the response
    self.assertEqual(response.status_code, 420)
    self.assertIn('error', response.json())
    self.assertIn('daily win limit', response.json()['error'].lower())
    
    # Verify with debug mode
    response_debug = self.client.get(
        reverse('play'), 
        {'contest': contest.code, 'user': user_id, 'debug': 'true'}
    )
    
    # Check the debug response
    self.assertEqual(response_debug.status_code, 420)
    self.assertIn('error', response_debug.json())
    
    # Now try with a different user who hasn't won anything yet
    new_user_id = 'fresh_user_456'
    
    # This should succeed since it's a different user
    response_new_user = self.client.get(
        reverse('play'), 
        {'contest': contest.code, 'user': new_user_id}
    )
    
    # Should get a 200 response 
    self.assertEqual(response_new_user.status_code, 200)
```

## API Documentation

The Bonus 2 implementation adds the following API behavior:

- **Endpoint**: `GET /play/?contest={code}&user={user_id}`
- **New Response**: HTTP 420 when a user has reached their daily win limit (WMAX = 3)
- **Response Format**:
  ```json
  {
    "error": "User has reached the daily win limit of 3"
  }
  ```

## Technical Considerations

1. **Cross-Contest Tracking**: The user win limit applies across all contests, not per contest. This means a user can win at most 3 prizes per day total, regardless of which contests they participate in.

2. **Anonymous Users**: Requests without a user parameter are not subject to user win limits but still respect the per-prize daily limits.

3. **Consistent Status Code**: The HTTP 420 status code was chosen as specified in the requirements to indicate when a user has reached their daily win limit.

4. **Debugging Support**: The implementation includes enhanced debugging information to aid in troubleshooting and monitoring user win patterns.

## Testing

The implementation includes:

1. **Unit Tests**: Testing the user win limit functionality in isolation.
2. **Integration Tests**: Testing the API endpoint behavior when users reach their daily win limits.
3. **Edge Cases**: Testing with different user IDs to ensure limits apply per user.

## Future Enhancements

Possible enhancements to the user daily win limit feature could include:

1. Making the WMAX value configurable per contest or globally through admin settings.
2. Adding analytics to track user win patterns across contests.
3. Implementing time-based reset of user win counts (e.g., at midnight).
4. Adding an API endpoint to check a user's remaining win count for the day. 