import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime
import threading
import queue
import os
from tools.processing import DataHandler

class MainApp(tk.Tk):
    def __init__(self, config):
        super().__init__()

        self.conf = config

        self.title("CSV Resampler for Water Temperatures")
        self.geometry("700x550")
        try:
            icon = tk.PhotoImage(file="gui/icon.png")
            self.iconphoto(True, icon)
        except Exception as e:
            print("Couldn't open gui/icon.png, using icon.png")
            try: 
                icon = tk.PhotoImage(file="icon.png")
                self.iconphoto(True, icon)
            except Exception as e:
                print("Couldn't open icon.png, proceeding without icon")

        self.selected_files = []
        
        # Main window grid configuration
        self.grid_rowconfigure(0, weight=1)  # Top frame (options)
        self.grid_rowconfigure(1, weight=1)  # Middle frame (info text)
        self.grid_rowconfigure(2, weight=0)  # Bottom frame (button)
        self.grid_columnconfigure(0, weight=1)

        # Main frame that holds the application content
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew", rowspan=3)
        main_frame.grid_rowconfigure(0, weight=1) # Options frame
        main_frame.grid_rowconfigure(1, weight=1) # Info text area will expand
        main_frame.grid_columnconfigure(0, weight=1)

        options_frame = ttk.LabelFrame(main_frame, text="Dateien zusammenfügen", padding="10")
        options_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        options_frame.grid_columnconfigure(1, weight=1) # Make entry widgets expand 

        # Base file path
        ttk.Label(options_frame, text="Bestehende Bibliothek (optional):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.file_path_var = tk.StringVar()
        folder_entry = ttk.Entry(options_frame, textvariable=self.file_path_var)
        folder_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(options_frame, text="Durchsuchen...", command=self.browse_lib_file).grid(row=0, column=2, sticky="e", padx=5, pady=5)

        # New files
        ttk.Label(options_frame, text="Neue Dateien:").grid(row=1, column=0, sticky="nw", padx=5, pady=5)

        # Frame for Listbox + Scrollbar
        list_frame = ttk.Frame(options_frame)
        list_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.file_listbox = tk.Listbox(list_frame, height=8, selectmode="extended")
        self.file_listbox.grid(row=0, column=0, sticky="nsew")

        list_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        list_scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox['yscrollcommand'] = list_scrollbar.set

        # Frame for Add/Remove Buttons
        button_list_frame = ttk.Frame(options_frame)
        button_list_frame.grid(row=1, column=2, sticky="n", padx=5, pady=5)

        ttk.Button(button_list_frame, text="Hinzufügen...", command=self.add_files).grid(row=0, column=0, sticky="ew", pady=2)
        ttk.Button(button_list_frame, text="Entfernen", command=self.remove_selected_files).grid(row=1, column=0, sticky="ew", pady=2)

        # Checkbox for sorting
        self.sort_active = tk.BooleanVar(value=False)
        self.sort_active_box = tk.Checkbutton(options_frame, text="Daten sortieren (optional)", variable=self.sort_active, onvalue=True, offvalue=False)
        self.sort_active_box.grid(row=4, column=0, columnspan=3, sticky="w", padx=5, pady=2)
        # Checkbox for deleting duplicate rows
        self.rm_duplicates_active = tk.BooleanVar(value=True)
        self.rm_duplicates_active_box = tk.Checkbutton(options_frame, text="Doppelte Daten entfernen (optional)", variable=self.rm_duplicates_active, onvalue=True, offvalue=False)
        self.rm_duplicates_active_box.grid(row=5, column=0, columnspan=3, sticky="w", padx=5, pady=2)

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
        self.data_processor = DataHandler(self.process_queue, self.conf)
        self.log_message("Welcome! Please configure the options and press 'Apply'.")
        
    def log_message(self, message):
        """ Inserts a message into the info text box safely. """
        self.info_text.configure(state="normal")
        self.info_text.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.info_text.configure(state="disabled")
        self.info_text.see(tk.END) # Auto-scroll to bottom

    def browse_lib_file(self):
        """ Opens a dialog to select a file. """
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
                self.file_path_var.set(path)
                self.log_message(f"File selected: {path}")
                self.start_processing_thread(0)

    def browse_save_as(self, initial_file=None):
        path = filedialog.asksaveasfilename(filetypes=[("CSV Files", "*.csv")], initialfile=initial_file)
        return path

    def add_files(self):
        """ Opens a dialog to select multiple files and adds them to the list. """
        paths = filedialog.askopenfilenames(filetypes=[("Excel Files", "*.xlsx")])
        if paths:
            count_added = 0
            for path in paths:
                if path not in self.selected_files:
                    self.selected_files.append(path)
                    self.file_listbox.insert(tk.END, path) # Add full path to listbox
                    count_added += 1
            self.log_message(f"Selected {count_added} new file(s). Total: {len(self.selected_files)}")
            
    def remove_selected_files(self):
        """ Removes the selected file(s) from the listbox and the internal list. """
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            self.log_message("No file selected to remove.")
            return

        # Iterate in reverse order to avoid index shifting issues
        for index in reversed(selected_indices):
            file_path = self.file_listbox.get(index)
            self.file_listbox.delete(index)
            if file_path in self.selected_files:
                self.selected_files.remove(file_path)
                
        self.log_message(f"Removed {len(selected_indices)} file(s). Total remaining: {len(self.selected_files)}")

    def clear_inputs(self):
        self.file_listbox.delete(0, tk.END)
        self.selected_files = []
        self.file_path_var.set("")
        
    def on_apply_button_click(self):
        """ Apply file concatenation with chosen settings. """

        if not self.selected_files or len(self.selected_files) < 1:
            basepath = self.file_path_var.get()
            if basepath == "" or basepath is None:
                messagebox.showerror("Error", "No files selected. Please select files to work with.")
                return
            else: messagebox.showinfo("No new files selected", "The selected settings will be applied to the selected file.")
        
        initial_name = "all_data.csv"
        path = self.browse_save_as(initial_name)
        
        if not path:
            self.log_message("Save operation cancelled.")
            return
            
        self.save_file_path = path
        self.log_message(f"Saving concatenated file to: {path}")
        self.start_processing_thread(1)

    def start_processing_thread(self, task):
        """ Validates inputs and starts the background task in a new thread. """
        if task == 0:
            file_path = self.file_path_var.get()
            if not file_path or not os.path.isfile(file_path):
                messagebox.showerror("Validation Error", "Please select a valid file path.")
                return
            else:
                # All inputs are valid
                self.apply_button.configure(state="disabled")

                # Start the queue checker
                self.check_queue()

                # Create and start the worker thread
                self.get_latest_thread = threading.Thread(
                    target=self.start_file_reading,
                    args=(file_path,),
                    daemon=True # Thread will exit when main app exits
                )
                self.get_latest_thread.start()

        elif task == 1:
            # File concatenation
            save_file = self.save_file_path
            old_file_path = self.file_path_var.get()
            sort = self.sort_active.get()
            drop_duplicates = self.rm_duplicates_active.get()
            if not old_file_path:
                self.log_message("Proceeding without existing data library")
                old_file_path = None
            elif not os.path.isfile(old_file_path):
                messagebox.showerror("File Error", f"{old_file_path} is not a file. Please pick a valid existing data library.")
                return
            
            if not self.selected_files or len(self.selected_files) < 1:
                if old_file_path is not None:
                    fpaths = None
                else:
                    messagebox.showerror("No files selected", "No base and no files selected. Please select someting.")
                    return
            else: fpaths = self.selected_files
            self.log_message(f"Starting Process.")
            self.check_queue()
            self.concat_thread = threading.Thread(
                target=self.start_concat_process,
                args=(fpaths, save_file, old_file_path, sort, drop_duplicates),
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
            elif message == "CONCAT_COMPLETED":
                self.log_message("Processing finished successfully.")
                self.clear_inputs()
                self.apply_button.configure(state="normal")
            elif message == "ERROR":
                self.log_message("An error occurred during processing.")
                self.apply_button.configure(state="normal")
            else:
                self.log_message(message)
                self.after(100, self.check_queue)
        except queue.Empty:
            self.after(100, self.check_queue)

    def start_file_reading(self, file: str):
        """ Subprocess routine triggered by the gui. """
        try:
            self.process_queue.put(f"Starting reading file: {file}")

            res = self.data_processor.get_newest_sensor_entries(file)
            for r in res:
                self.log_message(f"Sensor: {r["name"]}, latest entry: {r["latest"]}")  
            self.process_queue.put("COMPLETED")

        except Exception as e:
            self.process_queue.put(f"An error occured: {e}")
            self.process_queue.put("ERROR")

    def start_concat_process(self, fpaths: list[str] | None, savepath: str, oldfile=None, sort=True, drop_duplicates=True):
        try:
            self.process_queue.put("Process started")
            self.data_processor.append_sensor_files(fpaths, savepath, oldfile, sort, drop_duplicates)
        except Exception as e:
            self.process_queue.put(f"An error occured: {e}")
            self.process_queue.put("ERROR")