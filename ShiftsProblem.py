from ortools.sat.python import cp_model
import calendar
from datetime import date
import matplotlib.pyplot as plt
import numpy as np

class ShiftsProblem:
    def __init__(self, month, year, num_medics, medics_preferring_full_sundays, festive_days_no_sundays, vacation_days,\
                 num_morning_shifts_ferial, num_afternoon_shifts_ferial,
                 num_morning_shifts_saturday, num_afternoon_shifts_saturday):
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
        # self.num_shifts_ferial = 7  # 3 morning, 2 afternoon, 1 night, 1 resting
        # self.num_shifts_saturdays = 5  # 2 morning, 1 afternoon, 1 night, 1 resting
        # num_shifts_festive = 4  # 1 morning, 1 afternoon, 1 night, 1 resting
        num_days = max(max((self.calendar.monthdayscalendar(year, month))))
        self.num_morning_shifts_ferial = num_morning_shifts_ferial #need to store in class for plotting
        self.num_afternoon_shifts_ferial = num_afternoon_shifts_ferial #need to store in class for plotting
        self.all_medics = range(num_medics)
        self.all_days = range(num_days)
        self.shifts = {}
        ''' 
        Assign an integer ID to each shift and collect them in a dictionary all_shifts
        the dictionary maps from a day to a list containing the numeric IDs of the shifts included in that day
        The third-to-last shift is by convention the night shift.        
        The second-to-last shift is by convention the after-night resting "shift".       
        The third-to-last shift is by convention the second after-night resting "shift".    
        '''
        self.all_shifts = {}
        for d in self.all_days:
            if d not in self.saturdays and d not in self.festive_days:
                self.all_shifts.update({d: list(range(num_morning_shifts_ferial + num_afternoon_shifts_ferial + 3))})
            if d in self.saturdays:
                IDs_of_shift = list(range(num_morning_shifts_saturday))
                IDs_of_shift.extend(range(num_morning_shifts_ferial,
                                          num_morning_shifts_ferial + num_afternoon_shifts_saturday))
                IDs_of_shift.extend(range(num_morning_shifts_ferial + num_afternoon_shifts_ferial,
                                          num_morning_shifts_ferial + num_afternoon_shifts_ferial + 3))
                self.all_shifts.update({d: IDs_of_shift})
            if d in self.festive_days: # No choice allowed: only one medic on sundays
                IDs_of_shift = [0]
                IDs_of_shift.extend(range(num_morning_shifts_ferial,
                                          num_morning_shifts_ferial + 1))
                IDs_of_shift.extend(range(num_morning_shifts_ferial + num_afternoon_shifts_ferial,
                                          num_morning_shifts_ferial + num_afternoon_shifts_ferial + 3))
                self.all_shifts.update({d: IDs_of_shift})
        self.model = cp_model.CpModel()
        for n in self.all_medics:
            for d in self.all_days:
                for s in self.all_shifts[d]:
                    self.shifts[(n, d, s)] = self.model.NewBoolVar('shift_n%id%is%i' % (n, d, s))

        ######### Generate constraints###########
        # Each shift is assigned to exactly one medic in the schedule period (excluding rest "shifts").
        for d in self.all_days:
            for s in self.all_shifts[d][:-2]:
                self.model.AddExactlyOne(self.shifts[(n, d, s)] for n in self.all_medics)
        # Each medic works at most one shift per day, except for sundays (if the medic prefers 12h shifts on sundays).
        for n in self.all_medics:
            for d in self.all_days:
                if n in medics_preferring_full_sundays:
                    if d in self.festive_days:
                        self.model.Add(self.shifts[(n, d, self.all_shifts[d][0])] ==
                                       self.shifts[(n, d, self.all_shifts[d][1])]) # morning shift is equal to afternoon shift
                    else:
                        self.model.AddAtMostOne(self.shifts[(n, d, s)] for s in self.all_shifts[d])
                else:
                    self.model.AddAtMostOne(self.shifts[(n, d, s)] for s in self.all_shifts[d])

        # Two rest days after night shift
        for n in self.all_medics:
            for d in self.all_days:
                if d > 1:
                    night_shift = self.shifts[(n, d - 2, self.all_shifts[d-2][-3])]
                    afternight_shift = self.shifts[(n, d-1, self.all_shifts[d-1][-2])]
                    second_afternight_shift = self.shifts[(n, d, self.all_shifts[d][-1])]
                    self.model.Add(night_shift == afternight_shift)
                    self.model.Add(night_shift == second_afternight_shift)

        # Include vacation days
        for n in self.all_medics:
            for day in vacation_days[n]:
                d = day - 1 # convert to 0-indexing
                for s in self.all_shifts[d][:-2]:
                    self.model.Add(self.shifts[(n, d, s)]==0)

        '''
        Try to distribute the shifts evenly:
        Compute desired_shifts_per_nurse  as the number of shift each medic should work (in average)
        Define two auxiliary variables (aux_low, aux_up) per medic such that
        aux_low <= n_shifts_worked_by_medic - desired_shifts_per_nurse <=  aux_up
        Repeat for the number of nights worked and number of festive days worked.
        Then, minimize the sum of auxiliary variables.
        '''
        num_shifts_festive = 3 # 3 = 1 morning + 1 afternoon + 1 night
        total_number_of_shifts = (num_shifts_festive * len(self.festive_days) +
                    (num_morning_shifts_saturday + num_afternoon_shifts_saturday) * len(self.saturdays) +
                    (num_morning_shifts_ferial + num_afternoon_shifts_ferial) * (num_days - len(self.saturdays) - len(self.festive_days)))
        desired_shifts_per_nurse = (total_number_of_shifts // num_medics)
        total_festive_shifts = num_shifts_festive * len(self.festive_days)
        desired_festive_shifts_per_nurse = (total_festive_shifts // num_medics)
        total_night_shifts = num_days
        desired_night_shifts_per_nurse = total_night_shifts//num_medics
        self.aux_vars_up = {}

        self.aux_vars_low = {}
        for n in self.all_medics:
            shifts_worked = []
            night_shifts_worked = []
            festive_shifts_worked = []
            for d in self.all_days:
                for s in self.all_shifts[d][:-2]:
                    shifts_worked.append(self.shifts[(n, d, s)])
                    if d in self.festive_days:
                        festive_shifts_worked.append(self.shifts[(n, d, s)])
                    if s == self.all_shifts[d][-3]:
                        night_shifts_worked.append(self.shifts[(n, d, s)])
            self.aux_vars_up[(0, n)] = self.model.NewIntVar(0,5, 'aux_variable_up%it%im' % (0, n))
            self.aux_vars_low[(0, n)] = self.model.NewIntVar(0,5, 'aux_variable_low%it%im' % (0, n))
            avg_shifts_per_day = desired_shifts_per_nurse / num_days
            reduction_shifts_due_to_vacations = int(avg_shifts_per_day * len(vacation_days[n]))
            # print("Medic %d should work %d shifts" %(n, desired_shifts_per_nurse - reduction_shifts_due_to_vacations))
            self.model.Add( (desired_shifts_per_nurse - reduction_shifts_due_to_vacations) - sum(shifts_worked)<= self.aux_vars_up[(0,n)])
            self.model.Add( (desired_shifts_per_nurse - reduction_shifts_due_to_vacations) - sum(shifts_worked)>= -1*self.aux_vars_low[(0,n)])
            # self.model.Add(self.aux_vars_up[(0, n)] >= 0)
            # self.model.Add(self.aux_vars_low[(0, n)] >= 0)
            self.aux_vars_up[(1, n)] = self.model.NewIntVar(0,5, 'aux_variable_up%it%im' % (1, n))
            self.aux_vars_low[(1, n)] = self.model.NewIntVar(0,5, 'aux_variable_low%it%im' % (1, n))
            self.model.Add(desired_festive_shifts_per_nurse - sum(festive_shifts_worked) <= self.aux_vars_up[(1, n)])
            self.model.Add(desired_festive_shifts_per_nurse - sum(festive_shifts_worked) >= -1 * self.aux_vars_low[(1, n)])
            # self.model.Add(self.aux_vars_up[(1, n)] >= 0)
            # self.model.Add(self.aux_vars_low[(1, n)] >= 0)
            self.aux_vars_up[(2, n)] = self.model.NewIntVar(0,5, 'aux_variable_up%it%im' % (2, n))
            self.aux_vars_low[(2, n)] = self.model.NewIntVar(0,5, 'aux_variable_low%it%im' % (2, n))
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
        num_shifts_ferial = self.num_morning_shifts_ferial + self.num_afternoon_shifts_ferial + 1
        fig, ax = plt.subplots(n_weeks + 1, 1, figsize=(8, 0.3*num_shifts_ferial * (n_weeks + 1)))  # last one is for statistics
        fig.suptitle("Turni " + str(self.month) + '-' + str(self.year))
        for week in range(n_weeks):
            ax[week].set_axis_off()
            names_of_days = ('Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom')
            columns = []
            rows = ['Mattina' + str(i) for i in range(self.num_morning_shifts_ferial)]
            rows.extend(['Pomeriggio' + str(i) for i in range(self.num_afternoon_shifts_ferial)])
            rows.append('Notte')
            values = np.zeros((num_shifts_ferial, 7)) # 7 = days of the week
            days_in_week = self.calendar.monthdayscalendar(self.year, self.month)[week]
            index_day = 0
            for day in days_in_week:
                if day == 0:
                    columns.append('-')
                    # values[0, index_day] = 0
                else:
                    columns.append(names_of_days[date(self.year, self.month, day).weekday()])
                    d = day - 1  # convert to 0-index
                    for s in self.all_shifts[d][:-2]:
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
                for s in self.all_shifts[d][:-2]:
                    if self.solver.Value(self.shifts[(n, d, s)]) > 0:
                        count_shifts = count_shifts + 1
                        if s == self.all_shifts[d][-3]:
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
        plt.show()
        print("pause...")
        return fig
