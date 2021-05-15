from django.core.management.base import BaseCommand, CommandError
from app.views import get_top_members, get_top_tags


class Command(BaseCommand):
    help = 'Put top members and top tags to cache'
    
    def handle(self, *args, **options):
        get_top_members()
        get_top_tags()
