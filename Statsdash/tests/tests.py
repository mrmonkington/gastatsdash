# from datetime import datetime, date, timedelta
# import unittest
#
# from scheduler import RunLogger
#
#
# class TestDateUtils(unittest.TestCase):
#
#     def test_last_weekday_currentWeekdayMatches(self):
#         today = datetime(year=2015, month=7, day=2)
#         day = "Thursday"
#         result = find_last_weekday(today, day)
#         self.assertEqual(result, datetime(year=2015, month=7, day=2))
#
#     def test_last_weekday_currentWeekdayBelowDesired(self):
#         today = datetime(year=2015, month=7, day=2)
#         day = "Friday"
#         result = find_last_weekday(today, day)
#         self.assertEqual(result, datetime(year=2015, month=6, day=26))
#
#     def test_last_weekday_currentWeekdayAboveDesired(self):
#         today = datetime(year=2015, month=7, day=2)
#         day = "Wednesday"
#         result = find_last_weekday(today, day)
#         self.assertEqual(result, datetime(year=2015, month=7, day=1))
#
#     def test_next_weekday_currentWeekdayMatches(self):
#         today = datetime(year=2015, month=7, day=2)
#         day = "Thursday"
#         result = find_next_weekday(today, day)
#         self.assertEqual(result, datetime(year=2015, month=7, day=2))
#
#     def test_next_weekday_currentWeekdayBelowDesired(self):
#         today = datetime(year=2015, month=7, day=2)
#         day = "Friday"
#         result = find_next_weekday(today, day)
#         self.assertEqual(result, datetime(year=2015, month=7, day=3))
#
#     def test_next_weekday_currentWeekdayAboveDesired(self):
#         today = datetime(year=2015, month=7, day=2)
#         day = "Wednesday"
#         result = find_next_weekday(today, day)
#         self.assertEqual(result, datetime(year=2015, month=7, day=8))
#
#
# class TestNextRun(unittest.TestCase):
#     run_log = RunLogger()
#     dates = [
#         datetime(2016, 1, 31),
#         datetime(2015, 1, 31),
#         datetime(2015, 3, 1),
#         datetime(2015, 3, 23),
#         datetime(2016, 1, 1),
#         datetime(2016, 2, 28),
#         datetime(2016, 2, 29),
#         datetime(2016, 12, 1)
#     ]
#
#     """test_returns = [
#         (datetime(2016, 01, 31), datetime(2016, 03, 01)),
#         (datetime(2015, 01, 31), datetime(2015, 03, 01)),
#         (datetime(2016, 03, 31), datetime(2016, 04, 01)),
#         (datetime(2016, 03, 30), datetime(2016, 04, 01))
#     ]"""
#
#     def setUp(self):
#         pass
#
#     """Test for MONTHLY reports"""
#
#     def test_monthly_run_on_first_day(self):
#         """Test routine to check monthly runs on the first"""
#         for d in self.dates:
#             last_run = d
#             next_run = self.run_log.get_next_run(
#                 last_run,
#                 "MONTHLY",
#                 {"day": 1},
#             )
#             self.assertEqual(1, next_run.day)
#
#     def test_last_run_last_day(self):
#         """Test routine to check works when last run is last day in the month"""
#         test_date = [datetime(2016, 3, 31, 00, 00, 00, 1)]
#         test_next_run = datetime(2016, 5, 1, 00, 00, 00, 1)
#         for d in test_date:
#             last_run = d
#             next_run = self.run_log.get_next_run(last_run, "MONTHLY", {"day": 1})
#             self.assertEqual(next_run, test_next_run)
#
#     def test_leap_year(self):
#         """Test routine to check dates over a leap year"""
#         test_date = [datetime(2016, 1, 31)]
#         test_next_run = datetime(2016, 3, 1)
#         for d in test_date:
#             last_run = d
#             next_run = self.run_log.get_next_run(last_run, "MONTHLY", {"day": 1})
#             self.assertEqual(next_run, test_next_run)
#
#     def test_not_leap_year(self):
#         """Test routine to check dates over a non leap year"""
#         test_date = [datetime(2015, 1, 31)]
#         test_next_run = datetime(2015, 3, 1)
#         for d in test_date:
#             last_run = d
#             next_run = self.run_log.get_next_run(last_run, "MONTHLY", {"day": 1})
#             self.assertEqual(next_run, test_next_run)
#
#     def test_other_days(self):
#         """Test routine to check monthly correct for different day"""
#         # repace with range
#         days = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]
#         test_date = datetime(2015, 1, 31)
#         for day in days:
#             last_run = test_date
#             test_next_run = datetime(2015, 3, day)
#             next_run = self.run_log.get_next_run(
#                 last_run,
#                 "MONTHLY",
#                 {"day": day}
#             )
#             self.assertEqual(next_run, test_next_run)
#
#     def test_wrong_days(self):
#         """Test routine to check monthly returns error for wrong days"""
#         days = [29, 30, 31, 33, 32, 50, 100, 0, -10, -100]
#         test_date = datetime(2015, 1, 31)
#         for day in days:
#             last_run = test_date
#             self.assertRaises(
#                 ValueError,
#                 self.run_log.get_next_run,
#                 last_run,
#                 "MONTHLY",
#                 {"day": day}
#             )
#
#     def test_looping(self):
#         """Test routine to check return dates in a sequence"""
#         start_date = datetime(2015, 12, 31)
#         end_date = datetime(2016, 3, 31)
#         runs = []
#         periods = [start_date]
#         while start_date < end_date:
#             next_run = self.run_log.get_next_run(
#                 start_date,
#                 "MONTHLY",
#                 {"day": 1}
#             )
#             runs.append(next_run)
#             start_date = next_run - timedelta(days=1)
#             periods.append(start_date)
#         self.assertEqual(runs, [datetime(2016, 2, 1), datetime(2016, 3, 1), datetime(2016, 4, 1)])
#
#     def test_override_late_send(self):
#         """
#         Test routine to check monthly returns override true when next run was
#         over 2 days ago
#         """
#         last_run = datetime(2015, 11, 30)
#         self.run_log.get_next_run(last_run, "MONTHLY", {"day": 1})
#         self.assertTrue(self.run_log.override_data)
#
#     def test_override_2_days_late(self):
#         """
#         Test routine to check daily returns override true when last run was
#         over 2 days ago
#         """
#         today = date.today() - timedelta(days=1)
#         now = datetime(today.year, today.month, today.day)
#         last_run = datetime(2016, 2, 29)
#         last_run = now - timedelta(days=2)
#         self.run_log.get_next_run(last_run, "DAILY")
#         self.assertTrue(self.run_log.override_data)
#
#
# # class TestScheduler(unittest.TestCase):
# #     # mock_run = mock.Mock(spec = RunLogger)
# #     # mock_report = mock.Mock(spec = Report)
#
# #     # @patch('scheduler.create_report')
# #     # @patch('scheduler.reporting')
# #     # @patch('scheduler.RunLogger')
# #     def test_run_through(self):
# #         """
# #         Test routine to check the scheduler run through.
# #         """
# #         with nested(
# #             patch('scheduler.create_report'),
# #             patch('scheduler.RunLogger')
# #         ) as (mock, run):
# #             instance = mock.return_value
# #             instance.data_available.return_value = True
#
# #             runlog = run.return_value
# #             runlog.override_data = False
# #             runlog.get_last_run.return_value = datetime(2016, 3, 1)
# #             runlog.get_next_run.return_value = datetime(2016, 4, 1)
# #             runlog.record_run.return_value = None