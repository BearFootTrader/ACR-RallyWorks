"""
Rally Car Setup Calculator - GUI
Exact replica of ACR Car Setup Pro output format
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

try:
    from setup_calculator import (
        SetupCalculator, FullSetup,
        CarClass, Surface, TrackCondition, Weather,
        CAR_CLASS_CONFIGS
    )
except ImportError:
    from src.setup_calculator import (
        SetupCalculator, FullSetup,
        CarClass, Surface, TrackCondition, Weather,
        CAR_CLASS_CONFIGS
    )


class SetupCalculatorGUI:
    """Main GUI application matching original ACR Car Setup Pro layout"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Rally Car Setup Calculator - Engineering Edition")
        self.root.geometry("1000x900")
        self.root.minsize(950, 850)

        # Initialize calculator
        self.calculator = SetupCalculator()
        self.current_setup = None

        # Color scheme matching original
        self.bg_color = "#2D2D30"
        self.fg_color = "#F1F1F1"
        self.accent_color = "#007ACC"
        self.card_bg = "#3E3E42"
        self.success_color = "#4CAF50"

        # Configure root
        self.root.configure(bg=self.bg_color)

        # Configure style
        self.setup_styles()

        # Build UI
        self.create_widgets()

    def setup_styles(self):
        """Configure ttk styles for dark theme"""
        style = ttk.Style()

        # Use clam as base for better customization
        style.theme_use('clam')

        # Configure colors
        style.configure('.', background=self.bg_color, foreground=self.fg_color)
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        style.configure('TLabelframe', background=self.card_bg, foreground=self.accent_color)
        style.configure('TLabelframe.Label', background=self.card_bg, foreground=self.accent_color,
                       font=('Segoe UI', 10, 'bold'))
        style.configure('TCombobox', fieldbackground=self.card_bg, background=self.card_bg)
        style.configure('TRadiobutton', background=self.bg_color, foreground=self.fg_color)
        style.configure('TButton', background=self.accent_color, foreground='white')

        # Custom styles
        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'), foreground=self.accent_color)
        style.configure('Subtitle.TLabel', font=('Segoe UI', 9, 'italic'),
                       foreground='#B4B4B4')
        style.configure('Section.TLabel', font=('Segoe UI', 10, 'bold'), foreground=self.accent_color)
        style.configure('Calculate.TButton', font=('Segoe UI', 11, 'bold'))

    def create_widgets(self):
        """Create all UI widgets"""

        # Main container
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="ACR CAR SETUP PRO - ENGINEERING EDITION",
                 style='Title.TLabel').pack(anchor='w')
        ttk.Label(header_frame, text="Professional Rally Engineering Database",
                 style='Subtitle.TLabel').pack(anchor='w')

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Car Setup Preparation
        self.tab_setup = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_setup, text="Car Setup Preparation")

        # Tab 2: Fine-Tuning Guide
        self.tab_guide = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_guide, text="Fine-Tuning Guide")

        # Tab 3: Save/Load
        self.tab_save = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_save, text="Save / Load & Notes")

        # Build each tab
        self.create_setup_tab()
        self.create_guide_tab()
        self.create_save_tab()

    def create_setup_tab(self):
        """Create the main setup configuration tab"""

        # Top row - Selection controls
        top_frame = ttk.Frame(self.tab_setup)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # Surface selection (left)
        surface_frame = ttk.LabelFrame(top_frame, text="1. Surface Type", padding="10")
        surface_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        ttk.Label(surface_frame, text="Select the primary surface:").pack(anchor='w')
        self.surface_var = tk.StringVar(value="Asphalt")
        self.surface_combo = ttk.Combobox(surface_frame, textvariable=self.surface_var,
                                          values=["Asphalt", "Gravel", "Snow"],
                                          state="readonly", width=40)
        self.surface_combo.pack(fill=tk.X, pady=(5, 0))

        # Car class selection (right)
        car_frame = ttk.LabelFrame(top_frame, text="2. Car Class", padding="10")
        car_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        ttk.Label(car_frame, text="Select the car category:").pack(anchor='w')

        car_classes = [
            "Group A (4WD) - Lancia Delta",
            "WRC (2017+) (4WD)",
            "R5 / Rally2 (4WD)",
            "Group B (4WD) - Historic",
            "Group B (RWD) - Historic",
            "Modern RWD - Rally4",
            "FWD (KitCar/Rally4)",
            "RWD (Historic) - Escort/BMW",
            "Rally GT (RWD) - Porsche/Mustang",
            "Crosskart (AWD)",
            "Group S (Prototype)"
        ]

        self.car_class_var = tk.StringVar(value=car_classes[0])
        self.car_class_combo = ttk.Combobox(car_frame, textvariable=self.car_class_var,
                                            values=car_classes, state="readonly", width=40)
        self.car_class_combo.pack(fill=tk.X, pady=(5, 0))

        # Map display names to enums
        self.car_class_map = {
            "Group A (4WD) - Lancia Delta": CarClass.GROUP_A_4WD,
            "WRC (2017+) (4WD)": CarClass.WRC,
            "R5 / Rally2 (4WD)": CarClass.R5_RALLY2,
            "Group B (4WD) - Historic": CarClass.GROUP_B_4WD,
            "Group B (RWD) - Historic": CarClass.GROUP_B_RWD,
            "Modern RWD - Rally4": CarClass.RALLY4_RWD,
            "FWD (KitCar/Rally4)": CarClass.FWD_KITCAR,
            "RWD (Historic) - Escort/BMW": CarClass.RWD_HISTORIC,
            "Rally GT (RWD) - Porsche/Mustang": CarClass.RALLY_GT,
            "Crosskart (AWD)": CarClass.CROSSKART,
            "Group S (Prototype)": CarClass.GROUP_S,
        }

        # Second row - Condition and Weather
        second_frame = ttk.Frame(self.tab_setup)
        second_frame.pack(fill=tk.X, pady=(0, 10))

        # Track condition (left)
        track_frame = ttk.LabelFrame(second_frame, text="3. Track Condition", padding="10")
        track_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        ttk.Label(track_frame, text="Select the track condition:").pack(anchor='w')

        track_conditions = [
            "Smooth & Fast (Tarmac)",
            "Bumpy / Damaged (Rough)",
            "Loose & Slippery (Gravel)",
            "Mixed (Tarmac/Gravel)",
            "Ice (Packed Snow)",
            "Deep Gravel/Ruts",
            "Wet Mud/Clay"
        ]

        self.track_var = tk.StringVar(value=track_conditions[0])
        self.track_combo = ttk.Combobox(track_frame, textvariable=self.track_var,
                                        values=track_conditions, state="readonly", width=40)
        self.track_combo.pack(fill=tk.X, pady=(5, 0))

        self.track_map = {
            "Smooth & Fast (Tarmac)": TrackCondition.SMOOTH,
            "Bumpy / Damaged (Rough)": TrackCondition.BUMPY,
            "Loose & Slippery (Gravel)": TrackCondition.LOOSE,
            "Mixed (Tarmac/Gravel)": TrackCondition.MIXED,
            "Ice (Packed Snow)": TrackCondition.ICE,
            "Deep Gravel/Ruts": TrackCondition.DEEP_GRAVEL,
            "Wet Mud/Clay": TrackCondition.WET_MUD,
        }

        # Weather (right)
        weather_frame = ttk.LabelFrame(second_frame, text="4. Weather", padding="10")
        weather_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        ttk.Label(weather_frame, text="Select the weather condition:").pack(anchor='w')

        weather_options = [
            "Dry",
            "Damp / Humid",
            "Wet / Heavy Rain",
            "Fog/Mist",
            "Cold (Below 5°C)",
            "Hot (Above 25°C)"
        ]

        self.weather_var = tk.StringVar(value=weather_options[0])
        self.weather_combo = ttk.Combobox(weather_frame, textvariable=self.weather_var,
                                          values=weather_options, state="readonly", width=40)
        self.weather_combo.pack(fill=tk.X, pady=(5, 0))

        self.weather_map = {
            "Dry": Weather.DRY,
            "Damp / Humid": Weather.DAMP,
            "Wet / Heavy Rain": Weather.WET,
            "Fog/Mist": Weather.FOG,
            "Cold (Below 5°C)": Weather.COLD,
            "Hot (Above 25°C)": Weather.HOT,
        }

        # Calculate button
        calc_btn = tk.Button(self.tab_setup, text="GET ENGINEERING BASELINE SETUP",
                            command=self.calculate_setup,
                            bg=self.success_color, fg='white',
                            font=('Segoe UI', 11, 'bold'),
                            relief='flat', cursor='hand2', height=2)
        calc_btn.pack(fill=tk.X, pady=(0, 10))

        # Results area - split panes
        results_frame = ttk.Frame(self.tab_setup)
        results_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel - Setup results
        left_panel = ttk.LabelFrame(results_frame, text="ENGINEERING SETUP RESULTS", padding="10")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.setup_text = tk.Text(left_panel, font=('Consolas', 9),
                                  bg='#323232', fg=self.fg_color,
                                  relief='flat', wrap=tk.WORD)
        self.setup_text.pack(fill=tk.BOTH, expand=True)

        # Right panel - Differential results
        right_panel = ttk.LabelFrame(results_frame, text="DIFFERENTIAL ENGINEERING", padding="10")
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.diff_text = tk.Text(right_panel, font=('Consolas', 9),
                                 bg='#323232', fg=self.fg_color,
                                 relief='flat', wrap=tk.WORD)
        self.diff_text.pack(fill=tk.BOTH, expand=True)

    def create_guide_tab(self):
        """Create the tuning guide tab"""

        guide_text = tk.Text(self.tab_guide, font=('Segoe UI', 9),
                            bg='#323232', fg=self.fg_color,
                            relief='flat', wrap=tk.WORD, padx=15, pady=15)
        guide_text.pack(fill=tk.BOTH, expand=True)

        guide_content = """*** RALLY ENGINEERING PRINCIPLES ***
Based on Real-World WRC Engineering Data

DIFFERENTIAL ENGINEERING:
- POWER RAMP: Lower angle = MORE lock under acceleration
- COAST RAMP: Lower angle = MORE lock during deceleration
- PRELOAD: Higher values = Immediate locking response

DAMPER RATIOS (Competition Standard):
- Slow Rebound/Slow Bump: 1.6:1 ratio (Industry Standard)
- Fast Rebound/Fast Bump: 1.5:1 ratio (Bump Control)
- Transition Points: 0.15 m/s (AC Standard)

SPRING FREQUENCY ENGINEERING:
- Asphalt: 2.8-3.2 Hz (Stiff for aero platforms)
- Gravel: 1.8-2.2 Hz (Compliance for bumps)
- Snow: 1.4-1.8 Hz (Maximum traction)

-------------------------------------------------------

PROBLEM: UNDERSTEER on CORNER ENTRY
ENGINEERING SOLUTIONS:
- DIFFERENTIAL: Increase Front Coast Ramp angle (+10-15°)
- SUSPENSION: Soften Front ARB (-20-30%)
- DAMPERS: Increase Rear Slow Rebound (+15-20%)
- ALIGNMENT: More Front Toe-Out (-0.10 to -0.15°)

PROBLEM: OVERSTEER on CORNER ENTRY
ENGINEERING SOLUTIONS:
- DIFFERENTIAL: Decrease Rear Coast Ramp angle (-10°)
- SUSPENSION: Stiffen Front ARB (+20%)
- DAMPERS: Increase Front Slow Bump (+15%)
- BRAKES: Move bias forward (+2-3%)

PROBLEM: TRACTION ISSUES on EXIT
ENGINEERING SOLUTIONS:
- DIFFERENTIAL: Decrease Rear Power Ramp angle (-10-15°)
- SUSPENSION: Soften Rear Springs (-10%)
- DAMPERS: Soften Rear Fast Bump (-20%)
- RIDE HEIGHT: Lower Rear (+5mm rake)

PROBLEM: BUMPY SURFACE INSTABILITY
ENGINEERING SOLUTIONS:
- DAMPERS: Soften Fast settings (-30-40%)
- SPRINGS: Reduce rates (-15-20%)
- RIDE HEIGHT: Increase (+10-15mm)
- ARB: Soften significantly (-40-50%)

WEATHER ADJUSTMENTS:
- WET: Softer ARB, higher ride height, open diffs
- COLD: Stiffer springs, more camber
- HOT: Softer springs, less camber

-------------------------------------------------------

MODERN RALLY ENGINEERING REFERENCES:
- WRC Teams: Toyota Gazoo Racing, Hyundai Motorsport
- Development: M-Sport, Citroën Racing
- Data Source: ACR Extracted Engineering Setups

USEFUL LINKS:
- Github ilborga70: https://github.com/ilborga70
- Pro Sim FOV Utility: https://github.com/ilborga70/Pro-Sim-FOV-Utility
- Website: https://scl-tools.blogspot.com/
"""

        guide_text.insert('1.0', guide_content)
        guide_text.config(state=tk.DISABLED)

    def create_save_tab(self):
        """Create the save/load tab"""

        # Buttons frame
        btn_frame = ttk.Frame(self.tab_save)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Button(btn_frame, text="Save Current Setup", command=self.save_setup,
                 bg=self.accent_color, fg='white', font=('Segoe UI', 9, 'bold'),
                 relief='flat', padx=20, pady=5).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(btn_frame, text="Load Setup", command=self.load_setup,
                 bg=self.accent_color, fg='white', font=('Segoe UI', 9, 'bold'),
                 relief='flat', padx=20, pady=5).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(btn_frame, text="Copy to Clipboard", command=self.copy_to_clipboard,
                 bg=self.accent_color, fg='white', font=('Segoe UI', 9, 'bold'),
                 relief='flat', padx=20, pady=5).pack(side=tk.LEFT)

        # Notes area
        notes_frame = ttk.LabelFrame(self.tab_save, text="Engineering Notes", padding="10")
        notes_frame.pack(fill=tk.BOTH, expand=True)

        self.notes_text = tk.Text(notes_frame, font=('Segoe UI', 10),
                                  bg='#323232', fg=self.fg_color,
                                  relief='flat', wrap=tk.WORD)
        self.notes_text.pack(fill=tk.BOTH, expand=True)
        self.notes_text.insert('1.0', "Enter your engineering notes here...\n\n"
                              "Document:\n"
                              "- Stage-specific adjustments\n"
                              "- Handling observations\n"
                              "- Weather/condition notes\n"
                              "- Setup iterations and results")

    def calculate_setup(self):
        """Generate the setup based on selections"""

        try:
            # Map selections to enums
            surface_map = {
                "Asphalt": Surface.ASPHALT,
                "Gravel": Surface.GRAVEL,
                "Snow": Surface.SNOW,
            }

            surface = surface_map[self.surface_var.get()]
            car_class = self.car_class_map[self.car_class_var.get()]
            track_condition = self.track_map[self.track_var.get()]
            weather = self.weather_map[self.weather_var.get()]

            # Calculate
            self.current_setup = self.calculator.calculate_setup(
                car_class=car_class,
                surface=surface,
                track_condition=track_condition,
                weather=weather,
                setup_name="Engineering Baseline"
            )

            # Display results
            self.display_setup_results()
            self.display_diff_results()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate setup: {str(e)}")

    def display_setup_results(self):
        """Display setup results matching original format"""

        setup = self.current_setup
        self.setup_text.config(state=tk.NORMAL)
        self.setup_text.delete('1.0', tk.END)

        lines = []
        lines.append("--- ENGINEERING INPUTS ---")
        lines.append(f"Surface: {setup.surface} | Car: {setup.car_class}")
        lines.append(f"Condition: {setup.track_condition} | Weather: {setup.weather}")
        lines.append(f"Engineering Profile: {setup.engineering_profile}")
        lines.append("")

        lines.append("--- GEOMETRY & SUSPENSION (ENGINEERING SPEC) ---")
        lines.append(f"Ride Height (F/R): {setup.suspension.ride_height_front:.3f} m / {setup.suspension.ride_height_rear:.3f} m")
        lines.append(f"Spring Rate (F/R): {setup.suspension.spring_rate_front} N/m / {setup.suspension.spring_rate_rear} N/m")
        lines.append(f"Anti-Roll Bar (F/R): {setup.arb.front} Nm / {setup.arb.rear} Nm")
        lines.append(f"Camber (F/R): {setup.suspension.camber_front:.1f}° / {setup.suspension.camber_rear:.1f}°")
        lines.append(f"Toe (F/R): {setup.suspension.toe_front:.4f} / {setup.suspension.toe_rear:.4f}")
        lines.append("")

        lines.append("--- DAMPERS (N/m/s) [Engineering Ratios] ---")
        lines.append(f"Slow Bump (F/R): {setup.dampers.slow_bump_front} / {setup.dampers.slow_bump_rear}")
        lines.append(f"Slow Rebound (F/R): {setup.dampers.slow_rebound_front} / {setup.dampers.slow_rebound_rear}")
        lines.append(f"Fast Bump (F/R): {setup.dampers.fast_bump_front} / {setup.dampers.fast_bump_rear}")
        lines.append(f"Fast Rebound (F/R): {setup.dampers.fast_rebound_front} / {setup.dampers.fast_rebound_rear}")
        lines.append("")

        lines.append("--- BRAKES ---")
        lines.append(f"Brake Bias: {setup.brakes.bias:.2f}")
        lines.append(f"Brake Pressure: {setup.brakes.pressure}%")

        self.setup_text.insert('1.0', '\n'.join(lines))

        # Color based on surface
        surface_colors = {
            "asphalt": "#6495ED",   # Cornflower blue
            "gravel": "#D2B48C",    # Tan
            "snow": "#E0FFFF",      # Light cyan
        }
        color = surface_colors.get(setup.surface, self.fg_color)
        self.setup_text.config(fg=color)
        self.setup_text.config(state=tk.DISABLED)

    def display_diff_results(self):
        """Display differential results matching original format"""

        setup = self.current_setup
        self.diff_text.config(state=tk.NORMAL)
        self.diff_text.delete('1.0', tk.END)

        lines = []
        lines.append("--- DIFFERENTIAL ENGINEERING (ACR) ---")
        lines.append("Engineering Logic: Lower Angle = MORE Lock (Aggressive)")
        lines.append("                   Higher Angle = LESS Lock (Smooth)")
        lines.append("")

        if setup.traction in ["FWD", "4WD"]:
            lines.append("--- FRONT DIFFERENTIAL ---")
            lines.append(f"Accel Ramp (Power): {setup.differential.front_accel}°")
            lines.append(f"Coast Ramp (Decel): {setup.differential.front_coast}°")
            lines.append(f"Preload: {setup.differential.front_preload} Nm")
            lines.append("")

        if setup.traction in ["RWD", "4WD"]:
            lines.append("--- REAR DIFFERENTIAL ---")
            lines.append(f"Accel Ramp (Power): {setup.differential.rear_accel}°")
            lines.append(f"Coast Ramp (Decel): {setup.differential.rear_coast}°")
            lines.append(f"Preload: {setup.differential.rear_preload} Nm")
            lines.append("")

        if setup.traction == "4WD":
            lines.append("--- CENTER DIFFERENTIAL ---")
            lines.append("Torque Split: 50/50 (Default)")
            lines.append("Note: Adjust in-car for specific stage requirements")

        self.diff_text.insert('1.0', '\n'.join(lines))

        # Match color
        surface_colors = {
            "asphalt": "#6495ED",
            "gravel": "#D2B48C",
            "snow": "#E0FFFF",
        }
        color = surface_colors.get(setup.surface, self.fg_color)
        self.diff_text.config(fg=color)
        self.diff_text.config(state=tk.DISABLED)

    def save_setup(self):
        """Save current setup to JSON file"""

        if not self.current_setup:
            messagebox.showwarning("No Setup", "Generate a setup first before saving.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="rally_setup.json"
        )

        if filepath:
            try:
                self.current_setup.notes = self.notes_text.get('1.0', tk.END).strip()
                self.current_setup.save_to_file(filepath)
                messagebox.showinfo("Saved", f"Setup saved to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")

    def load_setup(self):
        """Load setup from JSON file"""

        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filepath:
            try:
                self.current_setup = FullSetup.load_from_file(filepath)
                self.display_setup_results()
                self.display_diff_results()

                self.notes_text.delete('1.0', tk.END)
                self.notes_text.insert('1.0', self.current_setup.notes)

                messagebox.showinfo("Loaded", f"Setup loaded: {self.current_setup.name}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {str(e)}")

    def copy_to_clipboard(self):
        """Copy results to clipboard"""

        if not self.current_setup:
            messagebox.showwarning("No Setup", "Generate a setup first.")
            return

        self.setup_text.config(state=tk.NORMAL)
        setup_content = self.setup_text.get('1.0', tk.END)
        self.setup_text.config(state=tk.DISABLED)

        self.diff_text.config(state=tk.NORMAL)
        diff_content = self.diff_text.get('1.0', tk.END)
        self.diff_text.config(state=tk.DISABLED)

        full_content = setup_content + "\n" + diff_content

        self.root.clipboard_clear()
        self.root.clipboard_append(full_content)
        messagebox.showinfo("Copied", "Setup copied to clipboard!")


def main():
    """Launch the GUI application"""
    root = tk.Tk()
    app = SetupCalculatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
