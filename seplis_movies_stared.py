from loguru import logger

from flexget import plugin
from flexget.event import event
from flexget.utils.cached_input import cached
from flexget.entry import Entry

from dateutil.parser import parse as dateutil_parse

log = logger.bind(name='seplis_movies_stared')

class seplis_movies_stared:
    """
    watchlist:
        priority: 1
        seplis_movies_stared:
            - username
    """

    schema = {
        'type': 'array', # list of usernames
    }
    @cached('seplis_movies_stared', persist='1 minute')
    def on_task_input(self, task, config):
        log.debug('Retriving movies users stared')
        user_ids = []
        titles = []
        for u in config:
            r = task.requests.get(f'https://api.seplis.net/1/users?username={u}')
            d = r.json()
            if not d:
                raise plugin.PluginError(f'Unknown user: {u}')
            user_ids.append(d[0]['id'])

        for uid in user_ids:
            r = task.requests.get(
                f'https://api.seplis.net/1/users/{uid}/movies-stared',
                params={
                    'per_page': 1000,
                }
            )
            for movie in r.json():
                if movie['title']:
                    entry = Entry()
                    entry['title'] = movie['title']
                    year = int(movie["release_date"][:4]) if movie['release_date'] else None
                    if year and str(year) not in entry['title']:
                        entry['title'] += f' ({year})' if year else ''
                    if entry['title'] in titles:
                        continue
                    entry['url'] = f'https://seplis.net/movie/{movie["id"]}'
                    entry['seplis_movie_id'] = movie['id']
                    entry['seplis_title'] = entry['title']
                    if movie['release_date']:
                        entry['tmdb_released'] = dateutil_parse(movie['release_date']).date()
                        entry['seplis_release_date'] = entry['tmdb_released']
                    entry['imdb_id'] = movie['externals'].get('imdb', None)
                    entry['tmdb_id'] = movie['externals'].get('themoviedb', None)
                    entry['movie_year'] = year 
                    titles.append(entry['title'])
                    yield entry

@event('plugin.register')
def register_plugin():
    plugin.register(seplis_movies_stared, 'seplis_movies_stared', api_ver=2)