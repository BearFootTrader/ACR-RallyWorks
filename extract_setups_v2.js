const fs = require('fs');
const path = require('path');

const setupsDir = path.join(__dirname, 'CarSetups');

// Car file mappings
const carFiles = [
    { file: 'DA_AlfaRomeoGiuliaGTAJunior1300Presets.json', name: 'Alfa Romeo Giulia GTA Junior 1300', drive: 'FWD' },
    { file: 'DA_AlpineA1101800Presets.json', name: 'Alpine A110 1800', drive: 'RWD' },
    { file: 'DA_CitroenXsaraWRCPresets.json', name: 'Citroen Xsara WRC', drive: 'AWD' },
    { file: 'DA_Fiat124AbarthPresets.json', name: 'Fiat 124 Abarth', drive: 'RWD' },
    { file: 'DA_Fiat131AbarthPresets.json', name: 'Fiat 131 Abarth', drive: 'RWD' },
    { file: 'DA_Hyundaii20NRally2Presets.json', name: 'Hyundai i20 N Rally 2', drive: 'AWD' },
    { file: 'DA_LanciaDeltaHFIntegraleEvoPresets.json', name: 'Lancia Delta HF Integrale Evo', drive: 'AWD' },
    { file: 'DA_LanciaRally037Evo2Presets.json', name: 'Lancia Rally 037 Evo 2', drive: 'RWD' },
    { file: 'DA_LanciaStratosPresets.json', name: 'Lancia Stratos', drive: 'RWD' },
    { file: 'DA_MiniCooperS1275Presets.json', name: 'Mini Cooper S 1275', drive: 'FWD' },
    { file: 'DA_Peugeot208Rally4Presets.json', name: 'Peugeot 208 Rally 4', drive: 'FWD' }
];

function extractSetups() {
    const allSetups = {};

    for (const car of carFiles) {
        const filePath = path.join(setupsDir, car.file);
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

        // Find PhysicsCarSetup object
        const physicsSetup = data.find(obj => obj.Type === 'PhysicsCarSetup');

        // Find surface variant objects and extract float overrides
        const tarmacVariant = data.find(obj => obj.Type === 'CarSetupVariantsSurface' && obj.Name === 'CarSetupVariantsSurface_0');
        const gravelVariant = data.find(obj => obj.Type === 'CarSetupVariantsSurface' && obj.Name === 'CarSetupVariantsSurface_1');

        // Extract clean overrides (float values and DB references only)
        const tarmacOverrides = extractCleanOverrides(data, tarmacVariant);
        const gravelOverrides = extractCleanOverrides(data, gravelVariant);

        if (physicsSetup) {
            const props = physicsSetup.Properties;

            allSetups[car.name] = {
                driveType: car.drive,
                baseline: {
                    drivetrain: formatDrivetrain(props.DrivetrainSetupData, car.drive),
                    suspension: formatSuspension(props.MechanicalBalanceSetupData),
                    dampers: formatDampers(props.DampersSetupData),
                    tyres: formatTyres(props.TyresSetupData),
                    brakes: formatBrakes(props.BrakesSetupData)
                },
                surfaceOverrides: {
                    tarmac: tarmacOverrides,
                    gravel: gravelOverrides
                }
            };
        }
    }

    return allSetups;
}

function extractCleanOverrides(data, surfaceVariant) {
    const result = {
        gearing: {},
        suspension: {},
        dampers: {},
        brakes: {},
        wheels: {},
        differential: {},
        other: {}
    };

    if (!surfaceVariant?.Properties?.ValuesOverrides) {
        return result;
    }

    for (const override of surfaceVariant.Properties.ValuesOverrides) {
        const key = override.Key;
        const valueRef = override.Value;

        // Find the actual override object by matching the name in the reference
        let valueObj = null;
        if (valueRef?.ObjectName) {
            const match = valueRef.ObjectName.match(/'[^:]+:([^']+)'/);
            if (match) {
                const objName = match[1];
                valueObj = data.find(obj =>
                    obj.Name === objName &&
                    obj.Outer === surfaceVariant.Name
                );
            }
        }

        if (!valueObj?.Properties) continue;

        // Extract the actual value based on type
        let value = null;
        if (valueObj.Type === 'CarSettingOverrideFloat' && typeof valueObj.Properties.Value === 'number') {
            value = valueObj.Properties.Value;
        } else if (valueObj.Type === 'CarSettingOverrideValueSetDBReference' && valueObj.Properties.Value?.Row) {
            value = valueObj.Properties.Value.Row;
        } else if (valueObj.Type === 'CarSettingOverrideInteger' && typeof valueObj.Properties.Value === 'number') {
            value = valueObj.Properties.Value;
        }

        if (value === null) continue;

        // Categorize the override
        if (key.startsWith('Gearbox.') || key.includes('GearsSet')) {
            result.gearing[simplifyKey(key)] = value;
        } else if (key.startsWith('Suspensions.')) {
            result.suspension[simplifyKey(key)] = value;
        } else if (key.startsWith('Dampers.')) {
            result.dampers[simplifyKey(key)] = value;
        } else if (key.startsWith('Brakes.')) {
            result.brakes[simplifyKey(key)] = value;
        } else if (key.startsWith('Wheels.')) {
            result.wheels[simplifyKey(key)] = value;
        } else if (key.startsWith('Differentials.') || key.startsWith('Axles.')) {
            result.differential[simplifyKey(key)] = value;
        } else {
            result.other[simplifyKey(key)] = value;
        }
    }

    // Remove empty categories
    for (const cat of Object.keys(result)) {
        if (Object.keys(result[cat]).length === 0) {
            delete result[cat];
        }
    }

    return result;
}

function simplifyKey(key) {
    return key
        .replace('Suspensions.', '')
        .replace('Dampers.', '')
        .replace('Brakes.', '')
        .replace('Wheels.', '')
        .replace('Differentials.', '')
        .replace('Axles.', '')
        .replace('Gearbox.GearboxMain.', '')
        .replace('Other.Electronic.', '');
}

function formatDrivetrain(data, driveType) {
    const result = {
        gearsSet: data.GearsSet?.Row || 'N/A'
    };

    if (driveType === 'AWD') {
        result.frontBias = Math.round((data.FrontBias || 0.5) * 100) + '%';
    }

    if (driveType === 'FWD' || driveType === 'AWD') {
        if (data.FrontDiff || data.FrontDiffRatio) {
            result.frontDiff = {
                ratio: data.FrontDiffRatio?.Row || 'N/A',
                lsdRampAngle: data.FrontDiff?.LSDRampAngle?.Row || 'N/A',
                lsdPlates: data.FrontDiff?.LSDPlatesNumber || 0,
                lsdPreload: (data.FrontDiff?.LSDPreload || 0) + ' Nm'
            };
        }
    }

    if (driveType === 'RWD' || driveType === 'AWD') {
        if (data.RearDiff || data.RearDiffRatio) {
            result.rearDiff = {
                ratio: data.RearDiffRatio?.Row || 'N/A',
                lsdRampAngle: data.RearDiff?.LSDRampAngle?.Row || 'N/A',
                lsdPlates: data.RearDiff?.LSDPlatesNumber || 0,
                lsdPreload: (data.RearDiff?.LSDPreload || 0) + ' Nm'
            };
        }
    }

    if (driveType === 'AWD' && data.CentreDiffRatio) {
        result.centreDiffRatio = data.CentreDiffRatio?.Row || 'N/A';
    }

    return result;
}

function formatSuspension(data) {
    const result = {
        frontARB: data.FrontARB + ' N/m'
    };

    if (data.RearARB) {
        result.rearARB = data.RearARB + ' N/m';
    }

    const wheels = ['FL', 'FR', 'RL', 'RR'];
    result.springs = {};
    result.rideHeight = {};

    data.Suspensions.forEach((susp, i) => {
        result.springs[wheels[i]] = susp.WheelRate + ' N/m';
        result.rideHeight[wheels[i]] = (susp.AdjusterRing * 1000).toFixed(1) + ' mm';
    });

    return result;
}

function formatDampers(data) {
    const wheels = ['FL', 'FR', 'RL', 'RR'];
    const result = {};

    data.forEach((damper, i) => {
        result[wheels[i]] = {
            slowBump: damper.Slow.Bump,
            slowRebound: damper.Slow.Rebound,
            fastBump: damper.Fast.Bump,
            fastRebound: damper.Fast.Rebound
        };
    });

    return result;
}

function formatTyres(data) {
    const wheels = ['FL', 'FR', 'RL', 'RR'];
    const result = {};

    data.forEach((tyre, i) => {
        result[wheels[i]] = {
            pressure: tyre.Pressure + ' PSI',
            camber: tyre.Camber + '°',
            toe: tyre.Toe === 0 ? '0°' : (tyre.Toe * (180/Math.PI)).toFixed(3) + '°'
        };
    });

    return result;
}

function formatBrakes(data) {
    return {
        brakeBias: Math.round(data.BrakeBias * 100) + '% front',
        propValvePressure: data.BrakePropValvePressure,
        handbrakeMultiplier: data.HandbrakeMult
    };
}

// Generate clean formatted output
function generateOutput(setups) {
    let output = '';
    output += '╔═══════════════════════════════════════════════════════════════════════════════╗\n';
    output += '║           ASSETTO CORSA RALLY - DEFAULT CAR SETUPS (ALL 11 CARS)             ║\n';
    output += '║                        Extracted from Game Files                              ║\n';
    output += '╚═══════════════════════════════════════════════════════════════════════════════╝\n\n';

    for (const [carName, setup] of Object.entries(setups)) {
        output += '━'.repeat(80) + '\n';
        output += `  ${carName.toUpperCase()}\n`;
        output += `  Drive Type: ${setup.driveType}\n`;
        output += '━'.repeat(80) + '\n\n';

        // DRIVETRAIN
        output += '┌──────────────────────────────────────────────────────────────────────────────┐\n';
        output += '│  DRIVETRAIN                                                                  │\n';
        output += '├──────────────────────────────────────────────────────────────────────────────┤\n';
        output += `│  Gear Set: ${setup.baseline.drivetrain.gearsSet.padEnd(63)}│\n`;

        if (setup.baseline.drivetrain.frontBias) {
            output += `│  Power Split: ${setup.baseline.drivetrain.frontBias.padEnd(60)}│\n`;
        }

        if (setup.baseline.drivetrain.frontDiff) {
            const fd = setup.baseline.drivetrain.frontDiff;
            output += '│                                                                              │\n';
            output += '│  Front Differential:                                                         │\n';
            output += `│    Final Drive Ratio: ${fd.ratio.padEnd(52)}│\n`;
            output += `│    LSD Ramp Angles: ${fd.lsdRampAngle.padEnd(54)}│\n`;
            output += `│    LSD Friction Plates: ${String(fd.lsdPlates).padEnd(50)}│\n`;
            output += `│    LSD Preload: ${fd.lsdPreload.padEnd(58)}│\n`;
        }

        if (setup.baseline.drivetrain.rearDiff) {
            const rd = setup.baseline.drivetrain.rearDiff;
            output += '│                                                                              │\n';
            output += '│  Rear Differential:                                                          │\n';
            output += `│    Final Drive Ratio: ${rd.ratio.padEnd(52)}│\n`;
            output += `│    LSD Ramp Angles: ${rd.lsdRampAngle.padEnd(54)}│\n`;
            output += `│    LSD Friction Plates: ${String(rd.lsdPlates).padEnd(50)}│\n`;
            output += `│    LSD Preload: ${rd.lsdPreload.padEnd(58)}│\n`;
        }

        if (setup.baseline.drivetrain.centreDiffRatio) {
            output += '│                                                                              │\n';
            output += `│  Centre Diff Ratio: ${setup.baseline.drivetrain.centreDiffRatio.padEnd(54)}│\n`;
        }
        output += '└──────────────────────────────────────────────────────────────────────────────┘\n\n';

        // SUSPENSION
        output += '┌──────────────────────────────────────────────────────────────────────────────┐\n';
        output += '│  SUSPENSION                                                                  │\n';
        output += '├──────────────────────────────────────────────────────────────────────────────┤\n';
        output += `│  Front ARB: ${setup.baseline.suspension.frontARB.padEnd(62)}│\n`;
        if (setup.baseline.suspension.rearARB) {
            output += `│  Rear ARB: ${setup.baseline.suspension.rearARB.padEnd(63)}│\n`;
        }
        output += '│                                                                              │\n';
        output += '│  Spring Rates:        FL              FR              RL              RR     │\n';
        const springs = setup.baseline.suspension.springs;
        output += `│                       ${springs.FL.padEnd(16)}${springs.FR.padEnd(16)}${springs.RL.padEnd(16)}${springs.RR.padEnd(5)}│\n`;
        output += '│                                                                              │\n';
        output += '│  Ride Height:         FL              FR              RL              RR     │\n';
        const rh = setup.baseline.suspension.rideHeight;
        output += `│                       ${rh.FL.padEnd(16)}${rh.FR.padEnd(16)}${rh.RL.padEnd(16)}${rh.RR.padEnd(5)}│\n`;
        output += '└──────────────────────────────────────────────────────────────────────────────┘\n\n';

        // DAMPERS
        output += '┌──────────────────────────────────────────────────────────────────────────────┐\n';
        output += '│  DAMPERS                                                                     │\n';
        output += '├──────────────────────────────────────────────────────────────────────────────┤\n';
        output += '│                       FL         FR         RL         RR                   │\n';
        const d = setup.baseline.dampers;
        output += `│  Slow Bump:           ${String(d.FL.slowBump).padEnd(11)}${String(d.FR.slowBump).padEnd(11)}${String(d.RL.slowBump).padEnd(11)}${String(d.RR.slowBump).padEnd(16)}│\n`;
        output += `│  Slow Rebound:        ${String(d.FL.slowRebound).padEnd(11)}${String(d.FR.slowRebound).padEnd(11)}${String(d.RL.slowRebound).padEnd(11)}${String(d.RR.slowRebound).padEnd(16)}│\n`;
        output += `│  Fast Bump:           ${String(d.FL.fastBump).padEnd(11)}${String(d.FR.fastBump).padEnd(11)}${String(d.RL.fastBump).padEnd(11)}${String(d.RR.fastBump).padEnd(16)}│\n`;
        output += `│  Fast Rebound:        ${String(d.FL.fastRebound).padEnd(11)}${String(d.FR.fastRebound).padEnd(11)}${String(d.RL.fastRebound).padEnd(11)}${String(d.RR.fastRebound).padEnd(16)}│\n`;
        output += '└──────────────────────────────────────────────────────────────────────────────┘\n\n';

        // TYRES
        output += '┌──────────────────────────────────────────────────────────────────────────────┐\n';
        output += '│  TYRES                                                                       │\n';
        output += '├──────────────────────────────────────────────────────────────────────────────┤\n';
        output += '│                       FL              FR              RL              RR     │\n';
        const t = setup.baseline.tyres;
        output += `│  Pressure:            ${t.FL.pressure.padEnd(16)}${t.FR.pressure.padEnd(16)}${t.RL.pressure.padEnd(16)}${t.RR.pressure.padEnd(5)}│\n`;
        output += `│  Camber:              ${t.FL.camber.padEnd(16)}${t.FR.camber.padEnd(16)}${t.RL.camber.padEnd(16)}${t.RR.camber.padEnd(5)}│\n`;
        output += `│  Toe:                 ${t.FL.toe.padEnd(16)}${t.FR.toe.padEnd(16)}${t.RL.toe.padEnd(16)}${t.RR.toe.padEnd(5)}│\n`;
        output += '└──────────────────────────────────────────────────────────────────────────────┘\n\n';

        // BRAKES
        output += '┌──────────────────────────────────────────────────────────────────────────────┐\n';
        output += '│  BRAKES                                                                      │\n';
        output += '├──────────────────────────────────────────────────────────────────────────────┤\n';
        output += `│  Brake Bias: ${setup.baseline.brakes.brakeBias.padEnd(61)}│\n`;
        output += `│  Prop Valve Pressure: ${String(setup.baseline.brakes.propValvePressure).padEnd(52)}│\n`;
        output += `│  Handbrake Multiplier: ${String(setup.baseline.brakes.handbrakeMultiplier).padEnd(51)}│\n`;
        output += '└──────────────────────────────────────────────────────────────────────────────┘\n\n';

        // SURFACE OVERRIDES
        const hasOverrides = (obj) => Object.keys(obj || {}).length > 0;

        if (hasOverrides(setup.surfaceOverrides.tarmac) || hasOverrides(setup.surfaceOverrides.gravel)) {
            output += '┌──────────────────────────────────────────────────────────────────────────────┐\n';
            output += '│  SURFACE-SPECIFIC CHANGES (vs baseline above)                                │\n';
            output += '├──────────────────────────────────────────────────────────────────────────────┤\n';

            if (hasOverrides(setup.surfaceOverrides.gravel)) {
                output += '│                                                                              │\n';
                output += '│  GRAVEL:                                                                     │\n';
                for (const [category, values] of Object.entries(setup.surfaceOverrides.gravel)) {
                    for (const [key, value] of Object.entries(values)) {
                        const displayValue = typeof value === 'number' ? value : String(value);
                        output += `│    ${key}: ${String(displayValue).substring(0, 55).padEnd(55)}│\n`;
                    }
                }
            }

            if (hasOverrides(setup.surfaceOverrides.tarmac)) {
                output += '│                                                                              │\n';
                output += '│  TARMAC:                                                                     │\n';
                for (const [category, values] of Object.entries(setup.surfaceOverrides.tarmac)) {
                    for (const [key, value] of Object.entries(values)) {
                        const displayValue = typeof value === 'number' ? value : String(value);
                        output += `│    ${key}: ${String(displayValue).substring(0, 55).padEnd(55)}│\n`;
                    }
                }
            }

            output += '└──────────────────────────────────────────────────────────────────────────────┘\n';
        }

        output += '\n\n';
    }

    return output;
}

// Run extraction
const setups = extractSetups();

// Save JSON data
fs.writeFileSync(
    path.join(__dirname, 'car_setups_clean.json'),
    JSON.stringify(setups, null, 2)
);

// Save readable output
const readableOutput = generateOutput(setups);
fs.writeFileSync(
    path.join(__dirname, 'CAR_SETUPS.txt'),
    readableOutput
);

console.log('Extraction complete!');
console.log('Files created:');
console.log('  - car_setups_clean.json (structured data for your app)');
console.log('  - CAR_SETUPS.txt (clean human-readable format)');
