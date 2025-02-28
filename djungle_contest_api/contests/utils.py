"""
Utility functions for the Djungle Contest API.
"""
from .prize_distribution import PrizeDistributor


def determine_win(prize, user_id=None, debug=False):
    """
    Determine if a user wins a prize based on a pseudo-random algorithm.
    
    The algorithm ensures that prizes are evenly distributed throughout the day,
    with the total number of wins not exceeding the daily limit (perday).
    
    This function delegates to the PrizeDistributor class for actual implementation.
    
    Args:
        prize: The Prize model instance.
        user_id (str, optional): User identifier for tracking wins per user.
        debug (bool, optional): Enable debug mode with enhanced logging.
        
    Returns:
        bool: True if the user wins the prize, False otherwise.
    """
    # Create a distributor with debug mode if requested
    distributor = PrizeDistributor(debug=debug)
    return distributor.can_win(prize, user_id)


def get_win_distribution_stats(prize, debug=False):
    """
    Get statistics about the distribution of wins for a prize.
    
    This function delegates to the PrizeDistributor class for actual implementation.
    
    Args:
        prize: The Prize model instance.
        debug (bool, optional): Enable debug mode with enhanced logging.
        
    Returns:
        dict: Statistics about the win distribution.
    """
    # Create a distributor with debug mode if requested
    distributor = PrizeDistributor(debug=debug)
    stats = distributor.get_daily_stats(prize)
    
    # For backward compatibility, return a simplified version
    simplified_stats = {
        'total_wins': stats['total_wins'],
        'perday_limit': stats['perday_limit'],
        'wins_by_hour': stats['wins_by_hour'],
        'max_wins_hour': max(stats['wins_by_hour'].values()) if stats['wins_by_hour'] else 0,
        'hours_with_wins': sum(1 for count in stats['wins_by_hour'].values() if count > 0),
        'distribution_evenness': stats['distribution_evenness']
    }
    
    if debug:
        print(f"Win distribution stats for prize {prize.code}:")
        print(f"Total wins today: {simplified_stats['total_wins']} out of {prize.perday}")
        print(f"Wins by hour: {simplified_stats['wins_by_hour']}")
        print(f"Max wins in any hour: {simplified_stats['max_wins_hour']}")
        print(f"Hours with at least one win: {simplified_stats['hours_with_wins']} out of 24")
        print(f"Distribution evenness (0-1): {simplified_stats['distribution_evenness']}")
    
    return simplified_stats 