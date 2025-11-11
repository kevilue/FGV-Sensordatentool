import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
import datetime
import threading
import queue
import os
from tools.processing import DataHandler

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("CSV Resampler for Water Temperatures")
        self.geometry("700x550")
        icon = tk.PhotoImage(file="gui/icon.png")
        self.iconphoto(True, icon)
        
        # Main window grid configuration
        self.grid_rowconfigure(0, weight=1)  # Top frame (options)
        self.grid_rowconfigure(1, weight=1)  # Middle frame (info text)
        self.grid_rowconfigure(2, weight=0)  # Bottom frame (button)
        self.grid_columnconfigure(0, weight=1)

        # Main frame that holds the application content
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew", rowspan=3)
        main_frame.grid_rowconfigure(0, weight=1) # Notebook will expand
        main_frame.grid_rowconfigure(1, weight=1) # Info text area will expand
        main_frame.grid_columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Resample tab
        self.resample_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.resample_tab, text="Resample")
        self.create_resample_tab()

        # Concatenate tab
        self.concatenate_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.concatenate_tab, text="Concatenate Files")
        self.create_concatenate_tab()

        # Info log
        info_frame = ttk.LabelFrame(main_frame, text="Info Log", padding="10")
        info_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        info_frame.grid_rowconfigure(0, weight=1)
        info_frame.grid_columnconfigure(0, weight=1)

        self.info_text = tk.Text(info_frame, height=10, state="disabled", wrap="word")
        self.info_text.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=self.info_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.info_text['yscrollcommand'] = scrollbar.set

        # Apply button
        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.grid(row=2, column=0, sticky="se")

        self.apply_button = ttk.Button(button_frame, text="Apply", command=self.on_apply_button_click)
        self.apply_button.pack()

        # Set up process queue
        self.process_queue = queue.Queue()
        self.data_processor = DataHandler(self.process_queue)
        self.log_message("Welcome! Please configure the options and press 'Apply'.")
        
    def create_resample_tab(self):
        """Add content of the 'Resample' tab"""
        options_frame = ttk.LabelFrame(self.resample_tab, text="Resampling Configuration", padding="10")
        options_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        options_frame.grid_columnconfigure(1, weight=1) # Make entry widgets expand
        
        self.resample_tab.grid_rowconfigure(0, weight=1)
        self.resample_tab.grid_columnconfigure(0, weight=1)

        # Folder Path
        ttk.Label(options_frame, text="File Path:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.file_path_var = tk.StringVar()
        folder_entry = ttk.Entry(options_frame, textvariable=self.file_path_var)
        folder_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(options_frame, text="Browse...", command=self.browse_file).grid(row=0, column=2, sticky="e", padx=5, pady=5)

        # Sample Rate
        ttk.Label(options_frame, text="Sample Rate:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.sample_rate_var = tk.StringVar()
        sample_rate_options = ["max", "15min", "30min", "1h", "2h", "5h", "12h", "24h", "2d", "3d", "7d", "14d", "1m"]
        sample_rate_dropdown = ttk.Combobox(options_frame, textvariable=self.sample_rate_var, values=sample_rate_options, state="readonly")
        sample_rate_dropdown.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        sample_rate_dropdown.set("1h") # Default value

        # Date Pickers
        self.min_date = datetime.date(2016, 1, 1)
        self.max_date = datetime.date.today()
        
        # Start Date/Time
        ttk.Label(options_frame, text="Start DateTime:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        start_frame = ttk.Frame(options_frame)
        start_frame.grid(row=2, column=1, columnspan=2, sticky="w")
        
        self.start_date_picker = DateEntry(start_frame, width=12, background='darkblue',
                                           foreground='white', borderwidth=2,
                                           mindate=self.min_date, maxdate=self.max_date,
                                           date_pattern='dd.MM.yyyy')
        self.start_date_picker.pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Label(start_frame, text="Time (HH:MM):").pack(side=tk.LEFT, padx=(10, 2))
        self.start_hour_var = tk.IntVar(value=0)
        ttk.Spinbox(start_frame, from_=0, to=23, wrap=True, textvariable=self.start_hour_var, width=3).pack(side=tk.LEFT)
        ttk.Label(start_frame, text=":").pack(side=tk.LEFT, padx=1)
        self.start_min_var = tk.IntVar(value=0)
        ttk.Spinbox(start_frame, from_=0, to=59, wrap=True, textvariable=self.start_min_var, width=3).pack(side=tk.LEFT)

        # End Date/Time
        ttk.Label(options_frame, text="End DateTime:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        end_frame = ttk.Frame(options_frame)
        end_frame.grid(row=3, column=1, columnspan=2, sticky="w")
        
        self.end_date_picker = DateEntry(end_frame, width=12, background='darkblue',
                                         foreground='white', borderwidth=2,
                                         mindate=self.min_date, maxdate=self.max_date,
                                         date_pattern='dd.MM.yyyy')
        self.end_date_picker.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Set default end time to now
        now = datetime.datetime.now()
        self.end_date_picker.set_date(now.date())
        
        ttk.Label(end_frame, text="Time (HH:MM):").pack(side=tk.LEFT, padx=(10, 2))
        self.end_hour_var = tk.IntVar(value=now.hour)
        ttk.Spinbox(end_frame, from_=0, to=23, wrap=True, textvariable=self.end_hour_var, width=3).pack(side=tk.LEFT)
        ttk.Label(end_frame, text=":").pack(side=tk.LEFT, padx=1)
        self.end_min_var = tk.IntVar(value=now.minute)
        ttk.Spinbox(end_frame, from_=0, to=59, wrap=True, textvariable=self.end_min_var, width=3).pack(side=tk.LEFT)

    def create_concatenate_tab(self):
        """Populates the 'Concatenate Files' tab."""
        self.concatenate_tab.grid_rowconfigure(0, weight=1)
        self.concatenate_tab.grid_columnconfigure(0, weight=1)

        # Frame for the listbox and scrollbar
        list_frame = ttk.LabelFrame(self.concatenate_tab, text="Files to Concatenate", padding="10")
        list_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=15)
        self.file_listbox.grid(row=0, column=0, sticky="nsew")

        list_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        list_scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox['yscrollcommand'] = list_scrollbar.set

        # Frame for the buttons
        button_frame = ttk.Frame(self.concatenate_tab)
        button_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        ttk.Button(button_frame, text="Add File(s)...", command=self.add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected_files).pack(side=tk.LEFT, padx=5)

    def add_files(self):
        """Opens dialog to add multiple files to the listbox."""
        files = filedialog.askopenfilenames(title="Select files", filetypes=[("CSV Files", "*.csv")])
        if files:
            excl_files = []
            for f in files:
                if os.path.isfile(f):
                    self.file_listbox.insert(tk.END, f)
                else:
                    excl_files.append(f)
            self.selected_files = [f for f in files if f not in excl_files]
            self.log_message(f"Added {len(self.selected_files)} file(s) to concatenate list.")

    def remove_selected_files(self):
        """Removes selected files from the listbox."""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            self.log_message("No files selected to remove.")
            return

        # Delete from the bottom up to avoid index shifting issues
        for i in reversed(selected_indices):
            del_file = self.file_listbox.get(i)
            self.file_listbox.delete(i)
            self.selected_files.remove(del_file)
        
        self.log_message(f"Removed {len(selected_indices)} file(s).")

    def log_message(self, message):
        """ Inserts a message into the info text box safely. """
        self.info_text.configure(state="normal")
        self.info_text.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.info_text.configure(state="disabled")
        self.info_text.see(tk.END) # Auto-scroll to bottom

    def browse_file(self):
        """ Opens a dialog to select a file. """
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
                self.file_path_var.set(path)
                self.log_message(f"File selected: {path}")

    def browse_save_as(self, initial_file=None):
        path = filedialog.asksaveasfilename(filetypes=[("CSV Files", "*.csv")], initialfile=initial_file)
        self.save_file_path = path

    def get_datetimes(self):
        """ Helper to get and validate datetime objects from pickers. """
        try:
            start_date = self.start_date_picker.get_date()
            start_time = datetime.time(self.start_hour_var.get(), self.start_min_var.get())
            start_datetime = datetime.datetime.combine(start_date, start_time)

            end_date = self.end_date_picker.get_date()
            end_time = datetime.time(self.end_hour_var.get(), self.end_min_var.get())
            end_datetime = datetime.datetime.combine(end_date, end_time)

            # Validation
            min_datetime = datetime.datetime(2016, 1, 1, 0, 0)
            max_datetime = datetime.datetime.now()

            if not (min_datetime <= start_datetime <= max_datetime):
                messagebox.showerror("Validation Error", f"Start datetime must be between {min_datetime.strftime('%Y-%m-%d %H:%M')} and now.")
                return None, None
            
            if not (min_datetime <= end_datetime <= max_datetime):
                messagebox.showerror("Validation Error", f"End datetime must be between {min_datetime.strftime('%Y-%m-%d %H:%M')} and now.")
                return None, None
            
            if start_datetime >= end_datetime:
                messagebox.showerror("Validation Error", "Start datetime must be before end datetime.")
                return None, None

            return start_datetime, end_datetime

        except Exception as e:
            messagebox.showerror("Date Error", f"Invalid date or time: {e}")
            return None, None
        
    def on_apply_button_click(self):
        """
        Checks which tab is active and calls the appropriate
        processing function.
        """
        selected_tab_index = self.notebook.index(self.notebook.select())
        
        if selected_tab_index == 0:
            # "Resample" tab is active
            self.start_processing_thread(selected_tab_index)
        elif selected_tab_index == 1:
            # "Concatenate Files" tab is active
            self.browse_save_as(initial_file="concatenated_files.csv")
            if self.save_file_path == "":
                return
            self.start_processing_thread(selected_tab_index)

    def start_processing_thread(self, task):
        """ Validates inputs and starts the background task in a new thread. """
        if task == 0:
            folder_path = self.file_path_var.get()
            if not folder_path or not os.path.isdir(folder_path):
                messagebox.showerror("Validation Error", "Please select a valid folder path.")
                return

            sample_rate = self.sample_rate_var.get()
            if not sample_rate:
                messagebox.showerror("Validation Error", "Please select a sample rate.")
                return

            start_dt, end_dt = self.get_datetimes()
            if start_dt is None or end_dt is None:
                return # Validation failed in get_datetimes

            # All inputs are valid, start the thread
            self.log_message("Starting processing...")
            self.apply_button.configure(state="disabled")

            # Start the queue checker
            self.check_queue()

            # Create and start the worker thread
            self.worker_thread = threading.Thread(
                target=self.subprocess_routine,
                args=(folder_path, sample_rate, start_dt, end_dt),
                daemon=True # Thread will exit when main app exits
            )
            self.worker_thread.start()
        elif task == 1:
            # File concatenation
            save_file = self.save_file_path
            self.log_message(f"Starting Process.")
            self.check_queue()
            self.concat_thread = threading.Thread(
                target=self.start_concat_process,
                args=(self.selected_files, save_file),
                daemon=True
            )            
            self.concat_thread.start()

    def check_queue(self):
        """
        Checks the queue for messages from the worker thread
        and updates the GUI. Runs on the main thread.
        """
        try:
            message = self.process_queue.get_nowait()
            if message == "COMPLETED":
                self.log_message("Processing finished successfully.")
                self.apply_button.configure(state="normal")
            elif message == "ERROR":
                self.log_message("An error occurred during processing.")
                self.apply_button.configure(state="normal")
            else:
                self.log_message(message)
                self.after(100, self.check_queue)
        except queue.Empty:
            self.after(100, self.check_queue)

    def subprocess_routine(self, folder, rate, start, end):
        """ Subprocess routine triggered by the gui. """
        try:
            self.process_queue.put(f"Starting subprocess for folder: {folder}")
            self.process_queue.put(f"Parameters: Rate={rate}, Start={start}, End={end}")
            
            # handler = DataHandler(self.process_queue)
            self.data_processor.simulate_process(2)

        except Exception as e:
            self.process_queue.put(f"FATAL THREAD ERROR: {e}")
            self.process_queue.put("ERROR")

    def start_concat_process(self, fpaths: list[str], savepath: str, time_format="%Y-%m-%d %H:%M:%S"):
        try:
            self.process_queue.put("Process started")

            self.data_processor.concatenate_csv_files(fpaths, savepath, time_format)
        except Exception as e:
            self.process_queue.put(f"FATAL THREAD ERROR: {e}")
            self.process_queue.put("ERROR")