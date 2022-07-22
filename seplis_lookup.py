from loguru import logger

from flexget import entry, plugin
from flexget.event import event
from flexget.utils.cached_input import cached
from flexget.utils import requests

logger = logger.bind(name='seplis_lookup')

class seplis_lookup:
    series_map = {
        'seplis_id': 'id',
        'seplis_title': 'title',
        'seplis_episode_type': 'episode_type',
    }

    episode_map = {
        'seplis_ep_title': 'title',
        'seplis_ep_air_date': 'air_date',
        'seplis_ep_number': 'number',
        'seplis_ep_season': 'season',
        'seplis_ep_episode': 'episode',
        'seplis_ep_id': 'id',
    }

    movie_map = {
        'seplis_id': 'id',
        'seplis_title': 'title',
        'seplis_year': 'year',

        # Generic fields filled by all movie lookup plugins:
        'movie_name': 'title',
        'movie_year': 'year',
    }

    @plugin.priority(110)
    def on_task_metainfo(self, task, config):
        if not config:
            return
        for entry in task.entries:
            if entry.get('series_name'):
                entry.add_lazy_fields(self.lazy_series_lookup, self.series_map)
                if entry.get('series_id_type') in ('ep', 'sequence', 'date'):
                    entry.add_lazy_fields(self.lazy_episode_lookup, self.episode_map)
            elif entry.get('title'):
                entry.add_lazy_fields(self.lazy_movie_lookup, self.movie_map)

    @entry.register_lazy_lookup('seplis_movie_lookup')
    def lazy_movie_lookup(self, entry):
        movie = None
        if entry.get('seplis_id', eval_lazy=False):
            movie = self.movie_by_id(entry['seplis_id'])
        elif entry.get('title'):
            movie = self.search_by_title(entry['title'], 'movie')
        if not movie:
            return
        entry.update_using_map(self.movie_map, movie)

    @entry.register_lazy_lookup('seplis_series_lookup')
    def lazy_series_lookup(self, entry):
        series = None
        if entry.get('seplis_id', eval_lazy=False):
            series = self.series_by_id(entry['seplis_id'])
        elif entry.get('series_name'):
            series = self.search_by_title(entry['series_name'], 'series')
        if not series:
            return
        entry.update_using_map(self.series_map, series)

    @entry.register_lazy_lookup('seplis_series_episode_lookup')
    def lazy_episode_lookup(self, entry):
        series_id = entry.get('seplis_id')
        if not series_id:
            return
        q = ''
        if entry['series_id_type'] == 'ep':
            q = f'season:{entry["series_season"]} AND episode:{entry["series_episode"]}'
        elif entry['series_id_type'] == 'sequence':
            q = f'number:{entry["series_id"]}'
        elif entry['series_id_type'] == 'date':
            q = f'air_date:"{entry["series_date"].strftime("%Y-%m-%d")}"'
        response = requests.get(f'https://api.seplis.net/1/shows/{series_id}/episodes',
            params={
                'q': q,
            },
        )
        if response.status_code != 200:
            return
        episodes = response.json()
        if not episodes:
            return
        episode = episodes[0]
        if entry['series_id_type'] == 'sequence':
            episode['id'] = str(episode['number'])
        elif entry['series_id_type'] == 'ep':
            episode['id'] = 'S{}E{}'.format(
                str(episode['season']).zfill(2),
                str(episode['episode']).zfill(2),
            )
        elif entry['series_id_type'] == 'date':
            episode['id'] = episode['air_date']

        entry.update_using_map(self.episode_map, episode)

    def series_by_id(self, series_id):
        response = requests.get(f'https://api.seplis.net/1/shows/{series_id}')
        if response.status_code == 200:
            return response.json()

    def movie_by_id(self, movie_id):
        response = requests.get(f'https://api.seplis.net/1/shows/{movie_id}')
        if response.status_code == 200:
            return response.json()

    def search_by_title(self, title, type):
        response = requests.get('https://api.seplis.net/1/search',
            params={
                'title': title,
                'type': type,
            }
        )
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0]
@event('plugin.register')
def register_plugin():
    plugin.register(seplis_lookup, 'seplis_lookup', api_ver=2, interfaces=['task', 'series_metainfo', 'movie_metainfo'])
