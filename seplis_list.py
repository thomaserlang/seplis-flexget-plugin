from loguru import logger

from flexget import plugin
from flexget.event import event
from flexget.utils.cached_input import cached
from flexget.entry import Entry

from dateutil.parser import parse as dateutil_parse

log = logger.bind(name='seplis_movies_stared')

class seplis_list:
    """
    watchlist:
        priority: 1
        seplis_list:
            type: movies
            urls:
                - url
    """

    schema = {
        "type": "object",
        "properties": {
            "type": {"type": "string"}, # series or movies
            "urls": {"type": "array"}, # list of api urls
        },
        "additionalProperties": False
    }
    @cached('seplis_list', persist='1 minute')
    def on_task_input(self, task, config):
        log.debug('Retriving movies users stared')
        ids = []

        for url in config['urls']:
            cursor = None
            while True:
                r = task.requests.get(
                    f'https://api.seplis.net{url}',
                    params={
                        'per_page': 100,
                        'cursor': cursor,
                    }
                )
                data = r.json()
                for item in data['items']:
                    if item['id'] in ids:
                        continue
                    ids.append(item['id'])
                    entry = None
                    if config['type'] == 'movies':
                        entry = self.movie_to_entry(item)
                    elif config['type'] == 'series':
                        entry = self.series_to_entry(item)
                    if entry:
                        yield entry
                if not data['cursor']:
                    break
                cursor = data['cursor']


    def movie_to_entry(self, movie):
        if not movie['title']:
            return
        entry = Entry()
        entry['title'] = movie['title']
        year = int(movie["release_date"][:4]) if movie['release_date'] else None
        if year and str(year) not in entry['title']:
            entry['title'] += f' ({year})' if year else ''
        entry['url'] = f'https://seplis.net/movies/{movie["id"]}'
        entry['seplis_movie_id'] = movie['id']
        entry['seplis_title'] = entry['title']
        if movie['release_date']:
            entry['tmdb_released'] = dateutil_parse(movie['release_date']).date()
            entry['seplis_release_date'] = entry['tmdb_released']
        entry['imdb_id'] = movie['externals'].get('imdb', None)
        entry['tmdb_id'] = movie['externals'].get('themoviedb', None)
        entry['movie_year'] = year
        return entry


    def series_to_entry(self, series):
        if not series['title']:
            return
        entry = Entry()
        if not series['title']:
            return
        entry['title'] = series['title']
        year = int(series["premiered"][:4]) if series['premiered'] else None
        if year and str(year) not in entry['title']:
            entry['title'] += f' ({year})'
        entry['alternate_name'] = list(filter(None, series['alternative_titles']))
        entry['url'] = f'https://seplis.net/series/{series["id"]}'
        entry['seplis_series_id'] = series['id']
        entry['seplis_title'] = entry['title']
        entry['imdb_id'] = series['externals'].get('imdb', None)
        entry['tvmaze_id'] = series['externals'].get('tvmaze_id', None)
        entry['tvdb_id'] = series['externals'].get('thetvdb', None)
        entry['tmdb_id'] = series['externals'].get('themoviedb', None)
        if series['episode_type'] == 1:
            entry['identified_by'] = 'sequence'
        elif series['episode_type'] == 2:
            entry['identified_by'] = 'ep'
        elif series['episode_type'] == 3:
            entry['identified_by'] = 'date'        
        return entry
    

@event('plugin.register')
def register_plugin():
    plugin.register(seplis_list, 'seplis_list', api_ver=2)