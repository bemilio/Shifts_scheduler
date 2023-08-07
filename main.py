import matplotlib.pyplot as plt
import numpy as np
from UI import run_UI
from ShiftsProblem import ShiftsProblem
from ortools.sat.python import cp_model

#
# class NursesPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
#     """Print intermediate solutions."""
#     def __init__(self, shifts, num_nurses, num_days, all_shifts, limit):
#         cp_model.CpSolverSolutionCallback.__init__(self)
#         self._shifts = shifts
#         self._num_nurses = num_nurses
#         self._num_days = num_days
#         self._all_shifts = all_shifts
#         self._solution_count = 0
#         self._solution_limit = limit
#
#     def on_solution_callback(self):
#         self._solution_count += 1
#         print('Solution %i, conflicts: %i' % (self._solution_count, self.NumConflicts()))
#         for d in range(self._num_days):
#             print('Day %i' % d)
#             for n in range(self._num_nurses):
#                 is_working = False
#                 for s in self._all_shifts[d]:
#                     if self.Value(self._shifts[(n, d, s)]):
#                         is_working = True
#                         print('  Nurse %i works shift %i' % (n+1, s))
#                 if not is_working:
#                     print('  Nurse {} does not work'.format(n+1))
#         if self._solution_count >= self._solution_limit:
#             print('Stop search after %i solutions' % self._solution_limit)
#             self.StopSearch()
#
#     def solution_count(self):
#         return self._solution_count



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    run_UI()
    # problem = ShiftsProblem(month=12, year=2022, num_medics=8,
    #                         medics_preferring_full_sundays=[], festive_days_no_sundays=[], vacation_days=[[] for _ in range(8)],
    #                         num_morning_shifts_ferial=3, num_afternoon_shifts_ferial=2,
    #                         num_morning_shifts_saturday=2, num_afternoon_shifts_saturday=1)
    # status = problem.Solve()
    # if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    #     print("Problem solved")
    # else:
    #     print('No solution found.')
    # print('\nStatistics')
    # print('  - conflicts      : %i' % problem.solver.NumConflicts())
    # print('  - branches       : %i' % problem.solver.NumBranches())
    # print('  - wall time      : %f s' % problem.solver.WallTime())
    #
    # problem.PrintTable()


    # print("pause...")

