from pprint import pprint
from datetime import datetime, timedelta
from html.parser import HTMLParser
from google.oauth2 import service_account
from googleapiclient.discovery import build
import logging.config
import logging.handlers
import re

from Statsdash.analytics import GoogleAnalytics, google_metrics, our_metrics
from Statsdash.GA import config
from Statsdash.utils import utils
from Statsdash.config import LOGGING
from Statsdash.stats_range import StatsRange

# TODO move this somewhere else?
SCOPES = ['https://www.googleapis.com/auth/analytics.readonly', ]
credentials = service_account.Credentials.from_service_account_file(
    config.KEY_FILE,
    scopes=SCOPES
)
service = build('analytics', 'v3', credentials=credentials)
resource = service.data().ga()

analytics = GoogleAnalytics(resource)

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('report')

Metrics = GoogleAnalytics.Metrics
Dimensions = GoogleAnalytics.Dimensions


# TODO use base class for this and YouTube
# class AnalyticsData:
#
#     def __init__(self, site_tables, period, frequency):
#         self.sites = site_tables.keys()
#         self.period = period
#         self.frequency = frequency
#         # shouldn't be implicit
#         self.previous = StatsRange.get_previous_period(self.period, self.frequency)
#         self.yearly = StatsRange.get_previous_period(self.period, "YEARLY")
#
#         self.date_list = [self.period, self.previous, self.yearly]
#
#         # TODO rename attribute
#         self.site_ids = site_tables
#
#     def check_available_data(self):
#         run_report = {"result": True, "site": []}
#         multiple_sites = True
#         # Get the end time of the period
#         period_end_time = datetime(
#             year=self.period.end_date.year,
#             month=self.period.end_date.month,
#             day=self.period.end_date.day,
#             hour=23,
#             minute=59,
#             second=59,
#         )
#         analytics_populated_time = period_end_time + timedelta(hours=1)
#         data_possibly_available = datetime.now() > analytics_populated_time
#         # TODO remove
#         data_possibly_available = True
#         if not data_possibly_available:
#             return {'result': False, 'site': ['Too early for data to be available!']}
#         if len(self.sites) == 1:
#             multiple_sites = False
#         for site in self.sites:
#             ids = self.site_ids[site]
#             for property_details in ids:
#                 wait = property_details.get('wait_for_data', True)
#                 # If we're running a report for multiple sites and this
#                 # property is not essential, we can safely go ahead with or
#                 # without the data available.
#                 if multiple_sites and not wait:
#                     continue
#                 data_available = analytics.data_available(property_details['id'], self.period.get_end())
#                 if not data_available:
#                     run_report["result"] = False
#                     run_report["site"].append(site)
#         return run_report
#
#     def _remove_ga_names(self, rows):
#         for row in rows:
#             keys = list(row.keys())
#             for key in keys:
#                 assert key.startswith('ga:')
#                 new_key = key[3:]
#                 row[new_key] = row.pop(key)
#         return rows
#


#
#     def _get_by_source(self, subdivide_by_medium=False):
#         data = {}
#         aggregate_key = "ga:source"
#         match_key = "source"
#         if subdivide_by_medium:
#             aggregate_key = "ga:sourceMedium"
#             match_key = "source_medium"
#         for count, date in enumerate(self.date_list):
#             traffic_sources = []
#             metrics = "ga:pageviews,ga:users"
#             for site in self.sites:
#                 rows = analytics.rollup_ids(
#                     self.site_ids[site],
#                     date.get_start(),
#                     date.get_end(),
#                     metrics=metrics,
#                     dimensions=aggregate_key,
#                     sort="-ga:users",
#                     aggregate_key=aggregate_key
#                 )
#                 rows = self._remove_ga_names(rows)
#                 if subdivide_by_medium:
#                     rows = utils.change_key_names(
#                         rows,
#                         {"source_medium": "sourceMedium"}
#                     )
#                 for row in rows:
#                     row = utils.convert_to_floats(row, ["pageviews", "users"])
#                 traffic_sources.extend(rows)
#
#             aggregated = utils.aggregate_data(
#                 traffic_sources,
#                 ["pageviews", "users"],
#                 match_key=match_key,
#             )
#             sorted = utils.sort_data(aggregated, "users")
#             data[count] = sorted
#
#         added_change = utils.add_change(
#             data[0],
#             data[1],
#             ["pageviews", "users"],
#             "previous",
#             match_key=match_key
#         )
#         added_change = utils.add_change(
#             added_change,
#             data[2],
#             ["pageviews", "users"],
#             "yearly",
#             match_key=match_key
#         )
#         return added_change
#
#     def traffic_source_table(self):
#         table = self._get_by_source(subdivide_by_medium=True)
#         table = table[:10]
#         return table
#
#     def referring_sites_table(self, num_articles):
#         sources = self._get_by_source()
#         count = 0
#         referrals = []
#         black_ex = '|'
#         black_string = black_ex.join(config.SOURCE_BLACK_LIST)
#         regex = re.compile(black_string)
#         for row in sources:
#             if count == 5:
#                 break
#             source = row["source"]
#             match = regex.search(source)
#             if match:
#                 continue
#             else:
#                 count += 1
#                 filter = "ga:source==%s" % source
#                 article = self.referral_articles(filter, num_articles)
#                 row["source"] = source
#                 row["articles"] = article
#                 referrals.append(row)
#         return referrals
#
#     def social_network_table(self, num_articles):
#         data = {}
#         for count, date in enumerate(self.date_list):
#             social = []
#             metrics = "ga:pageviews,ga:users,ga:sessions"
#             for site in self.sites:
#                 rows = analytics.rollup_ids(
#                     self.site_ids[site],
#                     date.get_start(),
#                     date.get_end(),
#                     metrics=metrics,
#                     dimensions="ga:socialNetwork",
#                     filters="ga:socialNetwork!=(not set)",
#                     sort="-ga:users",
#                     aggregate_key="ga:socialNetwork"
#                 )
#                 rows = self._remove_ga_names(rows)
#                 rows = utils.change_key_names(
#                     rows,
#                     {"social_network": "socialNetwork"}
#                 )
#                 for row in rows:
#                     row = utils.convert_to_floats(
#                         row,
#                         ["pageviews", "users", "sessions"]
#                     )
#                 social.extend(rows)
#
#             aggregated = utils.aggregate_data(
#                 social,
#                 ["pageviews", "users", "sessions"],
#                 match_key="social_network"
#             )
#             sorted = utils.sort_data(aggregated, "users", limit=15)
#             data[count] = sorted
#
#         added_change = utils.add_change(
#             data[0],
#             data[1],
#             ["pageviews", "users", "sessions"],
#             "previous",
#             match_key="social_network"
#         )
#         added_change = utils.add_change(
#             added_change,
#             data[2],
#             ["pageviews", "users", "sessions"],
#             "yearly",
#             match_key="social_network"
#         )
#         for row in added_change:
#             filter = "ga:socialNetwork==%s" % row["social_network"]
#             article = self.referral_articles(filter, num_articles)
#             row["articles"] = article
#         return added_change
#
#     def referral_articles(self, filter, limit):
#         filters = config.ARTICLE_FILTER + ";" + filter
#         article_previous = utils.StatsRange.get_previous_period(self.period, "DAILY")
#         data = {}
#         for count, date in enumerate([self.period, article_previous]):
#             articles = []
#             for site in self.sites:
#                 rows = analytics.rollup_ids(
#                     self.site_ids[site],
#                     date.get_start(),
#                     date.get_end(),
#                     metrics="ga:pageviews",
#                     dimensions="ga:pageTitle,ga:pagePath,ga:hostname",
#                     filters=filters,
#                     sort="-ga:pageviews",
#                     aggregate_key="ga:pagePath"
#                 )
#                 rows = self._remove_ga_names(rows)
#                 rows = utils.change_key_names(
#                     rows,
#                     {"title": "pageTitle", "path": "pagePath", "host": "hostname"}
#                 )
#                 for row in rows:
#                     path = row["path"]
#                     title = row["title"]
#                     new_path = self._remove_query_string(path)
#                     new_title = self._get_title(path, title)
#                     row["path"] = new_path
#                     row["title"] = new_title
#                     row["pageviews"] = float(row["pageviews"])
#
#                 articles.extend(rows)
#             aggregated = utils.aggregate_data(articles, ["pageviews"], match_key="path")
#             sorted = utils.sort_data(aggregated, "pageviews", limit=limit)
#             data[count] = sorted
#
#         # NOTE different to other tables?
#         added_change = utils.add_change(data[0], data[1], ["pageviews"], "previous", match_key="path")
#         return added_change
#
#     def device_table(self):
#         data = {}
#         for count, date in enumerate(self.date_list):
#             devices = []
#             for site in self.sites:
#                 rows = analytics.rollup_ids(self.site_ids[site], date.get_start(), date.get_end(), metrics="ga:users", dimensions="ga:deviceCategory", sort="-ga:users", aggregate_key="ga:deviceCategory")
#                 rows = self._remove_ga_names(rows)
#                 rows = utils.change_key_names(
#                     rows,
#                     {"device_category": "deviceCategory"}
#                 )
#                 for row in rows:
#                     row["users"] = float(row["users"])
#                 devices.extend(rows)
#
#             aggregated = utils.aggregate_data(devices, ["users"], match_key="device_category")
#             sorted = utils.sort_data(aggregated, "users", limit=6)
#             data[count] = sorted
#
#         added_change = utils.add_change(data[0], data[1], ["users"], "previous", match_key="device_category")
#         added_change = utils.add_change(added_change, data[2], ["users"], "yearly", match_key="device_category")
#         return added_change
#
#     def device_chart(self, data):
#         chart_data = {}
#         x_labels = []
#         for count, row in enumerate(data):
#             for device in row["data"]:
#                 try:
#                     chart_data[device["device_category"]].append(utils.percentage(device["users"], row["summary"]["users"]))
#                 except KeyError:
#                     chart_data[device["device_category"]] = [utils.percentage(device["users"], row["summary"]["users"])]
#
#             x_labels.append(row["month"])
#
#         chart = utils.chart("Device Chart", x_labels, chart_data, "Month", "Percentage of Users")
#         return chart
#
#     def social_chart(self):
#
#         current = self.period.start_date
#         end = self.period.end_date
#         dates = []
#         while current <= end:
#             current_range = utils.StatsRange("day", current, current)
#             dates.append(current_range)
#             current = current + timedelta(days=1)
#
#         data = {}
#         network_data = {}
#         for count, date in enumerate(dates):
#             social = []
#             network_social = []
#             metrics = "ga:pageviews,ga:users,ga:sessions"
#             for site in config.TABLES.keys():
#                 rows = [analytics.rollup_ids(self.site_ids[site], date.get_start(), date.get_end(), metrics=metrics, dimensions=None, filters="ga:socialNetwork!=(not set)", sort="-ga:users")]
#                 if rows[0]:
#                     rows = self._remove_ga_names(rows)
#                     for row in rows:
#                         row = utils.convert_to_floats(row, ["pageviews", "users", "sessions"])
#                     if site in self.sites:
#                         social.extend(rows)
#                     network_social.extend(rows)
#                 else:
#                     logger.debug("No data for site " + site + " on " + date.get_start() + " - " + date.get_end())
#
#             aggregate = utils.aggregate_data(social, ["pageviews", "users", "sessions"])
#             network_aggregate = utils.aggregate_data(network_social, ["pageviews", "users", "sessions"])
#
#             data[date.get_start()] = aggregate
#             network_data[date.get_start()] = network_aggregate
#
#         x_labels = []
#         graph_data = {"users": [], "pageviews": [], "network_pageviews": [], "network_users": []}
#         for range in dates:
#             x_labels.append(range.get_start())
#             graph_data["users"].append(data[range.get_start()]["users"])
#             graph_data["pageviews"].append(data[range.get_start()]["pageviews"])
#             graph_data["network_users"].append(network_data[range.get_start()]["users"])
#             graph_data["network_pageviews"].append(network_data[range.get_start()]["pageviews"])
#
#         chart = utils.chart("Social Data", x_labels, graph_data, "Day", "Number")
#         return chart

#
# def _get_title(self, path, title):
#     """
#     Checks if the article path includes 'amp' making it an AMP article, and
#     appends this to the name so easier to see in report
#     """
#     # NOTE title/docstring confusion
#     exp = "/amp/"
#     regex = re.compile(exp)
#     m = regex.search(path + "/")
#     if m:
#         title = title + " (AMP)"
#         # amp articles come with html characters
#         h = HTMLParser()
#         title = h.unescape(title)
#         return title
#     else:
#         return title


class AnalyticsData:

    metrics = []
    dimensions = []
    aggregate_key = None
    filters = None
    match_key = None
    sort_by = None

    def __init__(self, site_tables, period, frequency):
        self.sites = site_tables.keys()
        self.frequency = frequency
        # TODO pass name into get_pervious_period
        previous_period = StatsRange.get_previous_period(period, self.frequency)  # remove literal
        previous_period.name = 'previous'
        yearly_period = StatsRange.get_previous_period(period, "YEARLY")
        yearly_period.name = 'yearly'
        self.periods = [period, previous_period, yearly_period]
        # TODO rename attribute
        self.site_ids = site_tables

    # TODO test
    def get_table(self):
        """

        """
        period_data = []
        for period in self.periods:
            data = self._get_data_for_period(period)
            period_data.append(data)
        return self._join_periods(period_data)

    def _join_periods(self, data):
        """
        Gets the data for each period and combines them into a single dict.

        Args:
            * `data` - `list` - an executed query for each period.

        Returns:
            * `dict`
        """
        # each item in data is a period of data
        current_period = data[0]
        other_periods = data[1:]
        new_data = []
        #iterate over every item in the current period and get the change versus prevous periods
        for i, current_period_data in enumerate(current_period):
            joined_data = current_period_data
            for j, other_period in enumerate(other_periods, 1):
                period = self.periods[j]
                other_period_data = other_period[i]
                change = utils.get_change(
                    current_period_data,
                    other_period_data,
                    our_metrics(self.metrics),
                    match_key=self.match_key
                )
                change = utils.prefix_keys(change, period.name + '_')
                joined_data.update(change)
            new_data.append(joined_data)
        return new_data

    def _get_data_for_period(self, period):
        """
        Gets the analytics data for each site in `self.site_ids` for the given
        period and prepares it for the table: renames the keys for each metric,
        aggregates the data for each site, and gets the average for values where appropriate.

        Args:
            * `period` - `StatsRange`

        Returns:
            * `list` - data for each site.
        """
        all_sites_data = []
        for site in self.sites:
            data = analytics.get_data(
                self.site_ids[site],
                period.get_start(),
                period.get_end(),
                # TODO rename method.
                metrics=','.join(google_metrics(self.metrics)),
                dimensions=','.join(google_metrics(self.dimensions)),
                filters=self.filters,
                sort=self.sort_by,
                aggregate_key=self.aggregate_key,
            )
            # data is a list with a dict for each id in site config
            if data:
                data = self._format_all_data(data, site)
                all_sites_data = all_sites_data + data
            else:
                logger.debug(
                    f'No data for site {site} on {period.get_start()} - '
                    f'{period.get_end()}'
                )
        aggregated_data = self._aggregate_data(all_sites_data)
        return aggregated_data

    def _aggregate_data(self, data):
        return utils.aggregate_data(
            data,
            our_metrics(self.metrics),
            match_key=self.match_key
        )


    def _format_all_data(self, data, site):
        output = []
        for item in data:
            item = self._format_data(item, site)
            output.append(item)
        return output

    def _format_data(self, data, site):
        replacements = [(c[0], c[1]) for c in self.metrics + self.dimensions]
        data = utils.change_key_names(data, replacements)
        return data

    def _remove_query_string(self, path):
        """
        Removes any queries attached to the end of a page path, so aggregation
        can be accurate.
        """
        # TODO finish docstring
        # NOTE not sure why linter is compaining. Maybe `r`?
        exp = "^([^\?]+)\?.*"
        regex = re.compile(exp)
        m = regex.search(path)
        if m:
            new_path = regex.split(path)[1]
            return new_path
        else:
            return path

    def _get_title(self, path, title):
        """
        Checks if the article path includes 'amp' making it an AMP article, and
        appends this to the name so easier to see in report.
        """
        # TODO finish docstring
        # NOTE title/docstring confusion
        exp = "/amp/"
        regex = re.compile(exp)
        m = regex.search(path + "/")
        if m:
            title = title + " (AMP)"
            # amp articles come with html characters
            h = HTMLParser()
            title = h.unescape(title)
        return title


class SummaryData(AnalyticsData):
    """
    Gets the aggregated analytics data for all sites.
    """
    metrics = [
        Metrics.pageviews,
        Metrics.users,
        Metrics.sessions,
        Metrics.pv_per_sessions,
        Metrics.avg_session_time,
    ]

    def _format_data(self, data, site):
        data = super()._format_data(data, site)
        return self._apply_averages(data)


    # TODO look closely at this method.
    def _apply_averages(self, data):
        """
        Get average for metrics which are averages.

        Args:
            * `data` - `dict` - analytics data blob (after rename).

        Returns:
            * `dict`
        """
        len_sites = len(self.sites)
        # TODO metrics could be turned into classes. Each class could handle average.
        av = data.get(Metrics.pv_per_sessions[1], 0) / len_sites
        data[Metrics.pv_per_sessions[1]] = av
        av = data.get(Metrics.avg_session_time[1], 0) / len_sites / 60.0
        data[Metrics.avg_session_time[1]] = av
        return data


class SiteSummaryData(AnalyticsData):

    metrics = [
        Metrics.pageviews,
        Metrics.users,
        Metrics.sessions,
        Metrics.pv_per_sessions,
        Metrics.avg_session_time,
    ]

    match_key = 'site'

    def _format_data(self, data, site):
        data = super()._format_data(data, site)
        # Maybe we could add this by default?
        data['site'] = site
        return data

    # TODO replace with simple sort_by attribute.
    def _get_data_for_period(self, period):
        # sort sites by users
        data = super()._get_data_for_period(period)
        return utils.sort_data(data, Metrics.users[1])


class ArticleData(AnalyticsData):

    metrics = [
        Metrics.pageviews,
    ]
    dimensions = [
        Dimensions.title,
        Dimensions.path,
        Dimensions.host,
    ]
    filters = 'ga:pagePathLevel1!=/;ga:pagePath!~/page/*;ga:pagePath!~^/\?.*'
    sort_by = '-' + Metrics.pageviews[0]
    # TODO double check sorting
    match_key = 'site_path'
    aggregate_key = Dimensions.path[0]

    def _format_data(self, data, site):
        data = super()._format_data(data, site)

        # TODO clean logic
        path = data['path']
        title = data['title']
        new_path = self._remove_query_string(path)
        new_title = self._get_title(path, title)
        data['path'] = new_path
        data['site_path'] = site + new_path
        data['title'] = new_title
        return data


class CountryData(AnalyticsData):

    metrics = [
        Metrics.pageviews,
        Metrics.users,
    ]
    dimensions = [
        Dimensions.country,
    ]
    countries = [
        'Czec', 'Germa', 'Denma', 'Spai', 'Franc', 'Italy', 'Portug',
        'Swede', 'Polan', 'Brazi', 'Belgiu', 'Netherl', 'United Ki',
        'Irela', 'United St', 'Canad', 'Austral', 'New Ze'
    ]
    countries_regex = "|".join(countries)
    filters = f'ga:country=~{countries_regex}'
    sort_by = '-' + Metrics.pageviews[0]
    # TODO double check sorting
    match_key = 'site_path'
    aggregate_key = Dimensions.path[0]

#     def country_table(self):
#         countries = [
#             "Czec", "Germa", "Denma", "Spai", "Franc", "Italy", "Portug",
#             "Swede", "Polan", "Brazi", "Belgiu", "Netherl", "United Ki",
#             "Irela", "United St", "Canad", "Austral", "New Ze"
#         ]
#
#         countries_regex = "|".join(countries)
#         filters = "ga:country=~%s" % countries_regex
#         row_filters = "ga:country!~%s" % countries_regex
#         data = {}
#         for count, date in enumerate(self.date_list):
#             breakdown = []
#             metrics = "ga:pageviews,ga:users"
#             for site in self.sites:
#                 rows = analytics.rollup_ids(
#                     self.site_ids[site],
#                     date.get_start(),
#                     date.get_end(),
#                     metrics=metrics,
#                     dimensions="ga:country",
#                     filters=filters,
#                     sort="-ga:pageviews",
#                     aggregate_key="ga:country"
#                 )
#                 world_rows = [
#                     # TODO use some sort of *args for date range - also property
#                     analytics.rollup_ids(
#                         self.site_ids[site],
#                         date.get_start(),
#                         date.get_end(),
#                         metrics=metrics,
#                         dimensions=None,
#                         filters=row_filters,
#                         sort="-ga:pageviews",
#                         aggregate_key=None
#                     )
#                 ]
#
#                 if world_rows[0]:
#                     world_rows[0]["ga:country"] = "ROW"
#                 else:
#                     world_rows = [{"ga:country": "ROW", "ga:pageviews": 0, "ga:users": 0}]
#                 rows.extend(world_rows)
#
#                 for row in rows:
#                     row = utils.convert_to_floats(row, metrics.split(","))
#
#                 rows = self._remove_ga_names(rows)
#                 # NOTE inconsistent naming
#                 breakdown.extend(rows)
#
#             aggregated = utils.aggregate_data(
#                 breakdown,
#                 ["pageviews", "users"],
#                 match_key="country"
#             )
#             sorted = utils.sort_data(aggregated, "users")
#             data[count] = sorted
#
#         added_change = utils.add_change(
#             data[0],
#             data[1],
#             ["pageviews", "users"],
#             "previous",
#             match_key="country"
#         )
#         added_change = utils.add_change(
#             added_change,
#             data[2],
#             ["pageviews", "users"],
#             "yearly",
#             match_key="country"
#         )
#         return added_change
