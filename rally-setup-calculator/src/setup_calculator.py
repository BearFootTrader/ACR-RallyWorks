"""
Rally Car Setup Calculator for Assetto Corsa
Exact values extracted from ACR Car Setup Pro - Engineering Edition

Engineering References: Toyota Gazoo Racing, Hyundai Motorsport, M-Sport, Citroën Racing
Original Author: ilborga70 (https://github.com/ilborga70)
"""

import json
import math
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional
from pathlib import Path


# =============================================================================
# ENUMS - Surface, Track Conditions, Weather, Car Classes
# =============================================================================

class Surface(Enum):
    ASPHALT = "asphalt"
    GRAVEL = "gravel"
    SNOW = "snow"


class TrackCondition(Enum):
    SMOOTH = "smooth"              # "Smooth & Fast (Tarmac)"
    BUMPY = "bumpy"                # "Bumpy / Damaged (Rough)"
    LOOSE = "loose"                # "Loose & Slippery (Gravel)"
    MIXED = "mixed"                # "Mixed (Tarmac/Gravel)"
    ICE = "ice"                    # "Ice (Packed Snow)"
    DEEP_GRAVEL = "deep_gravel"    # "Deep Gravel/Ruts"
    WET_MUD = "wet_mud"            # "Wet Mud/Clay"


class Weather(Enum):
    DRY = "dry"
    DAMP = "damp"          # "Damp / Humid"
    WET = "wet"            # "Wet / Heavy Rain"
    FOG = "fog"            # "Fog/Mist"
    COLD = "cold"          # "Cold (Below 5°C)"
    HOT = "hot"            # "Hot (Above 25°C)"


class CarClass(Enum):
    GROUP_A_4WD = "group_a_4wd"       # "Group A (4WD) - Lancia Delta"
    WRC = "wrc"                        # "WRC (2017+) (4WD)"
    R5_RALLY2 = "r5_rally2"           # "R5 / Rally2 (4WD)"
    GROUP_B_4WD = "group_b_4wd"       # "Group B (4WD) - Historic"
    GROUP_B_RWD = "group_b_rwd"       # "Group B (RWD) - Historic"
    RALLY4_RWD = "rally4_rwd"         # "Modern RWD - Rally4"
    FWD_KITCAR = "fwd_kitcar"         # "FWD (KitCar/Rally4)"
    RWD_HISTORIC = "rwd_historic"     # "RWD (Historic) - Escort/BMW"
    RALLY_GT = "rally_gt"             # "Rally GT (RWD) - Porsche/Mustang"
    CROSSKART = "crosskart"           # "Crosskart (AWD)" - Not in original
    GROUP_S = "group_s"               # "Group S (Prototype)" - Not in original


# =============================================================================
# DATA CLASSES - Setup Components (using original units)
# =============================================================================

@dataclass
class SuspensionSetup:
    """Suspension settings - exact original units"""
    spring_rate_front: int      # N/m
    spring_rate_rear: int       # N/m
    ride_height_front: float    # meters (e.g., 0.051)
    ride_height_rear: float     # meters
    camber_front: float         # degrees (negative)
    camber_rear: float          # degrees (negative)
    toe_front: float            # raw value (e.g., -0.0005)
    toe_rear: float             # raw value (e.g., 0.0005)
    caster: float = 5.0         # degrees


@dataclass
class DamperSetup:
    """Damper settings in N/m/s - exact original values"""
    slow_bump_front: int        # N/m/s
    slow_bump_rear: int         # N/m/s
    slow_rebound_front: int     # N/m/s (~1.6x bump)
    slow_rebound_rear: int      # N/m/s
    fast_bump_front: int        # N/m/s
    fast_bump_rear: int         # N/m/s
    fast_rebound_front: int     # N/m/s
    fast_rebound_rear: int      # N/m/s


@dataclass
class DifferentialSetup:
    """Differential settings - ramp angles in degrees"""
    # Lower ramp angles = More lock (Aggressive)
    # Higher angles = Less lock (Smooth)
    front_accel: int            # degrees (power ramp)
    front_coast: int            # degrees (decel ramp)
    front_preload: int          # Nm
    rear_accel: int             # degrees
    rear_coast: int             # degrees
    rear_preload: int           # Nm


@dataclass
class BrakeSetup:
    """Brake settings"""
    bias: float                 # decimal (e.g., 0.65 = 65%)
    pressure: int               # percentage


@dataclass
class AntiRollBarSetup:
    """Anti-roll bar stiffness in Nm"""
    front: int                  # Nm
    rear: int                   # Nm


@dataclass
class FullSetup:
    """Complete car setup"""
    name: str
    car_class: str
    surface: str
    track_condition: str
    weather: str
    traction: str               # "4WD", "FWD", "RWD"
    engineering_profile: str
    suspension: SuspensionSetup
    dampers: DamperSetup
    differential: DifferentialSetup
    brakes: BrakeSetup
    arb: AntiRollBarSetup
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "car_class": self.car_class,
            "surface": self.surface,
            "track_condition": self.track_condition,
            "weather": self.weather,
            "traction": self.traction,
            "engineering_profile": self.engineering_profile,
            "suspension": asdict(self.suspension),
            "dampers": asdict(self.dampers),
            "differential": asdict(self.differential),
            "brakes": asdict(self.brakes),
            "arb": asdict(self.arb),
            "notes": self.notes
        }

    def save_to_file(self, filepath: str) -> None:
        """Save setup to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'FullSetup':
        """Load setup from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        return cls(
            name=data["name"],
            car_class=data["car_class"],
            surface=data["surface"],
            track_condition=data["track_condition"],
            weather=data["weather"],
            traction=data.get("traction", "4WD"),
            engineering_profile=data.get("engineering_profile", ""),
            suspension=SuspensionSetup(**data["suspension"]),
            dampers=DamperSetup(**data["dampers"]),
            differential=DifferentialSetup(**data["differential"]),
            brakes=BrakeSetup(**data["brakes"]),
            arb=AntiRollBarSetup(**data["arb"]),
            notes=data.get("notes", "")
        )


# =============================================================================
# BASE SETUP - Exact values from original ACR Car Setup Pro
# =============================================================================

# This is the base setup (Group A / Lancia Delta) from the original application
BASE_SETUP = {
    # Geometry
    "FrontCamber": -1.7,
    "RearCamber": -2.3,
    "FrontToe": -0.0005,
    "RearToe": 0.0005,
    "Caster": 5.0,

    # Suspension (N/m)
    "RideHeightF": 0.051,
    "RideHeightR": 0.048,
    "SpringRateF": 70000,
    "SpringRateR": 50000,
    "ARBFront": 18500,
    "ARBRear": 16500,

    # Dampers (N/m/s)
    "SlowBumpF": 5000,
    "SlowReboundF": 8000,
    "FastBumpF": 3500,
    "FastReboundF": 5250,
    "SlowBumpR": 4000,
    "SlowReboundR": 6250,
    "FastBumpR": 2500,
    "FastReboundR": 4500,

    # Brakes
    "BrakeBias": 0.65,
    "BrakePressure": 95,

    # Differentials (degrees)
    "FrontDiffAccel": 60,
    "FrontDiffDecel": 75,
    "FrontDiffPreload": 0,
    "RearDiffAccel": 45,
    "RearDiffDecel": 70,
    "RearDiffPreload": 0,
}


# =============================================================================
# CAR CLASS CONFIGURATIONS - Exact values from original
# =============================================================================

CAR_CLASS_CONFIGS = {
    CarClass.GROUP_A_4WD: {
        "name": "Group A (4WD) - Lancia Delta",
        "philosophy": "ACR Reference: High Front Stiffness, Sharp Entry",
        "traction": "4WD",
        # Uses base setup values
    },

    CarClass.WRC: {
        "name": "WRC (2017+) (4WD)",
        "philosophy": "WRC Aero Platform: Maximum Downforce",
        "traction": "4WD",
        "SpringRateF": 110000,
        "SpringRateR": 95000,
        "ARBFront": 40000,
        "ARBRear": 35000,
        "RideHeightF": 0.025,
        "RideHeightR": 0.030,
        "FrontCamber": -2.5,
        "RearCamber": -2.2,
        "BrakeBias": 0.58,
        # Note: Original uses "Active Map 5" for diffs, we use numeric
        "FrontDiffAccel": 50,
        "FrontDiffDecel": 60,
        "RearDiffAccel": 50,
        "RearDiffDecel": 60,
    },

    CarClass.R5_RALLY2: {
        "name": "R5 / Rally2 (4WD)",
        "philosophy": "R5 Platform: Balanced Performance",
        "traction": "4WD",
        "SpringRateF": 85000,
        "SpringRateR": 65000,
        "ARBFront": 25000,
        "ARBRear": 22000,
        "RideHeightF": 0.040,
        "RideHeightR": 0.045,
        "FrontCamber": -2.2,
        "RearCamber": -2.0,
        "FrontDiffAccel": 45,
        "FrontDiffDecel": 60,
        "FrontDiffPreload": 10,
        "RearDiffAccel": 45,
        "RearDiffDecel": 45,
        "RearDiffPreload": 20,
    },

    CarClass.GROUP_B_4WD: {
        "name": "Group B (4WD) - Historic",
        "philosophy": "Group B 4WD: Raw Power Management",
        "traction": "4WD",
        "SpringRateF": 60000,
        "SpringRateR": 45000,
        "ARBFront": 15000,
        "ARBRear": 12000,
        "RideHeightF": 0.055,
        "RideHeightR": 0.060,
        "FrontDiffAccel": 50,
        "FrontDiffDecel": 65,
        "RearDiffAccel": 40,
        "RearDiffDecel": 60,
    },

    CarClass.GROUP_B_RWD: {
        "name": "Group B (RWD) - Historic",
        "philosophy": "Group B RWD: Power Oversteer Control",
        "traction": "RWD",
        "SpringRateF": 50000,
        "SpringRateR": 35000,
        "ARBFront": 10000,
        "ARBRear": 5000,
        "RideHeightF": 0.065,
        "RideHeightR": 0.070,
        "RearDiffAccel": 35,
        "RearDiffDecel": 45,
        "RearDiffPreload": 50,
        "BrakeBias": 0.54,
    },

    CarClass.RALLY4_RWD: {
        "name": "Modern RWD - Rally4",
        "philosophy": "Modern RWD: Precision Handling",
        "traction": "RWD",
        "SpringRateF": 55000,
        "SpringRateR": 45000,
        "ARBFront": 18000,
        "ARBRear": 8000,
        "RideHeightF": 0.050,
        "RideHeightR": 0.055,
        "RearDiffAccel": 40,
        "RearDiffDecel": 55,
        "RearDiffPreload": 25,
    },

    CarClass.FWD_KITCAR: {
        "name": "FWD (KitCar/Rally4)",
        "philosophy": "FWD: Front Traction Priority",
        "traction": "FWD",
        "SpringRateF": 90000,
        "SpringRateR": 100000,
        "ARBFront": 20000,
        "ARBRear": 45000,
        "RideHeightF": 0.045,
        "RideHeightR": 0.055,
        "FrontDiffAccel": 30,
        "FrontDiffDecel": 60,
        "FrontDiffPreload": 60,
        "BrakeBias": 0.72,
    },

    CarClass.RWD_HISTORIC: {
        "name": "RWD (Historic) - Escort/BMW",
        "philosophy": "Historic RWD: Mechanical Grip",
        "traction": "RWD",
        "SpringRateF": 45000,
        "SpringRateR": 40000,
        "ARBFront": 12000,
        "ARBRear": 5000,
        "RideHeightF": 0.065,
        "RideHeightR": 0.070,
        "RearDiffAccel": 40,
        "RearDiffDecel": 40,
        "RearDiffPreload": 40,
    },

    CarClass.RALLY_GT: {
        "name": "Rally GT (RWD) - Porsche/Mustang",
        "philosophy": "Rally GT: Power Delivery Control",
        "traction": "RWD",
        "SpringRateF": 75000,
        "SpringRateR": 60000,
        "ARBFront": 22000,
        "ARBRear": 15000,
        "RideHeightF": 0.060,
        "RideHeightR": 0.065,
        "RearDiffAccel": 45,
        "RearDiffDecel": 60,
        "RearDiffPreload": 30,
    },

    # These were not in original - using estimated values
    CarClass.CROSSKART: {
        "name": "Crosskart (AWD)",
        "philosophy": "Crosskart: Lightweight Chassis Dynamics",
        "traction": "4WD",
        "SpringRateF": 40000,
        "SpringRateR": 38000,
        "ARBFront": 10000,
        "ARBRear": 8000,
        "RideHeightF": 0.070,
        "RideHeightR": 0.075,
        "FrontDiffAccel": 55,
        "FrontDiffDecel": 70,
        "RearDiffAccel": 50,
        "RearDiffDecel": 65,
    },

    CarClass.GROUP_S: {
        "name": "Group S (Prototype)",
        "philosophy": "Group S: Experimental Advanced Setup",
        "traction": "4WD",
        "SpringRateF": 100000,
        "SpringRateR": 85000,
        "ARBFront": 35000,
        "ARBRear": 30000,
        "RideHeightF": 0.030,
        "RideHeightR": 0.035,
        "FrontCamber": -2.8,
        "RearCamber": -2.5,
        "FrontDiffAccel": 45,
        "FrontDiffDecel": 55,
        "RearDiffAccel": 40,
        "RearDiffDecel": 55,
    },
}


# =============================================================================
# SETUP CALCULATOR ENGINE - Exact logic from original
# =============================================================================

class SetupCalculator:
    """Main calculator engine - matches original ACR Car Setup Pro logic exactly"""

    def __init__(self):
        pass

    def calculate_setup(
        self,
        car_class: CarClass,
        surface: Surface,
        track_condition: TrackCondition,
        weather: Weather,
        setup_name: str = "Custom Setup"
    ) -> FullSetup:
        """
        Calculate a complete setup matching the original application logic.

        Order of operations (from original):
        1. Start with base setup
        2. Apply car class modifications
        3. Apply surface modifications
        4. Apply track condition modifications
        5. Apply weather modifications
        """

        # Start with base setup (copy)
        setup = BASE_SETUP.copy()

        # Get car class config
        car_config = CAR_CLASS_CONFIGS[car_class]
        engineering_profile = car_config["philosophy"]
        traction = car_config["traction"]

        # Apply car class modifications
        for key, value in car_config.items():
            if key not in ["name", "philosophy", "traction"]:
                setup[key] = value

        # Apply surface modifications
        setup, engineering_profile = self._apply_surface_mods(
            setup, surface, engineering_profile
        )

        # Apply track condition modifications
        setup, engineering_profile = self._apply_track_condition_mods(
            setup, track_condition, engineering_profile
        )

        # Apply weather modifications
        setup, engineering_profile = self._apply_weather_mods(
            setup, weather, engineering_profile
        )

        # Build final setup object
        return FullSetup(
            name=setup_name,
            car_class=car_config["name"],
            surface=surface.value,
            track_condition=track_condition.value,
            weather=weather.value,
            traction=traction,
            engineering_profile=engineering_profile,
            suspension=SuspensionSetup(
                spring_rate_front=setup["SpringRateF"],
                spring_rate_rear=setup["SpringRateR"],
                ride_height_front=setup["RideHeightF"],
                ride_height_rear=setup["RideHeightR"],
                camber_front=setup["FrontCamber"],
                camber_rear=setup["RearCamber"],
                toe_front=setup["FrontToe"],
                toe_rear=setup["RearToe"],
                caster=setup["Caster"],
            ),
            dampers=DamperSetup(
                slow_bump_front=setup["SlowBumpF"],
                slow_bump_rear=setup["SlowBumpR"],
                slow_rebound_front=setup["SlowReboundF"],
                slow_rebound_rear=setup["SlowReboundR"],
                fast_bump_front=setup["FastBumpF"],
                fast_bump_rear=setup["FastBumpR"],
                fast_rebound_front=setup["FastReboundF"],
                fast_rebound_rear=setup["FastReboundR"],
            ),
            differential=DifferentialSetup(
                front_accel=setup["FrontDiffAccel"],
                front_coast=setup["FrontDiffDecel"],
                front_preload=setup["FrontDiffPreload"],
                rear_accel=setup["RearDiffAccel"],
                rear_coast=setup["RearDiffDecel"],
                rear_preload=setup["RearDiffPreload"],
            ),
            brakes=BrakeSetup(
                bias=setup["BrakeBias"],
                pressure=setup["BrakePressure"],
            ),
            arb=AntiRollBarSetup(
                front=setup["ARBFront"],
                rear=setup["ARBRear"],
            ),
        )

    def _apply_surface_mods(self, setup: dict, surface: Surface, profile: str) -> tuple:
        """Apply surface modifications - exact multipliers from original"""

        if surface == Surface.GRAVEL:
            profile += " | Gravel Compliance"

            # Springs: × 0.65
            setup["SpringRateF"] = int(round(setup["SpringRateF"] * 0.65))
            setup["SpringRateR"] = int(round(setup["SpringRateR"] * 0.65))

            # ARB: Front × 0.45, Rear × 0.40
            setup["ARBFront"] = int(round(setup["ARBFront"] * 0.45))
            setup["ARBRear"] = int(round(setup["ARBRear"] * 0.40))

            # Ride height: +0.030 F, +0.035 R
            setup["RideHeightF"] += 0.030
            setup["RideHeightR"] += 0.035

            # Camber: -1.0 both
            setup["FrontCamber"] = -1.0
            setup["RearCamber"] = -1.0

            # Dampers: × 0.6
            setup["SlowBumpF"] = int(round(setup["SlowBumpF"] * 0.6))
            setup["SlowReboundF"] = int(round(setup["SlowReboundF"] * 0.6))
            setup["FastBumpF"] = int(round(setup["FastBumpF"] * 0.6))
            setup["FastReboundF"] = int(round(setup["FastReboundF"] * 0.6))
            setup["SlowBumpR"] = int(round(setup["SlowBumpR"] * 0.6))
            setup["SlowReboundR"] = int(round(setup["SlowReboundR"] * 0.6))
            setup["FastBumpR"] = int(round(setup["FastBumpR"] * 0.6))
            setup["FastReboundR"] = int(round(setup["FastReboundR"] * 0.6))

            # Diffs: Accel -10° (min 40 front, 35 rear)
            setup["FrontDiffAccel"] = max(40, setup["FrontDiffAccel"] - 10)
            setup["RearDiffAccel"] = max(35, setup["RearDiffAccel"] - 10)

        elif surface == Surface.SNOW:
            profile += " | Snow/Ice Compliance"

            # Springs: F × 0.5, R × 0.45
            setup["SpringRateF"] = int(round(setup["SpringRateF"] * 0.5))
            setup["SpringRateR"] = int(round(setup["SpringRateR"] * 0.45))

            # ARB: Front × 0.3, Rear × 0.25
            setup["ARBFront"] = int(round(setup["ARBFront"] * 0.3))
            setup["ARBRear"] = int(round(setup["ARBRear"] * 0.25))

            # Ride height: +0.055 F, +0.060 R
            setup["RideHeightF"] += 0.055
            setup["RideHeightR"] += 0.060

            # Camber: -0.5 both
            setup["FrontCamber"] = -0.5
            setup["RearCamber"] = -0.5

            # Diffs: Fixed values for snow
            setup["FrontDiffAccel"] = 80
            setup["FrontDiffDecel"] = 85
            setup["RearDiffAccel"] = 75
            setup["RearDiffDecel"] = 80

            # Brake bias
            setup["BrakeBias"] = 0.52

        # Asphalt = no modifications (baseline)

        return setup, profile

    def _apply_track_condition_mods(self, setup: dict, condition: TrackCondition, profile: str) -> tuple:
        """Apply track condition modifications - exact logic from original"""

        if condition == TrackCondition.BUMPY:
            profile += " | Bump Absorption"
            # Fast dampers × 0.7
            setup["FastBumpF"] = int(round(setup["FastBumpF"] * 0.7))
            setup["FastReboundF"] = int(round(setup["FastReboundF"] * 0.7))
            setup["FastBumpR"] = int(round(setup["FastBumpR"] * 0.7))
            setup["FastReboundR"] = int(round(setup["FastReboundR"] * 0.7))
            # Ride height F +0.005
            setup["RideHeightF"] += 0.005

        elif condition == TrackCondition.LOOSE:
            profile += " | Traction Priority"
            # Diff accel +15 front, +10 rear
            setup["FrontDiffAccel"] = setup["FrontDiffAccel"] + 15
            setup["RearDiffAccel"] = setup["RearDiffAccel"] + 10
            # Springs × 0.9
            setup["SpringRateF"] = int(round(setup["SpringRateF"] * 0.9))
            setup["SpringRateR"] = int(round(setup["SpringRateR"] * 0.9))

        elif condition == TrackCondition.ICE:
            profile += " | Ice Optimization"
            # Springs × 0.8 F, × 0.75 R
            setup["SpringRateF"] = int(round(setup["SpringRateF"] * 0.8))
            setup["SpringRateR"] = int(round(setup["SpringRateR"] * 0.75))
            # Diffs fixed
            setup["FrontDiffAccel"] = 85
            setup["RearDiffAccel"] = 80

        elif condition == TrackCondition.DEEP_GRAVEL:
            profile += " | Rut Management"
            # Ride height +0.010 both
            setup["RideHeightF"] += 0.010
            setup["RideHeightR"] += 0.010
            # Fast dampers × 0.6
            setup["FastBumpF"] = int(round(setup["FastBumpF"] * 0.6))
            setup["FastReboundF"] = int(round(setup["FastReboundF"] * 0.6))

        # SMOOTH, MIXED, WET_MUD = no specific modifications in original

        return setup, profile

    def _apply_weather_mods(self, setup: dict, weather: Weather, profile: str) -> tuple:
        """Apply weather modifications - exact logic from original"""

        if weather == Weather.DAMP:
            profile += " | Damp Conditions"
            # ARB × 0.8
            setup["ARBFront"] = int(round(setup["ARBFront"] * 0.8))
            setup["ARBRear"] = int(round(setup["ARBRear"] * 0.8))
            # Brake bias -0.02
            setup["BrakeBias"] -= 0.02

        elif weather == Weather.WET:
            profile += " | Wet Conditions"
            # Springs × 0.85
            setup["SpringRateF"] = int(round(setup["SpringRateF"] * 0.85))
            setup["SpringRateR"] = int(round(setup["SpringRateR"] * 0.85))
            # ARB × 0.6
            setup["ARBFront"] = int(round(setup["ARBFront"] * 0.6))
            setup["ARBRear"] = int(round(setup["ARBRear"] * 0.6))
            # Ride height +0.010
            setup["RideHeightF"] += 0.010
            setup["RideHeightR"] += 0.010
            # Brake bias -0.04
            setup["BrakeBias"] -= 0.04
            # Diff accel +10
            setup["FrontDiffAccel"] = setup["FrontDiffAccel"] + 10
            setup["RearDiffAccel"] = setup["RearDiffAccel"] + 10

        elif weather == Weather.COLD:
            profile += " | Cold Conditions"
            # Springs × 1.1
            setup["SpringRateF"] = int(round(setup["SpringRateF"] * 1.1))
            setup["SpringRateR"] = int(round(setup["SpringRateR"] * 1.1))

        elif weather == Weather.HOT:
            profile += " | Hot Conditions"
            # Springs × 0.95
            setup["SpringRateF"] = int(round(setup["SpringRateF"] * 0.95))
            setup["SpringRateR"] = int(round(setup["SpringRateR"] * 0.95))

        # DRY, FOG = no modifications in original

        return setup, profile

    def get_car_classes(self) -> list:
        """Return list of available car classes"""
        return [(c, CAR_CLASS_CONFIGS[c]["name"]) for c in CarClass]

    def get_surfaces(self) -> list:
        """Return list of surfaces"""
        return list(Surface)

    def get_track_conditions(self) -> list:
        """Return list of track conditions"""
        return list(TrackCondition)

    def get_weather_options(self) -> list:
        """Return list of weather options"""
        return list(Weather)


# =============================================================================
# CLI INTERFACE (for testing)
# =============================================================================

def print_setup(setup: FullSetup) -> None:
    """Print a setup matching original output format"""

    print("\n" + "=" * 60)
    print(f"  {setup.name}")
    print(f"  {setup.car_class}")
    print("=" * 60)

    print("\n--- ENGINEERING INPUTS ---")
    print(f"Surface: {setup.surface} | Car: {setup.car_class}")
    print(f"Condition: {setup.track_condition} | Weather: {setup.weather}")
    print(f"Engineering Profile: {setup.engineering_profile}")

    print("\n--- GEOMETRY & SUSPENSION (ENGINEERING SPEC) ---")
    print(f"Ride Height (F/R): {setup.suspension.ride_height_front:.3f} m / {setup.suspension.ride_height_rear:.3f} m")
    print(f"Spring Rate (F/R): {setup.suspension.spring_rate_front} N/m / {setup.suspension.spring_rate_rear} N/m")
    print(f"Anti-Roll Bar (F/R): {setup.arb.front} Nm / {setup.arb.rear} Nm")
    print(f"Camber (F/R): {setup.suspension.camber_front:.1f}° / {setup.suspension.camber_rear:.1f}°")
    print(f"Toe (F/R): {setup.suspension.toe_front:.4f} / {setup.suspension.toe_rear:.4f}")

    print("\n--- DAMPERS (N/m/s) [Engineering Ratios] ---")
    print(f"Slow Bump (F/R): {setup.dampers.slow_bump_front} / {setup.dampers.slow_bump_rear}")
    print(f"Slow Rebound (F/R): {setup.dampers.slow_rebound_front} / {setup.dampers.slow_rebound_rear}")
    print(f"Fast Bump (F/R): {setup.dampers.fast_bump_front} / {setup.dampers.fast_bump_rear}")
    print(f"Fast Rebound (F/R): {setup.dampers.fast_rebound_front} / {setup.dampers.fast_rebound_rear}")

    print("\n--- BRAKES ---")
    print(f"Brake Bias: {setup.brakes.bias:.2f}")
    print(f"Brake Pressure: {setup.brakes.pressure}%")

    print("\n--- DIFFERENTIAL ENGINEERING (ACR) ---")
    print("Engineering Logic: Lower Angle = MORE Lock (Aggressive)")
    print("                   Higher Angle = LESS Lock (Smooth)")

    if setup.traction in ["FWD", "4WD"]:
        print("\n--- FRONT DIFFERENTIAL ---")
        print(f"Accel Ramp (Power): {setup.differential.front_accel}°")
        print(f"Coast Ramp (Decel): {setup.differential.front_coast}°")
        print(f"Preload: {setup.differential.front_preload} Nm")

    if setup.traction in ["RWD", "4WD"]:
        print("\n--- REAR DIFFERENTIAL ---")
        print(f"Accel Ramp (Power): {setup.differential.rear_accel}°")
        print(f"Coast Ramp (Decel): {setup.differential.rear_coast}°")
        print(f"Preload: {setup.differential.rear_preload} Nm")

    if setup.traction == "4WD":
        print("\n--- CENTER DIFFERENTIAL ---")
        print("Torque Split: 50/50 (Default)")
        print("Note: Adjust in-car for specific stage requirements")

    print("\n" + "=" * 60)


def main():
    """Main entry point for CLI testing"""

    calculator = SetupCalculator()

    print("\n🏎️ Rally Car Setup Calculator")
    print("Exact values from ACR Car Setup Pro - Engineering Edition\n")

    # Test: Group A + Gravel + Bumpy + Wet (complex case)
    setup = calculator.calculate_setup(
        car_class=CarClass.GROUP_A_4WD,
        surface=Surface.GRAVEL,
        track_condition=TrackCondition.BUMPY,
        weather=Weather.WET,
        setup_name="Finland Gravel Stage - Wet"
    )

    print_setup(setup)

    # Verify key calculation:
    # Base SpringRateF = 70000
    # Gravel: × 0.65 = 45500
    # Wet: × 0.85 = 38675
    print(f"\nVerification - SpringRateF should be ~38675: {setup.suspension.spring_rate_front}")

    # Save example
    save_path = Path(__file__).parent / "example_setup.json"
    setup.save_to_file(str(save_path))
    print(f"\nSetup saved to: {save_path}")


if __name__ == "__main__":
    main()
