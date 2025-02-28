from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import logging
import traceback

from .models import Contest, Prize, WinRecord
from .prize_distribution import PrizeDistributor

# Configure logging
logger = logging.getLogger('contests.views')

def index(request):
    """
    API homepage providing basic information and documentation.
    
    GET /
    
    Args:
        request: Django HTTP Request object.
        
    Returns:
        JsonResponse or rendered template: API information and endpoints documentation.
    """
    # Count active contests
    active_contests_count = Contest.objects.filter(
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date()
    ).count()
    
    # Current timestamp
    timestamp = timezone.now()
    
    # Log access with context
    log_context = getattr(request, 'log_context', {})
    logger.info(f"Homepage accessed", extra=log_context)
    
    # Check if the request accepts HTML
    accept_header = request.META.get('HTTP_ACCEPT', '')
    
    if 'text/html' in accept_header:
        # Render HTML template for browsers
        logger.info('API homepage accessed (HTML format)', extra=log_context)
        return render(request, 'contests/index.html', {
            'active_contests': active_contests_count,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')
        })
    else:
        # Prepare API information for JSON response
        api_info = {
            'name': 'Djungle Contest API',
            'version': '2.4',
            'description': 'API for contest participation with pseudo-random prize distribution',
            'active_contests': active_contests_count,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'endpoints': [
                {
                    'path': '/',
                    'method': 'GET',
                    'description': 'API documentation and information'
                },
                {
                    'path': '/play/',
                    'method': 'GET',
                    'description': 'Participate in a contest',
                    'parameters': [
                        {
                            'name': 'contest',
                            'type': 'string',
                            'required': True,
                            'description': 'Contest code'
                        },
                        {
                            'name': 'user',
                            'type': 'string',
                            'required': False,
                            'description': 'User identifier (optional)'
                        }
                    ]
                },
                {
                    'path': '/stats/',
                    'method': 'GET',
                    'description': 'Get statistics about prize distribution',
                    'parameters': [
                        {
                            'name': 'contest',
                            'type': 'string',
                            'required': True,
                            'description': 'Contest code'
                        }
                    ]
                }
            ]
        }
        logger.info('API homepage accessed (JSON format)', extra=log_context)
        return JsonResponse(api_info)

def play(request):
    """
    Participate in a contest for a chance to win a prize.
    
    GET /play/?contest={code}&user={user_id}
    
    Args:
        request: Django HTTP Request object with 'contest' parameter
                and optional 'user' parameter.
                
    Returns:
        JsonResponse: Contest result with appropriate HTTP status code.
    """
    # Get log context for logging
    log_context = getattr(request, 'log_context', {})
    debug_mode = request.GET.get('debug', '').lower() in ('true', '1', 'yes')
    
    # Log the request
    logger.info(f"Play endpoint accessed with params: {request.GET}", extra=log_context)
    
    # Get the contest parameter
    contest_code = request.GET.get('contest')
    user_id = request.GET.get('user')
    
    # Update log context with additional info
    if user_id:
        log_context['user_id'] = user_id
    if contest_code:
        log_context['contest_code'] = contest_code
    
    # Check if contest parameter is missing
    if not contest_code:
        error_msg = "Missing required parameter: contest"
        logger.warning(f"Bad request: {error_msg}", extra=log_context)
        return JsonResponse({'error': error_msg}, status=400)
    
    try:
        # Try to get the contest by code
        contest = Contest.objects.get(code=contest_code)
        
        # Update log context with contest details
        log_context['contest_name'] = contest.name
        
        logger.info(f"Contest found: {contest.name}", extra=log_context)
        
        # Check if the contest is active
        if not contest.is_active():
            error_msg = f"Contest '{contest_code}' is not active"
            logger.warning(f"Unprocessable entity: {error_msg}", extra=log_context)
            return JsonResponse({'error': error_msg}, status=422)
        
        # Get the prize for this contest
        try:
            prize = Prize.objects.filter(contest=contest).first()
            
            if not prize:
                error_msg = f"No prize configured for contest '{contest_code}'"
                logger.error(f"Contest configuration error: {error_msg}", extra=log_context)
                return JsonResponse({'error': error_msg}, status=500)
            
            # Update log context with prize details
            log_context['prize_code'] = prize.code
            log_context['prize_name'] = prize.name
            
            logger.info(f"Checking prize win for {prize.name}", extra=log_context)
            
            # Create a prize distributor with debug mode if requested
            distributor = PrizeDistributor(debug=debug_mode)
            
            # Check if the user wins
            win = distributor.can_win(prize, user_id)
            
            # Get today's win count
            today = timezone.now().date()
            wins_today = WinRecord.objects.filter(
                prize=prize,
                timestamp__date=today
            ).count()
            
            # Prepare response
            result = {
                'win': win,
                'prize': None,
                'contest': contest_code,
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add debug info if requested
            if debug_mode:
                result['debug_info'] = {
                    'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'contest_status': 'active' if contest.is_active() else 'inactive',
                    'daily_limit': prize.perday,
                    'wins_today': wins_today
                }
            
            # If it's a win, record it and include prize details
            if win:
                # Record the win
                WinRecord.objects.create(prize=prize, user_id=user_id)
                
                # Add prize details to the response
                result['prize'] = {
                    'code': prize.code,
                    'name': prize.name
                }
                
                logger.info(f"User won prize: {prize.name}", extra=log_context)
            else:
                logger.info("No win this time", extra=log_context)
            
            return JsonResponse(result)
            
        except Exception as e:
            error_msg = f"Error processing prize: {str(e)}"
            logger.error(f"Prize processing error: {error_msg}", extra={
                **log_context,
                'traceback': traceback.format_exc()
            })
            return JsonResponse({'error': error_msg}, status=500)
            
    except ObjectDoesNotExist:
        error_msg = f"Contest not found"
        logger.warning(f"Not found: {error_msg} - {contest_code}", extra=log_context)
        return JsonResponse({'error': error_msg}, status=404)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Server error: {error_msg}", extra={
            **log_context,
            'traceback': traceback.format_exc()
        })
        return JsonResponse({'error': error_msg}, status=500)

def stats(request):
    """
    Get statistics about prize distribution for a contest.
    
    GET /stats/?contest={code}
    
    Args:
        request: Django HTTP Request object with 'contest' parameter.
        
    Returns:
        JsonResponse: Statistics about prize distribution.
    """
    # Get log context for logging
    log_context = getattr(request, 'log_context', {})
    debug_mode = request.GET.get('debug', '').lower() in ('true', '1', 'yes')
    
    # Log the request
    logger.info(f"Stats endpoint accessed with params: {request.GET}", extra=log_context)
    
    # Get the contest parameter
    contest_code = request.GET.get('contest')
    
    # Update log context
    if contest_code:
        log_context['contest_code'] = contest_code
    
    # Check if contest parameter is missing
    if not contest_code:
        error_msg = "Missing required parameter: contest"
        logger.warning(f"Bad request: {error_msg}", extra=log_context)
        return JsonResponse({'error': error_msg}, status=400)
    
    try:
        # Try to get the contest by code
        contest = Contest.objects.get(code=contest_code)
        
        # Update log context
        log_context['contest_name'] = contest.name
        
        # Check if the contest is active
        if not contest.is_active():
            error_msg = f"Contest '{contest_code}' is not active"
            logger.warning(f"Unprocessable entity: {error_msg}", extra=log_context)
            return JsonResponse({'error': error_msg}, status=422)
        
        # Get the prize for this contest
        try:
            prize = Prize.objects.filter(contest=contest).first()
            
            if not prize:
                error_msg = f"No prize configured for contest '{contest_code}'"
                logger.error(f"Contest configuration error: {error_msg}", extra=log_context)
                return JsonResponse({'error': error_msg}, status=500)
            
            # Update log context
            log_context['prize_code'] = prize.code
            log_context['prize_name'] = prize.name
            
            logger.info(f"Getting stats for prize: {prize.name}", extra=log_context)
            
            # Create a prize distributor with debug mode if requested
            distributor = PrizeDistributor(debug=debug_mode)
            
            # Get the statistics which now includes total_actual_wins
            try:
                stats = distributor.get_daily_stats(prize)
            except Exception as dist_error:
                # Log the specific error with more context
                logger.error(f"Error in get_daily_stats: {str(dist_error)}", extra={
                    **log_context,
                    'prize_code': prize.code,
                    'prize_name': prize.name,
                    'traceback': traceback.format_exc()
                })
                
                # Attempt to get basic stats as a fallback
                try:
                    wins_today = prize.get_wins_today()
                    stats = {
                        'total_wins': wins_today,
                        'error': str(dist_error),
                        'perday_limit': prize.perday,
                        'wins_by_hour': {hour: 0 for hour in range(24)},
                        'hours_with_wins': 0,
                        'remaining_wins': prize.perday - wins_today,
                        'hourly_win_rates': [],
                        'total_actual_wins': wins_today
                    }
                except Exception as fallback_error:
                    # If even the fallback fails, return a generic error response
                    error_msg = f"Critical error processing prize stats: {str(fallback_error)}"
                    logger.critical(error_msg, extra={
                        **log_context,
                        'original_error': str(dist_error),
                        'fallback_error': str(fallback_error),
                        'traceback': traceback.format_exc()
                    })
                    return JsonResponse({'error': error_msg}, status=500)
            
            # Use the total_wins from stats which respects hourly limits
            wins_today = stats.get('total_wins', 0)
            total_actual_wins = stats.get('total_actual_wins', 0)
            
            # Prepare the response
            result = {
                'contest': {
                    'code': contest.code,
                    'name': contest.name
                },
                'prizes': [{
                    'code': prize.code,
                    'name': prize.name,
                    'perday': prize.perday
                }],
                'wins_today': wins_today,  # Use the limited wins count
                'prize': {
                    'code': prize.code,
                    'name': prize.name
                },
                'stats': stats,
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add debug info if requested
            if debug_mode:
                result['debug_info'] = {
                    'daily_stats': {
                        'perday_limit': prize.perday,
                        'wins_today': wins_today,
                        'total_actual_wins': total_actual_wins,  # Add actual wins for debugging
                        'remaining': prize.perday - wins_today
                    }
                }
            
            logger.info(f"Stats retrieved successfully for {prize.name}", extra=log_context)
            
            return JsonResponse(result)
            
        except Exception as e:
            error_msg = f"Error processing prize: {str(e)}"
            logger.error(f"Prize processing error: {error_msg}", extra={
                **log_context,
                'traceback': traceback.format_exc()
            })
            return JsonResponse({'error': error_msg}, status=500)
            
    except ObjectDoesNotExist:
        error_msg = f"Contest not found"
        logger.warning(f"Not found: {error_msg} - {contest_code}", extra=log_context)
        return JsonResponse({'error': error_msg}, status=404)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Server error: {error_msg}", extra={
            **log_context,
            'traceback': traceback.format_exc()
        })
        return JsonResponse({'error': error_msg}, status=500)
