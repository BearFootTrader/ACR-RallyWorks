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

        // Find PhysicsCarSetup object (baseline)
        const physicsSetup = data.find(obj => obj.Type === 'PhysicsCarSetup');

        // Find surface variant objects
        const tarmacVariant = data.find(obj => obj.Type === 'CarSetupVariantsSurface' && obj.Name === 'CarSetupVariantsSurface_0');
        const gravelVariant = data.find(obj => obj.Type === 'CarSetupVariantsSurface' && obj.Name === 'CarSetupVariantsSurface_1');

        if (physicsSetup) {
            const props = physicsSetup.Properties;

            // Extract baseline values
            const baseline = {
                drivetrain: extractDrivetrain(props.DrivetrainSetupData, car.drive),
                suspension: extractSuspension(props.MechanicalBalanceSetupData),
                dampers: extractDampers(props.DampersSetupData),
                tyres: extractTyres(props.TyresSetupData),
                brakes: extractBrakes(props.BrakesSetupData)
            };

            // Extract gravel overrides
            const gravelOverrides = extractOverridesWithKeys(data, gravelVariant);
            const tarmacOverrides = extractOverridesWithKeys(data, tarmacVariant);

            // Create merged gravel setup
            const gravelSetup = mergeSetupWithOverrides(JSON.parse(JSON.stringify(baseline)), gravelOverrides);
            const tarmacSetup = mergeSetupWithOverrides(JSON.parse(JSON.stringify(baseline)), tarmacOverrides);

            allSetups[car.name] = {
                driveType: car.drive,
                tarmac: tarmacSetup,
                gravel: gravelSetup,
                gravelChanges: gravelOverrides // Raw changes for reference
            };
        }
    }

    return allSetups;
}

function extractOverridesWithKeys(data, surfaceVariant) {
    const overrides = {};

    if (!surfaceVariant?.Properties?.ValuesOverrides) {
        return overrides;
    }

    for (const override of surfaceVariant.Properties.ValuesOverrides) {
        const key = override.Key;
        const valueRef = override.Value;

        // Find the actual override object by matching the name in the reference
        // ObjectName format: "CarSettingOverrideFloat'DA_Hyundaii20NRally2Presets:CarSetupVariantsSurface_1.CarSettingOverrideFloat_4'"
        let valueObj = null;
        if (valueRef?.ObjectName) {
            // Extract the object name after the last dot in the path
            const match = valueRef.ObjectName.match(/\.([^.']+)'$/);
            if (match) {
                const objName = match[1];
                // Find object with this name that has Outer matching the surface variant
                valueObj = data.find(obj =>
                    obj.Name === objName &&
                    obj.Outer === surfaceVariant.Name
                );
            }
        }

        if (!valueObj?.Properties) continue;

        // Extract the actual value based on type
        if (valueObj.Type === 'CarSettingOverrideFloat' && typeof valueObj.Properties.Value === 'number') {
            overrides[key] = { type: 'float', value: valueObj.Properties.Value };
        } else if (valueObj.Type === 'CarSettingOverrideValueSetDBReference' && valueObj.Properties.Value?.Row) {
            overrides[key] = { type: 'db', value: valueObj.Properties.Value.Row };
        } else if (valueObj.Type === 'CarSettingOverrideInteger' && typeof valueObj.Properties.Value === 'number') {
            overrides[key] = { type: 'int', value: valueObj.Properties.Value };
        }
    }
    return overrides;
}

function mergeSetupWithOverrides(setup, overrides) {
    for (const [key, data] of Object.entries(overrides)) {
        const value = data.value;

        // Parse the key to apply override
        if (key.startsWith('Suspensions.')) {
            const parts = key.split('.');
            const wheel = mapWheelName(parts[1]);
            const prop = parts[2];

            if (prop === 'SpringStiffness' && setup.suspension.springs[wheel]) {
                setup.suspension.springs[wheel] = value + ' N/m';
            } else if (prop === 'AdjusterRing' && setup.suspension.rideHeight[wheel]) {
                setup.suspension.rideHeight[wheel] = (value * 1000).toFixed(1) + ' mm';
            }
        } else if (key.startsWith('Axles.')) {
            const parts = key.split('.');
            if (parts[2] === 'ARBStiffness') {
                if (parts[1] === 'Front') {
                    setup.suspension.frontARB = value + ' N/m';
                } else if (parts[1] === 'Rear') {
                    setup.suspension.rearARB = value + ' N/m';
                }
            }
        } else if (key.startsWith('Wheels.')) {
            const parts = key.split('.');
            const wheel = mapWheelName(parts[1]);
            const prop = parts[2];

            if (prop === 'Camber' && setup.tyres[wheel]) {
                setup.tyres[wheel].camber = value + '°';
            } else if (prop === 'Toe' && setup.tyres[wheel]) {
                setup.tyres[wheel].toe = value === 0 ? '0°' : (value * (180/Math.PI)).toFixed(3) + '°';
            } else if (prop === 'Pressure' && setup.tyres[wheel]) {
                setup.tyres[wheel].pressure = value + ' PSI';
            }
        } else if (key === 'Gearbox.GearboxMain.GearsSet') {
            setup.drivetrain.gearsSet = value;
        } else if (key.startsWith('Differentials.')) {
            const parts = key.split('.');
            const diffType = parts[1]; // Front, Rear, or Centre
            const prop = parts[2];

            if (diffType === 'Front' && setup.drivetrain.frontDiff) {
                if (prop === 'DifferentialRatio') {
                    setup.drivetrain.frontDiff.ratio = value;
                } else if (prop === 'LSDRamps') {
                    setup.drivetrain.frontDiff.lsdRampAngle = value;
                } else if (prop === 'LSDPreload') {
                    setup.drivetrain.frontDiff.lsdPreload = value + ' Nm';
                } else if (prop === 'LSDFrictionPlates') {
                    setup.drivetrain.frontDiff.lsdPlates = value;
                }
            } else if (diffType === 'Rear' && setup.drivetrain.rearDiff) {
                if (prop === 'DifferentialRatio') {
                    setup.drivetrain.rearDiff.ratio = value;
                } else if (prop === 'LSDRamps') {
                    setup.drivetrain.rearDiff.lsdRampAngle = value;
                } else if (prop === 'LSDPreload') {
                    setup.drivetrain.rearDiff.lsdPreload = value + ' Nm';
                } else if (prop === 'LSDFrictionPlates') {
                    setup.drivetrain.rearDiff.lsdPlates = value;
                }
            } else if (diffType === 'Centre') {
                if (prop === 'CentreDifferentialRatio') {
                    setup.drivetrain.centreDiffRatio = value;
                }
            }
        } else if (key.startsWith('Dampers.')) {
            const parts = key.split('.');
            const wheel = mapWheelName(parts[1]);
            const prop = parts[2];

            if (setup.dampers[wheel]) {
                if (prop === 'SlowBump') {
                    setup.dampers[wheel].slowBump = value;
                } else if (prop === 'SlowRebound') {
                    setup.dampers[wheel].slowRebound = value;
                } else if (prop === 'FastBump') {
                    setup.dampers[wheel].fastBump = value;
                } else if (prop === 'FastRebound') {
                    setup.dampers[wheel].fastRebound = value;
                }
            }
        } else if (key === 'Brakes.BrakesMain.FrontBias') {
            setup.brakes.brakeBias = Math.round(value * 100) + '% front';
        }
        // Note: Brake disc/caliper/pad overrides are component selections, not displayed in basic setup
    }
    return setup;
}

function mapWheelName(name) {
    const map = {
        'FrontLeft': 'FL',
        'FrontRight': 'FR',
        'RearLeft': 'RL',
        'RearRight': 'RR'
    };
    return map[name] || name;
}

function extractDrivetrain(data, driveType) {
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

function extractSuspension(data) {
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

function extractDampers(data) {
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

function extractTyres(data) {
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

function extractBrakes(data) {
    return {
        brakeBias: Math.round(data.BrakeBias * 100) + '% front',
        propValvePressure: data.BrakePropValvePressure,
        handbrakeMultiplier: data.HandbrakeMult
    };
}

// Generate clean formatted output showing both setups
function generateOutput(setups) {
    let output = '';
    output += '╔═══════════════════════════════════════════════════════════════════════════════╗\n';
    output += '║           ASSETTO CORSA RALLY - COMPLETE CAR SETUPS                           ║\n';
    output += '║                   TARMAC & GRAVEL CONFIGURATIONS                              ║\n';
    output += '╚═══════════════════════════════════════════════════════════════════════════════╝\n\n';

    for (const [carName, data] of Object.entries(setups)) {
        output += '━'.repeat(80) + '\n';
        output += `  ${carName.toUpperCase()}\n`;
        output += `  Drive Type: ${data.driveType}\n`;
        output += '━'.repeat(80) + '\n\n';

        // Output both setups side by side conceptually
        output += outputSetupSection('TARMAC', data.tarmac, data.driveType);
        output += '\n';
        output += outputSetupSection('GRAVEL', data.gravel, data.driveType);

        // Show what changed for gravel
        if (Object.keys(data.gravelChanges).length > 0) {
            output += '┌──────────────────────────────────────────────────────────────────────────────┐\n';
            output += '│  GRAVEL CHANGES (from baseline/tarmac)                                       │\n';
            output += '├──────────────────────────────────────────────────────────────────────────────┤\n';
            for (const [key, val] of Object.entries(data.gravelChanges)) {
                const displayKey = key.replace('Suspensions.', '').replace('Axles.', '').replace('Wheels.', '').replace('Gearbox.GearboxMain.', '').replace('Differentials.', '');
                output += `│  ${displayKey}: ${String(val.value).substring(0, 50).padEnd(50)}│\n`;
            }
            output += '└──────────────────────────────────────────────────────────────────────────────┘\n';
        }

        output += '\n\n';
    }

    return output;
}

function outputSetupSection(surface, setup, driveType) {
    let output = '';

    output += `┌${'─'.repeat(76)}┐\n`;
    output += `│  ${surface} SETUP${' '.repeat(66)}│\n`;
    output += `├${'─'.repeat(76)}┤\n`;

    // DRIVETRAIN
    output += '│  DRIVETRAIN                                                                  │\n';
    output += `│    Gear Set: ${setup.drivetrain.gearsSet.padEnd(60)}│\n`;

    if (setup.drivetrain.frontBias) {
        output += `│    Power Split: ${setup.drivetrain.frontBias.padEnd(57)}│\n`;
    }

    if (setup.drivetrain.frontDiff) {
        const fd = setup.drivetrain.frontDiff;
        output += '│    Front Diff:                                                               │\n';
        output += `│      Ratio: ${fd.ratio.padEnd(62)}│\n`;
        output += `│      LSD Ramp: ${fd.lsdRampAngle.padEnd(59)}│\n`;
        output += `│      LSD Plates: ${String(fd.lsdPlates).padEnd(57)}│\n`;
        output += `│      LSD Preload: ${fd.lsdPreload.padEnd(56)}│\n`;
    }

    if (setup.drivetrain.rearDiff) {
        const rd = setup.drivetrain.rearDiff;
        output += '│    Rear Diff:                                                                │\n';
        output += `│      Ratio: ${rd.ratio.padEnd(62)}│\n`;
        output += `│      LSD Ramp: ${rd.lsdRampAngle.padEnd(59)}│\n`;
        output += `│      LSD Plates: ${String(rd.lsdPlates).padEnd(57)}│\n`;
        output += `│      LSD Preload: ${rd.lsdPreload.padEnd(56)}│\n`;
    }

    if (setup.drivetrain.centreDiffRatio) {
        output += `│    Centre Diff Ratio: ${setup.drivetrain.centreDiffRatio.padEnd(52)}│\n`;
    }

    // SUSPENSION
    output += '│                                                                              │\n';
    output += '│  SUSPENSION                                                                  │\n';
    output += `│    Front ARB: ${setup.suspension.frontARB.padEnd(60)}│\n`;
    if (setup.suspension.rearARB) {
        output += `│    Rear ARB: ${setup.suspension.rearARB.padEnd(61)}│\n`;
    }
    output += '│    Springs:      FL              FR              RL              RR          │\n';
    const s = setup.suspension.springs;
    output += `│                  ${s.FL.padEnd(16)}${s.FR.padEnd(16)}${s.RL.padEnd(16)}${s.RR.padEnd(10)}│\n`;
    output += '│    Ride Height:  FL              FR              RL              RR          │\n';
    const rh = setup.suspension.rideHeight;
    output += `│                  ${rh.FL.padEnd(16)}${rh.FR.padEnd(16)}${rh.RL.padEnd(16)}${rh.RR.padEnd(10)}│\n`;

    // DAMPERS
    output += '│                                                                              │\n';
    output += '│  DAMPERS         FL         FR         RL         RR                        │\n';
    const d = setup.dampers;
    output += `│    Slow Bump:    ${String(d.FL.slowBump).padEnd(11)}${String(d.FR.slowBump).padEnd(11)}${String(d.RL.slowBump).padEnd(11)}${String(d.RR.slowBump).padEnd(15)}│\n`;
    output += `│    Slow Rebound: ${String(d.FL.slowRebound).padEnd(11)}${String(d.FR.slowRebound).padEnd(11)}${String(d.RL.slowRebound).padEnd(11)}${String(d.RR.slowRebound).padEnd(15)}│\n`;
    output += `│    Fast Bump:    ${String(d.FL.fastBump).padEnd(11)}${String(d.FR.fastBump).padEnd(11)}${String(d.RL.fastBump).padEnd(11)}${String(d.RR.fastBump).padEnd(15)}│\n`;
    output += `│    Fast Rebound: ${String(d.FL.fastRebound).padEnd(11)}${String(d.FR.fastRebound).padEnd(11)}${String(d.RL.fastRebound).padEnd(11)}${String(d.RR.fastRebound).padEnd(15)}│\n`;

    // TYRES
    output += '│                                                                              │\n';
    output += '│  TYRES           FL              FR              RL              RR          │\n';
    const t = setup.tyres;
    output += `│    Pressure:     ${t.FL.pressure.padEnd(16)}${t.FR.pressure.padEnd(16)}${t.RL.pressure.padEnd(16)}${t.RR.pressure.padEnd(10)}│\n`;
    output += `│    Camber:       ${t.FL.camber.padEnd(16)}${t.FR.camber.padEnd(16)}${t.RL.camber.padEnd(16)}${t.RR.camber.padEnd(10)}│\n`;
    output += `│    Toe:          ${t.FL.toe.padEnd(16)}${t.FR.toe.padEnd(16)}${t.RL.toe.padEnd(16)}${t.RR.toe.padEnd(10)}│\n`;

    // BRAKES
    output += '│                                                                              │\n';
    output += '│  BRAKES                                                                      │\n';
    output += `│    Brake Bias: ${setup.brakes.brakeBias.padEnd(59)}│\n`;
    output += `│    Prop Valve: ${String(setup.brakes.propValvePressure).padEnd(59)}│\n`;
    output += `│    Handbrake Mult: ${String(setup.brakes.handbrakeMultiplier).padEnd(55)}│\n`;

    output += `└${'─'.repeat(76)}┘\n`;

    return output;
}

// Run extraction
const setups = extractSetups();

// Save JSON data
fs.writeFileSync(
    path.join(__dirname, 'car_setups_complete.json'),
    JSON.stringify(setups, null, 2)
);

// Save readable output
const readableOutput = generateOutput(setups);
fs.writeFileSync(
    path.join(__dirname, 'CAR_SETUPS_COMPLETE.txt'),
    readableOutput
);

console.log('Extraction complete!');
console.log('Files created:');
console.log('  - car_setups_complete.json (structured data with tarmac + gravel)');
console.log('  - CAR_SETUPS_COMPLETE.txt (human-readable format)');
