# ACR RallyWorks

<p align="center">
  <img src="logo_textonly.png" alt="ACR RallyWorks Logo" width="400">
</p>

A rally car setup tool for **Assetto Corsa Rally (ACR)** with baseline setups extracted directly from ACR content files. Features an ACR-inspired dark theme UI and the experimental **RallyWorks+** optimization system.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-1.0-orange.svg)

## Features

### Core Features
- **ACR Default Setups** - Baseline setups extracted directly from Assetto Corsa Rally content files
- **Surface-Based Selection** - Automatically loads gravel or tarmac setup based on stage selection
- **Dark Theme UI** - ACR-inspired interface with red accent styling
- **Save/Load Setups** - Save your custom setups locally and reload them anytime

### RallyWorks+ (Experimental)
RallyWorks+ is an experimental feature that provides optimized setup suggestions based on rally engineering principles and community data from DiRT Rally 2.0.

**Currently Available For:**
- Lancia Delta HF Integrale Evo (Gravel)

**How It Works:**
- Toggle RallyWorks+ to see suggested modifications alongside ACR defaults
- **Blue (↑)** indicates increased values
- **Red (↓)** indicates decreased values
- All suggestions are clamped to valid ACR parameter ranges

## Quick Start

### Requirements
- Python 3.8 or higher
- tkinter (included with Python on Windows)
- Pillow (optional, for logo display)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ACR-RallyWorks.git
cd ACR-RallyWorks

# Install optional dependencies
pip install -r rally-setup-calculator/requirements.txt

# Run the application
cd rally-setup-calculator
python run.py
```

Or on Windows, double-click `rally-setup-calculator/RallySetupCalculator.bat`

## Usage

1. **Select Car** - Choose your car from the dropdown
2. **Select Stage** - Choose your stage (surface type is determined automatically)
3. **Click LOAD SETUP** - Load the baseline setup for your selection
4. **Toggle RallyWorks+** - (If available) See optimized suggestions
5. **Save Setup** - Save your configuration for later use

## Setup Parameters

The tool displays all setup parameters organized by category:

| Category | Parameters |
|----------|------------|
| **Drivetrain** | Gear set, Front/Rear/Centre differentials, LSD settings |
| **Suspension** | Spring rates, Anti-roll bars, Ride height |
| **Dampers** | Slow/Fast bump and rebound for all corners |
| **Tyres** | Pressure, Camber, Toe for each corner |
| **Brakes** | Brake bias, Proportioning valve |

## Supported Content

### Cars
- **Group 2:** Mini Cooper S, Alfa Romeo Giulia GTA Junior
- **Group 4:** Alpine A110, Fiat 124/131 Abarth, Lancia Stratos
- **Group B:** Lancia Rally 037 Evo 2
- **Group A:** Lancia Delta HF Integrale Evo
- **WRC 2000s:** Citroen Xsara WRC
- **Rally2:** Hyundai i20N Rally2
- **Rally4:** Peugeot 208 Rally4

### Stages
- **France (Tarmac):** Vallee de Munster, Foret de Munster, Col du petit Ballon, and more
- **Wales (Gravel):** Cwmbiga, Afon Biga, Fedw Fain, Banc Gwyn, and more

## Project Structure

```
ACR-RallyWorks/
├── README.md
├── LICENSE
├── logo.ico / logo.png / logo_textonly.png
├── cars.tsv                    # Car metadata
├── stages.tsv                  # Stage metadata
├── car_setups_gravel.tsv       # Gravel default setups
├── car_setups_tarmac.tsv       # Tarmac default setups
├── docs/                       # Rally setup knowledge base
└── rally-setup-calculator/
    ├── run.py                  # Main launcher
    ├── requirements.txt
    ├── RallySetupCalculator.bat
    ├── saved_setups/           # User saved setups
    └── src/
        ├── setup_calculator.py # Data loading and setup logic
        ├── dirt_converter.py   # RallyWorks+ conversion engine
        └── gui.py              # Tkinter GUI
```

## Roadmap

### v1.1 - RallyWorks+ Expansion
- [ ] Add RallyWorks+ support for all Group A cars
- [ ] Add tarmac surface support for RallyWorks+
- [ ] Improve damper calculation algorithms

### v1.2 - Advanced Features
- [ ] Weather condition modifiers (wet, damp, cold, hot)
- [ ] Stage characteristic adjustments (bumpy, smooth, technical)
- [ ] Setup comparison tool

### Future
- [ ] Export setups to ACR format
- [ ] Import setups from ACR
- [ ] Community setup sharing
- [ ] RBR setup data integration

## Knowledge Base

The `docs/knowledge_week1/` folder contains rally setup guides covering:
- Suspension effects and tuning
- Differential setup principles
- Surface-specific tuning (gravel, tarmac)
- Troubleshooting handling issues

## Contributing

Contributions are welcome! Areas where help is needed:
- RallyWorks+ data for additional cars
- Testing and feedback on setup suggestions
- UI/UX improvements

## License

MIT License - See [LICENSE](LICENSE) for details.

## Disclaimer

This tool is unofficial and is not affiliated with Kunos Simulazioni or the ACR mod team. Setup data is extracted from publicly available ACR content files.

---

**Made for the rally sim community**
