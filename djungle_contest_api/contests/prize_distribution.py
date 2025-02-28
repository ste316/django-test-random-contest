"""
Prize distribution system for the Djungle Contest API.

This module contains advanced algorithms for determining contest winners
in a fair and evenly distributed manner throughout the day.
"""
import random
import time
import numpy as np
from django.utils import timezone
import logging
import json
from datetime import datetime
import secrets  # Add this import at the top of the file

# Configure logger
logger = logging.getLogger(__name__)

class PrizeDistributor:
    """
    Handles the distribution of prizes for contests.
    
    This class uses advanced algorithms to ensure that prizes are distributed
    fairly throughout the day, respecting daily limits while maintaining
    an element of randomness.
    """
    
    def __init__(self, debug=False):
        """
        Initialize the PrizeDistributor.
        
        Args:
            debug (bool): Enable debug mode with enhanced logging.
        """
        self.debug = debug
        self.logger = logging.getLogger('contests.prize_distribution')
        
        if self.debug:
            self.logger.debug("PrizeDistributor initialized with debug mode ON")
    
    def check_can_win_today(self, prize):
        """
        Check if a prize can still be won today (hasn't reached daily limit).
        
        Args:
            prize: The Prize model instance.
            
        Returns:
            bool: True if the prize can still be won today, False otherwise.
        """
        # Get current total wins today
        wins_today = self.get_wins_today_count(prize)
        
        # Check if we've reached the daily limit
        return wins_today < prize.perday

    def get_wins_today_count(self, prize):
        """
        Get the count of wins for today for a specific prize.
        
        Args:
            prize: The Prize model instance.
            
        Returns:
            int: Number of wins today for this prize.
        """
        today = timezone.now().date()
        return prize.win_records.filter(timestamp__date=today, prize=prize).count()
    
    def can_win(self, prize, user_id=None):
        """
        Determine if a user can win a prize based on distribution algorithm.
        
        The algorithm ensures prizes are evenly distributed throughout the day
        while maintaining a pseudo-random element for fairness.
        
        Args:
            prize: The Prize model instance.
            user_id (str, optional): User identifier for tracking wins per user.
            
        Returns:
            bool: True if the user wins the prize, False otherwise.
        """
        # Log entry with context
        context = {
            'prize_code': prize.code,
            'prize_name': prize.name,
            'contest_code': prize.contest.code,
            'user_id': user_id or 'anonymous'
        }
        
        self.logger.info(f"Checking win for {prize.code} (user: {user_id})", extra=context)
        
        # Check if the prize can still be won today
        if not self.check_can_win_today(prize):
            if self.debug:
                self.logger.debug(
                    f"Prize {prize.code} has reached its daily limit of {prize.perday} wins",
                    extra=context
                )
            return False
        
        # Use the time-slot based distribution algorithm
        return self._time_slot_distribution_algorithm(prize)
    
    def _time_slot_distribution_algorithm(self, prize):
        """
        Time-slot based distribution algorithm.
        
        This algorithm divides the day into time slots based on the number of prizes
        and determines if the current time falls within a winning slot.
        
        Args:
            prize: The Prize model instance.
            
        Returns:
            bool: True if the current time falls in a winning slot, False otherwise.
        """
        # Get current time and wins information
        now = timezone.now()
        current_timestamp = now.timestamp()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_elapsed = int(now.timestamp() - today_start.timestamp())
        total_seconds_in_day = 24 * 60 * 60
        
        # Get the pre-determined win slots for today
        win_slots = self._get_win_slots_for_day(prize, now.date())
        
        # Get current wins to ensure we don't exceed daily limit
        current_wins = self.get_wins_today_count(prize)
        
        # Early return if we've already hit the prize limit
        if current_wins >= prize.perday:
            return False
        
        # Calculate expected wins by now based on time elapsed
        expected_wins_by_now = (seconds_elapsed / total_seconds_in_day) * prize.perday
        
        # If we have slots and we're in a slot, determine win/loss
        if win_slots:
            # Check if the current time is in any win slot
            # We add a small time window (±30 seconds) around each slot for flexibility
            time_window = 30  # seconds
            
            for slot_time in win_slots:
                # Convert slot time to seconds since midnight
                slot_seconds = self._time_to_seconds(slot_time)
                
                # Check if current time is within ±30 seconds of the slot time
                if abs(seconds_elapsed - slot_seconds) <= time_window:
                    # Calculate the expected traffic and win probability
                    # Based on [S6] - we expect 100x more requests than prizes
                    expected_requests_per_day = prize.perday * 100
                    
                    # Calculate requests per slot (evenly distributed across all slots)
                    requests_per_slot = expected_requests_per_day / len(win_slots)
                    
                    # Calculate win probability for this slot
                    # Base probability is 1/requests_per_slot, but we adjust based on:
                    # 1. Remaining prizes vs remaining expected prizes
                    # 2. Time elapsed in the day
                    remaining_prizes = prize.perday - current_wins
                    
                    # Calculate adjusted win probability
                    base_probability = 1 / requests_per_slot
                    
                    # Adjust based on whether we're ahead or behind schedule
                    if expected_wins_by_now > 0:
                        schedule_factor = min(2.0, max(0.5, remaining_prizes / (prize.perday - expected_wins_by_now)))
                    else:
                        schedule_factor = 1.0
                    
                    # Apply the adjustment to base probability
                    win_probability = base_probability * schedule_factor
                    
                    # Ensure win probability is reasonable
                    win_probability = min(0.05, max(0.001, win_probability))
                    
                    if self.debug:
                        self.logger.debug(
                            f"In win slot! Slot time: {slot_time.strftime('%H:%M:%S')}, "
                            f"Current elapsed seconds: {seconds_elapsed}, "
                            f"Slot seconds: {slot_seconds}, "
                            f"Win probability: {win_probability:.4f}, "
                            f"Current wins: {current_wins}, "
                            f"Expected by now: {expected_wins_by_now:.2f}, "
                            f"Schedule factor: {schedule_factor:.2f}"
                        )
                    
                    # Use secrets.randbelow for cryptographically secure random number generation
                    # Convert probability to an integer range for fair comparison
                    result = secrets.randbelow(10000) < int(win_probability * 10000)
                    
                    if result:
                        return True
            
            # Not in a win slot - but check if we're falling behind
            catch_up_factor = max(0, (expected_wins_by_now - current_wins) / prize.perday)
            
            # If we're significantly behind schedule (>10% behind), introduce catch-up probability
            if catch_up_factor > 0.1:
                # Adjust catch-up probability based on how far behind we are
                catch_up_probability = min(0.005 * catch_up_factor * 10, 0.01)  # Max 1%
                
                if self.debug:
                    self.logger.debug(
                        f"Behind schedule! Catch-up factor: {catch_up_factor:.2f}, "
                        f"Catch-up probability: {catch_up_probability:.4f}"
                    )
                
                # Use secrets.randbelow for cryptographically secure random number generation
                result = secrets.randbelow(10000) < int(catch_up_probability * 10000)
                
                if result:
                    return True
            
        return False
    
    def _time_to_seconds(self, time_obj):
        """
        Convert a time object to seconds since midnight.
        
        Args:
            time_obj: A datetime.time object.
            
        Returns:
            int: Seconds since midnight.
        """
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
    
    def _get_win_slots_for_day(self, prize, date):
        """
        Get the predetermined win slots for a specific day.
        
        This method uses a deterministic algorithm to generate win slots for a given day,
        ensuring consistency across application restarts while still distributing wins
        evenly throughout the day.
        
        Args:
            prize: The Prize model instance.
            date: The date to generate win slots for.
            
        Returns:
            list: List of datetime.time objects representing win slots.
        """
        # Use the prize code and date as seed for consistent results
        seed_value = f"{prize.code}:{date.isoformat()}"
        seed = abs(hash(seed_value)) % 10000
        
        # Create a random number generator with this seed
        rng = np.random.RandomState(seed)
        
        # Get total minutes in a day and prizes to distribute
        total_minutes = 24 * 60
        num_prizes = prize.perday
        
        # Divide the day into segments
        segment_size = total_minutes / num_prizes
        
        # Generate evenly spaced base points
        base_points = np.arange(0, total_minutes, segment_size)
        
        # Add some randomness to each point (but keep within segment)
        # The jitter keeps the prizes within their segment but adds randomness
        max_jitter = min(segment_size * 0.4, 30)  # Maximum 30 minutes or 40% of segment
        jitter = rng.uniform(-max_jitter, max_jitter, size=len(base_points))
        
        # Calculate the adjusted points and ensure they stay within 0-1439 (minutes in day)
        points = np.clip(base_points + jitter, 0, total_minutes - 1)
        
        # Convert points to time objects
        win_slots = []
        for point in points:
            minutes = int(point)
            hour = minutes // 60
            minute = minutes % 60
            second = int((point - minutes) * 60)
            win_slots.append(datetime.min.time().replace(hour=hour, minute=minute, second=second))
        
        if self.debug:
            self.logger.debug(
                f"Generated {len(win_slots)} win slots for {prize.code} on {date}: " +
                ", ".join([slot.strftime("%H:%M:%S") for slot in win_slots[:5]]) + 
                (f"... and {len(win_slots)-5} more" if len(win_slots) > 5 else "")
            )
        
        return win_slots
    
    def get_hourly_distribution_plan(self, prize):
        """
        Generate an hourly distribution plan for the prize.
        
        Args:
            prize (Prize): Prize to generate distribution plan for.
            
        Returns:
            list: List of dictionaries containing hour and allocation information.
        """
        # Log method entry
        if self.debug:
            self.logger.debug(f"Generating hourly distribution plan for {prize.code}")
        
        # Get win slots for today
        today = timezone.now().date()
        win_slots = self._get_win_slots_for_day(prize, today)
        
        # Count wins per hour
        wins_by_hour = {hour: 0 for hour in range(24)}
        for slot in win_slots:
            wins_by_hour[slot.hour] += 1
        
        # Create the distribution plan
        plan = []
        for hour in range(24):
            plan.append({
                'hour': hour,
                'allocation': wins_by_hour[hour]
            })
        
        # Log the generated distribution plan
        if self.debug:
            self.logger.debug(
                f"Hourly distribution plan for {prize.code}: "
                f"{json.dumps(plan, indent=2)}"
            )
        
        return plan
    
    def get_daily_stats(self, prize):
        """
        Get detailed statistics about prize distribution for today.
        
        Args:
            prize: The Prize model instance.
            
        Returns:
            dict: Statistics about today's prize distribution.
        """
        # Log method entry
        context = {'prize_code': prize.code, 'prize_name': prize.name}
        self.logger.info(f"Getting daily stats for {prize.code}", extra=context)
        
        today = timezone.now().date()
        current_hour = timezone.now().hour
        minutes_elapsed = timezone.now().minute
        
        # Get the ideal distribution plan
        ideal_plan = self.get_hourly_distribution_plan(prize)
        hourly_allocations = {plan['hour']: plan['allocation'] for plan in ideal_plan}
        
        # Get all wins for today and sort them by timestamp
        win_records = prize.win_records.filter(
            timestamp__date=today,
            prize=prize
        ).order_by('timestamp')
        
        # Initialize counters
        wins_by_hour = {hour: 0 for hour in range(24)}
        actual_wins_by_hour = {hour: 0 for hour in range(24)}
        limited_wins = []
        
        # First count actual wins per hour
        for record in win_records:
            hour = record.timestamp.hour
            actual_wins_by_hour[hour] += 1
        
        # Then process wins respecting hourly allocations
        for record in win_records:
            hour = record.timestamp.hour
            if wins_by_hour[hour] < hourly_allocations[hour]:
                wins_by_hour[hour] += 1
                limited_wins.append(record)
        
        # Calculate distribution metrics
        hours_with_wins = sum(1 for count in wins_by_hour.values() if count > 0)
        total_wins = len(limited_wins)
        total_actual_wins = len(win_records)
        
        # Calculate hourly win rates
        hourly_win_rates = []
        for hour in range(24):
            if hour <= current_hour:
                if hour == current_hour:
                    # For current hour, calculate rate based on elapsed time
                    hours_fraction = minutes_elapsed / 60 if minutes_elapsed > 0 else 1
                    if hours_fraction > 0:
                        # Rate should be actual wins per hour (projected)
                        actual_rate = actual_wins_by_hour[hour] / hours_fraction
                        # But capped by allocation
                        hourly_rate = min(actual_rate, hourly_allocations[hour] / hours_fraction)
                    else:
                        hourly_rate = 0
                else:
                    # For past hours, show actual rate capped by allocation
                    hourly_rate = min(actual_wins_by_hour[hour], hourly_allocations[hour])
            else:
                hourly_rate = 0  # Future hour
            
            hourly_win_rates.append({
                'hour': hour,
                'win_count': min(wins_by_hour[hour], hourly_allocations[hour]),
                'actual_win_count': actual_wins_by_hour[hour],  # Add actual wins for transparency
                'hourly_allocation_pct': hourly_allocations[hour],
                'hourly_rate': round(hourly_rate, 2)
            })
        
        stats = {
            'total_wins': total_wins,  # Wins respecting hourly allocation
            'perday_limit': prize.perday,
            'hours_with_wins': hours_with_wins,
            'remaining_wins': prize.perday - total_wins,
            'hourly_win_rates': hourly_win_rates,
            'total_actual_wins': total_actual_wins  # Total actual wins for the day
        }
        
        # Log the statistics
        if self.debug:
            self.logger.debug(
                f"Daily stats for {prize.code}: {json.dumps(stats, indent=2, default=str)}",
                extra=context
            )
        
        return stats


def calculate_win_chances(prize, time_of_day=None, debug=False):
    """
    Calculate the probability of winning at a specific time of day.
    
    This is useful for forecasting and visualization purposes.
    
    Args:
        prize: The Prize model instance.
        time_of_day (datetime.time, optional): The time to calculate for. Defaults to current time.
        debug (bool, optional): Enable debug mode with enhanced logging.
        
    Returns:
        float: Probability of winning (0.0 to 1.0).
    """
    logger = logging.getLogger('contests.prize_distribution')
    
    if debug:
        logger.debug(f"Calculating win chances for {prize.code} at {time_of_day or 'now'}")
    
    if time_of_day is None:
        time_of_day = timezone.now().time()
    
    # Get the distributor 
    distributor = PrizeDistributor(debug=debug)
    
    # Get win slots for today
    today = timezone.now().date()
    win_slots = distributor._get_win_slots_for_day(prize, today)
    
    # Convert time_of_day to seconds
    seconds_in_day = distributor._time_to_seconds(time_of_day)
    
    # Check if we're close to any win slot
    window_size = 30  # seconds
    for slot_time in win_slots:
        slot_seconds = distributor._time_to_seconds(slot_time)
        if abs(seconds_in_day - slot_seconds) <= window_size:
            # In a win slot - higher probability
            # Assuming 100x more requests than prizes (req [S6])
            if debug:
                logger.debug(f"Time {time_of_day} is in a win slot! Base probability: 0.01")
            return 0.01  # 1% chance (assuming 100x traffic)
    
    # Not in a specific win slot - very low base chance
    # We still provide a small probability to allow for catch-up if behind
    base_probability = 0.0001  # 0.01% chance
    
    # But adjust for time of day patterns (e.g., higher during business hours)
    hour = time_of_day.hour
    if 9 <= hour <= 17:  # 9am to 5pm - business hours
        time_factor = 1.2
    elif 18 <= hour <= 22:  # 6pm to 10pm - evening hours
        time_factor = 1.1
    else:  # Late night and early morning
        time_factor = 0.8
    
    probability = base_probability * time_factor
    
    if debug:
        logger.debug(f"Win probability for {prize.code}: {probability:.6f}")
    
    return probability 