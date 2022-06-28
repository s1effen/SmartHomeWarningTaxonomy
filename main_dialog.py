import tkinter as tk
import time
import logging
import threading
import datetime as dt
from tkinter import *
from alert_dialog import Alert_Dialog
from feedback_dialog import Feedback_Dialog
from util import *
from scheduler import Scheduler
from os import listdir

# To make it run on pi via ssh: export DISPLAY=":0"

class Main_Dialog:

    state = "Studie läuft"

    def __init__(self):
        #print("Main    : Start program at {}".format(dt.datetime.now()))
        self.block_execution = False

        # Logger
        self.logger = setup_logger()
        self.logger.info("Main: Start program at {}".format(dt.datetime.now()))

        # GUI components
        self.window = tk.Toplevel()
        self.center_frame = tk.Frame(self.window, width=400, height=300)
        self.text_frame = tk.Frame(self.center_frame)
        self.label1 = Label(self.text_frame, text="Status: ", font=("Calibri", 20))
        self.label2 = Label(self.text_frame, text="Studie läuft", fg="green", font=("Calibri", 20))
        self.checkout_button = Button(self.center_frame, command=lambda: self.change_study_status(), text="Check-Out", height=2, background="#000000", foreground="white", font=("Calibri", 25))
        self.img = PhotoImage(file='/home/pi/masterthesis/executors/gui/peasec_logo.png')
        #self.img = PhotoImage(file='executors\gui\peasec_logo.png')
        self.img_label = Label(self.center_frame, image=self.img)
        self.error_label = Label(self.center_frame)

        # For demonstration
        event = {"id": 1, "categorie": "highest", "time": "14:03:10", "alerts": ['sms'], "message": "Die Sicherung der Kaffeemaschine ist durchgebrannt!"}
        self.trigger_button = Button(self.center_frame, command=lambda: self.dispatch_alarm(event, dt.datetime.now()), text="Trigger alarm", height=2, background="#000000", foreground="white", font=("Calibri", 25))

        self.alert_dialog = Alert_Dialog()
        self.feedback_dialog = Feedback_Dialog()
        self.create_dialog()

        # Connect to GSM hat
        connect_to_gsm_hat()

        # Load Simulation
        self.simulation = load_simulation()

        self.window.mainloop()

    def dispatch_alarm(self, event, execution_date):
        # Check if other alarm is running
        if (self.alert_dialog.alert_runs):
            logger.info("Main: Event with ID {} was missed because another alarm was still running".format(event["id"]))
            return
        # Check if feedback dialog is still open
        if (self.feedback_dialog.runs):
            logger.info("Main: Event with ID {} was missed because feedback collection from previous alarm was still running".format(event["id"]))
            return
        # Check if execution time is in the past
        if ((execution_date + dt.timedelta(seconds=2)) < dt.datetime.now()):
            logger.info("Main: Event with ID {} was missed because the execution time is in the past".format(event["id"]))
            return
        # Check if study is paused
        if (self.block_execution):
            logger.info("Main: Event with ID {} was missed because the study was paused".format(event["id"]))
            return
        # Check if alarm is during rest time
        if (is_time_between(self.simulation['user_data']['rest_time_start'], self.simulation['user_data']['rest_time_end'])):
            logger.info("Main: Event with ID {} was missed because the alarm was during the rest time".format(event["id"]))
        else:
            self.alert_dialog.dispatch_event(event, self.feedback_dialog)

    def setup_scheduler(self):
        schedule = Scheduler()
        date_array = self.simulation['config']['date'].split('-')
        events = self.simulation['events']

        for event in events:
            time_array = event['time'].split(':')
            execution_date = dt.datetime(year=int(date_array[0]), month=int(date_array[1]), day=int(date_array[2]),
                          hour=int(time_array[0]), minute=int(time_array[1]), second=int(time_array[2]))
            schedule.once(execution_date, self.dispatch_alarm, args=(event, execution_date))

        print(schedule)
        return schedule

    def run_simulation(self):
        schedule = Scheduler()
        schedule = self.setup_scheduler()
        while True:
            schedule.exec_jobs()
            time.sleep(1)

    def run_simulation_threat(self, start_button):

        # Check wether simulation with today as start date exist
        allow_start = False
        today_date = datetime.datetime.today().strftime('%Y%m%d')
        simulations = [f for f in listdir('resources/simulations')]
        for simulation in simulations:
            if today_date in str(simulation):
                allow_start = True
        if (not allow_start):
            self.error_label['text'] = 'No simulation found!'
            self.error_label.pack(pady=2)
            self.logger.error("Main: No simulation found!")
            return

        self.logger.info("Main: Simulation started at {}".format(dt.datetime.now()))

        # Change GUI
        self.text_frame.pack()
        self.label1.pack(pady=20, side=LEFT)
        self.label2.pack(pady=20, side=LEFT)
        start_button.pack_forget()
        self.checkout_button.pack(side=LEFT, padx=20)

        self.trigger_button.pack(side=LEFT, padx=20)

        # Setup files
        init_feedback_file()
        init_response_time_file()

        # Init and start thread
        simulation_thread = threading.Thread(target=self.run_simulation)
        simulation_thread.start()

    def change_study_status(self):
        if (not self.block_execution):
            self.logger.info("Main: Study paused at {}".format(dt.datetime.now()))
            self.block_execution = True
            self.label2["text"] = "Studie unterbrochen"
            self.checkout_button["text"] = "Check In"
            self.label2.config(fg="red")
        else:
            self.logger.info("Main: Study continued at {}".format(dt.datetime.now()))
            self.block_execution = False
            self.label2["text"] = "Studie läuft"
            self.label2.config(fg="green")
            self.checkout_button["text"] = "Check Out"
        self.window.update()

    def create_dialog(self):
        self.window.title('Smart Home Systems Study')

        # Make root window full screen
        w, h = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        self.window.attributes('-fullscreen', True)
        self.window.geometry("%dx%d+0+0" % (w, h))
        self.window.bind("<Escape>", lambda e: self.window.destroy())

        self.center_frame.pack(expand=TRUE, ipady=50)

        self.img_label.pack(pady=10)

        start_button = Button(self.center_frame, command=lambda: self.run_simulation_threat(start_button), text="Studie starten", height=2, background="#000000", foreground="white", font=("Calibri", 25))
        start_button.pack(pady=10)



root = tk.Tk()
root.withdraw()
dialog = Main_Dialog()
