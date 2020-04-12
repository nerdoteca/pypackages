import sys
import re

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from watcher.models import Package, Release


RELEASE_MIN_AGE = 15  # days


class GithubInterface:
    query = '''{
        repository(owner: "%s", name: "%s") {
            description
            homepageUrl
            url
            topics:repositoryTopics(first: 10) {
                nodes {
                  topic {
                    name
                  }
                }
            }
            tags:refs(refPrefix: "refs/tags/", first: 5, orderBy: {
            field: TAG_COMMIT_DATE, direction: DESC}) {
                nodes {
                    name
                    target {
                        ... on Commit {
                            author {
                                date
                            }
                        },
                        ... on Tag {
                            tagger {
                                date
                            }
                        }
                    }
                }
            }
        }
    }'''

    def __init__(self):
        access_token = settings.CODE_HOSTINGS['github']['ACCESS_TOKEN']
        transport = RequestsHTTPTransport(
            url='https://api.github.com/graphql',
            use_json=True,
            headers={
                'Authorization': 'bearer %s' % access_token,
                'Content-type': 'application/json',
            },
            verify=True
        )
        self.client = Client(
            retries=3,
            transport=transport,
            fetch_schema_from_transport=True
        )
        self.repository = {}
        self.topics = []
        self.releases = []
        self.now = timezone.now()

    def load_repository(self, repository_owner, repository_name):
        repository_owner = repository_owner.strip()
        repository_name = repository_name.strip()

        query = gql(self.query % (repository_owner, repository_name))
        payload = self.client.execute(query)

        self.repository = payload['repository']
        self.topics = payload['repository']['topics']['nodes']
        self.releases = payload['repository']['tags']['nodes']

    def get_repoinfo(self):
        return {
            'description': self.repository['description'] or '',
            'site_url': self.repository[
                'homepageUrl'] or self.repository['url']
        }

    def get_hasttags(self, extra_topics=[]):
        hashtags = set()
        for topic in self.topics:
            hashtag = '#' + topic['topic']['name']
            hashtag = hashtag.lower()
            hashtag = hashtag.replace('-', '')
            hashtag = hashtag.replace('_', '')
            hashtags.add(hashtag)
        for topic in extra_topics:
            hashtag = '#' + topic
            hashtag = hashtag.lower()
            hashtag = hashtag.replace('-', '')
            hashtag = hashtag.replace('_', '')
            hashtag = hashtag.replace('@', '')
            hashtag = hashtag.replace('/', '')
            hashtags.add(hashtag)
        return ' '.join(hashtags)

    def get_releases(self, release_regex):
        release_regex = release_regex.strip()
        previous_prefix = []
        for release in self.releases:
            created = parse_datetime(
                release['target']['tagger']['date']
                if 'tagger' in release['target']
                else release['target']['author']['date'])
            if abs(self.now - created).days > RELEASE_MIN_AGE:
                break
            matches = re.search(release_regex, release['name'])
            if matches is not None:
                current_prefix = matches.group(2)
                name = matches.group(1)
                if current_prefix not in previous_prefix:
                    previous_prefix.append(current_prefix)
                    yield {
                        'name': name.replace('_', '.').replace('-', '.'),
                        'created': created
                    }


class Command(BaseCommand):
    help = 'Watch for new releases in code hosting.'

    def handle(self, *args, **options):
        try:
            code_hostings = {
                'github': GithubInterface(),
            }
            Command.processing(code_hostings)
        except KeyboardInterrupt:
            sys.exit(0)

    @staticmethod
    def processing(code_hostings):
        packages = Package.objects.all()
        for package in packages:
            code_hosting = code_hostings[package.code_hosting]
            code_hosting.load_repository(
                package.repository_owner,
                package.repository_name,
            )

            repoinfo = code_hosting.get_repoinfo()
            releases = code_hosting.get_releases(package.release_regex)

            hashtags = code_hosting.get_hasttags([
                package.programming_language,
                package.name
            ])

            description = re.sub(
                r':\w+:', '', repoinfo['description']
            ).encode('ascii', 'ignore').decode('ascii').strip()

            while True:
                if len(description) < 255:
                    break
                description = description.split(' ')
                description = ' '.join(description[:-1]) + '...'

            package.description = description
            package.hashtags = hashtags
            package.site_url = repoinfo['site_url']
            package.save()

            Command.add_release(releases, package)

    @staticmethod
    def add_release(releases, package):
        for release in releases:
            release_exists = Release.objects.filter(
                name=release['name'], package=package
            ).exists()
            if release_exists is False:
                Release.objects.create(**{
                    **release, 'package': package
                })
