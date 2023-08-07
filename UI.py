import pandas as pd
import streamlit as st
import calendar
from datetime import date
from ShiftsProblem import ShiftsProblem
from ortools.sat.python import cp_model


def run_UI():
    num_medics = st.number_input('Numero di medici disponibili', 6,20,10, format="%d")
    '''
    The maximum number of medics that can work every morning/afternoon is given by the number of total medics N minus 3, 
    because every day 1 medic does night shift and 2 rest from previous night shifts. We then divide N-3 by 2 (morning and
    afternoon) and assign the remainder of the division to the morning (which should have more medics than the 
    afternoon)
    '''
    max_shifts_morning = ((num_medics-3)//2) + (num_medics-3)%2
    max_shifts_afternoon = ((num_medics-3)//2)
    num_morning_shifts_ferial = st.number_input('Numero medici richiesti la mattina (feriali)', 1, max_shifts_morning, 1, format="%d")
    num_morning_shifts_saturday = st.number_input('Numero medici richiesti la mattina (sabato)', 1, num_morning_shifts_ferial, 1, format="%d")
    num_afternoon_shifts_ferial = st.number_input('Numero medici richiesti il pomeriggio (feriali)', 1, max_shifts_afternoon, 1, format="%d")
    num_afternoon_shifts_saturday = st.number_input('Numero medici richiesti il pomeriggio (sabato)', 1, num_afternoon_shifts_ferial, 1, format="%d")
    list_months = ('Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 'Luglio', 'Agosto','Settembre', 'Ottobre', 'Novembre', 'Dicembre')
    month = st.selectbox(
        'Mese', list_months)
    month = list_months.index(month)+1
    year = st.number_input('Anno', 2023, 2040, 2023)
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
    for i in range(len(festive_days_no_sundays)):
        festive_days_no_sundays[i] = festive_days_no_sundays[i]-1 # convert to 0-index

    medics_preferring_full_sundays = st.multiselect('Seleziona medici che preferiscono festivi 12h', range(1, num_medics+1))
    for i in range(len(medics_preferring_full_sundays)):
        medics_preferring_full_sundays[i] = medics_preferring_full_sundays[i] - 1 # convert to 0-index
    vacation_days = [[] for _ in range(num_medics)]
    for medic in range(num_medics):
        vacation_days[medic] = st.multiselect('Giorni ferie medico %d' %(medic+1), all_days)

    if st.button('Genera'):
        problem = ShiftsProblem(month, year, num_medics,
                                medics_preferring_full_sundays, festive_days_no_sundays, vacation_days,
                                num_morning_shifts_ferial, num_afternoon_shifts_ferial,
                                num_morning_shifts_saturday, num_afternoon_shifts_saturday
                                )
        status = problem.Solve()
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            st.write("Soluzione trovata")
            fig = problem.PrintTable()
            st.pyplot(fig=fig )
        else:
            st.write('Nessuna soluzione trovata')

