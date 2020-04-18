import sys
import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from watcher.models import Package, Release


class Command(BaseCommand):
    help = 'Clear releases'

    def handle(self, *args, **options):
        try:
            Command.processing()
        except KeyboardInterrupt:
            sys.exit(0)

    @staticmethod
    def processing():
        now = timezone.now()
        delta = now - datetime.timedelta(days=5)
        # delete old releases
        Release.objects.filter(
            created__lte=delta
        ).delete()
        # delete releases of fail packages
        Release.objects.filter(
            package__status=Package.STATUS.fail
        ).delete()
        # delete release of no rank packages
        Release.objects.filter(
            package__status=Package.STATUS.done,
            package__rank__lt=settings.MIN_RANK,
        ).delete()