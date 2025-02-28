"""
Management command to visualize prize distribution.

This command generates ASCII charts to visualize the hourly distribution of prizes.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from contests.models import Contest, Prize
from contests.prize_distribution import PrizeDistributor
import json
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Visualizes prize distribution for a contest'
    
    def add_arguments(self, parser):
        parser.add_argument('contest_code', type=str, help='Code of the contest to visualize')
        parser.add_argument('--prize', type=str, help='Specific prize code to visualize (optional)')
    
    def handle(self, *args, **options):
        contest_code = options['contest_code']
        prize_code = options.get('prize')
        
        try:
            contest = Contest.objects.get(code=contest_code)
        except Contest.DoesNotExist:
            raise CommandError(f'Contest with code "{contest_code}" does not exist')
        
        self.stdout.write(self.style.SUCCESS(f'Visualizing prize distribution for contest: {contest.name} ({contest.code})'))
        
        # Get prizes for the contest
        if prize_code:
            prizes = Prize.objects.filter(contest=contest, code=prize_code)
            if not prizes.exists():
                raise CommandError(f'Prize with code "{prize_code}" does not exist in contest "{contest_code}"')
        else:
            prizes = Prize.objects.filter(contest=contest)
            if not prizes.exists():
                self.stdout.write(self.style.WARNING(f'No prizes found for contest {contest_code}'))
                return
        
        distributor = PrizeDistributor(debug=False)
        
        # Visualize each prize
        for prize in prizes:
            self.stdout.write(self.style.NOTICE(f'\nPrize: {prize.name} ({prize.code})'))
            self.stdout.write(f'Daily win limit: {prize.perday}')
            
            # Get today's stats
            stats = distributor.get_daily_stats(prize)
            
            # Generate ASCII chart for hourly distribution
            self.stdout.write('\nHourly Win Distribution:')
            self.stdout.write('Hour  |  Wins  | Distribution')
            self.stdout.write('-' * 50)
            
            max_wins = max(stats['wins_by_hour'].values()) if stats['wins_by_hour'].values() else 1
            scale_factor = min(20, max(1, max_wins))  # Scale to fit in terminal
            
            for hour in range(24):
                # Format the hour
                hour_display = f'{hour % 12 or 12} {"AM" if hour < 12 else "PM"}'
                
                # Get win count for this hour
                win_count = stats['wins_by_hour'][hour]
                
                # Calculate bar length
                bar_length = int((win_count / scale_factor) * 20) if scale_factor > 0 else 0
                bar = '█' * bar_length
                
                # Format the line
                self.stdout.write(f'{hour_display:5} | {win_count:5} | {bar}')
            
            # Show comparison with ideal distribution
            self.stdout.write('\nActual vs Ideal Distribution:')
            self.stdout.write('Hour  | Actual | Ideal | Comparison')
            self.stdout.write('-' * 60)
            
            current_hour = timezone.now().hour
            
            for hour in range(24):
                # Format the hour
                hour_display = f'{hour % 12 or 12} {"AM" if hour < 12 else "PM"}'
                
                # Get actual and ideal win counts
                actual = stats['wins_by_hour'][hour]
                
                # For future hours, scale ideal by 0
                # For current hour, scale by minutes elapsed
                # For past hours, use full ideal
                if hour > current_hour:
                    ideal = 0
                elif hour == current_hour:
                    minutes_elapsed = timezone.now().minute
                    ideal = (minutes_elapsed / 60) * stats['ideal_distribution'][hour]
                else:
                    ideal = stats['ideal_distribution'][hour]
                
                # Calculate the comparison
                if ideal == 0:
                    # Future hours, nothing expected yet
                    comparison = "○" * 10  # Empty circles for future
                else:
                    # Calculate percentage of expected
                    pct = (actual / ideal) if ideal > 0 else 0
                    
                    if pct >= 0.9 and pct <= 1.1:
                        # Within 10% of ideal
                        comparison = "✓" * 10  # Good
                    elif pct < 0.9:
                        # Below ideal
                        filled = int(pct * 10)
                        comparison = "●" * filled + "○" * (10 - filled)  # Partially filled
                    else:
                        # Above ideal
                        comparison = "!" * 10  # Too many
                
                # Format the line
                self.stdout.write(f'{hour_display:5} | {actual:6} | {ideal:5.1f} | {comparison}')
            
            # Show summary statistics
            self.stdout.write('\nSummary:')
            self.stdout.write(f'Total wins today: {stats["total_wins"]} out of {stats["perday_limit"]}')
            self.stdout.write(f'Remaining wins: {stats["remaining_wins"]}')
            evenness = stats["distribution_evenness"] * 100
            self.stdout.write(f'Distribution evenness: {evenness:.1f}%')
            
            # Calculate and show if we're on track
            current_time = timezone.now()
            minutes_elapsed = current_time.hour * 60 + current_time.minute
            expected_wins = (minutes_elapsed / (24 * 60)) * stats["perday_limit"]
            
            on_track = abs(stats["total_wins"] - expected_wins) < stats["perday_limit"] * 0.1
            
            if on_track:
                self.stdout.write(self.style.SUCCESS(f'Status: ON TRACK (Expected: {expected_wins:.1f}, Actual: {stats["total_wins"]})'))
            elif stats["total_wins"] < expected_wins:
                self.stdout.write(self.style.WARNING(f'Status: BEHIND (Expected: {expected_wins:.1f}, Actual: {stats["total_wins"]})'))
            else:
                self.stdout.write(self.style.WARNING(f'Status: AHEAD (Expected: {expected_wins:.1f}, Actual: {stats["total_wins"]})'))
        
        self.stdout.write(self.style.SUCCESS('\nVisualization complete!')) 