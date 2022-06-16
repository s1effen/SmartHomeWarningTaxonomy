import tkinter as tk
import time
import logging
import threading
import datetime as dt
from tkinter import *
from alert_dialog import Alert_Dialog
from feedback_dialog import Feedback_Dialog
from util import load_simulation
from scheduler import Scheduler

# To make it run on pi via ssh: export DISPLAY=":0"

class Main_Dialog:

    state = "Studie läuft"

    def __init__(self):
        print(dt.datetime.now())
        self.block_execution = False

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

        self.alert_dialog = Alert_Dialog()
        self.feedback_dialog = Feedback_Dialog()
        self.create_dialog()

        # Load Simulation
        self.simulation = load_simulation()

        self.window.mainloop()

    def dispatch_alarm(self, event, execution_date):
        # Check if other alarm is running
        if (self.alert_dialog.alert_runs):
            print("Main    : Event with ID {} was missed because another alarm was still running".format(event["id"]))
            return
        # Check if feedback dialog is still open
        if (self.feedback_dialog.runs):
            print("Main    : Event with ID {} was missed because feedback collection from previous alarm was still running".format(event["id"]))
            return
        # Check if execution time is in the past
        if ((execution_date + dt.timedelta(seconds=2)) < dt.datetime.now()):
            print("Main    : Event with ID {} was missed because the execution time is in the past".format(event["id"]))
            return
        # Check if study is paused
        if (self.block_execution):
            print("Main    : Event with ID {} was missed because the study was paused".format(event["id"]))
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
        # Change GUI
        self.text_frame.pack()
        self.label1.pack(pady=20, side=LEFT)
        self.label2.pack(pady=20, side=LEFT)
        start_button.pack_forget()
        self.checkout_button.pack(pady=20)

        # Init and start thread
        simulation_thread = threading.Thread(target=self.run_simulation)
        simulation_thread.start()

    def change_study_status(self):
        if (not self.block_execution):
            self.block_execution = True
            self.label2["text"] = "Studie unterbrochen"
            self.checkout_button["text"] = "Check In"
            self.label2.config(fg="red")
        else:
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
        start_button.pack(pady=20)


root = tk.Tk()
root.withdraw()
dialog = Main_Dialog()
