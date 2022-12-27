from ortools.sat.python import cp_model
import calendar
from datetime import date
import matplotlib.pyplot as plt
import numpy as np

class ShiftsProblem:
    def __init__(self, month, year, num_medics, medics_preferring_full_sundays, festive_days_no_sundays, vacation_days):
        self.month = month
        self.year = year
        self.num_medics = num_medics
        self.medics_preferring_full_sundays = medics_preferring_full_sundays
        self.calendar = calendar.TextCalendar(calendar.SUNDAY)
        self.festive_days = festive_days_no_sundays
        self.saturdays = []
        for day in self.calendar.itermonthdays(year, month):
            if day != 0:
                if date(year, month, day).weekday() == 6:
                    self.festive_days.append(day - 1)  # conversion to 0-index
                if date(year, month, day).weekday() == 5:
                    self.saturdays.append(day - 1)  # conversion to 0-index
        self.num_shifts_ferial = 6  # 3 morning, 2 afternoon, 1 night
        self.num_shifts_saturdays = 4  # 2 morning, 1 afternoon, 1 night
        num_shifts_festive = 3  # 1 morning, 1 afternoon, 1 night
        num_days = max(max((self.calendar.monthdayscalendar(year, month))))
        self.all_medics = range(num_medics)
        self.all_days = range(num_days)
        self.shifts = {}
        self.all_shifts = {}
        for d in self.all_days:
            if d not in self.saturdays and d not in self.festive_days:
                self.all_shifts.update({d: range(self.num_shifts_ferial)})
            if d in self.saturdays:
                # all_shifts.update({d: range(num_shifts_saturdays)})
                self.all_shifts.update({d: [0, 1, 3, 5]})
            if d in self.festive_days:
                self.all_shifts.update({d: [0, 3, 5]})
        self.model = cp_model.CpModel()
        for n in self.all_medics:
            for d in self.all_days:
                for s in self.all_shifts[d]:
                    self.shifts[(n, d, s)] = self.model.NewBoolVar('shift_n%id%is%i' % (n, d, s))

        ######### Generate constraints###########
        # Each shift is assigned to exactly one medic in the schedule period.
        for d in self.all_days:
            for s in self.all_shifts[d]:
                self.model.AddExactlyOne(self.shifts[(n, d, s)] for n in self.all_medics)
        # Each medic works at most one shift per day, except for sundays.
        for n in self.all_medics:
            for d in self.all_days:
                if d not in self.festive_days:
                    self.model.AddAtMostOne(self.shifts[(n, d, s)] for s in self.all_shifts[d])
                else:
                    # Handle medics preferring 12h shift sundays
                    if n not in medics_preferring_full_sundays:
                        self.model.AddAtMostOne(self.shifts[(n, d, s)] for s in self.all_shifts[d])
                    else:
                        self.model.Add(
                            self.shifts[(n, d, 0)] == self.shifts[(n, d, 3)])  # morning shift is equal to afternoon shift
        # Rest day after night shift
        for n in self.all_medics:
            for d in self.all_days:
                if d > 0:
                    night_shift = self.shifts[(n, d - 1, self.all_shifts[d - 1][-1])]
                    shifts_including_last_night = [self.shifts[(n, d, s)] for s in self.all_shifts[d]]
                    shifts_including_last_night.append(night_shift)
                    self.model.AddAtMostOne(shifts_including_last_night)

        # Try to distribute the shifts evenly, so that each medic works
        # min_shifts_per_nurse shifts.
        total_number_of_shifts = (num_shifts_festive * len(self.festive_days) + self.num_shifts_saturdays * len(self.saturdays) \
                                  + self.num_shifts_ferial * (num_days - len(self.saturdays) - len(self.festive_days)))
        min_shifts_per_nurse = (total_number_of_shifts // num_medics) - 1
        max_shifts_per_nurse = (total_number_of_shifts // num_medics) + 1
        desired_shifts_per_nurse = (total_number_of_shifts // num_medics)
        total_festive_shifts = num_shifts_festive * len(self.festive_days)
        min_festive_shifts_per_nurse = (total_festive_shifts // num_medics) - 1
        max_festive_shifts_per_nurse = (total_festive_shifts // num_medics) + 1
        desired_festive_shifts_per_nurse = (total_festive_shifts // num_medics)
        total_night_shifts = num_days
        min_night_shifts_per_nurse = (total_night_shifts // num_medics) - 1
        max_night_shifts_per_nurse = (total_night_shifts // num_medics) + 1
        desired_night_shifts_per_nurse = total_night_shifts//num_medics
        # for n in all_medics:
        #     shifts_worked = []
        #     night_shifts_worked = []
        #     festive_shifts_worked = []
        #     for d in all_days:
        #         for s in all_shifts[d]:
        #             shifts_worked.append(shifts[(n, d, s)])
        #             if d in self.festive_days:
        #                 festive_shifts_worked.append(shifts[(n, d, s)])
        #             if s == all_shifts[d][-1]:
        #                 night_shifts_worked.append(shifts[(n, d, s)])
        #     self.model.Add(min_shifts_per_nurse <= sum(shifts_worked))
        #     self.model.Add(sum(shifts_worked) <= max_shifts_per_nurse)
        #     self.model.Add(sum(festive_shifts_worked) <= max_festive_shifts_per_nurse)
        #     self.model.Add(min_festive_shifts_per_nurse <= sum(festive_shifts_worked))
        #     self.model.Add(sum(night_shifts_worked) <= max_night_shifts_per_nurse)
        #     self.model.Add(min_night_shifts_per_nurse <= sum(night_shifts_worked))

        # Set the desired number of shifts as soft constraints
        self.aux_vars_up = {}

        self.aux_vars_low = {}
        for n in self.all_medics:
            shifts_worked = []
            night_shifts_worked = []
            festive_shifts_worked = []
            for d in self.all_days:
                for s in self.all_shifts[d]:
                    shifts_worked.append(self.shifts[(n, d, s)])
                    if d in self.festive_days:
                        festive_shifts_worked.append(self.shifts[(n, d, s)])
                    if s == self.all_shifts[d][-1]:
                        night_shifts_worked.append(self.shifts[(n, d, s)])
            self.aux_vars_up[(0, n)] = self.model.NewIntVar(0,10, 'aux_variable_up%it%im' % (0, n))
            self.aux_vars_low[(0, n)] = self.model.NewIntVar(0,10, 'aux_variable_low%it%im' % (0, n))
            self.model.Add(desired_shifts_per_nurse - sum(shifts_worked)<= self.aux_vars_up[(0,n)])
            self.model.Add(desired_shifts_per_nurse - sum(shifts_worked)>= -1*self.aux_vars_low[(0,n)])
            # self.model.Add(self.aux_vars_up[(0, n)] >= 0)
            # self.model.Add(self.aux_vars_low[(0, n)] >= 0)
            self.aux_vars_up[(1, n)] = self.model.NewIntVar(0,10, 'aux_variable_up%it%im' % (1, n))
            self.aux_vars_low[(1, n)] = self.model.NewIntVar(0,10, 'aux_variable_low%it%im' % (1, n))
            self.model.Add(desired_festive_shifts_per_nurse - sum(festive_shifts_worked) <= self.aux_vars_up[(1, n)])
            self.model.Add(desired_festive_shifts_per_nurse - sum(festive_shifts_worked) >= -1 * self.aux_vars_low[(1, n)])
            # self.model.Add(self.aux_vars_up[(1, n)] >= 0)
            # self.model.Add(self.aux_vars_low[(1, n)] >= 0)
            self.aux_vars_up[(2, n)] = self.model.NewIntVar(0,10, 'aux_variable_up%it%im' % (2, n))
            self.aux_vars_low[(2, n)] = self.model.NewIntVar(0,10, 'aux_variable_low%it%im' % (2, n))
            self.model.Add(desired_night_shifts_per_nurse - sum(night_shifts_worked) <= self.aux_vars_up[(2, n)])
            self.model.Add(desired_night_shifts_per_nurse - sum(night_shifts_worked) >= -1 * self.aux_vars_low[(2, n)])
            # self.model.Add(self.aux_vars_up[(2, n)] >= 0)
            # self.model.Add(self.aux_vars_low[(2, n)] >= 0)
            self.solver = cp_model.CpSolver()
            self.solver.parameters.linearization_level = 0
        sum_aux_vars = 0
        for n in self.all_medics:
            sum_aux_vars = sum_aux_vars + self.aux_vars_up[(0, n)] + self.aux_vars_up[(1, n)]  + self.aux_vars_up[(2, n)] \
                           + self.aux_vars_low[(0, n)] + self.aux_vars_low[(1, n)] + self.aux_vars_low[(2, n)]
        self.model.Minimize(sum_aux_vars)

    def Solve(self):
        status = self.solver.Solve(self.model)

        return status

    def PrintTable(self):
        # Create and print table
        n_weeks = len(self.calendar.monthdayscalendar(self.year, self.month))
        fig, ax = plt.subplots(n_weeks + 1, 1, figsize=(8, 1.6 * (n_weeks + 1)))  # last one is for statistics
        fig.suptitle("Turni " + str(self.month) + '-' + str(self.year))
        for week in range(n_weeks):
            ax[week].set_axis_off()
            names_of_days = ('Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom')
            columns = []
            rows = ['Mattina 1', 'Mattina 2', 'Mattina 3', 'Pomeriggio 1', 'Pomeriggio 2', 'Notte']
            values = np.zeros((self.num_shifts_ferial, 7))
            days_in_week = self.calendar.monthdayscalendar(self.year, self.month)[week]
            index_day = 0
            for day in days_in_week:
                if day == 0:
                    columns.append('-')
                    # values[0, index_day] = 0
                else:
                    columns.append(names_of_days[date(self.year, self.month, day).weekday()])
                    d = day - 1  # convert to 0-index
                    for s in self.all_shifts[d]:
                        medic_working = None
                        for n in self.all_medics:
                            if self.solver.Value(self.shifts[(n, d, s)]) > 0:
                                medic_working = n
                        values[s, index_day] = medic_working + 1
                index_day = index_day + 1
            cell_text = []
            for row in range(len(rows)):
                cell_text.append(
                    [str(int(values[row, col])) if values[row, col] > 0. else "-" for col in range(len(columns))])
            ax[week].set_axis_off()
            table = ax[week].table(cellText=cell_text, rowLabels=rows, colLabels=columns, cellLoc='center',
                                   loc='upper left')
        # Print statistics medics
        columns = ['Dom. 12h', '# turni', '# notti', '# turni fest.']
        rows = ["Medico " + str(m + 1) for m in self.all_medics]
        values = np.zeros((self.num_medics, 4))
        for n in self.all_medics:
            count_shifts = 0
            count_night_shifts = 0
            count_festive_shifts = 0
            for d in self.all_days:
                for s in self.all_shifts[d]:
                    if self.solver.Value(self.shifts[(n, d, s)]) > 0:
                        count_shifts = count_shifts + 1
                        if s == self.all_shifts[d][-1]:
                            count_night_shifts = count_night_shifts + 1
                        if d in self.festive_days:
                            count_festive_shifts = count_festive_shifts + 1
            values[n, 0] = int(n in self.medics_preferring_full_sundays)
            values[n, 1] = count_shifts
            values[n, 2] = count_night_shifts
            values[n, 3] = count_festive_shifts
        cell_text = []
        for row in range(len(rows)):
            cell_text.append([str(int(values[row, col])) for col in range(len(columns))])
        ax[-1].set_axis_off()
        ax[-1].table(cellText=cell_text, rowLabels=rows, colLabels=columns, cellLoc='center', loc='upper left')
        return fig
        # plt.show()
        # print("pause...")