from django.contrib import admin
from .models import Contest, Prize, WinRecord

@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    """Admin interface for Contest model."""
    list_display = ('code', 'name', 'start_date', 'end_date', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('start_date', 'end_date')


@admin.register(Prize)
class PrizeAdmin(admin.ModelAdmin):
    """Admin interface for Prize model."""
    list_display = ('code', 'name', 'perday', 'contest', 'get_wins_today', 'can_win_today')
    search_fields = ('code', 'name', 'contest__name', 'contest__code')
    list_filter = ('contest',)


@admin.register(WinRecord)
class WinRecordAdmin(admin.ModelAdmin):
    """Admin interface for WinRecord model."""
    list_display = ('prize', 'user_id', 'timestamp')
    search_fields = ('prize__name', 'prize__code', 'user_id')
    list_filter = ('timestamp', 'prize__contest')
