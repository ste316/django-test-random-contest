from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import logging
import traceback

from .models import Contest, Prize, WinRecord
from .prize_distribution import PrizeDistributor
from .constants import USER_MAX_WINS_PER_DAY

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
        
        # Check if user has reached their daily win limit
        if user_id:
            if not WinRecord.user_can_win_today(user_id, USER_MAX_WINS_PER_DAY):
                error_msg = f"Enhance your calm: User has reached the daily win limit of {USER_MAX_WINS_PER_DAY}"
                logger.warning(f"Win limit reached: {error_msg}", extra=log_context)
                return JsonResponse({'error': error_msg}, status=420)
                
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

