import time

PENALITY = (1, 0.75, 0.5, 0.25)
MIN_SESSION = 0.32  # 19 min e 20 secondi
SECONDS_TO_HOURS = 0.00027777833333
SECONDS_TO_MIN   = 0.0166667

class Player:
    def __init__(self, member_id,
                 ishecaptain, name_faction, daily_points=0, points=0, daily_time=0, total_time=0, warnings=0):
        self.member_id = member_id
        self.captainflag = ishecaptain
        self.name_faction = name_faction
        self.daily_points = 0
        self.points = points
        self.total_time = total_time
        self.start_time = 0
        self.end_time = 0
        self.study_time = 0
        self.study_time_s = 0
        self.study_time_m = 0
        self.daily_time = daily_time  # hours
        self.daily_time_m = round(daily_time * 60, 2)  # minutes
        self.warnings = warnings
        self.current_date = time.time()

    def report(self):
        if self.warnings < 3:
            self.warnings += 1

    def update_session(self):
        hours = round(self.study_time, 2)
        self.daily_points = min(round(self.daily_points + hours * PENALITY[self.warnings], 1),
                                round(8 * PENALITY[self.warnings], 1))

    def updatePoints(self):
        self.points = self.points + self.daily_points
        self.resetDailyStat()

    def start_session(self, start):
        self.start_time = start
        self.end_time = start

    def end_session(self, end):
        if self.start_time != 0:
            self.end_time = end

    def updateStudyTime(self):
        self.study_time_s = self.end_time - self.start_time
        hours = round(self.study_time_s*SECONDS_TO_HOURS, 2)
        if hours >= MIN_SESSION:
            self.study_time = round(self.study_time_s * SECONDS_TO_HOURS, 2)
            self.study_time_m = round(self.study_time_s * SECONDS_TO_MIN, 2)
        else:
            self.study_time = 0
            self.study_time_m = 0
            self.study_time_s = 0
        self.start_session(0)
        self.end_session(0)

    def updateDailyTime(self):
        self.daily_time   = round(self.daily_time + self.study_time, 2)
        self.daily_time_m = round(self.daily_time_m + self.study_time_m, 2)
        self.total_time   = round(self.total_time + self.study_time, 2)

    def resetDailyStat(self):
        self.daily_points = 0
        self.daily_time   = 0
        self.daily_time_m = 0