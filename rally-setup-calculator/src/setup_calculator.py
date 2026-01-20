"""
ACR Rally Setup Calculator
Loads default car setups directly from Assetto Corsa Rally content files.

Data Sources:
- car_setups_gravel.tsv - Gravel surface default setups
- car_setups_tarmac.tsv - Tarmac surface default setups
- cars.tsv - Car list with metadata
- stages.tsv - Stage list with surface types
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Car:
    """Car metadata"""
    name: str
    manufacturer: str
    car_class: str
    drivetrain: str
    notes: str


@dataclass
class Stage:
    """Stage metadata"""
    name: str
    location: str
    surface: str  # "Gravel" or "Tarmac"
    style: str
    length: str
    notes: str


@dataclass
class CarSetup:
    """Complete car setup loaded from TSV"""
    car: str
    drive_type: str
    surface: str

    # Drivetrain
    gears_set: Optional[str] = None
    front_bias: Optional[str] = None
    front_diff_ratio: Optional[str] = None
    front_diff_lsd_ramp_angle: Optional[str] = None
    front_diff_lsd_plates: Optional[str] = None
    front_diff_lsd_preload: Optional[str] = None
    rear_diff_ratio: Optional[str] = None
    rear_diff_lsd_ramp_angle: Optional[str] = None
    rear_diff_lsd_plates: Optional[str] = None
    rear_diff_lsd_preload: Optional[str] = None
    centre_diff_ratio: Optional[str] = None

    # Suspension
    front_arb: Optional[str] = None
    rear_arb: Optional[str] = None
    spring_fl: Optional[str] = None
    spring_fr: Optional[str] = None
    spring_rl: Optional[str] = None
    spring_rr: Optional[str] = None
    ride_height_fl: Optional[str] = None
    ride_height_fr: Optional[str] = None
    ride_height_rl: Optional[str] = None
    ride_height_rr: Optional[str] = None

    # Dampers
    damper_fl_slow_bump: Optional[str] = None
    damper_fl_slow_rebound: Optional[str] = None
    damper_fl_fast_bump: Optional[str] = None
    damper_fl_fast_rebound: Optional[str] = None
    damper_fr_slow_bump: Optional[str] = None
    damper_fr_slow_rebound: Optional[str] = None
    damper_fr_fast_bump: Optional[str] = None
    damper_fr_fast_rebound: Optional[str] = None
    damper_rl_slow_bump: Optional[str] = None
    damper_rl_slow_rebound: Optional[str] = None
    damper_rl_fast_bump: Optional[str] = None
    damper_rl_fast_rebound: Optional[str] = None
    damper_rr_slow_bump: Optional[str] = None
    damper_rr_slow_rebound: Optional[str] = None
    damper_rr_fast_bump: Optional[str] = None
    damper_rr_fast_rebound: Optional[str] = None

    # Tyres
    tyre_fl_pressure: Optional[str] = None
    tyre_fl_camber: Optional[str] = None
    tyre_fl_toe: Optional[str] = None
    tyre_fr_pressure: Optional[str] = None
    tyre_fr_camber: Optional[str] = None
    tyre_fr_toe: Optional[str] = None
    tyre_rl_pressure: Optional[str] = None
    tyre_rl_camber: Optional[str] = None
    tyre_rl_toe: Optional[str] = None
    tyre_rr_pressure: Optional[str] = None
    tyre_rr_camber: Optional[str] = None
    tyre_rr_toe: Optional[str] = None

    # Brakes
    brake_bias: Optional[str] = None
    prop_valve_pressure: Optional[str] = None
    handbrake_multiplier: Optional[str] = None


# =============================================================================
# DATA LOADER
# =============================================================================

class SetupDataLoader:
    """Loads setup data from TSV files"""

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            # Default to parent of rally-setup-calculator folder
            self.data_dir = Path(__file__).parent.parent.parent.parent
        else:
            self.data_dir = Path(data_dir)

        self.cars: Dict[str, Car] = {}
        self.stages: Dict[str, Stage] = {}
        self.gravel_setups: Dict[str, CarSetup] = {}
        self.tarmac_setups: Dict[str, CarSetup] = {}

        self._load_all_data()

    def _load_all_data(self):
        """Load all data files"""
        self._load_cars()
        self._load_stages()
        self._load_setups("gravel")
        self._load_setups("tarmac")

    def _load_cars(self):
        """Load cars.tsv"""
        cars_file = self.data_dir / "cars.tsv"
        if not cars_file.exists():
            print(f"Warning: {cars_file} not found")
            return

        with open(cars_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                car = Car(
                    name=row.get('Car Name', ''),
                    manufacturer=row.get('Manufacturer', ''),
                    car_class=row.get('Class/Era', ''),
                    drivetrain=row.get('Drivetrain', ''),
                    notes=row.get('Notes', '')
                )
                self.cars[car.name] = car

    def _load_stages(self):
        """Load stages.tsv"""
        stages_file = self.data_dir / "stages.tsv"
        if not stages_file.exists():
            print(f"Warning: {stages_file} not found")
            return

        with open(stages_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                stage = Stage(
                    name=row.get('Stage Name (Variant)', ''),
                    location=row.get('Location', ''),
                    surface=row.get('Surface', ''),
                    style=row.get('Style/Character', ''),
                    length=row.get('Length', ''),
                    notes=row.get('Notes', '')
                )
                self.stages[stage.name] = stage

    def _load_setups(self, surface: str):
        """Load car setups from TSV file"""
        filename = f"car_setups_{surface}.tsv"
        setups_file = self.data_dir / filename

        if not setups_file.exists():
            print(f"Warning: {setups_file} not found")
            return

        # Path to attribute mapping
        path_map = {
            "drivetrain.gearsSet": "gears_set",
            "drivetrain.frontBias": "front_bias",
            "drivetrain.frontDiff.ratio": "front_diff_ratio",
            "drivetrain.frontDiff.lsdRampAngle": "front_diff_lsd_ramp_angle",
            "drivetrain.frontDiff.lsdPlates": "front_diff_lsd_plates",
            "drivetrain.frontDiff.lsdPreload": "front_diff_lsd_preload",
            "drivetrain.rearDiff.ratio": "rear_diff_ratio",
            "drivetrain.rearDiff.lsdRampAngle": "rear_diff_lsd_ramp_angle",
            "drivetrain.rearDiff.lsdPlates": "rear_diff_lsd_plates",
            "drivetrain.rearDiff.lsdPreload": "rear_diff_lsd_preload",
            "drivetrain.centreDiffRatio": "centre_diff_ratio",
            "suspension.frontARB": "front_arb",
            "suspension.rearARB": "rear_arb",
            "suspension.springs.FL": "spring_fl",
            "suspension.springs.FR": "spring_fr",
            "suspension.springs.RL": "spring_rl",
            "suspension.springs.RR": "spring_rr",
            "suspension.rideHeight.FL": "ride_height_fl",
            "suspension.rideHeight.FR": "ride_height_fr",
            "suspension.rideHeight.RL": "ride_height_rl",
            "suspension.rideHeight.RR": "ride_height_rr",
            "dampers.FL.slowBump": "damper_fl_slow_bump",
            "dampers.FL.slowRebound": "damper_fl_slow_rebound",
            "dampers.FL.fastBump": "damper_fl_fast_bump",
            "dampers.FL.fastRebound": "damper_fl_fast_rebound",
            "dampers.FR.slowBump": "damper_fr_slow_bump",
            "dampers.FR.slowRebound": "damper_fr_slow_rebound",
            "dampers.FR.fastBump": "damper_fr_fast_bump",
            "dampers.FR.fastRebound": "damper_fr_fast_rebound",
            "dampers.RL.slowBump": "damper_rl_slow_bump",
            "dampers.RL.slowRebound": "damper_rl_slow_rebound",
            "dampers.RL.fastBump": "damper_rl_fast_bump",
            "dampers.RL.fastRebound": "damper_rl_fast_rebound",
            "dampers.RR.slowBump": "damper_rr_slow_bump",
            "dampers.RR.slowRebound": "damper_rr_slow_rebound",
            "dampers.RR.fastBump": "damper_rr_fast_bump",
            "dampers.RR.fastRebound": "damper_rr_fast_rebound",
            "tyres.FL.pressure": "tyre_fl_pressure",
            "tyres.FL.camber": "tyre_fl_camber",
            "tyres.FL.toe": "tyre_fl_toe",
            "tyres.FR.pressure": "tyre_fr_pressure",
            "tyres.FR.camber": "tyre_fr_camber",
            "tyres.FR.toe": "tyre_fr_toe",
            "tyres.RL.pressure": "tyre_rl_pressure",
            "tyres.RL.camber": "tyre_rl_camber",
            "tyres.RL.toe": "tyre_rl_toe",
            "tyres.RR.pressure": "tyre_rr_pressure",
            "tyres.RR.camber": "tyre_rr_camber",
            "tyres.RR.toe": "tyre_rr_toe",
            "brakes.brakeBias": "brake_bias",
            "brakes.propValvePressure": "prop_valve_pressure",
            "brakes.handbrakeMultiplier": "handbrake_multiplier",
        }

        # Read the TSV and group by car
        car_data: Dict[str, Dict[str, str]] = {}
        car_drive_types: Dict[str, str] = {}

        with open(setups_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                car = row.get('car', '').strip('"')
                drive_type = row.get('driveType', '').strip('"')
                path = row.get('path', '').strip('"')
                value = row.get('value', '').strip('"')

                if car not in car_data:
                    car_data[car] = {}
                    car_drive_types[car] = drive_type

                if path in path_map:
                    attr_name = path_map[path]
                    car_data[car][attr_name] = value

        # Create CarSetup objects
        target_dict = self.gravel_setups if surface == "gravel" else self.tarmac_setups

        for car_name, data in car_data.items():
            setup = CarSetup(
                car=car_name,
                drive_type=car_drive_types.get(car_name, ''),
                surface=surface,
                **data
            )
            target_dict[car_name] = setup

    def get_car_list(self) -> List[str]:
        """Get list of all cars with setups"""
        # Return cars that have both gravel and tarmac setups
        gravel_cars = set(self.gravel_setups.keys())
        tarmac_cars = set(self.tarmac_setups.keys())
        all_cars = gravel_cars | tarmac_cars
        return sorted(list(all_cars))

    def get_stage_list(self) -> List[str]:
        """Get list of all stages"""
        return sorted(list(self.stages.keys()))

    def get_gravel_stages(self) -> List[str]:
        """Get list of gravel stages"""
        return sorted([s.name for s in self.stages.values() if s.surface.lower() == 'gravel'])

    def get_tarmac_stages(self) -> List[str]:
        """Get list of tarmac stages"""
        return sorted([s.name for s in self.stages.values() if s.surface.lower() == 'tarmac'])

    def get_setup(self, car: str, stage: str) -> Optional[CarSetup]:
        """Get setup for a car based on stage surface"""
        stage_obj = self.stages.get(stage)
        if not stage_obj:
            return None

        surface = stage_obj.surface.lower()
        if surface == 'gravel':
            return self.gravel_setups.get(car)
        else:
            return self.tarmac_setups.get(car)

    def get_stage_surface(self, stage: str) -> str:
        """Get the surface type for a stage"""
        stage_obj = self.stages.get(stage)
        if stage_obj:
            return stage_obj.surface
        return "Unknown"

    def get_stage_info(self, stage: str) -> Optional[Stage]:
        """Get full stage info"""
        return self.stages.get(stage)

    def get_car_info(self, car: str) -> Optional[Car]:
        """Get full car info"""
        return self.cars.get(car)


# =============================================================================
# SETUP CALCULATOR
# =============================================================================

class SetupCalculator:
    """Main calculator - now simply loads default setups from TSV files"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.loader = SetupDataLoader(data_dir)

    def get_cars(self) -> List[str]:
        """Get list of available cars"""
        return self.loader.get_car_list()

    def get_stages(self) -> List[str]:
        """Get list of available stages"""
        return self.loader.get_stage_list()

    def get_setup(self, car: str, stage: str) -> Optional[CarSetup]:
        """Get setup for car and stage"""
        return self.loader.get_setup(car, stage)

    def get_stage_surface(self, stage: str) -> str:
        """Get surface type for a stage"""
        return self.loader.get_stage_surface(stage)

    def get_stage_info(self, stage: str) -> Optional[Stage]:
        """Get stage information"""
        return self.loader.get_stage_info(stage)

    def get_car_info(self, car: str) -> Optional[Car]:
        """Get car information"""
        return self.loader.get_car_info(car)


# =============================================================================
# CLI TESTING
# =============================================================================

def main():
    """Test the setup calculator"""
    print("\nACR Rally Setup Calculator")
    print("=" * 50)

    calc = SetupCalculator()

    print(f"\nLoaded {len(calc.get_cars())} cars")
    print(f"Loaded {len(calc.get_stages())} stages")

    # Test getting a setup
    cars = calc.get_cars()
    stages = calc.get_stages()

    if cars and stages:
        test_car = cars[0]
        test_stage = stages[0]

        print(f"\nTest: {test_car} on {test_stage}")
        print(f"Surface: {calc.get_stage_surface(test_stage)}")

        setup = calc.get_setup(test_car, test_stage)
        if setup:
            print(f"\nDrivetrain: {setup.drive_type}")
            print(f"Front ARB: {setup.front_arb}")
            print(f"Rear ARB: {setup.rear_arb}")
            print(f"Springs FL: {setup.spring_fl}")
            print(f"Brake Bias: {setup.brake_bias}")


if __name__ == "__main__":
    main()
