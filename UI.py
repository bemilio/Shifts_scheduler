import pandas as pd
import streamlit as st
import calendar
from datetime import date, datetime
from ShiftsProblem import ShiftsProblem
from ortools.sat.python import cp_model
import matplotlib.pyplot as plt
import os


def run_UI():
    st.title("Generatore di turni")
    st.write("Questo programma cerca di assegnare ad ogni medico il numero piu' equilibrato possibile " +
            "di turni, cercando anche di assegnare lo stesso numero di turni festivi e di turni notturni, "
            "rispettando le ferie ed il giorno di riposo dopo il turno notturno. " +
            "Ogni medico puo' fare solo un turno al giorno, eccetto se il medico ha fatto richiesta di preferire il doppio turno " +
            "nei giorni festivi. Per questa eccezione, usare l'apposita opzione.")
    st.subheader("Dettagli medici")  # Horizontal line
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
    medics_preferring_full_sundays = st.multiselect('Quali medici preferiscono fare turni festivi doppi (12h)?', range(1, num_medics+1))
    st.subheader("Data")
    list_months = list(calendar.month_name)[1:]
    month = st.selectbox(
        'Mese', list_months, index=datetime.now().month-1)
    month = list_months.index(month)+1
    year = st.number_input('Anno', datetime.now().year, 2040, datetime.now().year)
    A = calendar.TextCalendar(calendar.SUNDAY)
    days_without_sundays = []
    all_days = []
    for day in A.itermonthdays(year,month):
        if day != 0:
            all_days.append(day)
            if date(year, month, day).weekday() != 6:
                days_without_sundays.append(day)
    festive_days_no_sundays = st.multiselect('Quali giorni sono festivi? (escluse domeniche)',
     days_without_sundays)
    for i in range(len(festive_days_no_sundays)):
        festive_days_no_sundays[i] = festive_days_no_sundays[i]-1 # convert to 0-index

    for i in range(len(medics_preferring_full_sundays)):
        medics_preferring_full_sundays[i] = medics_preferring_full_sundays[i] - 1 # convert to 0-index
    vacation_days = [[] for _ in range(num_medics)]
    st.subheader("Ferie")
    for medic in range(num_medics):
        vacation_days[medic] = st.multiselect('Giorni ferie medico %d' %(medic+1), all_days)
    st.subheader("Esubero turni")
    st.write("Usare i punti seguenti per richiedere turni in più (o in meno) ad uno specifico medico. ")
    st.write("Nota: il programma cerca comunque di mantenere un numero di turni festivi e notturni uguali per tutti. " +
             "Se ad un medico sono richiesti turni festivi/notturni addizionali, utilizzare anche le sezioni successive.")
    additional_shifts_ferial = [0 for _ in range(num_medics)]
    for medic in range(num_medics):
        additional_shifts_ferial[medic] = st.number_input('Numero turni supplementari richiesti al medico %d' %(medic+1), -10, 10, 0, format="%d")
    st.subheader("Esubero turni festivi")
    additional_shifts_festive = [0 for _ in range(num_medics)]
    for medic in range(num_medics):
        additional_shifts_festive[medic] = st.number_input('Numero turni festivi supplementari richiesti al medico %d' %(medic+1),-10, 10, 0, format="%d")
    st.subheader("Esubero turni notturni")
    additional_shifts_nights = [0 for _ in range(num_medics)]
    for medic in range(num_medics):
        additional_shifts_nights[medic] = st.number_input('Numero turni notturni supplementari richiesti al medico %d' %(medic+1),-10, 10, 0, format="%d")

    st.markdown("---")  # Horizontal line
    if st.button('Genera'):
        problem = ShiftsProblem(month, year, num_medics,
                                medics_preferring_full_sundays, festive_days_no_sundays, vacation_days,
                                num_morning_shifts_ferial, num_afternoon_shifts_ferial,
                                num_morning_shifts_saturday, num_afternoon_shifts_saturday,
                                additional_shifts_ferial, additional_shifts_festive, additional_shifts_nights
                                )
        status = problem.Solve()
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            st.write("Soluzione trovata")
            st.subheader("Tabella turni")
            fig = problem.PrintTable()
            st.pyplot(fig=fig )
            # Save figure on the host server
            pdf_filename = "Turni_" + list(calendar.month_name)[month] + "_" + str(year) + ".pdf"
            plt.savefig(pdf_filename, format='pdf')
            # Create download button
            st.write("Soddisfattə? Usa questo pulsante per scaricare la tabella. Altrimenti, modifica pure i parametri inseriti e genera una nuova tabella.")
            with open(pdf_filename, "rb") as f:
                st.download_button(
                    label="Scarica PDF",
                    data=f,
                    file_name=pdf_filename,
                    mime="application/pdf"
                )
            # Delete PDF from host
            os.remove(pdf_filename)

        else:
            st.write('Nessuna soluzione trovata')

