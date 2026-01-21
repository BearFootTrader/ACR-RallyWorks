"""
RallyWorks+ Setup Calculator

Generates optimized setup suggestions for ACR based on:
1. ACR default values as baseline
2. DiRT Rally 2.0 community setup tendencies (directional guidance)
3. Real rally engineering principles (damper ratios, surface modifiers)
4. Min/max range clamping for the Lancia Delta HF Integrale Evo

Key principles from rally engineering:
- Gravel needs softer suspension than tarmac
- Damper ratio: Slow Rebound is ~60% higher than Slow Bump (1.6:1 ratio)
- ARB: Rear often softened or disconnected on gravel
- Springs: Front stiffer than rear for stability ("Stiff Front / Soft Rear")
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class ACRRanges:
    """Min/max ranges for Lancia Delta HF Integrale Evo setup parameters."""
    # Springs (N/m)
    spring_front_min: int = 40000
    spring_front_max: int = 75000
    spring_rear_min: int = 30000
    spring_rear_max: int = 55000

    # Dampers (Ns/m)
    front_slow_bump_min: int = 3500
    front_slow_bump_max: int = 6500
    front_slow_rebound_min: int = 5500
    front_slow_rebound_max: int = 12500
    front_fast_bump_min: int = 2000
    front_fast_bump_max: int = 4500
    front_fast_rebound_min: int = 3000
    front_fast_rebound_max: int = 6000

    rear_slow_bump_min: int = 3000
    rear_slow_bump_max: int = 6000
    rear_slow_rebound_min: int = 4500
    rear_slow_rebound_max: int = 9000
    rear_fast_bump_min: int = 1500
    rear_fast_bump_max: int = 4000
    rear_fast_rebound_min: int = 3000
    rear_fast_rebound_max: int = 6000

    # ARB (N/m)
    arb_front_min: int = 12000
    arb_front_max: int = 23000
    arb_rear_min: int = 4000
    arb_rear_max: int = 22000

    # Ride Height (mm) - converted from meters (0.0000m - 0.2000m = 0-200mm)
    ride_height_min: float = 0.0
    ride_height_max: float = 200.0

    # LSD Preload (Nm)
    lsd_preload_rear_min: float = 0.0
    lsd_preload_rear_max: float = 250.0

    # Camber (degrees)
    camber_front_min: float = -3.5
    camber_front_max: float = 1.0
    camber_rear_min: float = -3.7
    camber_rear_max: float = 1.0

    # Toe (meters) - ACR uses meters for toe
    toe_min: float = -0.0100
    toe_max: float = 0.0100

    # Brake bias (as decimal)
    brake_bias_min: float = 0.350
    brake_bias_max: float = 0.800


# Lancia Delta HF ACR default values (gravel setup from car_setups_gravel.tsv)
LANCIA_DELTA_DEFAULTS = {
    "spring_front": 40000,      # N/m
    "spring_rear": 40000,       # N/m
    "arb_front": 11500,         # N/m
    "arb_rear": 13500,          # N/m
    "ride_height_front": 130.0,  # mm
    "ride_height_rear": 100.0,   # mm
    "front_slow_bump": 4250,    # Ns/m
    "front_slow_rebound": 9000,
    "front_fast_bump": 2500,
    "front_fast_rebound": 5000,
    "rear_slow_bump": 3750,
    "rear_slow_rebound": 6750,
    "rear_fast_bump": 2500,
    "rear_fast_rebound": 4500,
    "camber_front": -2.4,       # degrees
    "camber_rear": -2.6,
    "toe_front": 0.006,         # degrees (displayed)
    "toe_rear": 0.0,
    "brake_bias": 67,           # % front
    "front_lsd_ramp": "60_75",
    "front_lsd_preload": 60,    # Nm
    "rear_lsd_ramp": "45_70",
    "rear_lsd_preload": 90,     # Nm
}

# DiRT Rally 2.0 community setup tendencies (relative to default)
# These are directional modifiers based on analyzing DiRT community setups
# Combined with rally engineering principles for a balanced approach
DIRT_GRAVEL_TENDENCIES = {
    # Springs: DiRT community tends to run STIFFER springs for better control
    # DiRT showed ~78000 N/m front, ~71000 N/m rear preferences
    # We'll use a more moderate increase that stays in range
    "spring_front_modifier": 1.50,   # 40000 * 1.5 = 60000 N/m (within 40-75k range)
    "spring_rear_modifier": 1.30,    # 40000 * 1.3 = 52000 N/m (within 30-55k range)

    # ARB: DiRT community prefers SOFTER ARBs for gravel compliance
    # This matches rally engineering (rear soft/disconnected on gravel)
    "arb_front_modifier": 1.04,      # Keep front near minimum: 11500 * 1.04 = 12000
    "arb_rear_modifier": 0.50,       # Softer rear: 13500 * 0.5 = 6750 (clamped to min 4000)

    # Ride height: Community prefers LOWER for better CG and handling
    # But we need to stay reasonable for gravel
    "ride_height_front": 100.0,      # Lower than 130mm default
    "ride_height_rear": 85.0,        # Lower than 100mm default

    # Dampers: Based on DiRT relative scale interpretation
    # DiRT: Front Bump -1 (softer), Rebound +1 (stiffer)
    # DiRT: Rear Bump -3 (much softer), Rebound +2 (stiffer)
    # Applying these as percentage modifiers to ACR defaults
    "front_slow_bump_modifier": 0.90,    # Slightly softer
    "front_slow_rebound_modifier": 1.10, # Slightly stiffer
    "rear_slow_bump_modifier": 0.80,     # Softer
    "rear_slow_rebound_modifier": 1.15,  # Stiffer

    # Fast dampers: Scale proportionally based on slow damper direction
    "front_fast_bump_modifier": 0.92,
    "front_fast_rebound_modifier": 1.08,
    "rear_fast_bump_modifier": 0.85,
    "rear_fast_rebound_modifier": 1.10,

    # Alignment: DiRT community setups (direct values)
    "camber_front": -1.50,   # Less negative than ACR default
    "camber_rear": -0.40,    # Much less negative
    "toe_front": 0.00,       # Neutral
    "toe_rear": -0.20,       # Slight toe-out

    # Brakes
    "brake_bias": 66,        # Slightly less front bias

    # Differentials: Based on DiRT lock % converted to ACR ramp angles
    # DiRT: Front 28/32%, Rear 36/36% - indicates preference for more open diffs
    "front_lsd_ramp": "55_85",   # Less aggressive than default 60_75
    "front_lsd_preload": 40,     # Lower preload (from 60)
    "rear_lsd_ramp": "55_75",    # Moderate adjustment from 45_70
    "rear_lsd_preload": 70,      # Lower preload (from 90)

    # Centre diff: DiRT torque bias 70% rear = 30% front in ACR terms
    "front_bias": 30,
    "centre_diff_ratio": "50//12",

    # Gearing recommendation
    "gear_set": "Set 2 (Balanced)",
}


@dataclass
class RallyWorksSetup:
    """Container for RallyWorks+ calculated setup data."""
    car: str
    surface: str
    source: str

    # Springs (N/m)
    spring_front: int
    spring_rear: int

    # ARB (N/m)
    arb_front: int
    arb_rear: int

    # Ride Height (mm)
    ride_height_front: float
    ride_height_rear: float

    # Dampers (Ns/m)
    front_slow_bump: int
    front_slow_rebound: int
    front_fast_bump: int
    front_fast_rebound: int
    rear_slow_bump: int
    rear_slow_rebound: int
    rear_fast_bump: int
    rear_fast_rebound: int

    # Alignment
    camber_front: float
    camber_rear: float
    toe_front: float
    toe_rear: float

    # Brakes
    brake_bias: float

    # Differentials
    front_lsd_ramp_accel: int
    front_lsd_ramp_decel: int
    front_lsd_preload: float
    rear_lsd_ramp_accel: int
    rear_lsd_ramp_decel: int
    rear_lsd_preload: float
    front_bias: float
    centre_diff_ratio: str

    # Gearing
    gear_set_recommendation: str


class DirtConverter:
    """
    Generates RallyWorks+ setups based on DiRT community tendencies
    and rally engineering principles.
    """

    def __init__(self):
        self.ranges = ACRRanges()
        self.rallyworks_setups: Dict[str, Dict[str, RallyWorksSetup]] = {}

    def clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value to within min/max range."""
        return max(min_val, min(max_val, value))

    def calculate_value(self, base: float, modifier: float, min_val: float, max_val: float) -> int:
        """Calculate new value with modifier, clamped to range."""
        new_value = base * modifier
        clamped = self.clamp(new_value, min_val, max_val)
        return int(round(clamped))

    def parse_ramp_angle(self, ramp_str: str) -> Tuple[int, int]:
        """Parse ramp angle string like '60_75' into (accel, decel)."""
        parts = ramp_str.split('_')
        return int(parts[0]), int(parts[1])

    def generate_rallyworks_setup(self, car: str, surface: str) -> RallyWorksSetup:
        """
        Generate a RallyWorks+ setup for the given car and surface.
        Currently only supports Lancia Delta HF Integrale Evo on gravel.
        """
        defaults = LANCIA_DELTA_DEFAULTS
        tendencies = DIRT_GRAVEL_TENDENCIES
        r = self.ranges

        # Calculate springs (clamped to ACR ranges)
        spring_front = self.calculate_value(
            defaults["spring_front"],
            tendencies["spring_front_modifier"],
            r.spring_front_min, r.spring_front_max
        )
        spring_rear = self.calculate_value(
            defaults["spring_rear"],
            tendencies["spring_rear_modifier"],
            r.spring_rear_min, r.spring_rear_max
        )

        # Calculate ARBs (clamped to ACR ranges)
        arb_front = self.calculate_value(
            defaults["arb_front"],
            tendencies["arb_front_modifier"],
            r.arb_front_min, r.arb_front_max
        )
        arb_rear = self.calculate_value(
            defaults["arb_rear"],
            tendencies["arb_rear_modifier"],
            r.arb_rear_min, r.arb_rear_max
        )

        # Ride height (direct values, clamped)
        ride_height_front = self.clamp(
            tendencies["ride_height_front"],
            r.ride_height_min, r.ride_height_max
        )
        ride_height_rear = self.clamp(
            tendencies["ride_height_rear"],
            r.ride_height_min, r.ride_height_max
        )

        # Calculate dampers
        front_slow_bump = self.calculate_value(
            defaults["front_slow_bump"],
            tendencies["front_slow_bump_modifier"],
            r.front_slow_bump_min, r.front_slow_bump_max
        )
        front_slow_rebound = self.calculate_value(
            defaults["front_slow_rebound"],
            tendencies["front_slow_rebound_modifier"],
            r.front_slow_rebound_min, r.front_slow_rebound_max
        )
        front_fast_bump = self.calculate_value(
            defaults["front_fast_bump"],
            tendencies["front_fast_bump_modifier"],
            r.front_fast_bump_min, r.front_fast_bump_max
        )
        front_fast_rebound = self.calculate_value(
            defaults["front_fast_rebound"],
            tendencies["front_fast_rebound_modifier"],
            r.front_fast_rebound_min, r.front_fast_rebound_max
        )

        rear_slow_bump = self.calculate_value(
            defaults["rear_slow_bump"],
            tendencies["rear_slow_bump_modifier"],
            r.rear_slow_bump_min, r.rear_slow_bump_max
        )
        rear_slow_rebound = self.calculate_value(
            defaults["rear_slow_rebound"],
            tendencies["rear_slow_rebound_modifier"],
            r.rear_slow_rebound_min, r.rear_slow_rebound_max
        )
        rear_fast_bump = self.calculate_value(
            defaults["rear_fast_bump"],
            tendencies["rear_fast_bump_modifier"],
            r.rear_fast_bump_min, r.rear_fast_bump_max
        )
        rear_fast_rebound = self.calculate_value(
            defaults["rear_fast_rebound"],
            tendencies["rear_fast_rebound_modifier"],
            r.rear_fast_rebound_min, r.rear_fast_rebound_max
        )

        # Alignment (clamped)
        camber_front = self.clamp(
            tendencies["camber_front"],
            r.camber_front_min, r.camber_front_max
        )
        camber_rear = self.clamp(
            tendencies["camber_rear"],
            r.camber_rear_min, r.camber_rear_max
        )

        # Toe values
        toe_front = tendencies["toe_front"]
        toe_rear = tendencies["toe_rear"]

        # Brakes
        brake_bias = self.clamp(
            tendencies["brake_bias"],
            r.brake_bias_min * 100, r.brake_bias_max * 100
        )

        # Differentials
        front_accel, front_decel = self.parse_ramp_angle(tendencies["front_lsd_ramp"])
        rear_accel, rear_decel = self.parse_ramp_angle(tendencies["rear_lsd_ramp"])

        front_lsd_preload = self.clamp(tendencies["front_lsd_preload"], 0, 250)
        rear_lsd_preload = self.clamp(tendencies["rear_lsd_preload"], r.lsd_preload_rear_min, r.lsd_preload_rear_max)

        return RallyWorksSetup(
            car=car,
            surface=surface,
            source="DiRT Rally 2.0 + Rally Engineering",
            spring_front=spring_front,
            spring_rear=spring_rear,
            arb_front=arb_front,
            arb_rear=arb_rear,
            ride_height_front=round(ride_height_front, 1),
            ride_height_rear=round(ride_height_rear, 1),
            front_slow_bump=front_slow_bump,
            front_slow_rebound=front_slow_rebound,
            front_fast_bump=front_fast_bump,
            front_fast_rebound=front_fast_rebound,
            rear_slow_bump=rear_slow_bump,
            rear_slow_rebound=rear_slow_rebound,
            rear_fast_bump=rear_fast_bump,
            rear_fast_rebound=rear_fast_rebound,
            camber_front=camber_front,
            camber_rear=camber_rear,
            toe_front=toe_front,
            toe_rear=toe_rear,
            brake_bias=brake_bias,
            front_lsd_ramp_accel=front_accel,
            front_lsd_ramp_decel=front_decel,
            front_lsd_preload=front_lsd_preload,
            rear_lsd_ramp_accel=rear_accel,
            rear_lsd_ramp_decel=rear_decel,
            rear_lsd_preload=rear_lsd_preload,
            front_bias=tendencies["front_bias"],
            centre_diff_ratio=tendencies["centre_diff_ratio"],
            gear_set_recommendation=tendencies["gear_set"]
        )

    def get_rallyworks_setup(self, car: str, surface: str) -> Optional[RallyWorksSetup]:
        """
        Get a RallyWorks+ setup for a car and surface.
        Currently only returns setup for Lancia Delta HF Integrale Evo on gravel.
        """
        if car == "Lancia Delta HF Integrale Evo" and surface == "gravel":
            return self.generate_rallyworks_setup(car, surface)
        return None

    def has_rallyworks_setup(self, car: str, surface: str) -> bool:
        """Check if a RallyWorks+ setup exists for this car/surface combo."""
        return car == "Lancia Delta HF Integrale Evo" and surface == "gravel"

    def compare_values(self, acr_value: float, rw_value: float) -> Tuple[str, str]:
        """
        Compare ACR and RallyWorks+ values to determine direction and color.
        Returns: (direction_symbol, color_code)
        - Increase: "↑", blue (#5DADE2)
        - Decrease: "↓", red (#E74C3C)
        - Same: "=", gray
        """
        # Handle string comparisons (for special values)
        if isinstance(acr_value, str) or isinstance(rw_value, str):
            return "=", "#888888"

        tolerance = 0.01  # Small tolerance for floating point comparison
        diff = float(rw_value) - float(acr_value)

        if abs(diff) < tolerance:
            return "=", "#888888"
        elif diff > 0:
            return "↑", "#5DADE2"  # Blue for increase
        else:
            return "↓", "#E74C3C"  # Red for decrease


def create_test_setup() -> DirtConverter:
    """
    Create the converter instance.
    The Lancia Delta HF gravel setup is generated on-demand.
    """
    return DirtConverter()


# Test the converter
if __name__ == "__main__":
    converter = create_test_setup()

    setup = converter.get_rallyworks_setup("Lancia Delta HF Integrale Evo", "gravel")
    if setup:
        print("RallyWorks+ Setup: Lancia Delta HF Integrale Evo (Gravel)")
        print("=" * 60)
        print(f"Source: {setup.source}")
        print()

        print("SUSPENSION")
        print(f"  Front Springs: {setup.spring_front} N/m")
        print(f"  Rear Springs: {setup.spring_rear} N/m")
        print(f"  Front ARB: {setup.arb_front} N/m")
        print(f"  Rear ARB: {setup.arb_rear} N/m")
        print(f"  Ride Height (F): {setup.ride_height_front} mm")
        print(f"  Ride Height (R): {setup.ride_height_rear} mm")
        print()

        print("DAMPERS")
        print(f"  Front Slow Bump: {setup.front_slow_bump} Ns/m")
        print(f"  Front Slow Rebound: {setup.front_slow_rebound} Ns/m")
        print(f"  Front Fast Bump: {setup.front_fast_bump} Ns/m")
        print(f"  Front Fast Rebound: {setup.front_fast_rebound} Ns/m")
        print(f"  Rear Slow Bump: {setup.rear_slow_bump} Ns/m")
        print(f"  Rear Slow Rebound: {setup.rear_slow_rebound} Ns/m")
        print(f"  Rear Fast Bump: {setup.rear_fast_bump} Ns/m")
        print(f"  Rear Fast Rebound: {setup.rear_fast_rebound} Ns/m")
        print()

        print("ALIGNMENT/TYRES")
        print(f"  Camber (F): {setup.camber_front}deg")
        print(f"  Camber (R): {setup.camber_rear}deg")
        print(f"  Toe (F): {setup.toe_front}deg")
        print(f"  Toe (R): {setup.toe_rear}deg")
        print()

        print("BRAKES")
        print(f"  Brake Bias: {setup.brake_bias}% front")
        print()

        print("DIFFERENTIAL")
        print(f"  Front LSD Ramp: {setup.front_lsd_ramp_accel}_{setup.front_lsd_ramp_decel}")
        print(f"  Front LSD Preload: {setup.front_lsd_preload} Nm")
        print(f"  Rear LSD Ramp: {setup.rear_lsd_ramp_accel}_{setup.rear_lsd_ramp_decel}")
        print(f"  Rear LSD Preload: {setup.rear_lsd_preload} Nm")
        print(f"  Front Bias: {setup.front_bias}%")
        print(f"  Centre Diff Ratio: {setup.centre_diff_ratio}")
        print()

        print("GEARING")
        print(f"  Recommendation: {setup.gear_set_recommendation}")
