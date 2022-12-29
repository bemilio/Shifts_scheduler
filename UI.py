import pandas as pd
import streamlit as st
import calendar
from datetime import date
from ShiftsProblem import ShiftsProblem
from ortools.sat.python import cp_model


def run_UI():
    num_medics = st.slider('Numero medici', 4,12,8)
    month = st.slider(
        'Mese', 1,12,1)
        # ('Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 'Luglio', 'Agosto','Settembre', 'Ottobre', 'Novembre', 'Dicembre'))
    year = st.slider('Anno', 2022, 2032, 2023)
    A = calendar.TextCalendar(calendar.SUNDAY)
    days_without_sundays = []
    all_days = []
    for day in A.itermonthdays(year,month):
        if day != 0:
            all_days.append(day)
            if date(year, month, day).weekday() != 6:
                days_without_sundays.append(day)
    festive_days_no_sundays = st.multiselect(
     'Seleziona giorni festivi (escluse domeniche)',
     days_without_sundays)

    medics_preferring_full_sundays = st.multiselect('Seleziona medici che preferiscono festivi 12h', range(num_medics))
    vacation_days = [[] for _ in range(num_medics)]
    for medic in range(num_medics):
        vacation_days[medic] = st.multiselect('Giorni ferie medico %d' %(medic+1), all_days)

    if st.button('Genera'):
        problem = ShiftsProblem(month=month, year=year, num_medics=num_medics,
                                medics_preferring_full_sundays=medics_preferring_full_sundays,
                                festive_days_no_sundays=festive_days_no_sundays,
                                vacation_days=vacation_days)
        status = problem.Solve()
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            st.write("Soluzione trovata")
            fig = problem.PrintTable()
            st.pyplot(fig=fig )
        else:
            st.write('Nessuna soluzione trovata')

