from loguru import logger

from flexget import plugin
from flexget.event import event
from flexget.utils.cached_input import cached
from flexget.entry import Entry


log = logger.bind(name='seplis_series_following_missing_episodes')

class seplis_series_following_missing_episodes:
    """
    configure_series:
      from:
        seplis_series_following_missing_episodes:
          - play-server-id
    """

    schema = {
        'type': 'array', # list of play server ids
    }
    @cached('seplis_series_following_missing_episodes', persist='1 minute')
    def on_task_input(self, task, config):
        titles = []
        for play_server_id in config:
            cursor = None
            while True:
                r = task.requests.get(
                    f'https://api.seplis.net/2/play-servers/{play_server_id}/user-series-following-missing-episodes',
                    params={
                        'per_page': 100,
                        'cursor': cursor,
                    }
                )
                data = r.json()
                for series in data['items']:                
                    entry = Entry()
                    if not series['title']:
                        continue
                    entry['title'] = series['title']
                    year = int(series["premiered"][:4]) if series['premiered'] else None
                    if year and str(year) not in entry['title']:
                        entry['title'] += f' ({year})'
                    if entry['title'] in titles:
                        continue
                    entry['alternate_name'] = list(filter(None, series['alternative_titles']))
                    entry['url'] = f'https://seplis.net/series/{series["id"]}'
                    entry['seplis_series_id'] = series['id']
                    entry['seplis_title'] = entry['title']
                    entry['imdb_id'] = series['externals'].get('imdb', None)
                    entry['tvmaze_id'] = series['externals'].get('tvmaze_id', None)
                    entry['tvdb_id'] = series['externals'].get('thetvdb', None)
                    entry['tmdb_id'] = series['externals'].get('themoviedb', None)
                    titles.append(entry['title'])
                    yield entry
                if not data['cursor']:
                    break
                cursor = data['cursor']

@event('plugin.register')
def register_plugin():
    plugin.register(seplis_series_following_missing_episodes, 'seplis_series_following_missing_episodes', api_ver=2)