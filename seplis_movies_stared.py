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
            - play-server-id
    """

    schema = {
        'type': 'array', # list of play server ids
    }
    @cached('seplis_movies_stared', persist='1 minute')
    def on_task_input(self, task, config):
        log.debug('Retriving movies users stared')
        titles = []

        for play_server_id in config:
            cursor = None
            while True:
                r = task.requests.get(
                    f'https://api.seplis.net/2/play-servers/{play_server_id}/user-movies-stared',
                    params={
                        'per_page': 100,
                        'cursor': cursor,
                    }
                )
                data = r.json()
                for movie in data['items']:
                    if movie['title']:
                        entry = Entry()
                        entry['title'] = movie['title']
                        year = int(movie["release_date"][:4]) if movie['release_date'] else None
                        if year and str(year) not in entry['title']:
                            entry['title'] += f' ({year})' if year else ''
                        if entry['title'] in titles:
                            continue
                        entry['url'] = f'https://seplis.net/movies/{movie["id"]}'
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
                if not data['cursor']:
                    break
                cursor = data['cursor']

@event('plugin.register')
def register_plugin():
    plugin.register(seplis_movies_stared, 'seplis_movies_stared', api_ver=2)