import datetime
from itertools import chain

from subscriptions.feeds import ContentFeed
from subscriptions.feeds import ContentFeedLibrary
from phillyleg.models import LegFile
from phillyleg.models import LegMinutes
from haystack.query import SearchQuerySet


library = ContentFeedLibrary()

class NewLegislationFeed (ContentFeed):
    def get_content(self):
        return LegFile.objects.all()

    def get_updates_since(self, datetime):
        return self.get_content().filter(intro_date__gt=datetime)

    def get_changes_to(self, legfile):
        return {'Title': legfile.title}

    def get_last_updated(self, legfile):
        return legfile.intro_date

    def get_params(self):
        return {}


class LegislationUpdatesFeed (ContentFeed):
    manager = LegFile.objects

    def __init__(self, **selectors):
        self.selectors = selectors

    def get_content(self):
        if self.selectors:
            return self.manager.filter(**self.selectors)
        else:
            return self.manager.all()

    def get_last_updated(self, legfile):
        legfile_date = max(legfile.intro_date,
                           legfile.final_date or datetime.date(1970, 1, 1))
        action_dates = [action.date_taken
                        for action in legfile.actions.all()]

        return max([legfile_date] + action_dates)

    def get_params(self):
        return self.selectors


class SearchResultsFeed (ContentFeed):
    def __init__(self, search_filter):
        """
        As you'll see in main.SearchView.get_content_feed, we use the value of
        search_view.results.queryset.query.query_filter to store the search.
        I'm not certain, but I'm pretty sure this value is search backend-
        specific.  Just keep that in mind.

        """
        self.filter = search_filter

    def get_content(self):
        return SearchQuerySet().raw_search(self.filter)

    def get_changes_to(self, item):
        if isinstance(item, LegFile):
            return {'Title': item.title}
        elif isinstance(item, LegMinutes):
            return {'Minutes': str(item)}

    def get_last_updated(self, item):
        if isinstance(item, LegFile):
            return item.intro_date
        elif isinstance(item, LegMinutes):
            return item.date_taken

    def get_params(self):
        return {'search_filter': self.filter}


library.register(NewLegislationFeed, 'newly introduced legislation')
library.register(LegislationUpdatesFeed, 'updates to a piece of legislation')
library.register(SearchResultsFeed, 'results of a search query')
