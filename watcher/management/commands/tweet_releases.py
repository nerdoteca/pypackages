import sys
import traceback

from django.core.management.base import BaseCommand
from django.conf import settings

import tweepy

from ...models import Release, Log


class Command(BaseCommand):
    help = 'Tweet new releases.'

    api = {}
    tweet_message = "#{} a new release was launched: {}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        twitter_accounts = settings.get("TWITTER_ACCOUNT", {})
        for language in ['python', 'javascript', 'css']:
            twitter_account = twitter_accounts.get(language)
            if twitter_account is not None:
                auth = tweepy.OAuthHandler(
                    twitter_account["API_KEY"],
                    twitter_account["API_SECRET"]
                )
                auth.set_access_token(
                    twitter_account["ACCESS_TOKEN"],
                    twitter_account["ACCESS_TOKEN_SECRET"]
                )
                self.api[language] = tweepy.API(auth)

    def handle(self, *args, **options):
        try:
            print('start processing')
            while True:
                self.processing()
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception:
            Log.objects.create(
                message=traceback.format_exc())
            raise

    def processing(self):
        releases = Release.objects.filter(status=Release.STATUS.new)
        for release in releases:
            self.write_tweet(release)

    def write_tweet(self, release):
        try:
            api = self.api[release.package.programming_language]
            api.update_status(self.tweet_message.format(
                release.package.name, release.name))
            release.status = Release.STATUS.tweeted
        except Exception:
            release.status = Release.STATUS.fail
            Log.objects.create(message=traceback.format_exc())
        finally:
            release.save()