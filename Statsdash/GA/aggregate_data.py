
import config
import re
import pygal
from datetime import date, timedelta, datetime
from analytics import Analytics

import Statsdash.utilities as utils

site_ids = config.TABLES
analytics = Analytics()

from Statsdash.config import LOGGING
import logging, logging.config, logging.handlers

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('report')

class AnalyticsData(object):
    
    def __init__(self, sites, period, frequency):
        self.sites = sites
        self.period = period
        self.frequency = frequency
        self.previous = utils.StatsRange.get_previous_period(self.period, self.frequency)
        self.yearly = utils.StatsRange.get_previous_period(self.period, "YEARLY")
        
        self.date_list = [self.period, self.previous, self.yearly]
        
        self.site_ids = utils.convert_values_list(site_ids)
    
    def check_available_data(self):
        run_report = {"result":True, "site":[]}
        for site in self.sites:
            ids = self.site_ids[site]
            for id in ids:
                data_available = analytics.data_available(id, self.period.get_end())
                if not data_available:
                    run_report["result"] = False
                    run_report["site"].append(site)		
    	return run_report    
		
		
    def _remove_ga_names(self, rows):
        for row in rows:
            for key in row.keys():
                new = key.split("ga:")[1]
                row[new] = row.pop(key)
        return rows   
            

    def summary_table(self):	
        data = {}
        for count, date in enumerate(self.date_list):
            totals = []
            metrics="ga:pageviews,ga:users,ga:sessions,ga:pageviewsPerSession,ga:avgSessionDuration"
            for site in self.sites:
                rows = [analytics.rollup_ids(self.site_ids[site], date.get_start(), date.get_end(), metrics=metrics)]

                if rows[0]:
                    rows = self._remove_ga_names(rows)
                    rows = utils.change_key_names(rows, {"pv_per_session":"pageviewsPerSession", "avg_session_time":"avgSessionDuration"})
                
                    totals.extend(rows)
                else:
                    #print "No data for site " + site + " on " + date.get_start() + " - " + date.get_end()
                    logger.debug("No data for site " + site + " on " + date.get_start() + " - " + date.get_end())

            
            aggregate  = utils.aggregate_data(totals, ["pageviews", "users", "sessions", "pv_per_session", "avg_session_time"])
            
            data[count] = aggregate      
        
        for period in data:
            data[period]["pv_per_session"] = data[period]["pv_per_session"]/len(self.sites)
            data[period]["avg_session_time"] = (data[period]["avg_session_time"]/len(self.sites))/60.0
            
            
        this_period = utils.add_change(data[0], data[1], ["pageviews", "users", "sessions", "pv_per_session", "avg_session_time"], "previous")
        this_period = utils.add_change(this_period, data[2], ["pageviews", "users", "sessions", "pv_per_session", "avg_session_time"], "yearly")

        return this_period          
                
                              
    def site_summary_table(self):
        #should this be combined with overall summary table?
        data = {}
        for count, date in enumerate(self.date_list):
            totals = []
            metrics="ga:pageviews,ga:users,ga:sessions,ga:pageviewsPerSession,ga:avgSessionDuration"
            for site in self.sites:
                rows = [analytics.rollup_ids(self.site_ids[site], date.get_start(), date.get_end(), metrics=metrics)]
                if rows[0]:
                    for row in rows:
                        row =  utils.convert_to_floats(row, metrics.split(","))
                        row["ga:site"] = site 
    
                    rows = self._remove_ga_names(rows)
                    rows = utils.change_key_names(rows, {"pv_per_session":"pageviewsPerSession", "avg_session_time":"avgSessionDuration"})
                                        
                    totals.extend(rows)
                else:
                    #print "No data for site " + site + " on " + date.get_start() + " - " + date.get_end()
                    logger.debug("No data for site " + site + " on " + date.get_start() + " - " + date.get_end())
                                    
            aggregated = utils.aggregate_data(totals, ["pageviews", "users", "sessions", "pv_per_session", "avg_session_time"], match_key="site")
            sorted = utils.sort_data(aggregated, "users")
            data[count] = sorted
            
        added_change = utils.add_change(data[0], data[1], ["pageviews", "users", "sessions", "pv_per_session", "avg_session_time"], "previous", match_key="site")
        added_change = utils.add_change(added_change, data[2], ["pageviews", "users", "sessions", "pv_per_session", "avg_session_time"], "yearly", match_key="site")
        
        return added_change
                           


    def _remove_query_string(self, path):
        """
        Removes any queries attached to the end of a page path, so aggregation can be accurate
        """
        exp = "^([^\?]+)\?.*"
        regex = re.compile(exp) 
        m = regex.search(path)
        if m:
            new_path = regex.split(path)[1]            
            return new_path       
        else:
            return path    
            
 
    def article_table(self):
        """
        Return top articles as a list of dictionaries
        Each dictionary has the pageviews, page title, page path and host name
        """
        article_previous = utils.StatsRange.get_previous_period(self.period, "DAILY")#how to do this
        data = {}
        for count, date in enumerate([self.period, article_previous]):
            articles = []
            for site in self.sites:
                rows = analytics.rollup_ids(self.site_ids[site], date.get_start(), date.get_end(), metrics="ga:pageviews", dimensions="ga:pageTitle,ga:pagePath,ga:hostname", 
                                                filters= config.ARTICLE_FILTER, sort="-ga:pageviews", aggregate_key="ga:pagePath")
                rows = self._remove_ga_names(rows)
                rows = utils.change_key_names(rows, {"title":"pageTitle", "path":"pagePath", "host":"hostname"})
                for row in rows:
                    path = row["path"]
                    new_path = self._remove_query_string(path)
                    row["path"] = new_path
                    row["pageviews"] = float(row["pageviews"])
                
                articles.extend(rows)
            aggregated = utils.aggregate_data(articles, ["pageviews"], match_key="path")
            sorted = utils.sort_data(aggregated, "pageviews", limit=20)
            data[count] = sorted
            #group

        added_change = utils.add_change(data[0], data[1], ["pageviews"], "previous", match_key="path")

        return added_change
        
        
        
    def country_table(self):
        countries = ["Czec", "Germa", "Denma", "Spai", "Franc", "Italy", 
            "Portug", "Swede", "Polan", "Brazi", "Belgiu", "Netherl", 
            "United Ki", "Irela", "United St", "Canad", "Austral", "New Ze"]
            
        countries_regex = "|".join(countries)
        filters = "ga:country=~%s" % countries_regex
        row_filters = "ga:country!~%s" % countries_regex
        data = {}
        for count, date in enumerate(self.date_list):
            breakdown = []
            metrics = "ga:pageviews,ga:users"
            for site in self.sites:
                rows = analytics.rollup_ids(self.site_ids[site], date.get_start(), date.get_end(), metrics=metrics, dimensions="ga:country", filters=filters, 
                                                sort="-ga:pageviews", aggregate_key="ga:country")
                world_rows = [analytics.rollup_ids(self.site_ids[site], date.get_start(), date.get_end(), metrics=metrics, dimensions=None, filters=row_filters, 
                                                        sort="-ga:pageviews", aggregate_key=None)]
                try:
                    world_rows[0]["ga:country"] = "ROW"
                except IndexError:
                    world_rows = [{"ga:country":"ROW", "ga:pageviews":0, "ga:users":0}]
                    
                rows.extend(world_rows)
                for row in rows:
                    row =  utils.convert_to_floats(row, metrics.split(","))
                    
                rows = self._remove_ga_names(rows)   
                breakdown.extend(rows)
                    
            aggregated = utils.aggregate_data(breakdown, ["pageviews", "users"], match_key="country")
            sorted = utils.sort_data(aggregated, "users")
            data[count] = sorted
            
        added_change = utils.add_change(data[0], data[1], ["pageviews", "users"], "previous", match_key="country")
        added_change = utils.add_change(added_change, data[2], ["pageviews", "users"], "yearly", match_key="country")
        
        return added_change
            
    def _get_source_list(self):
        data = {}
        for count, date in enumerate(self.date_list):
            traffic_sources = []
            metrics = "ga:pageviews,ga:users"
            for site in self.sites:       
                rows = analytics.rollup_ids(self.site_ids[site], date.get_start(), date.get_end(), metrics=metrics, dimensions="ga:sourceMedium", sort="-ga:users", aggregate_key="ga:sourceMedium")
                rows = self._remove_ga_names(rows)
                rows = utils.change_key_names(rows, {"source_medium":"sourceMedium"})
                for row in rows:
                    row =  utils.convert_to_floats(row, ["pageviews", "users"])
                    
                traffic_sources.extend(rows)
                
            aggregated = utils.aggregate_data(traffic_sources, ["pageviews", "users"], match_key="source_medium")
            sorted = utils.sort_data(aggregated, "users")
            data[count] = sorted   
            
        added_change = utils.add_change(data[0], data[1], ["pageviews", "users"], "previous", match_key="source_medium")
        added_change = utils.add_change(added_change, data[2], ["pageviews", "users"], "yearly", match_key="source_medium")
        
        return added_change

        
    def traffic_source_table(self):
        table = self._get_source_list()
        table = table[:10]
        return table    
        
        
    def referring_sites_table(self):
        sources = self._get_source_list()
        count = 0
        referrals = []
        for row in sources:
            source = row["source_medium"].split(" / ")[0] 
            black_ex = '|'
            black_string = black_ex.join(config.SOURCE_BLACK_LIST)
            regex = re.compile(black_string)
            match = regex.search(source)
            if match: 
                continue;           
            else:
                if count == 5:
                    break
                else:
                    count += 1
                    filter = "ga:source==%s" % source
                    article = self.referral_articles(filter, 1)
                    row["source"] = source
                    row["articles"] = article   
                    referrals.append(row)    
        
        return referrals 
        
        
    def social_network_table(self, num_articles):
        data = {}
        for count, date in enumerate(self.date_list):
            social = []
            metrics = "ga:pageviews,ga:users,ga:sessions"
            for site in self.sites:
                rows = analytics.rollup_ids(self.site_ids[site], date.get_start(), date.get_end(), metrics=metrics, dimensions="ga:socialNetwork", filters="ga:socialNetwork!=(not set)", 
                                                sort="-ga:users", aggregate_key="ga:socialNetwork")
                rows = self._remove_ga_names(rows)
                rows = utils.change_key_names(rows, {"social_network":"socialNetwork"})
                for row in rows:
                    row =  utils.convert_to_floats(row, ["pageviews", "users", "sessions"])
                    
                social.extend(rows)
            
            aggregated = utils.aggregate_data(social, ["pageviews", "users", "sessions"], match_key="social_network")
            sorted = utils.sort_data(aggregated, "users", limit=15)
            data[count] = sorted
            
        added_change = utils.add_change(data[0], data[1], ["pageviews", "users", "sessions"], "previous", match_key="social_network")
        added_change = utils.add_change(added_change, data[2], ["pageviews", "users", "sessions"], "yearly", match_key="social_network")
        
        for row in added_change:
            filter = "ga:socialNetwork==%s" % row["social_network"]
            article = self.referral_articles(filter, num_articles)
            row["articles"] = article            
        
        return added_change
        
        
    def referral_articles(self, filter, limit):
        filters = config.ARTICLE_FILTER + ";" + filter
        article_previous = utils.StatsRange.get_previous_period(self.period, "DAILY")#how to do this
        data = {}
        for count, date in enumerate([self.period, article_previous]):
            articles = []
            for site in self.sites:
                rows = analytics.rollup_ids(self.site_ids[site], date.get_start(), date.get_end(), metrics="ga:pageviews", dimensions="ga:pageTitle,ga:pagePath,ga:hostname", filters=filters, 
                                                sort="-ga:pageviews", aggregate_key="ga:pagePath")
                rows = self._remove_ga_names(rows)
                rows = utils.change_key_names(rows, {"title":"pageTitle", "path":"pagePath", "host":"hostname"})
                for row in rows:
                    path = row["path"]
                    new_path = self._remove_query_string(path)
                    row["path"] = new_path
                    row["pageviews"] = float(row["pageviews"])
                
                articles.extend(rows)
            aggregated = utils.aggregate_data(articles, ["pageviews"], match_key="path")
            sorted = utils.sort_data(aggregated, "pageviews", limit=limit)
            data[count] = sorted
            #group

        added_change = utils.add_change(data[0], data[1], ["pageviews"], "previous", match_key="path")

        return added_change                
        
        
    def device_table(self):
        data = {}
        for count, date in enumerate(self.date_list):
            devices = []
            for site in self.sites:
                rows = analytics.rollup_ids(self.site_ids[site], date.get_start(), date.get_end(), metrics="ga:users", dimensions="ga:deviceCategory", sort="-ga:users", aggregate_key="ga:deviceCategory")
                rows = self._remove_ga_names(rows)
                rows = utils.change_key_names(rows, {"device_category":"deviceCategory"})
                for row in rows:
                    row["users"] = float(row["users"])
                    
                devices.extend(rows)
            
            aggregated = utils.aggregate_data(devices, ["users"], match_key="device_category")
            sorted = utils.sort_data(aggregated, "users", limit=6)
            data[count] = sorted 
            
        added_change = utils.add_change(data[0], data[1], ["users"], "previous", match_key="device_category")
        added_change = utils.add_change(added_change, data[2], ["users"], "yearly", match_key="device_category")
        
        return added_change
        
        
    def device_chart(self, data):
        chart_data = {}
        x_labels = []
        for count, row in enumerate(data):
            for device in row["data"]:
                try:
                    chart_data[device["device_category"]].append(utils.percentage(device["users"], row["summary"]["users"]))
                except KeyError:
                    chart_data[device["device_category"]] = [utils.percentage(device["users"], row["summary"]["users"])]
                
            x_labels.append(row["month"])

        
        chart = utils.chart("Device Chart", x_labels, chart_data, "Month", "Percentage of Users")
        return chart
        
    
    def social_chart(self):

        current = self.period.start_date
        end = self.period.end_date
        dates = []
        while current <= end:
            current_range = utils.StatsRange("day", current, current)
            dates.append(current_range)
            current = current + timedelta(days=1)   
        

        data = {}
        network_data = {}
        for count, date in enumerate(dates):
            social = []
            network_social = []
            metrics = "ga:pageviews,ga:users,ga:sessions"
            for site in config.TABLES.keys():
                rows = [analytics.rollup_ids(self.site_ids[site], date.get_start(), date.get_end(), metrics=metrics, dimensions=None, filters="ga:socialNetwork!=(not set)", 
                                                sort="-ga:users")]
                if rows[0]:
                    rows = self._remove_ga_names(rows)
                    for row in rows:
                        row =  utils.convert_to_floats(row, ["pageviews", "users", "sessions"])
                        
                    if site in self.sites:    
                        social.extend(rows)
                        
                    network_social.extend(rows)
                else:
                    #print "No data for site " + site + " on " + date.get_start() + " - " + date.get_end()
                    logger.debug("No data for site " + site + " on " + date.get_start() + " - " + date.get_end())

            
            aggregate  = utils.aggregate_data(social, ["pageviews", "users", "sessions"])
            network_aggregate  = utils.aggregate_data(network_social, ["pageviews", "users", "sessions"])
            
            data[date.get_start()] = aggregate  
            network_data[date.get_start()] = network_aggregate  
            

        x_labels = []
        graph_data = {"users":[], "pageviews":[], "network_pageviews":[], "network_users":[]}
        for range in dates:
            x_labels.append(range.get_start())
            graph_data["users"].append(data[range.get_start()]["users"])
            graph_data["pageviews"].append(data[range.get_start()]["pageviews"])
            graph_data["network_users"].append(network_data[range.get_start()]["users"])
            graph_data["network_pageviews"].append(network_data[range.get_start()]["pageviews"])

        
        chart = utils.chart("Social Data", x_labels, graph_data, "Day", "Number")
        return chart
            
        
        
        
        
            
                
        
        
        