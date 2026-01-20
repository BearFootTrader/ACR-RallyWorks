# ACR Rally Setup Calculator

A Python-based rally car setup tool for Assetto Corsa Rally (ACR). Provides default baseline setups for gravel and tarmac stages, extracted directly from ACR content files.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Overview

This tool loads default car setups from Assetto Corsa Rally and displays them in a clean, organized interface. Select your car and stage, and the appropriate setup (gravel or tarmac) is automatically loaded based on the stage surface type.

**Future Development:** Setup optimization logic based on data from RBR (Richard Burns Rally) and DiRT Rally 2.0 community setups will be implemented to provide improved baseline configurations.

## Features

- **Direct ACR Data:** Setups extracted directly from Assetto Corsa Rally content files
- **Surface-Based Selection:** Automatically selects gravel or tarmac setup based on stage
- **Complete Setup Display:** All setup parameters organized into clear sections:
  - Drivetrain (differentials, ratios, LSD settings)
  - Suspension (springs, ARBs, ride height)
  - Dampers (slow/fast bump and rebound for all corners)
  - Tyres (pressure, camber, toe)
  - Brakes (bias, proportioning valve)

## Supported Content

### Surfaces
- **Tarmac** - Alsace (France) stages
- **Gravel** - Wales (UK) stages

### Cars
Cars from multiple eras including:
- Group 2 (Mini Cooper S, Alfa Romeo Giulia GTAm)
- Group 4 (Alpine A110, Fiat 124/131 Abarth, Lancia Stratos)
- Group B (Lancia Rally 037)
- Group A / Modern (Lancia Delta HF Integrale)
- WRC 2000s (Citroen Xsara WRC)
- Rally2 (Hyundai i20N Rally2)
- Rally4 (Peugeot 208 Rally4)

## Installation

### Requirements
- Python 3.8 or higher
- tkinter (included with Python on Windows)

### Quick Start

```bash
# Navigate to the rally-setup-calculator folder
cd rally-setup-calculator

# Run the application
python run.py
```

Or on Windows, double-click `RallySetupCalculator.bat`

## Usage

1. **Select Car** - Choose your car from the dropdown
2. **Select Stage** - Choose your stage (surface type shown automatically)
3. The setup is displayed immediately, organized by component group

## Data Files

The application loads data from TSV files in the project root:

| File | Description |
|------|-------------|
| `cars.tsv` | Car list with metadata (manufacturer, class, drivetrain) |
| `stages.tsv` | Stage list with location and surface type |
| `car_setups_gravel.tsv` | Default gravel setups for all cars |
| `car_setups_tarmac.tsv` | Default tarmac setups for all cars |

## Project Structure

```
ACR-RSC/
├── cars.tsv                    # Car metadata
├── stages.tsv                  # Stage metadata
├── car_setups_gravel.tsv       # Gravel default setups
├── car_setups_tarmac.tsv       # Tarmac default setups
└── rally-setup-calculator/
    ├── run.py                  # Main launcher
    ├── RallySetupCalculator.bat
    └── src/
        ├── setup_calculator.py # Data loading and setup logic
        └── gui.py              # Tkinter GUI
```

## Roadmap

- [ ] Setup optimization based on RBR/DiRT 2.0 community data
- [ ] Weather condition adjustments
- [ ] Stage characteristic modifiers (bumpy, smooth, technical)
- [ ] Export setups back to ACR format


### Data Sources
- Default setups extracted from Assetto Corsa Rally content
- Future: RBR and DiRT Rally 2.0 community setup databases

## License

MIT License - Feel free to modify and distribute.

## Disclaimer

This tool is unofficial and is not affiliated with Kunos Simulazioni or the ACR mod team.
