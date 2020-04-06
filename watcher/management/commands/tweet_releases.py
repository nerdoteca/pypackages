import sys
import datetime

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

import tweepy

from ...models import Release


RELEASE_MIN_AGE = 1  # days


class Command(BaseCommand):
    help = 'Tweet new releases.'

    text_template = (
        'The release of %s package %s is now available. 🥳'
        '\n\n#%s #%s 😍'
    )

    def handle(self, *args, **options):
        try:
            accounts = self.get_accounts()
            self.processing(accounts)
        except KeyboardInterrupt:
            sys.exit(0)

    def processing(self, accounts):
        created = timezone.now() - datetime.timedelta(days=RELEASE_MIN_AGE)
        for account in accounts:
            releases = Release.objects.filter(
                package__programming_language=account['programming_language'],
                created__lte=created, status=Release.STATUS.new
            ).order_by('created')[0:1]
            if releases:
                self.write_tweet(releases[0], account['api'])

    def get_accounts(self):
        if 'TWITTER_ACCOUNTS' in settings:
            for programming_language in ['python', 'javascript', 'css']:
                if programming_language in settings['TWITTER_ACCOUNTS']:
                    secrets = settings[
                        'TWITTER_ACCOUNTS'][programming_language]
                    auth = tweepy.OAuthHandler(
                        secrets['API_KEY'],
                        secrets['API_SECRET']
                    )
                    auth.set_access_token(
                        secrets['ACCESS_TOKEN'],
                        secrets['ACCESS_TOKEN_SECRET']
                    )
                    yield {
                        'programming_language': programming_language,
                        'api': tweepy.API(auth)
                    }

    def write_tweet(self, release, api):
        try:
            package_name = release.package.name
            programming_language = release.package.programming_language
            release_name = release.name
            text = self.text_template % (
                package_name, release_name, programming_language,
                package_name.replace('-', '').replace('_', ''))
            api.update_status(text)
            release.status = Release.STATUS.tweeted
            release.save()
        except Exception:
            raise
