"""
ACR Rally Setup Calculator
Loads default car setups directly from TSV files extracted from Assetto Corsa Rally.

No modifiers or calculations - just the raw default values for gravel and tarmac stages.
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional


class SetupData:
    """Container for car setup data organized by category."""

    def __init__(self, car: str, drive_type: str, surface: str):
        self.car = car
        self.drive_type = drive_type
        self.surface = surface
        self.raw_data: Dict[str, str] = {}  # path -> value (keeps original paths)

    def add_value(self, path: str, value: str):
        """Add a setup value by its path."""
        self.raw_data[path] = value

    def get(self, path: str, default: str = "N/A") -> str:
        """Get a value by path."""
        return self.raw_data.get(path, default)

    def get_drivetrain(self) -> Dict[str, str]:
        """Get drivetrain settings grouped logically."""
        result = {}

        # Gear set
        if "drivetrain.gearsSet" in self.raw_data:
            result["Gear Set"] = self.raw_data["drivetrain.gearsSet"]

        # Front bias (AWD only)
        if "drivetrain.frontBias" in self.raw_data:
            result["Front Bias"] = self.raw_data["drivetrain.frontBias"]

        # Centre diff (AWD only)
        if "drivetrain.centreDiffRatio" in self.raw_data:
            result["Centre Diff Ratio"] = self.raw_data["drivetrain.centreDiffRatio"]

        # Front differential (FWD and AWD)
        front_diff = {}
        for key in ["ratio", "lsdRampAngle", "lsdPlates", "lsdPreload"]:
            path = f"drivetrain.frontDiff.{key}"
            if path in self.raw_data and self.raw_data[path] != "N/A":
                display_key = {
                    "ratio": "Ratio",
                    "lsdRampAngle": "LSD Ramp Angle",
                    "lsdPlates": "LSD Plates",
                    "lsdPreload": "LSD Preload"
                }[key]
                front_diff[display_key] = self.raw_data[path]
        if front_diff:
            result["Front Diff"] = front_diff

        # Rear differential (RWD and AWD)
        rear_diff = {}
        for key in ["ratio", "lsdRampAngle", "lsdPlates", "lsdPreload"]:
            path = f"drivetrain.rearDiff.{key}"
            if path in self.raw_data:
                display_key = {
                    "ratio": "Ratio",
                    "lsdRampAngle": "LSD Ramp Angle",
                    "lsdPlates": "LSD Plates",
                    "lsdPreload": "LSD Preload"
                }[key]
                rear_diff[display_key] = self.raw_data[path]
        if rear_diff:
            result["Rear Diff"] = rear_diff

        return result

    def get_suspension(self) -> Dict[str, str]:
        """Get suspension settings grouped logically."""
        result = {}

        # ARBs
        if "suspension.frontARB" in self.raw_data:
            result["Front ARB"] = self.raw_data["suspension.frontARB"]
        if "suspension.rearARB" in self.raw_data:
            result["Rear ARB"] = self.raw_data["suspension.rearARB"]

        # Springs
        springs = {}
        for corner in ["FL", "FR", "RL", "RR"]:
            path = f"suspension.springs.{corner}"
            if path in self.raw_data:
                springs[corner] = self.raw_data[path]
        if springs:
            result["Springs"] = springs

        # Ride height
        ride_height = {}
        for corner in ["FL", "FR", "RL", "RR"]:
            path = f"suspension.rideHeight.{corner}"
            if path in self.raw_data:
                ride_height[corner] = self.raw_data[path]
        if ride_height:
            result["Ride Height"] = ride_height

        return result

    def get_dampers(self) -> Dict[str, Dict[str, str]]:
        """Get damper settings grouped by corner."""
        result = {}

        for corner in ["FL", "FR", "RL", "RR"]:
            corner_data = {}
            for setting in ["slowBump", "slowRebound", "fastBump", "fastRebound"]:
                path = f"dampers.{corner}.{setting}"
                if path in self.raw_data:
                    display_key = {
                        "slowBump": "Slow Bump",
                        "slowRebound": "Slow Rebound",
                        "fastBump": "Fast Bump",
                        "fastRebound": "Fast Rebound"
                    }[setting]
                    corner_data[display_key] = self.raw_data[path]
            if corner_data:
                result[corner] = corner_data

        return result

    def get_tyres(self) -> Dict[str, Dict[str, str]]:
        """Get tyre settings grouped by corner."""
        result = {}

        for corner in ["FL", "FR", "RL", "RR"]:
            corner_data = {}
            for setting in ["pressure", "camber", "toe"]:
                path = f"tyres.{corner}.{setting}"
                if path in self.raw_data:
                    display_key = setting.capitalize()
                    value = self.raw_data[path]
                    # Clean up the ? character in camber/toe values
                    if "?" in value:
                        value = value.replace("?", "°")
                    corner_data[display_key] = value
            if corner_data:
                result[corner] = corner_data

        return result

    def get_brakes(self) -> Dict[str, str]:
        """Get brake settings."""
        result = {}

        if "brakes.brakeBias" in self.raw_data:
            result["Brake Bias"] = self.raw_data["brakes.brakeBias"]
        if "brakes.propValvePressure" in self.raw_data:
            result["Prop Valve Pressure"] = self.raw_data["brakes.propValvePressure"]
        if "brakes.handbrakeMultiplier" in self.raw_data:
            result["Handbrake Multiplier"] = self.raw_data["brakes.handbrakeMultiplier"]

        return result


class StageData:
    """Container for stage information."""

    def __init__(self, name: str, location: str, surface: str, style: str, length: str, notes: str):
        self.name = name
        self.location = location
        self.surface = surface.lower()  # "tarmac" or "gravel"
        self.style = style
        self.length = length
        self.notes = notes


class CarData:
    """Container for car information."""

    def __init__(self, name: str, manufacturer: str, car_class: str, drivetrain: str, notes: str):
        self.name = name
        self.manufacturer = manufacturer
        self.car_class = car_class
        self.drivetrain = drivetrain
        self.notes = notes


class SetupCalculator:
    """
    Main calculator class that loads and provides access to car setup data.

    Loads data from TSV files:
    - cars.tsv: Car list with metadata
    - stages.tsv: Stage list with surface types
    - car_setups_gravel.tsv: Default gravel setups
    - car_setups_tarmac.tsv: Default tarmac setups
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize calculator and load data from TSV files."""

        # Find data directory (parent of rally-setup-calculator folder)
        if data_dir is None:
            # Try to find data files relative to this script
            script_dir = Path(__file__).parent
            data_dir = script_dir.parent.parent  # Go up from src to rally-setup-calculator to root

        self.data_dir = Path(data_dir)

        # Data containers
        self.cars: Dict[str, CarData] = {}
        self.stages: Dict[str, StageData] = {}
        self.gravel_setups: Dict[str, SetupData] = {}
        self.tarmac_setups: Dict[str, SetupData] = {}

        # Load all data
        self._load_cars()
        self._load_stages()
        self._load_setups("gravel")
        self._load_setups("tarmac")

    def _load_cars(self):
        """Load car data from cars.tsv."""
        cars_file = self.data_dir / "cars.tsv"
        if not cars_file.exists():
            print(f"Warning: {cars_file} not found")
            return

        with open(cars_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                name = row.get("Car Name", "").strip()
                if name:
                    self.cars[name] = CarData(
                        name=name,
                        manufacturer=row.get("Manufacturer", ""),
                        car_class=row.get("Class/Era", ""),
                        drivetrain=row.get("Drivetrain", ""),
                        notes=row.get("Notes", "")
                    )

    def _load_stages(self):
        """Load stage data from stages.tsv."""
        stages_file = self.data_dir / "stages.tsv"
        if not stages_file.exists():
            print(f"Warning: {stages_file} not found")
            return

        with open(stages_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                name = row.get("Stage Name (Variant)", "").strip()
                if name:
                    self.stages[name] = StageData(
                        name=name,
                        location=row.get("Location", ""),
                        surface=row.get("Surface", ""),
                        style=row.get("Style/Character", ""),
                        length=row.get("Length", ""),
                        notes=row.get("Notes", "")
                    )

    def _load_setups(self, surface: str):
        """Load setup data from car_setups_{surface}.tsv."""
        setups_file = self.data_dir / f"car_setups_{surface}.tsv"
        if not setups_file.exists():
            print(f"Warning: {setups_file} not found")
            return

        setups_dict = self.gravel_setups if surface == "gravel" else self.tarmac_setups

        with open(setups_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                car = row.get("car", "").strip().strip('"')
                drive_type = row.get("driveType", "").strip().strip('"')
                path = row.get("path", "").strip().strip('"')
                value = row.get("value", "").strip().strip('"')

                if car and path:
                    # Create setup data if not exists
                    if car not in setups_dict:
                        setups_dict[car] = SetupData(car, drive_type, surface)

                    setups_dict[car].add_value(path, value)

    def get_car_list(self) -> List[str]:
        """Get list of available cars from setup data."""
        # Use cars from gravel setups as the canonical list
        return sorted(self.gravel_setups.keys())

    def get_stage_list(self) -> List[str]:
        """Get list of available stages."""
        return sorted(self.stages.keys())

    def get_car_info(self, car_name: str) -> Optional[CarData]:
        """Get car information by name."""
        # Try exact match first
        if car_name in self.cars:
            return self.cars[car_name]

        # Try partial match (setup names may differ from car names)
        for name, data in self.cars.items():
            if car_name in name or name in car_name:
                return data

        return None

    def get_stage_info(self, stage_name: str) -> Optional[StageData]:
        """Get stage information by name."""
        return self.stages.get(stage_name)

    def get_surface_for_stage(self, stage_name: str) -> str:
        """Get the surface type for a stage (gravel or tarmac)."""
        stage = self.stages.get(stage_name)
        if stage:
            return stage.surface
        return "tarmac"  # Default to tarmac

    def get_setup(self, car_name: str, surface: str) -> Optional[SetupData]:
        """Get setup data for a car and surface type."""
        if surface == "gravel":
            return self.gravel_setups.get(car_name)
        else:
            return self.tarmac_setups.get(car_name)

    def get_setup_for_stage(self, car_name: str, stage_name: str) -> Optional[SetupData]:
        """Get setup data for a car based on stage surface."""
        surface = self.get_surface_for_stage(stage_name)
        return self.get_setup(car_name, surface)


def main():
    """Test the setup calculator."""
    calculator = SetupCalculator()

    print("ACR Rally Setup Calculator")
    print("=" * 50)

    print("\nAvailable Cars:")
    for car in calculator.get_car_list():
        print(f"  - {car}")

    print("\nAvailable Stages:")
    for stage in calculator.get_stage_list():
        stage_info = calculator.get_stage_info(stage)
        if stage_info:
            print(f"  - {stage} ({stage_info.surface.capitalize()})")

    # Test loading a setup
    test_car = "Lancia Delta HF Integrale Evo"
    test_stage = "Cwmbiga – Afon Biga"

    print(f"\n\nTest Setup: {test_car} on {test_stage}")
    print("=" * 50)

    setup = calculator.get_setup_for_stage(test_car, test_stage)
    if setup:
        print(f"\nSurface: {setup.surface}")
        print(f"Drive Type: {setup.drive_type}")

        print("\n--- DRIVETRAIN ---")
        drivetrain = setup.get_drivetrain()
        for key, value in drivetrain.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")

        print("\n--- SUSPENSION ---")
        suspension = setup.get_suspension()
        for key, value in suspension.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")

        print("\n--- DAMPERS ---")
        dampers = setup.get_dampers()
        for corner, values in dampers.items():
            print(f"  {corner}:")
            for k, v in values.items():
                print(f"    {k}: {v}")

        print("\n--- TYRES ---")
        tyres = setup.get_tyres()
        for corner, values in tyres.items():
            print(f"  {corner}:")
            for k, v in values.items():
                print(f"    {k}: {v}")

        print("\n--- BRAKES ---")
        brakes = setup.get_brakes()
        for key, value in brakes.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
