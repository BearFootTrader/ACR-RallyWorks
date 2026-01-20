# Rally Car Setup Calculator

A Python-based rally car setup calculator for Assetto Corsa, built using engineering data extracted from ACR Car Setup Pro.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Overview

This tool generates competition-ready baseline setups for rally cars in Assetto Corsa. It uses real engineering data derived from telemetry analysis and WRC engineering principles, with calculations based on the original ACR Car Setup Pro by [ilborga70](https://github.com/ilborga70).

**Key difference from original:** This is a Python rewrite with full source code available, making it easy to modify, extend, and understand the engineering calculations.

## Features

### Car Classes Supported
- **Group A (4WD)** - Lancia Delta Integrale (reference car)
- **WRC (2017+)** - Modern aero-dependent platforms
- **R5 / Rally2** - Balanced 4WD performance
- **Group B (4WD & RWD)** - Historic power machines
- **Rally4 / Modern RWD** - Precision handling
- **FWD KitCar** - Front traction priority
- **RWD Historic** - Escort, BMW E30 style
- **Rally GT** - Porsche, Mustang high-torque RWD
- **Crosskart (AWD)** - Lightweight chassis
- **Group S (Prototype)** - Experimental setups

### Engineering Modifiers
- **Surfaces:** Asphalt, Gravel, Snow
- **Track Conditions:** Smooth, Bumpy, Loose, Mixed, Ice, Deep Gravel, Wet Mud
- **Weather:** Dry, Damp, Wet/Heavy Rain, Fog, Cold (<5°C), Hot (>25°C)

### Output Values
- Spring rates (N/m)
- Damper settings (N/m/s) - Slow/Fast Bump & Rebound
- Anti-roll bar stiffness (Nm)
- Ride height (meters)
- Camber & Toe alignment
- Differential ramp angles & preload
- Brake bias & pressure

## Installation

### Requirements
- Python 3.8 or higher
- tkinter (included with Python on Windows)

### Quick Start

```bash
# Clone or download this repository
cd rally-setup-calculator

# Run the application
python run.py
```

Or on Windows, double-click `RallySetupCalculator.bat`

## Usage

1. **Select Surface** - Asphalt, Gravel, or Snow
2. **Select Car Class** - Choose your vehicle category
3. **Select Track Condition** - Smooth, Bumpy, Loose, etc.
4. **Select Weather** - Dry, Wet, Cold, etc.
5. Click **GET ENGINEERING BASELINE SETUP**
6. Apply the values to your Assetto Corsa setup

### Save/Load
- Save setups as `.json` files
- Load previously saved configurations
- Copy results to clipboard

## Engineering Principles

### Damper Ratios
Professional 1.6:1 Rebound/Bump ratio (industry standard)

### Spring Frequencies by Surface
| Surface | Frequency | Characteristic |
|---------|-----------|----------------|
| Asphalt | 2.8-3.2 Hz | Stiff for grip |
| Gravel | 1.8-2.2 Hz | Compliance for bumps |
| Snow | 1.4-1.8 Hz | Maximum traction |

### Differential Logic
- **Lower ramp angles** = More lock (aggressive)
- **Higher ramp angles** = Less lock (smooth)

### Surface Multipliers
| Modifier | Gravel | Snow |
|----------|--------|------|
| Springs | ×0.65 | ×0.50 |
| ARB Front | ×0.45 | ×0.30 |
| ARB Rear | ×0.40 | ×0.25 |
| Dampers | ×0.60 | - |

## Project Structure

```
rally-setup-calculator/
├── run.py                    # Main launcher
├── RallySetupCalculator.bat  # Windows launcher
├── BUILD_EXE.bat             # Build standalone executable
├── requirements.txt
└── src/
    ├── setup_calculator.py   # Core calculation engine
    └── gui.py                # Tkinter GUI
```

## Building Standalone Executable

To create a standalone `.exe` file:

```bash
# Install PyInstaller
pip install pyinstaller

# Run the build script
BUILD_EXE.bat
```

The executable will be created in the `dist/` folder.

## Credits

### Original Application
- **ACR Car Setup Pro** by [ilborga70](https://github.com/ilborga70)
- Website: [scl-tools.blogspot.com](https://scl-tools.blogspot.com/)

### Engineering References
- Toyota Gazoo Racing
- Hyundai Motorsport
- M-Sport
- Citroën Racing

### Python Rewrite
This Python implementation extracts and reimplements the exact engineering calculations from the original PowerShell application, with full source code transparency.

## License

MIT License - Feel free to modify and distribute.

## Disclaimer

This tool is unofficial and is not affiliated with Kunos Simulazioni. Professional engineering principles applied for authentic rally simulation experience.
