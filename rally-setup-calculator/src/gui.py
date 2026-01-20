"""
ACR Rally Setup Calculator - GUI
Modern interface styled to match Assetto Corsa Rally's garage menus.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Try to import PIL for better icon support
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from setup_calculator import SetupCalculator, CarSetup
except ImportError:
    from src.setup_calculator import SetupCalculator, CarSetup


class SetupCalculatorGUI:
    """Main GUI application - ACR-styled interface"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ACR RallyWorks - Setup Calculator")
        self.root.geometry("1100x800")
        self.root.minsize(1000, 750)

        # Initialize calculator
        self.calculator = SetupCalculator()
        self.current_setup = None
        self.setup_loaded = False

        # ACR Color scheme - matches the game UI
        self.colors = {
            'bg_dark': '#1a1a1a',
            'bg_panel': '#252525',
            'bg_section': '#2d2d2d',
            'bg_input': '#1e1e1e',
            'fg_primary': '#ffffff',
            'fg_secondary': '#b0b0b0',
            'fg_dim': '#666666',
            'accent_red': '#c41e3a',
            'accent_red_hover': '#e62850',
            'accent_red_dark': '#8b1528',
            'border': '#3a3a3a',
            'gravel': '#d4a574',
            'tarmac': '#7da7d9',
            'selected_bg': '#3d1a1a',
        }

        # Configure root
        self.root.configure(bg=self.colors['bg_dark'])

        # Set app icon
        self.set_app_icon()

        # Current tab
        self.current_tab = "SUSPENSIONS"

        # Setup styles first
        self.setup_styles()

        # Build UI
        self.create_widgets()

    def set_app_icon(self):
        """Set the application icon from logo.png"""
        try:
            # Look for logo in project root
            logo_path = Path(__file__).parent.parent.parent / "logo.png"
            ico_path = Path(__file__).parent.parent.parent / "logo.ico"

            # Try .ico file first on Windows (better taskbar support)
            if ico_path.exists():
                self.root.iconbitmap(str(ico_path))
                return

            # Fall back to PNG with PIL if available
            if logo_path.exists() and HAS_PIL:
                icon_image = Image.open(logo_path)
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.root.iconphoto(True, icon_photo)
                # Keep reference to prevent garbage collection
                self._icon_photo = icon_photo
        except Exception as e:
            print(f"Could not load icon: {e}")

    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure the dropdown list colors globally
        self.root.option_add('*TCombobox*Listbox.background', self.colors['bg_section'])
        self.root.option_add('*TCombobox*Listbox.foreground', self.colors['fg_primary'])
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.colors['accent_red'])
        self.root.option_add('*TCombobox*Listbox.selectForeground', '#ffffff')

        # Car combobox style
        style.configure(
            'Car.TCombobox',
            fieldbackground=self.colors['bg_section'],
            background=self.colors['bg_section'],
            foreground=self.colors['fg_primary'],
            arrowcolor=self.colors['fg_primary'],
            borderwidth=1,
            relief='flat',
            padding=5
        )
        style.map('Car.TCombobox',
                  fieldbackground=[('readonly', self.colors['bg_section'])],
                  selectbackground=[('readonly', self.colors['accent_red'])],
                  selectforeground=[('readonly', '#ffffff')])

        # Stage combobox style
        style.configure(
            'Stage.TCombobox',
            fieldbackground=self.colors['bg_section'],
            background=self.colors['bg_section'],
            foreground=self.colors['fg_primary'],
            arrowcolor=self.colors['fg_primary'],
            borderwidth=1,
            relief='flat',
            padding=5
        )
        style.map('Stage.TCombobox',
                  fieldbackground=[('readonly', self.colors['bg_section'])],
                  selectbackground=[('readonly', self.colors['accent_red'])],
                  selectforeground=[('readonly', '#ffffff')])

    def create_widgets(self):
        """Create all UI widgets"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header bar with title and car/stage selection
        self.create_header(main_frame)

        # Info bar showing selected car/stage
        self.create_info_bar(main_frame)

        # Tab bar
        self.create_tab_bar(main_frame)

        # Content area
        self.content_frame = tk.Frame(main_frame, bg=self.colors['bg_dark'])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Results widgets storage
        self.results_widgets = {}

        # Create initial content
        self.create_tab_content()

    def create_header(self, parent):
        """Create the header with title and selection dropdowns"""
        header = tk.Frame(parent, bg=self.colors['bg_panel'], height=90)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Left side - Title
        title_frame = tk.Frame(header, bg=self.colors['bg_panel'])
        title_frame.pack(side=tk.LEFT, padx=20, pady=15)

        title_label = tk.Label(
            title_frame,
            text="CAR SETUP",
            font=('Segoe UI', 22, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_panel']
        )
        title_label.pack(anchor='w')

        subtitle_label = tk.Label(
            title_frame,
            text="ACR RallyWorks",
            font=('Segoe UI', 10),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_panel']
        )
        subtitle_label.pack(anchor='w')

        # Right side - Selection controls
        selection_frame = tk.Frame(header, bg=self.colors['bg_panel'])
        selection_frame.pack(side=tk.RIGHT, padx=20, pady=15)

        # Car selection
        car_container = tk.Frame(selection_frame, bg=self.colors['bg_panel'])
        car_container.pack(side=tk.LEFT, padx=(0, 15))

        car_label = tk.Label(
            car_container,
            text="CAR",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_panel']
        )
        car_label.pack(anchor='w')

        self.car_var = tk.StringVar()
        cars = self.calculator.get_cars()
        self.car_combo = ttk.Combobox(
            car_container,
            textvariable=self.car_var,
            values=cars,
            state="readonly",
            width=32,
            style='Car.TCombobox',
            font=('Segoe UI', 10)
        )
        self.car_combo.pack()

        # Stage selection
        stage_container = tk.Frame(selection_frame, bg=self.colors['bg_panel'])
        stage_container.pack(side=tk.LEFT, padx=(0, 15))

        stage_label = tk.Label(
            stage_container,
            text="STAGE",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_panel']
        )
        stage_label.pack(anchor='w')

        self.stage_var = tk.StringVar()
        stages = self.calculator.get_stages()
        self.stage_combo = ttk.Combobox(
            stage_container,
            textvariable=self.stage_var,
            values=stages,
            state="readonly",
            width=32,
            style='Stage.TCombobox',
            font=('Segoe UI', 10)
        )
        self.stage_combo.pack()

        # Load button
        self.load_button = tk.Button(
            selection_frame,
            text="LOAD BASELINE SETUP",
            font=('Segoe UI', 10, 'bold'),
            fg='#ffffff',
            bg=self.colors['accent_red'],
            activebackground=self.colors['accent_red_hover'],
            activeforeground='#ffffff',
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.load_setup
        )
        self.load_button.pack(side=tk.LEFT)

        # Hover effects for button
        self.load_button.bind('<Enter>', lambda e: self.load_button.configure(bg=self.colors['accent_red_hover']))
        self.load_button.bind('<Leave>', lambda e: self.load_button.configure(bg=self.colors['accent_red']))

    def create_info_bar(self, parent):
        """Create the info bar showing current car/stage selection"""
        self.info_bar = tk.Frame(parent, bg=self.colors['bg_dark'], height=50)
        self.info_bar.pack(fill=tk.X, padx=20, pady=(15, 0))

        # Left side - Car and Stage info
        info_left = tk.Frame(self.info_bar, bg=self.colors['bg_dark'])
        info_left.pack(side=tk.LEFT)

        # Car label
        self.car_display = tk.Label(
            info_left,
            text="Car: Not selected",
            font=('Segoe UI', 11),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_dark']
        )
        self.car_display.pack(side=tk.LEFT, padx=(0, 30))

        # Stage label
        self.stage_display = tk.Label(
            info_left,
            text="Stage: Not selected",
            font=('Segoe UI', 11),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_dark']
        )
        self.stage_display.pack(side=tk.LEFT, padx=(0, 30))

        # Surface indicator (right side)
        self.surface_label = tk.Label(
            self.info_bar,
            text="",
            font=('Segoe UI', 11, 'bold'),
            fg=self.colors['bg_dark'],
            bg=self.colors['bg_dark'],
            padx=15,
            pady=5
        )
        self.surface_label.pack(side=tk.RIGHT)

    def create_tab_bar(self, parent):
        """Create the tab navigation bar"""
        tab_bar = tk.Frame(parent, bg=self.colors['bg_dark'], height=45)
        tab_bar.pack(fill=tk.X, padx=20, pady=(15, 0))
        tab_bar.pack_propagate(False)

        self.tabs = {}
        tab_names = ["SUSPENSIONS", "DAMPERS", "DIFFERENTIALS", "TYRES", "BRAKES"]

        for tab_name in tab_names:
            tab_btn = tk.Label(
                tab_bar,
                text=tab_name,
                font=('Segoe UI', 10, 'bold'),
                fg=self.colors['fg_secondary'],
                bg=self.colors['bg_dark'],
                padx=20,
                pady=10,
                cursor='hand2'
            )
            tab_btn.pack(side=tk.LEFT)
            tab_btn.bind('<Button-1>', lambda e, t=tab_name: self.switch_tab(t))
            tab_btn.bind('<Enter>', lambda e, btn=tab_btn: self.on_tab_hover(btn, True))
            tab_btn.bind('<Leave>', lambda e, btn=tab_btn: self.on_tab_hover(btn, False))
            self.tabs[tab_name] = tab_btn

        # Update initial tab appearance
        self.update_tab_styles()

    def on_tab_hover(self, btn, entering):
        """Handle tab hover effect"""
        tab_name = btn.cget('text')
        if tab_name != self.current_tab:
            if entering:
                btn.configure(fg=self.colors['fg_primary'])
            else:
                btn.configure(fg=self.colors['fg_secondary'])

    def update_tab_styles(self):
        """Update tab styles based on current selection"""
        for name, btn in self.tabs.items():
            if name == self.current_tab:
                btn.configure(
                    fg=self.colors['accent_red'],
                    bg=self.colors['bg_dark']
                )
            else:
                btn.configure(
                    fg=self.colors['fg_secondary'],
                    bg=self.colors['bg_dark']
                )

    def switch_tab(self, tab_name):
        """Switch to a different tab"""
        self.current_tab = tab_name
        self.update_tab_styles()
        self.create_tab_content()

        # Re-display current setup if available
        if self.current_setup:
            self.display_setup(self.current_setup)

    def create_tab_content(self):
        """Create content for the current tab"""
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.results_widgets = {}

        # Create content based on current tab
        if self.current_tab == "SUSPENSIONS":
            self.create_suspensions_tab()
        elif self.current_tab == "DAMPERS":
            self.create_dampers_tab()
        elif self.current_tab == "DIFFERENTIALS":
            self.create_differentials_tab()
        elif self.current_tab == "TYRES":
            self.create_tyres_tab()
        elif self.current_tab == "BRAKES":
            self.create_brakes_tab()

    def create_panel(self, parent, title, row=0, col=0, rowspan=1, colspan=1):
        """Create a styled panel with title and red border on top"""
        # Outer frame for border effect
        outer = tk.Frame(parent, bg=self.colors['accent_red'])
        outer.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan,
                   sticky='nsew', padx=8, pady=8)

        # Inner panel
        panel = tk.Frame(outer, bg=self.colors['bg_panel'])
        panel.pack(fill=tk.BOTH, expand=True, padx=(0, 0), pady=(3, 0))

        # Title bar
        title_bar = tk.Frame(panel, bg=self.colors['bg_panel'])
        title_bar.pack(fill=tk.X, padx=15, pady=(12, 8))

        title_label = tk.Label(
            title_bar,
            text=title,
            font=('Segoe UI', 11, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_panel']
        )
        title_label.pack(anchor='w')

        # Content area
        content = tk.Frame(panel, bg=self.colors['bg_panel'])
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        return content

    def create_value_row(self, parent, label_text, key, row, show_unit=True):
        """Create a label-value row in ACR style"""
        row_frame = tk.Frame(parent, bg=self.colors['bg_panel'])
        row_frame.grid(row=row, column=0, sticky='ew', pady=3)
        parent.columnconfigure(0, weight=1)

        # Label
        label = tk.Label(
            row_frame,
            text=label_text,
            font=('Segoe UI', 10),
            fg=self.colors['fg_secondary'],
            bg=self.colors['bg_panel'],
            anchor='w'
        )
        label.pack(side=tk.LEFT)

        # Value (styled like a read-only input)
        value_frame = tk.Frame(row_frame, bg=self.colors['bg_input'], padx=10, pady=5)
        value_frame.pack(side=tk.RIGHT)

        value_label = tk.Label(
            value_frame,
            text="-",
            font=('Segoe UI', 10),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_input'],
            width=12,
            anchor='e'
        )
        value_label.pack()

        self.results_widgets[key] = value_label

    def create_suspensions_tab(self):
        """Create the suspensions tab content"""
        # Grid layout: 2x2 for corners
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.columnconfigure(1, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        self.content_frame.rowconfigure(1, weight=1)

        # Front Left
        fl_content = self.create_panel(self.content_frame, "FRONT LEFT", 0, 0)
        self.create_value_row(fl_content, "Ride Height", "ride_height_fl", 0)
        self.create_value_row(fl_content, "Spring Stiffness", "spring_fl", 1)

        # Front Right
        fr_content = self.create_panel(self.content_frame, "FRONT RIGHT", 0, 1)
        self.create_value_row(fr_content, "Ride Height", "ride_height_fr", 0)
        self.create_value_row(fr_content, "Spring Stiffness", "spring_fr", 1)

        # Rear Left
        rl_content = self.create_panel(self.content_frame, "REAR LEFT", 1, 0)
        self.create_value_row(rl_content, "Ride Height", "ride_height_rl", 0)
        self.create_value_row(rl_content, "Spring Stiffness", "spring_rl", 1)

        # Rear Right
        rr_content = self.create_panel(self.content_frame, "REAR RIGHT", 1, 1)
        self.create_value_row(rr_content, "Ride Height", "ride_height_rr", 0)
        self.create_value_row(rr_content, "Spring Stiffness", "spring_rr", 1)

        # Center panel for ARBs (add a third row)
        self.content_frame.rowconfigure(2, weight=0)

        arb_frame = tk.Frame(self.content_frame, bg=self.colors['bg_dark'])
        arb_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=8, pady=(0, 8))
        arb_frame.columnconfigure(0, weight=1)
        arb_frame.columnconfigure(1, weight=1)

        # Front ARB
        front_arb_panel = self.create_mini_panel(arb_frame, "FRONT ARB", 0, 0)
        self.create_value_row(front_arb_panel, "Stiffness", "front_arb", 0)

        # Rear ARB
        rear_arb_panel = self.create_mini_panel(arb_frame, "REAR ARB", 0, 1)
        self.create_value_row(rear_arb_panel, "Stiffness", "rear_arb", 0)

    def create_mini_panel(self, parent, title, row, col):
        """Create a smaller panel for single values"""
        outer = tk.Frame(parent, bg=self.colors['accent_red'])
        outer.grid(row=row, column=col, sticky='ew', padx=8, pady=8)

        panel = tk.Frame(outer, bg=self.colors['bg_panel'])
        panel.pack(fill=tk.BOTH, expand=True, padx=(0, 0), pady=(3, 0))

        title_label = tk.Label(
            panel,
            text=title,
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['fg_primary'],
            bg=self.colors['bg_panel']
        )
        title_label.pack(anchor='w', padx=15, pady=(10, 5))

        content = tk.Frame(panel, bg=self.colors['bg_panel'])
        content.pack(fill=tk.X, padx=15, pady=(0, 10))

        return content

    def create_dampers_tab(self):
        """Create the dampers tab content"""
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.columnconfigure(1, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        self.content_frame.rowconfigure(1, weight=1)

        # Front Left
        fl_content = self.create_panel(self.content_frame, "FRONT LEFT", 0, 0)
        self.create_value_row(fl_content, "Slow Bump", "damper_fl_slow_bump", 0)
        self.create_value_row(fl_content, "Slow Rebound", "damper_fl_slow_rebound", 1)
        self.create_value_row(fl_content, "Fast Bump", "damper_fl_fast_bump", 2)
        self.create_value_row(fl_content, "Fast Rebound", "damper_fl_fast_rebound", 3)

        # Front Right
        fr_content = self.create_panel(self.content_frame, "FRONT RIGHT", 0, 1)
        self.create_value_row(fr_content, "Slow Bump", "damper_fr_slow_bump", 0)
        self.create_value_row(fr_content, "Slow Rebound", "damper_fr_slow_rebound", 1)
        self.create_value_row(fr_content, "Fast Bump", "damper_fr_fast_bump", 2)
        self.create_value_row(fr_content, "Fast Rebound", "damper_fr_fast_rebound", 3)

        # Rear Left
        rl_content = self.create_panel(self.content_frame, "REAR LEFT", 1, 0)
        self.create_value_row(rl_content, "Slow Bump", "damper_rl_slow_bump", 0)
        self.create_value_row(rl_content, "Slow Rebound", "damper_rl_slow_rebound", 1)
        self.create_value_row(rl_content, "Fast Bump", "damper_rl_fast_bump", 2)
        self.create_value_row(rl_content, "Fast Rebound", "damper_rl_fast_rebound", 3)

        # Rear Right
        rr_content = self.create_panel(self.content_frame, "REAR RIGHT", 1, 1)
        self.create_value_row(rr_content, "Slow Bump", "damper_rr_slow_bump", 0)
        self.create_value_row(rr_content, "Slow Rebound", "damper_rr_slow_rebound", 1)
        self.create_value_row(rr_content, "Fast Bump", "damper_rr_fast_bump", 2)
        self.create_value_row(rr_content, "Fast Rebound", "damper_rr_fast_rebound", 3)

    def create_differentials_tab(self):
        """Create the differentials tab content"""
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.columnconfigure(1, weight=1)
        self.content_frame.rowconfigure(0, weight=0)
        self.content_frame.rowconfigure(1, weight=1)

        # Drive Type info at top
        info_frame = tk.Frame(self.content_frame, bg=self.colors['bg_panel'])
        info_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=8, pady=8)

        self.drive_type_label = tk.Label(
            info_frame,
            text="DRIVE TYPE: -",
            font=('Segoe UI', 12, 'bold'),
            fg=self.colors['accent_red'],
            bg=self.colors['bg_panel'],
            pady=10
        )
        self.drive_type_label.pack()
        self.results_widgets['drive_type_display'] = self.drive_type_label

        # Front Diff
        front_content = self.create_panel(self.content_frame, "FRONT", 1, 0)
        self.create_value_row(front_content, "Diff Ratio", "front_diff_ratio", 0)
        self.create_value_row(front_content, "LSD Ramp Angle", "front_diff_lsd_ramp_angle", 1)
        self.create_value_row(front_content, "LSD Plates", "front_diff_lsd_plates", 2)
        self.create_value_row(front_content, "LSD Preload", "front_diff_lsd_preload", 3)

        # Rear Diff
        rear_content = self.create_panel(self.content_frame, "REAR", 1, 1)
        self.create_value_row(rear_content, "Diff Ratio", "rear_diff_ratio", 0)
        self.create_value_row(rear_content, "LSD Ramp Angle", "rear_diff_lsd_ramp_angle", 1)
        self.create_value_row(rear_content, "LSD Plates", "rear_diff_lsd_plates", 2)
        self.create_value_row(rear_content, "LSD Preload", "rear_diff_lsd_preload", 3)

        # Center Diff (if AWD)
        self.content_frame.rowconfigure(2, weight=0)
        center_frame = tk.Frame(self.content_frame, bg=self.colors['bg_dark'])
        center_frame.grid(row=2, column=0, columnspan=2, sticky='ew')

        center_content = self.create_mini_panel(center_frame, "CENTER", 0, 0)
        center_frame.columnconfigure(0, weight=1)
        self.create_value_row(center_content, "Front Bias", "front_bias", 0)
        self.create_value_row(center_content, "Centre Diff Ratio", "centre_diff_ratio", 1)

    def create_tyres_tab(self):
        """Create the tyres tab content"""
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.columnconfigure(1, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        self.content_frame.rowconfigure(1, weight=1)

        # Front Left
        fl_content = self.create_panel(self.content_frame, "FRONT LEFT", 0, 0)
        self.create_value_row(fl_content, "Pressure", "tyre_fl_pressure", 0)
        self.create_value_row(fl_content, "Camber", "tyre_fl_camber", 1)
        self.create_value_row(fl_content, "Toe", "tyre_fl_toe", 2)

        # Front Right
        fr_content = self.create_panel(self.content_frame, "FRONT RIGHT", 0, 1)
        self.create_value_row(fr_content, "Pressure", "tyre_fr_pressure", 0)
        self.create_value_row(fr_content, "Camber", "tyre_fr_camber", 1)
        self.create_value_row(fr_content, "Toe", "tyre_fr_toe", 2)

        # Rear Left
        rl_content = self.create_panel(self.content_frame, "REAR LEFT", 1, 0)
        self.create_value_row(rl_content, "Pressure", "tyre_rl_pressure", 0)
        self.create_value_row(rl_content, "Camber", "tyre_rl_camber", 1)
        self.create_value_row(rl_content, "Toe", "tyre_rl_toe", 2)

        # Rear Right
        rr_content = self.create_panel(self.content_frame, "REAR RIGHT", 1, 1)
        self.create_value_row(rr_content, "Pressure", "tyre_rr_pressure", 0)
        self.create_value_row(rr_content, "Camber", "tyre_rr_camber", 1)
        self.create_value_row(rr_content, "Toe", "tyre_rr_toe", 2)

    def create_brakes_tab(self):
        """Create the brakes tab content"""
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)

        # Main brakes panel
        brakes_content = self.create_panel(self.content_frame, "BRAKES", 0, 0)
        self.create_value_row(brakes_content, "Brake Bias", "brake_bias", 0)
        self.create_value_row(brakes_content, "Prop Valve Pressure", "prop_valve_pressure", 1)

    def load_setup(self):
        """Load the setup when button is clicked"""
        car = self.car_var.get()
        stage = self.stage_var.get()

        if not car:
            messagebox.showwarning("Selection Required", "Please select a car.")
            return

        if not stage:
            messagebox.showwarning("Selection Required", "Please select a stage.")
            return

        # Update info bar
        self.car_display.config(text=f"Car: {car}", fg=self.colors['fg_primary'])
        self.stage_display.config(text=f"Stage: {stage}", fg=self.colors['fg_primary'])

        # Update surface indicator
        surface = self.calculator.get_stage_surface(stage)
        if surface.lower() == 'gravel':
            self.surface_label.config(
                text="GRAVEL",
                bg=self.colors['gravel'],
                fg=self.colors['bg_dark']
            )
        else:
            self.surface_label.config(
                text="TARMAC",
                bg=self.colors['tarmac'],
                fg=self.colors['bg_dark']
            )

        # Get and display setup
        setup = self.calculator.get_setup(car, stage)
        if setup:
            self.current_setup = setup
            self.setup_loaded = True
            self.display_setup(setup)
        else:
            self.current_setup = None
            self.setup_loaded = False
            self.clear_results()
            messagebox.showwarning("No Setup",
                                   f"No {surface.lower()} setup found for {car}")

    def display_setup(self, setup: CarSetup):
        """Display setup values in the UI"""
        # Map setup attributes to widget keys
        attr_map = {
            "drive_type": setup.drive_type,
            "front_bias": setup.front_bias,
            "front_diff_ratio": setup.front_diff_ratio,
            "front_diff_lsd_ramp_angle": setup.front_diff_lsd_ramp_angle,
            "front_diff_lsd_plates": setup.front_diff_lsd_plates,
            "front_diff_lsd_preload": setup.front_diff_lsd_preload,
            "rear_diff_ratio": setup.rear_diff_ratio,
            "rear_diff_lsd_ramp_angle": setup.rear_diff_lsd_ramp_angle,
            "rear_diff_lsd_plates": setup.rear_diff_lsd_plates,
            "rear_diff_lsd_preload": setup.rear_diff_lsd_preload,
            "centre_diff_ratio": setup.centre_diff_ratio,
            "front_arb": setup.front_arb,
            "rear_arb": setup.rear_arb,
            "spring_fl": setup.spring_fl,
            "spring_fr": setup.spring_fr,
            "spring_rl": setup.spring_rl,
            "spring_rr": setup.spring_rr,
            "ride_height_fl": setup.ride_height_fl,
            "ride_height_fr": setup.ride_height_fr,
            "ride_height_rl": setup.ride_height_rl,
            "ride_height_rr": setup.ride_height_rr,
            "damper_fl_slow_bump": setup.damper_fl_slow_bump,
            "damper_fl_slow_rebound": setup.damper_fl_slow_rebound,
            "damper_fl_fast_bump": setup.damper_fl_fast_bump,
            "damper_fl_fast_rebound": setup.damper_fl_fast_rebound,
            "damper_fr_slow_bump": setup.damper_fr_slow_bump,
            "damper_fr_slow_rebound": setup.damper_fr_slow_rebound,
            "damper_fr_fast_bump": setup.damper_fr_fast_bump,
            "damper_fr_fast_rebound": setup.damper_fr_fast_rebound,
            "damper_rl_slow_bump": setup.damper_rl_slow_bump,
            "damper_rl_slow_rebound": setup.damper_rl_slow_rebound,
            "damper_rl_fast_bump": setup.damper_rl_fast_bump,
            "damper_rl_fast_rebound": setup.damper_rl_fast_rebound,
            "damper_rr_slow_bump": setup.damper_rr_slow_bump,
            "damper_rr_slow_rebound": setup.damper_rr_slow_rebound,
            "damper_rr_fast_bump": setup.damper_rr_fast_bump,
            "damper_rr_fast_rebound": setup.damper_rr_fast_rebound,
            "tyre_fl_pressure": setup.tyre_fl_pressure,
            "tyre_fl_camber": setup.tyre_fl_camber,
            "tyre_fl_toe": setup.tyre_fl_toe,
            "tyre_fr_pressure": setup.tyre_fr_pressure,
            "tyre_fr_camber": setup.tyre_fr_camber,
            "tyre_fr_toe": setup.tyre_fr_toe,
            "tyre_rl_pressure": setup.tyre_rl_pressure,
            "tyre_rl_camber": setup.tyre_rl_camber,
            "tyre_rl_toe": setup.tyre_rl_toe,
            "tyre_rr_pressure": setup.tyre_rr_pressure,
            "tyre_rr_camber": setup.tyre_rr_camber,
            "tyre_rr_toe": setup.tyre_rr_toe,
            "brake_bias": setup.brake_bias,
            "prop_valve_pressure": setup.prop_valve_pressure,
        }

        for key, value in attr_map.items():
            if key in self.results_widgets:
                display_value = value if value else "-"
                self.results_widgets[key].config(text=display_value)

        # Special handling for drive type display in differentials tab
        if 'drive_type_display' in self.results_widgets:
            drive_type = setup.drive_type if setup.drive_type else "Unknown"
            self.results_widgets['drive_type_display'].config(text=f"DRIVE TYPE: {drive_type}")

    def clear_results(self):
        """Clear all result values"""
        for key, widget in self.results_widgets.items():
            if key == 'drive_type_display':
                widget.config(text="DRIVE TYPE: -")
            else:
                widget.config(text="-")


def main():
    """Launch the GUI application"""
    root = tk.Tk()
    app = SetupCalculatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
