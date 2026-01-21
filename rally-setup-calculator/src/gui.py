"""
ACR RallyWorks - GUI
Rally setup calculator for Assetto Corsa Rally with RallyWorks+ optimization.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import json
from datetime import datetime

# Try to import PIL for image support
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from setup_calculator import SetupCalculator
    from dirt_converter import create_test_setup, DirtConverter, ACRRanges
except ImportError:
    from src.setup_calculator import SetupCalculator
    from src.dirt_converter import create_test_setup, DirtConverter, ACRRanges


# ACR parameter ranges for validation (Lancia Delta HF Integrale Evo)
ACR_RANGES = ACRRanges()


class EditableSetup:
    """
    Stores user-editable setup values with validation.
    Initialized from a baseline setup (ACR default or loaded).
    """

    def __init__(self, baseline_setup=None):
        """Initialize with values from a baseline setup."""
        self.values = {}
        self.surface = "gravel"

        if baseline_setup:
            self.surface = getattr(baseline_setup, 'surface', 'gravel')
            self._load_from_setup(baseline_setup)

    def _load_from_setup(self, setup):
        """Extract editable values from a setup object."""
        # Suspension
        suspension = setup.get_suspension()
        self.values['arb_front'] = self._parse_value(suspension.get('Front ARB', '12000'), 'N/m')
        self.values['arb_rear'] = self._parse_value(suspension.get('Rear ARB', '4000'), 'N/m')

        springs = suspension.get('Springs', {})
        self.values['spring_front'] = self._parse_value(springs.get('FL', '40000'), 'N/m')
        self.values['spring_rear'] = self._parse_value(springs.get('RL', '30000'), 'N/m')

        ride_height = suspension.get('Ride Height', {})
        self.values['ride_height_front'] = self._parse_value(ride_height.get('FL', '130'), 'mm')
        self.values['ride_height_rear'] = self._parse_value(ride_height.get('RL', '100'), 'mm')

        # Dampers
        dampers = setup.get_dampers()
        fl_dampers = dampers.get('FL', {})
        rl_dampers = dampers.get('RL', {})

        self.values['front_slow_bump'] = self._parse_value(fl_dampers.get('Slow Bump', '4250'), 'Ns/m')
        self.values['front_slow_rebound'] = self._parse_value(fl_dampers.get('Slow Rebound', '9000'), 'Ns/m')
        self.values['front_fast_bump'] = self._parse_value(fl_dampers.get('Fast Bump', '2500'), 'Ns/m')
        self.values['front_fast_rebound'] = self._parse_value(fl_dampers.get('Fast Rebound', '5000'), 'Ns/m')

        self.values['rear_slow_bump'] = self._parse_value(rl_dampers.get('Slow Bump', '3750'), 'Ns/m')
        self.values['rear_slow_rebound'] = self._parse_value(rl_dampers.get('Slow Rebound', '6750'), 'Ns/m')
        self.values['rear_fast_bump'] = self._parse_value(rl_dampers.get('Fast Bump', '2500'), 'Ns/m')
        self.values['rear_fast_rebound'] = self._parse_value(rl_dampers.get('Fast Rebound', '4500'), 'Ns/m')

        # Tyres
        tyres = setup.get_tyres()
        fl_tyres = tyres.get('FL', {})
        rl_tyres = tyres.get('RL', {})

        self.values['camber_front'] = self._parse_value(fl_tyres.get('Camber', '-2.4'), '°')
        self.values['camber_rear'] = self._parse_value(rl_tyres.get('Camber', '-2.6'), '°')
        self.values['toe_front'] = self._parse_value(fl_tyres.get('Toe', '0.006'), '°')
        self.values['toe_rear'] = self._parse_value(rl_tyres.get('Toe', '0.0'), '°')
        self.values['pressure_front'] = self._parse_value(fl_tyres.get('Pressure', '32'), 'PSI')
        self.values['pressure_rear'] = self._parse_value(rl_tyres.get('Pressure', '32'), 'PSI')

        # Brakes
        brakes = setup.get_brakes()
        bias_str = brakes.get('Brake Bias', '67% front')
        self.values['brake_bias'] = self._parse_value(bias_str, '%')

        # Drivetrain
        drivetrain = setup.get_drivetrain()
        self.values['front_bias'] = self._parse_value(drivetrain.get('Front Bias', '47%'), '%')

        front_diff = drivetrain.get('Front Diff', {})
        self.values['front_lsd_preload'] = self._parse_value(front_diff.get('LSD Preload', '60'), 'Nm')

        rear_diff = drivetrain.get('Rear Diff', {})
        self.values['rear_lsd_preload'] = self._parse_value(rear_diff.get('LSD Preload', '90'), 'Nm')

    def _parse_value(self, value_str, unit):
        """Parse a value string and extract the numeric part."""
        if isinstance(value_str, (int, float)):
            return float(value_str)
        if isinstance(value_str, str):
            # Remove units and clean up
            cleaned = value_str.replace(unit, '').replace('N/m', '').replace('Ns/m', '')
            cleaned = cleaned.replace('mm', '').replace('PSI', '').replace('psi', '')
            cleaned = cleaned.replace('Nm', '').replace('front', '').replace('°', '')
            cleaned = cleaned.replace('%', '').strip()
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        return 0.0

    def get(self, key, default=0.0):
        """Get a value by key."""
        return self.values.get(key, default)

    def set(self, key, value):
        """Set a value with range validation."""
        validated = self._validate(key, value)
        self.values[key] = validated
        return validated

    def _validate(self, key, value):
        """Validate and clamp value to ACR ranges."""
        try:
            val = float(value)
        except (ValueError, TypeError):
            return self.values.get(key, 0.0)

        # Define ranges for each parameter
        ranges = {
            'spring_front': (ACR_RANGES.spring_front_min, ACR_RANGES.spring_front_max),
            'spring_rear': (ACR_RANGES.spring_rear_min, ACR_RANGES.spring_rear_max),
            'arb_front': (ACR_RANGES.arb_front_min, ACR_RANGES.arb_front_max),
            'arb_rear': (ACR_RANGES.arb_rear_min, ACR_RANGES.arb_rear_max),
            'ride_height_front': (ACR_RANGES.ride_height_min, ACR_RANGES.ride_height_max),
            'ride_height_rear': (ACR_RANGES.ride_height_min, ACR_RANGES.ride_height_max),
            'front_slow_bump': (ACR_RANGES.front_slow_bump_min, ACR_RANGES.front_slow_bump_max),
            'front_slow_rebound': (ACR_RANGES.front_slow_rebound_min, ACR_RANGES.front_slow_rebound_max),
            'front_fast_bump': (ACR_RANGES.front_fast_bump_min, ACR_RANGES.front_fast_bump_max),
            'front_fast_rebound': (ACR_RANGES.front_fast_rebound_min, ACR_RANGES.front_fast_rebound_max),
            'rear_slow_bump': (ACR_RANGES.rear_slow_bump_min, ACR_RANGES.rear_slow_bump_max),
            'rear_slow_rebound': (ACR_RANGES.rear_slow_rebound_min, ACR_RANGES.rear_slow_rebound_max),
            'rear_fast_bump': (ACR_RANGES.rear_fast_bump_min, ACR_RANGES.rear_fast_bump_max),
            'rear_fast_rebound': (ACR_RANGES.rear_fast_rebound_min, ACR_RANGES.rear_fast_rebound_max),
            'camber_front': (ACR_RANGES.camber_front_min, ACR_RANGES.camber_front_max),
            'camber_rear': (ACR_RANGES.camber_rear_min, ACR_RANGES.camber_rear_max),
            'toe_front': (-1.0, 1.0),  # Display in degrees, simplified range
            'toe_rear': (-1.0, 1.0),
            'pressure_front': (10.0, 45.0),
            'pressure_rear': (10.0, 45.0),
            'brake_bias': (35.0, 80.0),  # As percentage
            'front_bias': (30.0, 70.0),
            'front_lsd_preload': (0.0, 250.0),
            'rear_lsd_preload': (ACR_RANGES.lsd_preload_rear_min, ACR_RANGES.lsd_preload_rear_max),
        }

        if key in ranges:
            min_val, max_val = ranges[key]
            return max(min_val, min(max_val, val))
        return val

    def get_range(self, key):
        """Get the min/max range for a parameter."""
        ranges = {
            'spring_front': (ACR_RANGES.spring_front_min, ACR_RANGES.spring_front_max),
            'spring_rear': (ACR_RANGES.spring_rear_min, ACR_RANGES.spring_rear_max),
            'arb_front': (ACR_RANGES.arb_front_min, ACR_RANGES.arb_front_max),
            'arb_rear': (ACR_RANGES.arb_rear_min, ACR_RANGES.arb_rear_max),
            'ride_height_front': (ACR_RANGES.ride_height_min, ACR_RANGES.ride_height_max),
            'ride_height_rear': (ACR_RANGES.ride_height_min, ACR_RANGES.ride_height_max),
            'front_slow_bump': (ACR_RANGES.front_slow_bump_min, ACR_RANGES.front_slow_bump_max),
            'front_slow_rebound': (ACR_RANGES.front_slow_rebound_min, ACR_RANGES.front_slow_rebound_max),
            'front_fast_bump': (ACR_RANGES.front_fast_bump_min, ACR_RANGES.front_fast_bump_max),
            'front_fast_rebound': (ACR_RANGES.front_fast_rebound_min, ACR_RANGES.front_fast_rebound_max),
            'rear_slow_bump': (ACR_RANGES.rear_slow_bump_min, ACR_RANGES.rear_slow_bump_max),
            'rear_slow_rebound': (ACR_RANGES.rear_slow_rebound_min, ACR_RANGES.rear_slow_rebound_max),
            'rear_fast_bump': (ACR_RANGES.rear_fast_bump_min, ACR_RANGES.rear_fast_bump_max),
            'rear_fast_rebound': (ACR_RANGES.rear_fast_rebound_min, ACR_RANGES.rear_fast_rebound_max),
            'camber_front': (ACR_RANGES.camber_front_min, ACR_RANGES.camber_front_max),
            'camber_rear': (ACR_RANGES.camber_rear_min, ACR_RANGES.camber_rear_max),
            'toe_front': (-1.0, 1.0),
            'toe_rear': (-1.0, 1.0),
            'pressure_front': (10.0, 45.0),
            'pressure_rear': (10.0, 45.0),
            'brake_bias': (35.0, 80.0),
            'front_bias': (30.0, 70.0),
            'front_lsd_preload': (0.0, 250.0),
            'rear_lsd_preload': (ACR_RANGES.lsd_preload_rear_min, ACR_RANGES.lsd_preload_rear_max),
        }
        return ranges.get(key, (0, 100))

    def to_dict(self):
        """Convert to dictionary for saving."""
        return {
            "suspension": {
                "Front ARB": f"{int(self.values.get('arb_front', 12000))} N/m",
                "Rear ARB": f"{int(self.values.get('arb_rear', 4000))} N/m",
                "Springs": {
                    "FL": f"{int(self.values.get('spring_front', 40000))} N/m",
                    "FR": f"{int(self.values.get('spring_front', 40000))} N/m",
                    "RL": f"{int(self.values.get('spring_rear', 30000))} N/m",
                    "RR": f"{int(self.values.get('spring_rear', 30000))} N/m"
                },
                "Ride Height": {
                    "FL": f"{self.values.get('ride_height_front', 130.0):.1f} mm",
                    "FR": f"{self.values.get('ride_height_front', 130.0):.1f} mm",
                    "RL": f"{self.values.get('ride_height_rear', 100.0):.1f} mm",
                    "RR": f"{self.values.get('ride_height_rear', 100.0):.1f} mm"
                }
            },
            "dampers": {
                "FL": {
                    "Slow Bump": f"{int(self.values.get('front_slow_bump', 4250))} Ns/m",
                    "Slow Rebound": f"{int(self.values.get('front_slow_rebound', 9000))} Ns/m",
                    "Fast Bump": f"{int(self.values.get('front_fast_bump', 2500))} Ns/m",
                    "Fast Rebound": f"{int(self.values.get('front_fast_rebound', 5000))} Ns/m"
                },
                "FR": {
                    "Slow Bump": f"{int(self.values.get('front_slow_bump', 4250))} Ns/m",
                    "Slow Rebound": f"{int(self.values.get('front_slow_rebound', 9000))} Ns/m",
                    "Fast Bump": f"{int(self.values.get('front_fast_bump', 2500))} Ns/m",
                    "Fast Rebound": f"{int(self.values.get('front_fast_rebound', 5000))} Ns/m"
                },
                "RL": {
                    "Slow Bump": f"{int(self.values.get('rear_slow_bump', 3750))} Ns/m",
                    "Slow Rebound": f"{int(self.values.get('rear_slow_rebound', 6750))} Ns/m",
                    "Fast Bump": f"{int(self.values.get('rear_fast_bump', 2500))} Ns/m",
                    "Fast Rebound": f"{int(self.values.get('rear_fast_rebound', 4500))} Ns/m"
                },
                "RR": {
                    "Slow Bump": f"{int(self.values.get('rear_slow_bump', 3750))} Ns/m",
                    "Slow Rebound": f"{int(self.values.get('rear_slow_rebound', 6750))} Ns/m",
                    "Fast Bump": f"{int(self.values.get('rear_fast_bump', 2500))} Ns/m",
                    "Fast Rebound": f"{int(self.values.get('rear_fast_rebound', 4500))} Ns/m"
                }
            },
            "tyres": {
                "FL": {
                    "Pressure": f"{self.values.get('pressure_front', 32):.0f} PSI",
                    "Camber": f"{self.values.get('camber_front', -2.4):.1f}°",
                    "Toe": f"{self.values.get('toe_front', 0.0):.3f}°"
                },
                "FR": {
                    "Pressure": f"{self.values.get('pressure_front', 32):.0f} PSI",
                    "Camber": f"{self.values.get('camber_front', -2.4):.1f}°",
                    "Toe": f"{self.values.get('toe_front', 0.0):.3f}°"
                },
                "RL": {
                    "Pressure": f"{self.values.get('pressure_rear', 32):.0f} PSI",
                    "Camber": f"{self.values.get('camber_rear', -2.6):.1f}°",
                    "Toe": f"{self.values.get('toe_rear', 0.0):.3f}°"
                },
                "RR": {
                    "Pressure": f"{self.values.get('pressure_rear', 32):.0f} PSI",
                    "Camber": f"{self.values.get('camber_rear', -2.6):.1f}°",
                    "Toe": f"{self.values.get('toe_rear', 0.0):.3f}°"
                }
            },
            "brakes": {
                "Brake Bias": f"{self.values.get('brake_bias', 67):.0f}% front"
            },
            "drivetrain": {
                "Front Bias": f"{self.values.get('front_bias', 47):.0f}%",
                "Front Diff": {
                    "LSD Preload": f"{self.values.get('front_lsd_preload', 60):.0f} Nm"
                },
                "Rear Diff": {
                    "LSD Preload": f"{self.values.get('rear_lsd_preload', 90):.0f} Nm"
                }
            }
        }


class LoadedSetup:
    """Wrapper for loaded JSON setup data that provides the same interface as CarSetup."""

    def __init__(self, data: dict):
        self.data = data
        self.surface = data.get("metadata", {}).get("surface", "gravel")

    def get_drivetrain(self) -> dict:
        return self.data.get("drivetrain", {})

    def get_suspension(self) -> dict:
        return self.data.get("suspension", {})

    def get_dampers(self) -> dict:
        return self.data.get("dampers", {})

    def get_tyres(self) -> dict:
        return self.data.get("tyres", {})

    def get_brakes(self) -> dict:
        return self.data.get("brakes", {})


class SetupCalculatorGUI:
    """Main GUI application for ACR Rally Setup Calculator."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ACR RallyWorks")
        self.root.geometry("1000x850")
        self.root.minsize(900, 750)

        # Set window icon
        self.set_window_icon()

        # Initialize calculator
        self.calculator = SetupCalculator()

        # Initialize RallyWorks+ converter
        self.dirt_converter = create_test_setup()
        self.rallyworks_mode = False  # Toggle state
        self.current_setup = None  # Store current ACR setup
        self.current_car = None
        self.current_surface = None

        # Editable setup - stores user modifications
        self.editable_setup = None
        self.entry_widgets = {}  # Store references to entry widgets

        # Color scheme - ACR-inspired dark theme
        self.bg_color = "#1A1A1A"          # Dark background
        self.fg_color = "#E0E0E0"          # Light text
        self.accent_color = "#E53935"      # ACR Red accent
        self.card_bg = "#2A2A2A"           # Card background
        self.section_bg = "#333333"        # Section background
        self.highlight_color = "#404040"   # Selection highlight
        self.border_color = "#3A3A3A"      # Border color

        # RallyWorks+ colors
        self.acr_value_color = "#CCCCCC"    # Light gray for ACR default
        self.rw_increase_color = "#5DADE2"  # Blue for increase
        self.rw_decrease_color = "#E74C3C"  # Red for decrease
        self.rw_same_color = "#888888"      # Gray for same

        # Configure root
        self.root.configure(bg=self.bg_color)

        # Configure styles
        self.setup_styles()

        # Build UI
        self.create_widgets()

        # Auto-load first car/stage
        self.on_selection_changed()

    def set_window_icon(self):
        """Set the window icon from the logo file."""
        try:
            # Find the icon file
            script_dir = Path(__file__).parent.parent.parent
            icon_path = script_dir / "logo.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass  # Silently fail if icon can't be loaded

    def setup_styles(self):
        """Configure ttk styles for ACR-inspired dark theme."""
        style = ttk.Style()
        style.theme_use('clam')

        # Base styles
        style.configure('.', background=self.bg_color, foreground=self.fg_color)
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color,
                       font=('Segoe UI', 10))

        # LabelFrame with ACR-style red accent
        style.configure('TLabelframe', background=self.card_bg, bordercolor=self.border_color)
        style.configure('TLabelframe.Label', background=self.card_bg, foreground=self.accent_color,
                       font=('Segoe UI', 11, 'bold'))

        # Combobox styling - dark background with light text
        style.configure('TCombobox',
                       font=('Segoe UI', 10),
                       fieldbackground=self.section_bg,
                       background=self.section_bg,
                       foreground=self.fg_color,
                       arrowcolor=self.fg_color,
                       selectbackground=self.highlight_color,
                       selectforeground=self.fg_color,
                       bordercolor=self.border_color)
        style.map('TCombobox',
                 fieldbackground=[('readonly', self.section_bg)],
                 foreground=[('readonly', self.fg_color)],
                 background=[('readonly', self.section_bg)],
                 bordercolor=[('focus', self.accent_color)])

        # Custom styles
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground=self.accent_color)
        style.configure('Subtitle.TLabel', font=('Segoe UI', 10), foreground='#888888')
        style.configure('Section.TLabel', font=('Segoe UI', 11, 'bold'), foreground=self.accent_color,
                       background=self.section_bg)
        style.configure('Value.TLabel', font=('Consolas', 10), foreground=self.fg_color,
                       background=self.card_bg)
        style.configure('Key.TLabel', font=('Segoe UI', 9), foreground='#AAAAAA',
                       background=self.card_bg)
        style.configure('Surface.TLabel', font=('Segoe UI', 12, 'bold'))

    def create_widgets(self):
        """Create all UI widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with logo
        self.create_header(main_frame)

        # Selection area
        self.create_selection_area(main_frame)

        # Results area (scrollable)
        self.create_results_area(main_frame)

    def create_header(self, parent):
        """Create the header with logo and title."""
        header_frame = tk.Frame(parent, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        # Try to load and display the logo
        self.logo_image = None
        if PIL_AVAILABLE:
            try:
                script_dir = Path(__file__).parent.parent.parent
                logo_path = script_dir / "logo_textonly.png"
                if logo_path.exists():
                    img = Image.open(logo_path)
                    # Resize to fit header (height ~50px)
                    aspect = img.width / img.height
                    new_height = 50
                    new_width = int(new_height * aspect)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    self.logo_image = ImageTk.PhotoImage(img)

                    logo_label = tk.Label(header_frame, image=self.logo_image, bg=self.bg_color)
                    logo_label.pack(side=tk.LEFT, padx=(0, 15))
            except Exception:
                pass

        # Title text (fallback if no logo)
        title_frame = tk.Frame(header_frame, bg=self.bg_color)
        title_frame.pack(side=tk.LEFT, fill=tk.Y)

        if not self.logo_image:
            title_label = tk.Label(title_frame, text="ACR RallyWorks",
                                  font=('Segoe UI', 18, 'bold'),
                                  bg=self.bg_color, fg=self.accent_color)
            title_label.pack(anchor='w')

        subtitle_label = tk.Label(title_frame, text="Rally Setup Calculator with RallyWorks+ Optimization",
                                 font=('Segoe UI', 10),
                                 bg=self.bg_color, fg='#888888')
        subtitle_label.pack(anchor='w')

    def create_selection_area(self, parent):
        """Create the car and stage selection area."""
        selection_frame = ttk.Frame(parent)
        selection_frame.pack(fill=tk.X, pady=(0, 15))

        # Car selection
        car_frame = ttk.LabelFrame(selection_frame, text="Car", padding="10")
        car_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.car_var = tk.StringVar()
        car_list = self.calculator.get_car_list()
        if car_list:
            self.car_var.set(car_list[0])

        self.car_combo = ttk.Combobox(car_frame, textvariable=self.car_var,
                                      values=car_list, state="readonly", width=35)
        self.car_combo.pack(fill=tk.X)
        self.car_combo.bind('<<ComboboxSelected>>', lambda e: self.on_car_selected())

        # Style the dropdown list
        self.root.option_add('*TCombobox*Listbox.background', self.card_bg)
        self.root.option_add('*TCombobox*Listbox.foreground', self.fg_color)
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.highlight_color)
        self.root.option_add('*TCombobox*Listbox.selectForeground', self.fg_color)

        # Car info label
        self.car_info_label = ttk.Label(car_frame, text="", style='Subtitle.TLabel')
        self.car_info_label.pack(anchor='w', pady=(5, 0))

        # Stage selection
        stage_frame = ttk.LabelFrame(selection_frame, text="Stage", padding="10")
        stage_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.stage_var = tk.StringVar()
        stage_list = self.calculator.get_stage_list()
        if stage_list:
            self.stage_var.set(stage_list[0])

        self.stage_combo = ttk.Combobox(stage_frame, textvariable=self.stage_var,
                                        values=stage_list, state="readonly", width=35)
        self.stage_combo.pack(fill=tk.X)
        self.stage_combo.bind('<<ComboboxSelected>>', lambda e: self.on_stage_selected())

        # Stage info label
        self.stage_info_label = ttk.Label(stage_frame, text="", style='Subtitle.TLabel')
        self.stage_info_label.pack(anchor='w', pady=(5, 0))

        # Load button frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # Selection status label
        self.selection_status = tk.Label(button_frame, text="",
                                         font=('Segoe UI', 9),
                                         bg=self.bg_color, fg='#888888')
        self.selection_status.pack(side=tk.LEFT, padx=(0, 15))

        # Load Setup button (ACR red style)
        self.load_button = tk.Button(button_frame, text="LOAD SETUP",
                                     font=('Segoe UI', 10, 'bold'),
                                     bg=self.accent_color, fg='white',
                                     activebackground='#C62828',
                                     activeforeground='white',
                                     relief='flat', padx=25, pady=8,
                                     cursor='hand2',
                                     command=self.load_setup)
        self.load_button.pack(side=tk.LEFT)

        # RallyWorks+ toggle button
        self.rallyworks_button = tk.Button(button_frame, text="RALLYWORKS+",
                                           font=('Segoe UI', 10, 'bold'),
                                           bg='#3A3A3A', fg='#666666',
                                           activebackground='#4A4A4A',
                                           activeforeground='#888888',
                                           relief='flat', padx=20, pady=8,
                                           state='disabled',
                                           cursor='hand2',
                                           command=self.toggle_rallyworks)
        self.rallyworks_button.pack(side=tk.LEFT, padx=(10, 0))

        # Spacer
        spacer = tk.Frame(button_frame, bg=self.bg_color, width=30)
        spacer.pack(side=tk.LEFT)

        # Save Setup button
        self.save_button = tk.Button(button_frame, text="SAVE",
                                     font=('Segoe UI', 9, 'bold'),
                                     bg='#2E7D32', fg='white',
                                     activebackground='#1B5E20',
                                     activeforeground='white',
                                     relief='flat', padx=15, pady=8,
                                     state='disabled',
                                     cursor='hand2',
                                     command=self.save_setup_dialog)
        self.save_button.pack(side=tk.LEFT, padx=(0, 5))

        # Load Saved Setup button
        self.load_saved_button = tk.Button(button_frame, text="LOAD SAVED",
                                           font=('Segoe UI', 9, 'bold'),
                                           bg='#1565C0', fg='white',
                                           activebackground='#0D47A1',
                                           activeforeground='white',
                                           relief='flat', padx=15, pady=8,
                                           cursor='hand2',
                                           command=self.load_saved_setup_dialog)
        self.load_saved_button.pack(side=tk.LEFT)

        # Initialize selection status
        self.update_selection_status()

    def create_results_area(self, parent):
        """Create the scrollable results area."""
        # Surface indicator
        self.surface_frame = tk.Frame(parent, bg=self.bg_color)
        self.surface_frame.pack(fill=tk.X, pady=(0, 10))

        self.surface_label = tk.Label(self.surface_frame, text="GRAVEL",
                                      font=('Segoe UI', 14, 'bold'),
                                      bg=self.bg_color, fg=self.accent_color)
        self.surface_label.pack(anchor='w')

        # Create canvas with scrollbar for results
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)

        self.results_frame = ttk.Frame(self.canvas)

        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.results_frame, anchor="nw")

        # Bind events for scrolling
        self.results_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    def on_frame_configure(self, event):
        """Update scroll region when frame size changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """Update frame width when canvas size changes."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_car_selected(self):
        """Handle car selection change."""
        car = self.car_var.get()
        if car:
            car_info = self.calculator.get_car_info(car)
            if car_info:
                self.car_info_label.config(text=f"{car_info.car_class} | {car_info.drivetrain}")
            else:
                self.car_info_label.config(text="")
        # Remove focus from combobox to prevent visual issues
        self.root.focus_set()
        self.update_selection_status()

    def on_stage_selected(self):
        """Handle stage selection change."""
        stage = self.stage_var.get()
        if stage:
            stage_info = self.calculator.get_stage_info(stage)
            if stage_info:
                self.stage_info_label.config(text=f"{stage_info.location} | {stage_info.length}")
        # Remove focus from combobox to prevent visual issues
        self.root.focus_set()
        self.update_selection_status()

    def update_selection_status(self):
        """Update the selection status text."""
        car = self.car_var.get()
        stage = self.stage_var.get()

        if car and stage:
            surface = self.calculator.get_surface_for_stage(stage)
            self.selection_status.config(
                text=f"Selected: {car} on {stage} ({surface.capitalize()})"
            )
        elif car:
            self.selection_status.config(text=f"Selected: {car} - Choose a stage")
        elif stage:
            self.selection_status.config(text=f"Selected: {stage} - Choose a car")
        else:
            self.selection_status.config(text="Select a car and stage")

    def load_setup(self):
        """Load and display the setup for current selection."""
        car = self.car_var.get()
        stage = self.stage_var.get()

        if not car or not stage:
            return

        # Get setup
        setup = self.calculator.get_setup_for_stage(car, stage)
        if setup:
            # Store current state
            self.current_setup = setup
            self.current_car = car
            self.current_surface = setup.surface
            self.rallyworks_mode = False

            # Create editable setup from baseline
            self.editable_setup = EditableSetup(setup)
            self.entry_widgets = {}

            # Update surface indicator
            surface = setup.surface.upper()
            if surface == "GRAVEL":
                self.surface_label.config(text="GRAVEL SETUP (Editable)", fg="#D4A574")
            else:
                self.surface_label.config(text="TARMAC SETUP (Editable)", fg="#7CB9E8")

            # Check if RallyWorks+ is available for this car/surface
            if self.dirt_converter.has_rallyworks_setup(car, setup.surface):
                self.rallyworks_button.config(
                    state='normal',
                    bg='#5DADE2',  # Blue color
                    fg='white',
                    activebackground='#3498DB',
                    activeforeground='white'
                )
            else:
                self.rallyworks_button.config(
                    state='disabled',
                    bg='#3A3A3A',
                    fg='#666666'
                )

            # Enable save button
            self.save_button.config(state='normal')

            # Display editable setup
            self.display_editable_setup()

    def toggle_rallyworks(self):
        """Toggle between editable view and comparison view with RallyWorks+ suggestions."""
        if not self.current_setup or not self.editable_setup:
            return

        # Save current values from entry widgets before switching
        self.save_entries_to_editable()

        self.rallyworks_mode = not self.rallyworks_mode

        if self.rallyworks_mode:
            # Switch to comparison view (User values + RallyWorks+ suggestions)
            self.rallyworks_button.config(
                text="HIDE RALLYWORKS+",
                bg=self.rw_increase_color,
                fg='white',
                activebackground='#3498DB'
            )
            surface = self.current_surface.upper()
            if surface == "GRAVEL":
                self.surface_label.config(text="GRAVEL SETUP (+ RallyWorks+)", fg="#D4A574")
            else:
                self.surface_label.config(text="TARMAC SETUP (+ RallyWorks+)", fg="#7CB9E8")

            # Display comparison view with user values vs RallyWorks+ suggestions
            rallyworks_setup = self.dirt_converter.get_rallyworks_setup(
                self.current_car, self.current_surface
            )
            if rallyworks_setup:
                self.display_editable_with_rallyworks(rallyworks_setup)
        else:
            # Switch back to editable view
            self.rallyworks_button.config(
                text="RALLYWORKS+",
                bg='#5DADE2',
                fg='white',
                activebackground='#3498DB'
            )
            surface = self.current_surface.upper()
            if surface == "GRAVEL":
                self.surface_label.config(text="GRAVEL SETUP (Editable)", fg="#D4A574")
            else:
                self.surface_label.config(text="TARMAC SETUP (Editable)", fg="#7CB9E8")

            # Display editable setup
            self.display_editable_setup()

    def save_entries_to_editable(self):
        """Save current entry widget values to editable setup."""
        if not self.editable_setup:
            return
        for key, entry in self.entry_widgets.items():
            try:
                value = entry.get()
                self.editable_setup.set(key, value)
            except (tk.TclError, ValueError):
                pass  # Keep existing value if entry is invalid

    def get_saved_setups_dir(self):
        """Get the directory for saved setups."""
        script_dir = Path(__file__).parent.parent
        saved_dir = script_dir / "saved_setups"
        saved_dir.mkdir(exist_ok=True)
        return saved_dir

    def save_setup_dialog(self):
        """Show save dialog and save current setup to JSON."""
        if not self.editable_setup:
            messagebox.showwarning("No Setup", "No setup loaded to save.")
            return

        # Save current entry values first
        self.save_entries_to_editable()

        # Generate default filename
        car_name = self.current_car.replace(" ", "_").replace("/", "-")
        surface = self.current_surface
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"{car_name}_{surface}_{timestamp}.json"

        # Show save dialog
        saved_dir = self.get_saved_setups_dir()
        filepath = filedialog.asksaveasfilename(
            initialdir=saved_dir,
            initialfile=default_name,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Setup"
        )

        if not filepath:
            return

        # Build setup data from editable setup (user's modified values)
        editable_dict = self.editable_setup.to_dict()
        setup_data = {
            "metadata": {
                "car": self.current_car,
                "surface": self.current_surface,
                "saved_at": datetime.now().isoformat(),
                "version": "1.0",
                "custom": True  # Mark as user-modified
            },
            **editable_dict
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(setup_data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Saved", f"Setup saved to:\n{Path(filepath).name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save setup:\n{str(e)}")

    def load_saved_setup_dialog(self):
        """Show load dialog and load a saved setup from JSON."""
        saved_dir = self.get_saved_setups_dir()

        filepath = filedialog.askopenfilename(
            initialdir=saved_dir,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Saved Setup"
        )

        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                setup_data = json.load(f)

            # Validate structure
            if "metadata" not in setup_data:
                messagebox.showerror("Error", "Invalid setup file: missing metadata")
                return

            # Create a custom setup object from loaded data
            loaded_setup = LoadedSetup(setup_data)

            # Update UI
            self.current_setup = loaded_setup
            self.current_car = setup_data["metadata"].get("car", "Unknown")
            self.current_surface = setup_data["metadata"].get("surface", "gravel")
            self.rallyworks_mode = False

            # Create editable setup from loaded data
            self.editable_setup = EditableSetup(loaded_setup)
            self.entry_widgets = {}

            # Update surface indicator
            surface = self.current_surface.upper()
            if surface == "GRAVEL":
                self.surface_label.config(text=f"GRAVEL SETUP (Loaded - Editable)", fg="#D4A574")
            else:
                self.surface_label.config(text=f"TARMAC SETUP (Loaded - Editable)", fg="#7CB9E8")

            # Check if RallyWorks+ is available for this car/surface
            if self.dirt_converter.has_rallyworks_setup(self.current_car, self.current_surface):
                self.rallyworks_button.config(
                    state='normal',
                    bg='#5DADE2',
                    fg='white',
                    activebackground='#3498DB',
                    activeforeground='white'
                )
            else:
                self.rallyworks_button.config(
                    state='disabled',
                    bg='#3A3A3A',
                    fg='#666666'
                )

            # Enable save button
            self.save_button.config(state='normal')

            # Update selection display
            self.selection_status.config(
                text=f"Loaded: {self.current_car} ({self.current_surface})"
            )

            # Display the editable setup
            self.display_editable_setup()

            messagebox.showinfo("Loaded", f"Setup loaded:\n{Path(filepath).name}")

        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load setup:\n{str(e)}")

    def on_selection_changed(self):
        """Legacy method - now just updates info labels."""
        self.on_car_selected()
        self.on_stage_selected()
        self.load_setup()

    def display_setup(self, setup):
        """Display the setup data in organized sections (read-only)."""
        # Clear existing content
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        # Create sections
        self.create_drivetrain_section(setup)
        self.create_suspension_section(setup)
        self.create_dampers_section(setup)
        self.create_tyres_section(setup)
        self.create_brakes_section(setup)

    def display_editable_setup(self):
        """Display the setup with editable input fields."""
        if not self.editable_setup:
            return

        # Clear existing content
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        self.entry_widgets = {}

        # Instructions
        info_frame = tk.Frame(self.results_frame, bg=self.card_bg, pady=8, padx=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_label = tk.Label(info_frame, text="Edit values below. Changes are validated to ACR ranges.",
                             font=('Segoe UI', 9, 'italic'),
                             bg=self.card_bg, fg='#888888')
        info_label.pack(side=tk.LEFT)

        # Create editable sections
        self.create_editable_suspension_section()
        self.create_editable_dampers_section()
        self.create_editable_tyres_section()
        self.create_editable_brakes_section()

    def display_editable_with_rallyworks(self, rw_setup):
        """Display editable setup with RallyWorks+ suggestions shown alongside."""
        if not self.editable_setup:
            return

        # Clear existing content
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        self.entry_widgets = {}

        # Legend
        legend_frame = tk.Frame(self.results_frame, bg=self.card_bg, pady=8, padx=10)
        legend_frame.pack(fill=tk.X, pady=(0, 10))

        legend_label = tk.Label(legend_frame, text="Legend: ",
                               font=('Segoe UI', 9),
                               bg=self.card_bg, fg='#888888')
        legend_label.pack(side=tk.LEFT)

        your_legend = tk.Label(legend_frame, text="Your Setup (Editable)",
                              font=('Segoe UI', 9, 'bold'),
                              bg=self.card_bg, fg='#FFFFFF')
        your_legend.pack(side=tk.LEFT, padx=(0, 15))

        rw_legend = tk.Label(legend_frame, text="RallyWorks+ Suggestion",
                            font=('Segoe UI', 9, 'bold'),
                            bg=self.card_bg, fg=self.rw_increase_color)
        rw_legend.pack(side=tk.LEFT, padx=(0, 15))

        source_label = tk.Label(legend_frame, text=f"(Source: {rw_setup.source})",
                               font=('Segoe UI', 8, 'italic'),
                               bg=self.card_bg, fg='#666666')
        source_label.pack(side=tk.LEFT)

        # Create editable sections with RW suggestions
        self.create_editable_suspension_with_rw(rw_setup)
        self.create_editable_dampers_with_rw(rw_setup)
        self.create_editable_tyres_with_rw(rw_setup)
        self.create_editable_brakes_with_rw(rw_setup)

    def create_editable_entry(self, parent, key, unit, row, col=0, width=8):
        """Create an editable entry field with validation."""
        min_val, max_val = self.editable_setup.get_range(key)
        current_val = self.editable_setup.get(key, 0)

        # Frame for entry and unit
        entry_frame = tk.Frame(parent, bg=self.card_bg)
        entry_frame.grid(row=row, column=col, sticky='w', padx=(0, 15), pady=2)

        # Entry widget
        entry_var = tk.StringVar(value=f"{current_val:.1f}" if isinstance(current_val, float) and '.' in str(current_val) else str(int(current_val)))
        entry = tk.Entry(entry_frame, textvariable=entry_var, width=width,
                        font=('Consolas', 10),
                        bg=self.section_bg, fg=self.fg_color,
                        insertbackground=self.fg_color,
                        relief='flat', bd=2)
        entry.pack(side=tk.LEFT)

        # Unit label
        unit_label = tk.Label(entry_frame, text=unit, font=('Segoe UI', 9),
                             bg=self.card_bg, fg='#888888')
        unit_label.pack(side=tk.LEFT, padx=(3, 0))

        # Range tooltip
        range_label = tk.Label(entry_frame, text=f"({min_val}-{max_val})",
                              font=('Segoe UI', 8),
                              bg=self.card_bg, fg='#555555')
        range_label.pack(side=tk.LEFT, padx=(5, 0))

        # Bind validation on focus out
        def on_focus_out(e):
            try:
                val = float(entry.get())
                validated = self.editable_setup.set(key, val)
                entry_var.set(f"{validated:.1f}" if '.' in str(validated) else str(int(validated)))
            except ValueError:
                entry_var.set(f"{current_val:.1f}" if isinstance(current_val, float) else str(int(current_val)))

        entry.bind('<FocusOut>', on_focus_out)

        self.entry_widgets[key] = entry
        return entry

    def create_editable_entry_with_rw(self, parent, key, unit, rw_value, row, col=0, width=8):
        """Create an editable entry with RallyWorks+ suggestion shown."""
        min_val, max_val = self.editable_setup.get_range(key)
        current_val = self.editable_setup.get(key, 0)

        # Frame for entry, unit, and RW suggestion
        entry_frame = tk.Frame(parent, bg=self.card_bg)
        entry_frame.grid(row=row, column=col, sticky='w', padx=(0, 10), pady=2)

        # Entry widget
        if isinstance(current_val, float) and (current_val != int(current_val)):
            entry_var = tk.StringVar(value=f"{current_val:.2f}")
        else:
            entry_var = tk.StringVar(value=str(int(current_val)))

        entry = tk.Entry(entry_frame, textvariable=entry_var, width=width,
                        font=('Consolas', 10),
                        bg=self.section_bg, fg=self.fg_color,
                        insertbackground=self.fg_color,
                        relief='flat', bd=2)
        entry.pack(side=tk.LEFT)

        # Unit label
        unit_label = tk.Label(entry_frame, text=unit, font=('Segoe UI', 9),
                             bg=self.card_bg, fg='#888888')
        unit_label.pack(side=tk.LEFT, padx=(3, 0))

        # RallyWorks+ suggestion
        arrow, color = self.get_comparison_color(current_val, rw_value)
        if isinstance(rw_value, float) and (rw_value != int(rw_value)):
            rw_text = f"{arrow} {rw_value:.2f}"
        else:
            rw_text = f"{arrow} {int(rw_value)}"

        rw_label = tk.Label(entry_frame, text=rw_text,
                           font=('Consolas', 9),
                           bg=self.card_bg, fg=color)
        rw_label.pack(side=tk.LEFT, padx=(10, 0))

        # Bind validation on focus out
        def on_focus_out(e):
            try:
                val = float(entry.get())
                validated = self.editable_setup.set(key, val)
                if isinstance(validated, float) and (validated != int(validated)):
                    entry_var.set(f"{validated:.2f}")
                else:
                    entry_var.set(str(int(validated)))
                # Update RW comparison
                arrow, color = self.get_comparison_color(validated, rw_value)
                if isinstance(rw_value, float) and (rw_value != int(rw_value)):
                    rw_label.config(text=f"{arrow} {rw_value:.2f}", fg=color)
                else:
                    rw_label.config(text=f"{arrow} {int(rw_value)}", fg=color)
            except ValueError:
                pass

        entry.bind('<FocusOut>', on_focus_out)

        self.entry_widgets[key] = entry
        return entry

    def create_editable_suspension_section(self):
        """Create editable suspension section."""
        content = self.create_section_frame("SUSPENSION")

        row = 0

        # ARBs
        tk.Label(content, text="Front ARB", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'arb_front', 'N/m', row, col=1)
        row += 1

        tk.Label(content, text="Rear ARB", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'arb_rear', 'N/m', row, col=1)
        row += 1

        # Springs header
        header = tk.Label(content, text="Springs", font=('Segoe UI', 10, 'bold'),
                         bg=self.card_bg, fg='#AAAAAA')
        header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(8, 4))
        row += 1

        tk.Label(content, text="Front", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'spring_front', 'N/m', row, col=1)
        row += 1

        tk.Label(content, text="Rear", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'spring_rear', 'N/m', row, col=1)
        row += 1

        # Ride Height header
        header = tk.Label(content, text="Ride Height", font=('Segoe UI', 10, 'bold'),
                         bg=self.card_bg, fg='#AAAAAA')
        header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(8, 4))
        row += 1

        tk.Label(content, text="Front", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'ride_height_front', 'mm', row, col=1)
        row += 1

        tk.Label(content, text="Rear", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'ride_height_rear', 'mm', row, col=1)

    def create_editable_dampers_section(self):
        """Create editable dampers section."""
        content = self.create_section_frame("DAMPERS")

        row = 0

        # Front header
        header = tk.Label(content, text="Front", font=('Segoe UI', 10, 'bold'),
                         bg=self.card_bg, fg='#AAAAAA')
        header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(0, 4))
        row += 1

        tk.Label(content, text="Slow Bump", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'front_slow_bump', 'Ns/m', row, col=1)
        row += 1

        tk.Label(content, text="Slow Rebound", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'front_slow_rebound', 'Ns/m', row, col=1)
        row += 1

        tk.Label(content, text="Fast Bump", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'front_fast_bump', 'Ns/m', row, col=1)
        row += 1

        tk.Label(content, text="Fast Rebound", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'front_fast_rebound', 'Ns/m', row, col=1)
        row += 1

        # Rear header
        header = tk.Label(content, text="Rear", font=('Segoe UI', 10, 'bold'),
                         bg=self.card_bg, fg='#AAAAAA')
        header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(8, 4))
        row += 1

        tk.Label(content, text="Slow Bump", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'rear_slow_bump', 'Ns/m', row, col=1)
        row += 1

        tk.Label(content, text="Slow Rebound", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'rear_slow_rebound', 'Ns/m', row, col=1)
        row += 1

        tk.Label(content, text="Fast Bump", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'rear_fast_bump', 'Ns/m', row, col=1)
        row += 1

        tk.Label(content, text="Fast Rebound", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'rear_fast_rebound', 'Ns/m', row, col=1)

    def create_editable_tyres_section(self):
        """Create editable tyres section."""
        content = self.create_section_frame("TYRES")

        row = 0

        # Front header
        header = tk.Label(content, text="Front", font=('Segoe UI', 10, 'bold'),
                         bg=self.card_bg, fg='#AAAAAA')
        header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(0, 4))
        row += 1

        tk.Label(content, text="Pressure", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'pressure_front', 'PSI', row, col=1)
        row += 1

        tk.Label(content, text="Camber", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'camber_front', '°', row, col=1)
        row += 1

        tk.Label(content, text="Toe", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'toe_front', '°', row, col=1)
        row += 1

        # Rear header
        header = tk.Label(content, text="Rear", font=('Segoe UI', 10, 'bold'),
                         bg=self.card_bg, fg='#AAAAAA')
        header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(8, 4))
        row += 1

        tk.Label(content, text="Pressure", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'pressure_rear', 'PSI', row, col=1)
        row += 1

        tk.Label(content, text="Camber", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'camber_rear', '°', row, col=1)
        row += 1

        tk.Label(content, text="Toe", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'toe_rear', '°', row, col=1)

    def create_editable_brakes_section(self):
        """Create editable brakes section."""
        content = self.create_section_frame("BRAKES")

        row = 0

        tk.Label(content, text="Brake Bias", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'brake_bias', '% front', row, col=1)

    def create_editable_suspension_with_rw(self, rw_setup):
        """Create editable suspension section with RallyWorks+ suggestions."""
        content = self.create_section_frame("SUSPENSION")

        row = 0

        # ARBs
        tk.Label(content, text="Front ARB", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'arb_front', 'N/m', rw_setup.arb_front, row, col=1)
        row += 1

        tk.Label(content, text="Rear ARB", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'arb_rear', 'N/m', rw_setup.arb_rear, row, col=1)
        row += 1

        # Springs header
        header = tk.Label(content, text="Springs", font=('Segoe UI', 10, 'bold'),
                         bg=self.card_bg, fg='#AAAAAA')
        header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(8, 4))
        row += 1

        tk.Label(content, text="Front", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'spring_front', 'N/m', rw_setup.spring_front, row, col=1)
        row += 1

        tk.Label(content, text="Rear", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'spring_rear', 'N/m', rw_setup.spring_rear, row, col=1)
        row += 1

        # Ride Height header
        header = tk.Label(content, text="Ride Height", font=('Segoe UI', 10, 'bold'),
                         bg=self.card_bg, fg='#AAAAAA')
        header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(8, 4))
        row += 1

        tk.Label(content, text="Front", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'ride_height_front', 'mm', rw_setup.ride_height_front, row, col=1)
        row += 1

        tk.Label(content, text="Rear", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'ride_height_rear', 'mm', rw_setup.ride_height_rear, row, col=1)

    def create_editable_dampers_with_rw(self, rw_setup):
        """Create editable dampers section with RallyWorks+ suggestions."""
        content = self.create_section_frame("DAMPERS")

        row = 0

        # Front header
        header = tk.Label(content, text="Front", font=('Segoe UI', 10, 'bold'),
                         bg=self.card_bg, fg='#AAAAAA')
        header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(0, 4))
        row += 1

        tk.Label(content, text="Slow Bump", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'front_slow_bump', 'Ns/m', rw_setup.front_slow_bump, row, col=1)
        row += 1

        tk.Label(content, text="Slow Rebound", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'front_slow_rebound', 'Ns/m', rw_setup.front_slow_rebound, row, col=1)
        row += 1

        tk.Label(content, text="Fast Bump", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'front_fast_bump', 'Ns/m', rw_setup.front_fast_bump, row, col=1)
        row += 1

        tk.Label(content, text="Fast Rebound", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'front_fast_rebound', 'Ns/m', rw_setup.front_fast_rebound, row, col=1)
        row += 1

        # Rear header
        header = tk.Label(content, text="Rear", font=('Segoe UI', 10, 'bold'),
                         bg=self.card_bg, fg='#AAAAAA')
        header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(8, 4))
        row += 1

        tk.Label(content, text="Slow Bump", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'rear_slow_bump', 'Ns/m', rw_setup.rear_slow_bump, row, col=1)
        row += 1

        tk.Label(content, text="Slow Rebound", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'rear_slow_rebound', 'Ns/m', rw_setup.rear_slow_rebound, row, col=1)
        row += 1

        tk.Label(content, text="Fast Bump", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'rear_fast_bump', 'Ns/m', rw_setup.rear_fast_bump, row, col=1)
        row += 1

        tk.Label(content, text="Fast Rebound", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'rear_fast_rebound', 'Ns/m', rw_setup.rear_fast_rebound, row, col=1)

    def create_editable_tyres_with_rw(self, rw_setup):
        """Create editable tyres section with RallyWorks+ suggestions."""
        content = self.create_section_frame("TYRES")

        row = 0

        # Front header
        header = tk.Label(content, text="Front", font=('Segoe UI', 10, 'bold'),
                         bg=self.card_bg, fg='#AAAAAA')
        header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(0, 4))
        row += 1

        tk.Label(content, text="Pressure", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        # No RW suggestion for pressure
        self.create_editable_entry(content, 'pressure_front', 'PSI', row, col=1)
        row += 1

        tk.Label(content, text="Camber", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'camber_front', '°', rw_setup.camber_front, row, col=1)
        row += 1

        tk.Label(content, text="Toe", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'toe_front', '°', rw_setup.toe_front, row, col=1)
        row += 1

        # Rear header
        header = tk.Label(content, text="Rear", font=('Segoe UI', 10, 'bold'),
                         bg=self.card_bg, fg='#AAAAAA')
        header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(8, 4))
        row += 1

        tk.Label(content, text="Pressure", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry(content, 'pressure_rear', 'PSI', row, col=1)
        row += 1

        tk.Label(content, text="Camber", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'camber_rear', '°', rw_setup.camber_rear, row, col=1)
        row += 1

        tk.Label(content, text="Toe", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'toe_rear', '°', rw_setup.toe_rear, row, col=1)

    def create_editable_brakes_with_rw(self, rw_setup):
        """Create editable brakes section with RallyWorks+ suggestions."""
        content = self.create_section_frame("BRAKES")

        row = 0

        tk.Label(content, text="Brake Bias", font=('Segoe UI', 9),
                bg=self.card_bg, fg='#888888').grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.create_editable_entry_with_rw(content, 'brake_bias', '% front', rw_setup.brake_bias, row, col=1)

    def display_comparison_setup(self, acr_setup, rw_setup):
        """Display both ACR and RallyWorks+ values side by side."""
        # Clear existing content
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        # Legend
        legend_frame = tk.Frame(self.results_frame, bg=self.card_bg, pady=8, padx=10)
        legend_frame.pack(fill=tk.X, pady=(0, 10))

        legend_label = tk.Label(legend_frame, text="Legend: ",
                               font=('Segoe UI', 9),
                               bg=self.card_bg, fg='#888888')
        legend_label.pack(side=tk.LEFT)

        acr_legend = tk.Label(legend_frame, text="ACR Default",
                             font=('Segoe UI', 9, 'bold'),
                             bg=self.card_bg, fg=self.acr_value_color)
        acr_legend.pack(side=tk.LEFT, padx=(0, 15))

        increase_legend = tk.Label(legend_frame, text="↑ Increase",
                                  font=('Segoe UI', 9, 'bold'),
                                  bg=self.card_bg, fg=self.rw_increase_color)
        increase_legend.pack(side=tk.LEFT, padx=(0, 10))

        decrease_legend = tk.Label(legend_frame, text="↓ Decrease",
                                  font=('Segoe UI', 9, 'bold'),
                                  bg=self.card_bg, fg=self.rw_decrease_color)
        decrease_legend.pack(side=tk.LEFT, padx=(0, 15))

        source_label = tk.Label(legend_frame, text=f"(Source: {rw_setup.source})",
                               font=('Segoe UI', 8, 'italic'),
                               bg=self.card_bg, fg='#666666')
        source_label.pack(side=tk.LEFT)

        # Create comparison sections
        self.create_comparison_drivetrain(acr_setup, rw_setup)
        self.create_comparison_suspension(acr_setup, rw_setup)
        self.create_comparison_dampers(acr_setup, rw_setup)
        self.create_comparison_tyres(acr_setup, rw_setup)
        self.create_comparison_brakes(acr_setup, rw_setup)

    def add_comparison_value(self, parent, key, acr_value, rw_value, row, col=0):
        """Add a key with both ACR (green) and RallyWorks+ (colored by direction) values."""
        key_label = tk.Label(parent, text=key, font=('Segoe UI', 9),
                            bg=self.card_bg, fg='#888888', anchor='w')
        key_label.grid(row=row, column=col*3, sticky='w', padx=(0, 10), pady=2)

        acr_label = tk.Label(parent, text=str(acr_value), font=('Consolas', 10),
                            bg=self.card_bg, fg=self.acr_value_color, anchor='w')
        acr_label.grid(row=row, column=col*3+1, sticky='w', padx=(0, 5), pady=2)

        # Only show RW value if different from ACR
        if str(rw_value) != str(acr_value):
            # Determine direction and color
            arrow, color = self.get_comparison_color(acr_value, rw_value)
            rw_label = tk.Label(parent, text=f"{arrow} {rw_value}", font=('Consolas', 10),
                               bg=self.card_bg, fg=color, anchor='w')
            rw_label.grid(row=row, column=col*3+2, sticky='w', padx=(0, 20), pady=2)

    def get_comparison_color(self, acr_value, rw_value):
        """
        Get the arrow direction and color for a comparison.
        Blue (↑) for increase, Red (↓) for decrease, Gray for same.
        """
        try:
            # Try to extract numeric values for comparison
            acr_num = self.extract_number(acr_value)
            rw_num = self.extract_number(rw_value)

            if acr_num is not None and rw_num is not None:
                diff = rw_num - acr_num
                if abs(diff) < 0.01:
                    return "=", self.rw_same_color
                elif diff > 0:
                    return "↑", self.rw_increase_color
                else:
                    return "↓", self.rw_decrease_color
        except:
            pass

        return "→", self.rw_same_color

    def extract_number(self, value):
        """Extract a number from a string value."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove common units and symbols
            cleaned = value.replace('N/m', '').replace('Nm', '').replace('mm', '')
            cleaned = cleaned.replace('°', '').replace('%', '').replace(' ', '')
            cleaned = cleaned.replace('front', '').replace('Ns/m', '')
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    def create_comparison_drivetrain(self, acr_setup, rw_setup):
        """Create drivetrain comparison section."""
        content = self.create_section_frame("DRIVETRAIN")
        drivetrain = acr_setup.get_drivetrain()

        row = 0

        # Gear Set
        if "Gear Set" in drivetrain:
            self.add_comparison_value(content, "Gear Set",
                                      drivetrain["Gear Set"],
                                      rw_setup.gear_set_recommendation, row)
            row += 1

        # Front Bias
        if "Front Bias" in drivetrain:
            self.add_comparison_value(content, "Front Bias",
                                      drivetrain["Front Bias"],
                                      f"{rw_setup.front_bias}%", row)
            row += 1

        # Centre Diff Ratio
        if "Centre Diff Ratio" in drivetrain:
            self.add_comparison_value(content, "Centre Diff Ratio",
                                      drivetrain["Centre Diff Ratio"],
                                      rw_setup.centre_diff_ratio, row)
            row += 1

        # Front Diff
        if "Front Diff" in drivetrain:
            header = tk.Label(content, text="Front Diff", font=('Segoe UI', 10, 'bold'),
                             bg=self.card_bg, fg='#AAAAAA')
            header.grid(row=row, column=0, columnspan=6, sticky='w', pady=(8, 4))
            row += 1

            fd = drivetrain["Front Diff"]
            if "LSD Ramp Angle" in fd:
                self.add_comparison_value(content, "LSD Ramp Angle",
                                          fd["LSD Ramp Angle"],
                                          f"{rw_setup.front_lsd_ramp_accel}_{rw_setup.front_lsd_ramp_decel}", row)
                row += 1
            if "LSD Preload" in fd:
                self.add_comparison_value(content, "LSD Preload",
                                          fd["LSD Preload"],
                                          f"{rw_setup.front_lsd_preload} Nm", row)
                row += 1

        # Rear Diff
        if "Rear Diff" in drivetrain:
            header = tk.Label(content, text="Rear Diff", font=('Segoe UI', 10, 'bold'),
                             bg=self.card_bg, fg='#AAAAAA')
            header.grid(row=row, column=0, columnspan=6, sticky='w', pady=(8, 4))
            row += 1

            rd = drivetrain["Rear Diff"]
            if "LSD Ramp Angle" in rd:
                self.add_comparison_value(content, "LSD Ramp Angle",
                                          rd["LSD Ramp Angle"],
                                          f"{rw_setup.rear_lsd_ramp_accel}_{rw_setup.rear_lsd_ramp_decel}", row)
                row += 1
            if "LSD Preload" in rd:
                self.add_comparison_value(content, "LSD Preload",
                                          rd["LSD Preload"],
                                          f"{rw_setup.rear_lsd_preload} Nm", row)
                row += 1

    def create_comparison_suspension(self, acr_setup, rw_setup):
        """Create suspension comparison section."""
        content = self.create_section_frame("SUSPENSION")
        suspension = acr_setup.get_suspension()

        row = 0

        # ARBs
        if "Front ARB" in suspension:
            self.add_comparison_value(content, "Front ARB",
                                      suspension["Front ARB"],
                                      f"{rw_setup.arb_front} N/m", row)
            row += 1
        if "Rear ARB" in suspension:
            self.add_comparison_value(content, "Rear ARB",
                                      suspension["Rear ARB"],
                                      f"{rw_setup.arb_rear} N/m", row)
            row += 1

        # Springs
        if "Springs" in suspension:
            header = tk.Label(content, text="Springs", font=('Segoe UI', 10, 'bold'),
                             bg=self.card_bg, fg='#AAAAAA')
            header.grid(row=row, column=0, columnspan=6, sticky='w', pady=(8, 4))
            row += 1

            springs = suspension["Springs"]
            # Front springs (FL/FR typically same)
            fl_val = springs.get("FL", "N/A")
            self.add_comparison_value(content, "Front",
                                      fl_val,
                                      f"{rw_setup.spring_front} N/m", row)
            row += 1
            # Rear springs
            rl_val = springs.get("RL", "N/A")
            self.add_comparison_value(content, "Rear",
                                      rl_val,
                                      f"{rw_setup.spring_rear} N/m", row)
            row += 1

        # Ride Height
        if "Ride Height" in suspension:
            header = tk.Label(content, text="Ride Height", font=('Segoe UI', 10, 'bold'),
                             bg=self.card_bg, fg='#AAAAAA')
            header.grid(row=row, column=0, columnspan=6, sticky='w', pady=(8, 4))
            row += 1

            rh = suspension["Ride Height"]
            fl_val = rh.get("FL", "N/A")
            self.add_comparison_value(content, "Front",
                                      fl_val,
                                      f"{rw_setup.ride_height_front} mm", row)
            row += 1
            rl_val = rh.get("RL", "N/A")
            self.add_comparison_value(content, "Rear",
                                      rl_val,
                                      f"{rw_setup.ride_height_rear} mm", row)
            row += 1

    def create_comparison_dampers(self, acr_setup, rw_setup):
        """Create dampers comparison section with actual values."""
        content = self.create_section_frame("DAMPERS")
        dampers = acr_setup.get_dampers()

        row = 0

        # Headers
        label = tk.Label(content, text="", font=('Segoe UI', 9, 'bold'),
                        bg=self.card_bg, fg='#888888')
        label.grid(row=row, column=0, sticky='w', padx=(0, 10), pady=(0, 5))

        label = tk.Label(content, text="Slow Bump", font=('Segoe UI', 9, 'bold'),
                        bg=self.card_bg, fg='#888888')
        label.grid(row=row, column=1, columnspan=2, sticky='w', padx=(0, 10), pady=(0, 5))

        label = tk.Label(content, text="Slow Rebound", font=('Segoe UI', 9, 'bold'),
                        bg=self.card_bg, fg='#888888')
        label.grid(row=row, column=3, columnspan=2, sticky='w', padx=(0, 10), pady=(0, 5))

        label = tk.Label(content, text="Fast Bump", font=('Segoe UI', 9, 'bold'),
                        bg=self.card_bg, fg='#888888')
        label.grid(row=row, column=5, columnspan=2, sticky='w', padx=(0, 10), pady=(0, 5))

        label = tk.Label(content, text="Fast Rebound", font=('Segoe UI', 9, 'bold'),
                        bg=self.card_bg, fg='#888888')
        label.grid(row=row, column=7, columnspan=2, sticky='w', padx=(0, 10), pady=(0, 5))
        row += 1

        # Get RW damper values based on corner
        rw_dampers = {
            "FL": {
                "Slow Bump": rw_setup.front_slow_bump,
                "Slow Rebound": rw_setup.front_slow_rebound,
                "Fast Bump": rw_setup.front_fast_bump,
                "Fast Rebound": rw_setup.front_fast_rebound
            },
            "FR": {
                "Slow Bump": rw_setup.front_slow_bump,
                "Slow Rebound": rw_setup.front_slow_rebound,
                "Fast Bump": rw_setup.front_fast_bump,
                "Fast Rebound": rw_setup.front_fast_rebound
            },
            "RL": {
                "Slow Bump": rw_setup.rear_slow_bump,
                "Slow Rebound": rw_setup.rear_slow_rebound,
                "Fast Bump": rw_setup.rear_fast_bump,
                "Fast Rebound": rw_setup.rear_fast_rebound
            },
            "RR": {
                "Slow Bump": rw_setup.rear_slow_bump,
                "Slow Rebound": rw_setup.rear_slow_rebound,
                "Fast Bump": rw_setup.rear_fast_bump,
                "Fast Rebound": rw_setup.rear_fast_rebound
            }
        }

        for corner in ["FL", "FR", "RL", "RR"]:
            if corner in dampers:
                corner_data = dampers[corner]
                rw_corner = rw_dampers[corner]

                # Corner label
                corner_label = tk.Label(content, text=corner, font=('Segoe UI', 10, 'bold'),
                                       bg=self.card_bg, fg='#AAAAAA')
                corner_label.grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)

                col = 1
                for key in ["Slow Bump", "Slow Rebound", "Fast Bump", "Fast Rebound"]:
                    acr_val = corner_data.get(key, "N/A")
                    rw_val = rw_corner[key]

                    # ACR value
                    val_label = tk.Label(content, text=str(acr_val), font=('Consolas', 10),
                                        bg=self.card_bg, fg=self.acr_value_color)
                    val_label.grid(row=row, column=col, sticky='w', padx=(0, 2), pady=2)

                    # RW value with color based on direction
                    acr_num = self.extract_number(acr_val)
                    if acr_num is not None and rw_val != acr_num:
                        arrow, color = self.get_comparison_color(acr_num, rw_val)
                        rw_label = tk.Label(content, text=f"{arrow}{rw_val}",
                                           font=('Consolas', 9),
                                           bg=self.card_bg, fg=color)
                        rw_label.grid(row=row, column=col+1, sticky='w', padx=(0, 8), pady=2)

                    col += 2

                row += 1

    def create_comparison_tyres(self, acr_setup, rw_setup):
        """Create tyres comparison section."""
        content = self.create_section_frame("TYRES")
        tyres = acr_setup.get_tyres()

        row = 0

        # Headers
        label = tk.Label(content, text="", font=('Segoe UI', 9, 'bold'),
                        bg=self.card_bg, fg='#888888')
        label.grid(row=row, column=0, sticky='w', padx=(0, 15), pady=(0, 5))

        label = tk.Label(content, text="Pressure", font=('Segoe UI', 9, 'bold'),
                        bg=self.card_bg, fg='#888888')
        label.grid(row=row, column=1, sticky='w', padx=(0, 15), pady=(0, 5))

        label = tk.Label(content, text="Camber", font=('Segoe UI', 9, 'bold'),
                        bg=self.card_bg, fg='#888888')
        label.grid(row=row, column=2, columnspan=2, sticky='w', padx=(0, 15), pady=(0, 5))

        label = tk.Label(content, text="Toe", font=('Segoe UI', 9, 'bold'),
                        bg=self.card_bg, fg='#888888')
        label.grid(row=row, column=4, columnspan=2, sticky='w', padx=(0, 15), pady=(0, 5))
        row += 1

        # Get RW values
        rw_camber = {"FL": rw_setup.camber_front, "FR": rw_setup.camber_front,
                     "RL": rw_setup.camber_rear, "RR": rw_setup.camber_rear}
        rw_toe = {"FL": rw_setup.toe_front, "FR": rw_setup.toe_front,
                  "RL": rw_setup.toe_rear, "RR": rw_setup.toe_rear}

        for corner in ["FL", "FR", "RL", "RR"]:
            if corner in tyres:
                corner_data = tyres[corner]

                # Corner label
                corner_label = tk.Label(content, text=corner, font=('Segoe UI', 10, 'bold'),
                                       bg=self.card_bg, fg='#AAAAAA')
                corner_label.grid(row=row, column=0, sticky='w', padx=(0, 15), pady=2)

                # Pressure - ACR only (no DiRT data)
                val = corner_data.get("Pressure", "N/A")
                val_label = tk.Label(content, text=val, font=('Consolas', 10),
                                    bg=self.card_bg, fg=self.acr_value_color)
                val_label.grid(row=row, column=1, sticky='w', padx=(0, 15), pady=2)

                # Camber - ACR
                val = corner_data.get("Camber", "N/A")
                val_label = tk.Label(content, text=val, font=('Consolas', 10),
                                    bg=self.card_bg, fg=self.acr_value_color)
                val_label.grid(row=row, column=2, sticky='w', padx=(0, 2), pady=2)

                # Camber - RW
                rw_val = f"{rw_camber[corner]}°"
                acr_num = self.extract_number(val)
                rw_num = rw_camber[corner]
                if acr_num is not None and abs(rw_num - acr_num) > 0.01:
                    arrow, color = self.get_comparison_color(acr_num, rw_num)
                    rw_label = tk.Label(content, text=f"{arrow} {rw_val}", font=('Consolas', 10),
                                       bg=self.card_bg, fg=color)
                    rw_label.grid(row=row, column=3, sticky='w', padx=(0, 15), pady=2)

                # Toe - ACR
                val = corner_data.get("Toe", "N/A")
                val_label = tk.Label(content, text=val, font=('Consolas', 10),
                                    bg=self.card_bg, fg=self.acr_value_color)
                val_label.grid(row=row, column=4, sticky='w', padx=(0, 2), pady=2)

                # Toe - RW
                rw_val = f"{rw_toe[corner]}°"
                acr_num = self.extract_number(val)
                rw_num = rw_toe[corner]
                if acr_num is not None and abs(rw_num - acr_num) > 0.01:
                    arrow, color = self.get_comparison_color(acr_num, rw_num)
                    rw_label = tk.Label(content, text=f"{arrow} {rw_val}", font=('Consolas', 10),
                                       bg=self.card_bg, fg=color)
                    rw_label.grid(row=row, column=5, sticky='w', padx=(0, 15), pady=2)

                row += 1

        # Note
        note = tk.Label(content, text="(Tyre pressure: No DiRT data)",
                       font=('Segoe UI', 8, 'italic'),
                       bg=self.card_bg, fg='#555555')
        note.grid(row=row, column=0, columnspan=6, sticky='w', pady=(8, 0))

    def create_comparison_brakes(self, acr_setup, rw_setup):
        """Create brakes comparison section."""
        content = self.create_section_frame("BRAKES")
        brakes = acr_setup.get_brakes()

        row = 0

        # Brake Bias
        if "Brake Bias" in brakes:
            self.add_comparison_value(content, "Brake Bias",
                                      brakes["Brake Bias"],
                                      f"{rw_setup.brake_bias}% front", row)
            row += 1

        # Other brake settings - ACR only
        if "Prop Valve Pressure" in brakes:
            key_label = tk.Label(content, text="Prop Valve Pressure", font=('Segoe UI', 9),
                                bg=self.card_bg, fg='#888888', anchor='w')
            key_label.grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
            val_label = tk.Label(content, text=brakes["Prop Valve Pressure"], font=('Consolas', 10),
                                bg=self.card_bg, fg=self.acr_value_color, anchor='w')
            val_label.grid(row=row, column=1, sticky='w', padx=(0, 10), pady=2)
            row += 1

        if "Handbrake Multiplier" in brakes:
            key_label = tk.Label(content, text="Handbrake Multiplier", font=('Segoe UI', 9),
                                bg=self.card_bg, fg='#888888', anchor='w')
            key_label.grid(row=row, column=0, sticky='w', padx=(0, 10), pady=2)
            val_label = tk.Label(content, text=brakes["Handbrake Multiplier"], font=('Consolas', 10),
                                bg=self.card_bg, fg=self.acr_value_color, anchor='w')
            val_label.grid(row=row, column=1, sticky='w', padx=(0, 10), pady=2)
            row += 1

        # Note
        note = tk.Label(content, text="(Prop Valve & Handbrake: No DiRT data)",
                       font=('Segoe UI', 8, 'italic'),
                       bg=self.card_bg, fg='#555555')
        note.grid(row=row, column=0, columnspan=3, sticky='w', pady=(8, 0))

    def create_section_frame(self, title):
        """Create a styled section frame with ACR-style red header."""
        # Main container with border effect
        outer_frame = tk.Frame(self.results_frame, bg=self.border_color, pady=1, padx=1)
        outer_frame.pack(fill=tk.X, pady=(0, 10))

        frame = tk.Frame(outer_frame, bg=self.card_bg, pady=10, padx=12)
        frame.pack(fill=tk.X)

        # Section title with red accent bar
        title_frame = tk.Frame(frame, bg=self.card_bg)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        # Red accent bar
        accent_bar = tk.Frame(title_frame, bg=self.accent_color, width=4, height=18)
        accent_bar.pack(side=tk.LEFT, padx=(0, 8))
        accent_bar.pack_propagate(False)

        title_label = tk.Label(title_frame, text=title, font=('Segoe UI', 11, 'bold'),
                              bg=self.card_bg, fg=self.fg_color)
        title_label.pack(side=tk.LEFT)

        # Content frame
        content = tk.Frame(frame, bg=self.card_bg)
        content.pack(fill=tk.X)

        return content

    def add_key_value(self, parent, key, value, row, col=0):
        """Add a key-value pair to the grid."""
        key_label = tk.Label(parent, text=key, font=('Segoe UI', 9),
                            bg=self.card_bg, fg='#888888', anchor='w')
        key_label.grid(row=row, column=col*2, sticky='w', padx=(0, 10), pady=2)

        value_label = tk.Label(parent, text=str(value), font=('Consolas', 10),
                              bg=self.card_bg, fg=self.fg_color, anchor='w')
        value_label.grid(row=row, column=col*2+1, sticky='w', padx=(0, 30), pady=2)

    def create_drivetrain_section(self, setup):
        """Create the drivetrain section."""
        content = self.create_section_frame("DRIVETRAIN")
        drivetrain = setup.get_drivetrain()

        row = 0
        for key, value in drivetrain.items():
            if isinstance(value, dict):
                # Subsection header
                header = tk.Label(content, text=key, font=('Segoe UI', 10, 'bold'),
                                 bg=self.card_bg, fg='#AAAAAA')
                header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(8, 4))
                row += 1

                # Subsection values
                col = 0
                for k, v in value.items():
                    self.add_key_value(content, k, v, row, col)
                    col += 1
                    if col >= 2:
                        col = 0
                        row += 1
                if col > 0:
                    row += 1
            else:
                self.add_key_value(content, key, value, row)
                row += 1

    def create_suspension_section(self, setup):
        """Create the suspension section."""
        content = self.create_section_frame("SUSPENSION")
        suspension = setup.get_suspension()

        row = 0

        # ARBs first
        if "Front ARB" in suspension:
            self.add_key_value(content, "Front ARB", suspension["Front ARB"], row, 0)
        if "Rear ARB" in suspension:
            self.add_key_value(content, "Rear ARB", suspension.get("Rear ARB", "N/A"), row, 1)
        row += 1

        # Springs
        if "Springs" in suspension:
            header = tk.Label(content, text="Springs", font=('Segoe UI', 10, 'bold'),
                             bg=self.card_bg, fg='#AAAAAA')
            header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(8, 4))
            row += 1

            springs = suspension["Springs"]
            self.add_key_value(content, "FL", springs.get("FL", "N/A"), row, 0)
            self.add_key_value(content, "FR", springs.get("FR", "N/A"), row, 1)
            row += 1
            self.add_key_value(content, "RL", springs.get("RL", "N/A"), row, 0)
            self.add_key_value(content, "RR", springs.get("RR", "N/A"), row, 1)
            row += 1

        # Ride Height
        if "Ride Height" in suspension:
            header = tk.Label(content, text="Ride Height", font=('Segoe UI', 10, 'bold'),
                             bg=self.card_bg, fg='#AAAAAA')
            header.grid(row=row, column=0, columnspan=4, sticky='w', pady=(8, 4))
            row += 1

            rh = suspension["Ride Height"]
            self.add_key_value(content, "FL", rh.get("FL", "N/A"), row, 0)
            self.add_key_value(content, "FR", rh.get("FR", "N/A"), row, 1)
            row += 1
            self.add_key_value(content, "RL", rh.get("RL", "N/A"), row, 0)
            self.add_key_value(content, "RR", rh.get("RR", "N/A"), row, 1)

    def create_dampers_section(self, setup):
        """Create the dampers section."""
        content = self.create_section_frame("DAMPERS")
        dampers = setup.get_dampers()

        row = 0

        # Create header row
        headers = ["", "Slow Bump", "Slow Rebound", "Fast Bump", "Fast Rebound"]
        for col, header in enumerate(headers):
            label = tk.Label(content, text=header, font=('Segoe UI', 9, 'bold'),
                            bg=self.card_bg, fg='#888888')
            label.grid(row=row, column=col, sticky='w', padx=(0, 15), pady=(0, 5))
        row += 1

        # Data rows
        for corner in ["FL", "FR", "RL", "RR"]:
            if corner in dampers:
                corner_data = dampers[corner]

                corner_label = tk.Label(content, text=corner, font=('Segoe UI', 10, 'bold'),
                                       bg=self.card_bg, fg='#AAAAAA')
                corner_label.grid(row=row, column=0, sticky='w', padx=(0, 15), pady=2)

                for col, key in enumerate(["Slow Bump", "Slow Rebound", "Fast Bump", "Fast Rebound"]):
                    value = corner_data.get(key, "N/A")
                    value_label = tk.Label(content, text=value, font=('Consolas', 10),
                                          bg=self.card_bg, fg=self.fg_color)
                    value_label.grid(row=row, column=col+1, sticky='w', padx=(0, 15), pady=2)

                row += 1

    def create_tyres_section(self, setup):
        """Create the tyres section."""
        content = self.create_section_frame("TYRES")
        tyres = setup.get_tyres()

        row = 0

        # Create header row
        headers = ["", "Pressure", "Camber", "Toe"]
        for col, header in enumerate(headers):
            label = tk.Label(content, text=header, font=('Segoe UI', 9, 'bold'),
                            bg=self.card_bg, fg='#888888')
            label.grid(row=row, column=col, sticky='w', padx=(0, 20), pady=(0, 5))
        row += 1

        # Data rows
        for corner in ["FL", "FR", "RL", "RR"]:
            if corner in tyres:
                corner_data = tyres[corner]

                corner_label = tk.Label(content, text=corner, font=('Segoe UI', 10, 'bold'),
                                       bg=self.card_bg, fg='#AAAAAA')
                corner_label.grid(row=row, column=0, sticky='w', padx=(0, 20), pady=2)

                for col, key in enumerate(["Pressure", "Camber", "Toe"]):
                    value = corner_data.get(key, "N/A")
                    value_label = tk.Label(content, text=value, font=('Consolas', 10),
                                          bg=self.card_bg, fg=self.fg_color)
                    value_label.grid(row=row, column=col+1, sticky='w', padx=(0, 20), pady=2)

                row += 1

    def create_brakes_section(self, setup):
        """Create the brakes section."""
        content = self.create_section_frame("BRAKES")
        brakes = setup.get_brakes()

        row = 0
        col = 0
        for key, value in brakes.items():
            self.add_key_value(content, key, value, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1


def main():
    """Launch the GUI application."""
    root = tk.Tk()
    app = SetupCalculatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
