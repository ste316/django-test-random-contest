"""
Management command to analyze prize distribution for a contest.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from contests.models import Contest, Prize
from contests.prize_distribution import PrizeDistributor
import json
from datetime import datetime, timedelta
import logging

# Configure logging
logger = logging.getLogger('contests.management.commands.analyze_prize_distribution')

class Command(BaseCommand):
    help = 'Analyzes prize distribution for a contest'
    
    def add_arguments(self, parser):
        parser.add_argument('contest_code', type=str, help='Code of the contest to analyze')
        parser.add_argument('--days', type=int, default=1, help='Number of days to analyze')
        parser.add_argument('--format', type=str, choices=['text', 'json'], default='text', 
                          help='Output format (text or json)')
        parser.add_argument('--debug', action='store_true', help='Enable debug mode with enhanced logging')
    
    def handle(self, *args, **options):
        contest_code = options['contest_code']
        days = options['days']
        output_format = options['format']
        debug_mode = options['debug']
        
        # Configure logger with appropriate verbosity
        if debug_mode:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled for prize distribution analysis")
        
        logger.info(f"Analyzing prize distribution for contest: {contest_code}")
        
        try:
            contest = Contest.objects.get(code=contest_code)
            logger.info(f"Found contest: {contest.name}")
        except Contest.DoesNotExist:
            logger.error(f"Contest not found: {contest_code}")
            raise CommandError(f'Contest with code "{contest_code}" does not exist')
        
        self.stdout.write(self.style.SUCCESS(f'Analyzing prize distribution for contest: {contest.name} ({contest.code})'))
        
        prizes = Prize.objects.filter(contest=contest)
        if not prizes.exists():
            logger.warning(f"No prizes found for contest: {contest_code}")
            self.stdout.write(self.style.WARNING(f'No prizes found for contest {contest_code}'))
            return
        
        distributor = PrizeDistributor(debug=debug_mode)
        
        # Analyze each prize
        for prize in prizes:
            prize_context = {
                'prize_code': prize.code,
                'prize_name': prize.name,
                'contest_code': contest.code
            }
            logger.info(f"Analyzing prize: {prize.name}", extra=prize_context)
            
            self.stdout.write(self.style.NOTICE(f'\nPrize: {prize.name} ({prize.code})'))
            self.stdout.write(f'Daily win limit: {prize.perday}')
            
            # Get today's stats
            today_stats = distributor.get_daily_stats(prize)
            
            if debug_mode:
                logger.debug(f"Stats for {prize.code}: {json.dumps(today_stats, indent=2)}", extra=prize_context)
            
            if output_format == 'json':
                self.stdout.write(json.dumps(today_stats, indent=2))
            else:
                # Text format
                self.stdout.write('\nToday\'s Distribution:')
                self.stdout.write(f'Ideal wins (respecting hourly allocations): {today_stats["ideal_wins"]} out of {today_stats["perday_limit"]}')
                self.stdout.write(f'Total actual wins: {today_stats["total_actual_wins"]}')
                self.stdout.write(f'Remaining wins: {today_stats["remaining_wins"]}')
                self.stdout.write(f'Distribution evenness: {today_stats["distribution_evenness"]:.2f}')
                
                # Print hourly distribution
                self.stdout.write('\nHourly Distribution:')
                self.stdout.write('Hour | Actual Wins | Ideal Distribution | Variance')
                self.stdout.write('-' * 60)
                
                for hour in range(24):
                    # Format for display: e.g. "9 AM", "3 PM", etc.
                    hour_display = f'{hour % 12 or 12} {"AM" if hour < 12 else "PM"}'
                    self.stdout.write(f'{hour_display:5} | {today_stats["wins_by_hour"][hour]:11} | '
                                    f'{today_stats["ideal_distribution"][hour]:17} | '
                                    f'{today_stats["variance_by_hour"][hour]:8.2f}')
            
            # Generate recommended distribution for tomorrow
            self.stdout.write('\nRecommended Distribution for Tomorrow:')
            hourly_plan = distributor.get_hourly_distribution_plan(prize)
            
            if output_format == 'json':
                self.stdout.write(json.dumps(hourly_plan, indent=2))
            else:
                self.stdout.write('Hour | Target Wins')
                self.stdout.write('-' * 20)
                for hour in range(24):
                    hour_display = f'{hour % 12 or 12} {"AM" if hour < 12 else "PM"}'
                    self.stdout.write(f'{hour_display:5} | {hourly_plan[hour]}')
        
        self.stdout.write(self.style.SUCCESS('\nAnalysis complete!')) 