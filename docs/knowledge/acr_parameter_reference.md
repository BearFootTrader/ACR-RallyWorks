# ACR Parameter Reference

This list mirrors the parameter paths used in the ACR setup files. Values and units are shown as they commonly appear in the data.

## Drivetrain
- drivetrain.gearsSet: named gearset preset.
- drivetrain.frontBias: front torque bias in percent.
- drivetrain.centreDiffRatio: center diff ratio pair (format like 50//12).
- drivetrain.frontDiff.ratio: front diff ratio pair.
- drivetrain.frontDiff.lsdRampAngle: power and coast ramp angle pair (format like 60_75).
- drivetrain.frontDiff.lsdPlates: number of clutch plates.
- drivetrain.frontDiff.lsdPreload: preload torque in Nm.
- drivetrain.rearDiff.ratio: rear diff ratio pair.
- drivetrain.rearDiff.lsdRampAngle: power and coast ramp angle pair.
- drivetrain.rearDiff.lsdPlates: number of clutch plates.
- drivetrain.rearDiff.lsdPreload: preload torque in Nm.

## Suspension
- suspension.frontARB: front anti-roll bar rate (N/m).
- suspension.rearARB: rear anti-roll bar rate (N/m).
- suspension.springs.FL: front left spring rate (N/m).
- suspension.springs.FR: front right spring rate (N/m).
- suspension.springs.RL: rear left spring rate (N/m).
- suspension.springs.RR: rear right spring rate (N/m).
- suspension.rideHeight.FL: front left ride height (mm).
- suspension.rideHeight.FR: front right ride height (mm).
- suspension.rideHeight.RL: rear left ride height (mm).
- suspension.rideHeight.RR: rear right ride height (mm).

## Dampers
- dampers.FL.slowBump: front left slow bump.
- dampers.FL.slowRebound: front left slow rebound.
- dampers.FL.fastBump: front left fast bump.
- dampers.FL.fastRebound: front left fast rebound.
- dampers.FR.slowBump: front right slow bump.
- dampers.FR.slowRebound: front right slow rebound.
- dampers.FR.fastBump: front right fast bump.
- dampers.FR.fastRebound: front right fast rebound.
- dampers.RL.slowBump: rear left slow bump.
- dampers.RL.slowRebound: rear left slow rebound.
- dampers.RL.fastBump: rear left fast bump.
- dampers.RL.fastRebound: rear left fast rebound.
- dampers.RR.slowBump: rear right slow bump.
- dampers.RR.slowRebound: rear right slow rebound.
- dampers.RR.fastBump: rear right fast bump.
- dampers.RR.fastRebound: rear right fast rebound.

## Tyres
- tyres.FL.pressure: front left pressure (PSI).
- tyres.FL.camber: front left camber (deg).
- tyres.FL.toe: front left toe (deg or mm).
- tyres.FR.pressure: front right pressure (PSI).
- tyres.FR.camber: front right camber (deg).
- tyres.FR.toe: front right toe (deg or mm).
- tyres.RL.pressure: rear left pressure (PSI).
- tyres.RL.camber: rear left camber (deg).
- tyres.RL.toe: rear left toe (deg or mm).
- tyres.RR.pressure: rear right pressure (PSI).
- tyres.RR.camber: rear right camber (deg).
- tyres.RR.toe: rear right toe (deg or mm).
- Reference gravel geometry (Suspension Secrets WRC base): front camber -1.5 to -3.0 deg; rear -1.0 to -2.0 deg; front toe 0 to 2 mm out; rear toe 1 to 3 mm in. (Caster is not exposed in the ACR data but is typically around +6 deg in that guide.)

## Brakes
- brakes.brakeBias: front brake bias in percent.
- brakes.propValvePressure: brake pressure scaling value.
- brakes.handbrakeMultiplier: handbrake strength multiplier.
