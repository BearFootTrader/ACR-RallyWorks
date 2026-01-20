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

        // Find surface variant objects
        const surfaceVariants = data.filter(obj => obj.Type === 'CarSetupVariantsSurface');

        // Find override values for gravel
        const gravelOverrideRefs = surfaceVariants.find(v => v.Name === 'CarSetupVariantsSurface_1');
        const tarmacOverrideRefs = surfaceVariants.find(v => v.Name === 'CarSetupVariantsSurface_0');

        // Extract override values
        const gravelOverrides = extractOverrides(data, gravelOverrideRefs);
        const tarmacOverrides = extractOverrides(data, tarmacOverrideRefs);

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
                tarmacOverrides: tarmacOverrides,
                gravelOverrides: gravelOverrides
            };
        }
    }

    return allSetups;
}

function extractOverrides(data, surfaceVariant) {
    if (!surfaceVariant || !surfaceVariant.Properties || !surfaceVariant.Properties.ValuesOverrides) {
        return {};
    }

    const overrides = {};
    for (const override of surfaceVariant.Properties.ValuesOverrides) {
        const key = override.Key;
        const valueRef = override.Value;

        // Find the actual value object
        const valueObj = data.find(obj =>
            valueRef.ObjectName && valueRef.ObjectName.includes(obj.Name)
        );

        if (valueObj && valueObj.Properties) {
            if (valueObj.Properties.Value) {
                // DB Reference value
                if (typeof valueObj.Properties.Value === 'object' && valueObj.Properties.Value.Row) {
                    overrides[key] = valueObj.Properties.Value.Row;
                } else {
                    overrides[key] = valueObj.Properties.Value;
                }
            } else if (valueObj.Type === 'CarSettingOverrideFloat') {
                overrides[key] = valueObj.Properties;
            }
        }
    }
    return overrides;
}

function formatDrivetrain(data, driveType) {
    const result = {
        gearsSet: data.GearsSet?.Row || 'N/A',
        frontBias: data.FrontBias
    };

    if (driveType === 'FWD' || driveType === 'AWD') {
        result.frontDiff = {
            ratio: data.FrontDiffRatio?.Row || 'N/A',
            lsdRampAngle: data.FrontDiff?.LSDRampAngle?.Row || 'N/A',
            lsdPlates: data.FrontDiff?.LSDPlatesNumber || 0,
            lsdPreload: data.FrontDiff?.LSDPreload || 0
        };
    }

    if (driveType === 'RWD' || driveType === 'AWD') {
        result.rearDiff = {
            ratio: data.RearDiffRatio?.Row || 'N/A',
            lsdRampAngle: data.RearDiff?.LSDRampAngle?.Row || 'N/A',
            lsdPlates: data.RearDiff?.LSDPlatesNumber || 0,
            lsdPreload: data.RearDiff?.LSDPreload || 0
        };
    }

    if (driveType === 'AWD') {
        result.centreDiff = {
            ratio: data.CentreDiffRatio?.Row || 'N/A',
            toFrontRatio: data.CentreDiffToFrontRatio?.Row || 'N/A',
            toRearRatio: data.CentreDiffToRearRatio?.Row || 'N/A'
        };
    }

    return result;
}

function formatSuspension(data) {
    const wheels = ['Front Left', 'Front Right', 'Rear Left', 'Rear Right'];
    const result = {
        frontARB: data.FrontARB,
        rearARB: data.RearARB || null,
        cFactor: data.CFactor,
        wheels: {}
    };

    data.Suspensions.forEach((susp, i) => {
        result.wheels[wheels[i]] = {
            springRate: susp.WheelRate,
            rideHeight: Math.round(susp.AdjusterRing * 1000 * 10) / 10, // Convert to mm
            bumpStopUp: Math.round(susp.BumpStopGapUp * 1000 * 10) / 10,
            bumpStopDown: Math.round(susp.BumpStopGapDn * 1000 * 10) / 10
        };
    });

    return result;
}

function formatDampers(data) {
    const wheels = ['Front Left', 'Front Right', 'Rear Left', 'Rear Right'];
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
    const wheels = ['Front Left', 'Front Right', 'Rear Left', 'Rear Right'];
    const result = {};

    data.forEach((tyre, i) => {
        result[wheels[i]] = {
            pressure: tyre.Pressure,
            camber: tyre.Camber,
            toe: Math.round(tyre.Toe * 10000) / 10000, // Keep precision
            caster: tyre.Caster
        };
    });

    return result;
}

function formatBrakes(data) {
    return {
        brakeBias: Math.round(data.BrakeBias * 100), // Convert to percentage
        propValvePressure: data.BrakePropValvePressure,
        handbrakeMultiplier: data.HandbrakeMult
    };
}

// Generate clean readable output
function generateReadableOutput(setups) {
    let output = '═══════════════════════════════════════════════════════════════════════════════\n';
    output += '                    ASSETTO CORSA RALLY - DEFAULT SETUPS\n';
    output += '═══════════════════════════════════════════════════════════════════════════════\n\n';

    for (const [carName, setup] of Object.entries(setups)) {
        output += `┌─────────────────────────────────────────────────────────────────────────────┐\n`;
        output += `│  ${carName.padEnd(71)}  │\n`;
        output += `│  Drive: ${setup.driveType.padEnd(66)}  │\n`;
        output += `└─────────────────────────────────────────────────────────────────────────────┘\n\n`;

        // DRIVETRAIN
        output += '  ▸ DRIVETRAIN\n';
        output += `    Gear Set: ${setup.baseline.drivetrain.gearsSet}\n`;
        output += `    Front Bias: ${(setup.baseline.drivetrain.frontBias * 100).toFixed(0)}%\n`;

        if (setup.baseline.drivetrain.frontDiff) {
            output += `    Front Diff:\n`;
            output += `      • Ratio: ${setup.baseline.drivetrain.frontDiff.ratio}\n`;
            output += `      • LSD Ramp: ${setup.baseline.drivetrain.frontDiff.lsdRampAngle}\n`;
            output += `      • LSD Plates: ${setup.baseline.drivetrain.frontDiff.lsdPlates}\n`;
            output += `      • LSD Preload: ${setup.baseline.drivetrain.frontDiff.lsdPreload} Nm\n`;
        }

        if (setup.baseline.drivetrain.rearDiff) {
            output += `    Rear Diff:\n`;
            output += `      • Ratio: ${setup.baseline.drivetrain.rearDiff.ratio}\n`;
            output += `      • LSD Ramp: ${setup.baseline.drivetrain.rearDiff.lsdRampAngle}\n`;
            output += `      • LSD Plates: ${setup.baseline.drivetrain.rearDiff.lsdPlates}\n`;
            output += `      • LSD Preload: ${setup.baseline.drivetrain.rearDiff.lsdPreload} Nm\n`;
        }

        if (setup.baseline.drivetrain.centreDiff) {
            output += `    Centre Diff:\n`;
            output += `      • Ratio: ${setup.baseline.drivetrain.centreDiff.ratio}\n`;
        }

        // SUSPENSION
        output += '\n  ▸ SUSPENSION\n';
        output += `    Front ARB: ${setup.baseline.suspension.frontARB} N/m\n`;
        if (setup.baseline.suspension.rearARB) {
            output += `    Rear ARB: ${setup.baseline.suspension.rearARB} N/m\n`;
        }

        output += '    Springs & Ride Height:\n';
        output += '    ┌──────────────┬────────────┬─────────────┐\n';
        output += '    │    Wheel     │ Spring (N) │ Height (mm) │\n';
        output += '    ├──────────────┼────────────┼─────────────┤\n';
        for (const [wheel, data] of Object.entries(setup.baseline.suspension.wheels)) {
            output += `    │ ${wheel.padEnd(12)} │ ${String(data.springRate).padStart(10)} │ ${String(data.rideHeight).padStart(11)} │\n`;
        }
        output += '    └──────────────┴────────────┴─────────────┘\n';

        // DAMPERS
        output += '\n  ▸ DAMPERS\n';
        output += '    ┌──────────────┬───────────┬────────────┬──────────┬───────────┐\n';
        output += '    │    Wheel     │ Slow Bump │ Slow Reb.  │ Fast Bump│ Fast Reb. │\n';
        output += '    ├──────────────┼───────────┼────────────┼──────────┼───────────┤\n';
        for (const [wheel, data] of Object.entries(setup.baseline.dampers)) {
            output += `    │ ${wheel.padEnd(12)} │ ${String(data.slowBump).padStart(9)} │ ${String(data.slowRebound).padStart(10)} │ ${String(data.fastBump).padStart(8)} │ ${String(data.fastRebound).padStart(9)} │\n`;
        }
        output += '    └──────────────┴───────────┴────────────┴──────────┴───────────┘\n';

        // TYRES
        output += '\n  ▸ TYRES\n';
        output += '    ┌──────────────┬──────────┬─────────┬─────────┐\n';
        output += '    │    Wheel     │ Pressure │ Camber  │   Toe   │\n';
        output += '    ├──────────────┼──────────┼─────────┼─────────┤\n';
        for (const [wheel, data] of Object.entries(setup.baseline.tyres)) {
            const toeDisplay = data.toe === 0 ? '0' : data.toe.toFixed(4);
            output += `    │ ${wheel.padEnd(12)} │ ${String(data.pressure + ' PSI').padStart(8)} │ ${String(data.camber + '°').padStart(7)} │ ${toeDisplay.padStart(7)} │\n`;
        }
        output += '    └──────────────┴──────────┴─────────┴─────────┘\n';

        // BRAKES
        output += '\n  ▸ BRAKES\n';
        output += `    Brake Bias: ${setup.baseline.brakes.brakeBias}% front\n`;
        output += `    Prop Valve Pressure: ${setup.baseline.brakes.propValvePressure}\n`;
        output += `    Handbrake Multiplier: ${setup.baseline.brakes.handbrakeMultiplier}\n`;

        // SURFACE OVERRIDES
        if (Object.keys(setup.tarmacOverrides).length > 0) {
            output += '\n  ▸ TARMAC OVERRIDES\n';
            for (const [key, value] of Object.entries(setup.tarmacOverrides)) {
                output += `    • ${key}: ${typeof value === 'object' ? JSON.stringify(value) : value}\n`;
            }
        }

        if (Object.keys(setup.gravelOverrides).length > 0) {
            output += '\n  ▸ GRAVEL OVERRIDES\n';
            for (const [key, value] of Object.entries(setup.gravelOverrides)) {
                output += `    • ${key}: ${typeof value === 'object' ? JSON.stringify(value) : value}\n`;
            }
        }

        output += '\n' + '─'.repeat(77) + '\n\n';
    }

    return output;
}

// Run extraction
const setups = extractSetups();

// Save JSON data
fs.writeFileSync(
    path.join(__dirname, 'car_setups_data.json'),
    JSON.stringify(setups, null, 2)
);

// Save readable output
const readableOutput = generateReadableOutput(setups);
fs.writeFileSync(
    path.join(__dirname, 'car_setups_readable.txt'),
    readableOutput
);

console.log('Extraction complete!');
console.log('- car_setups_data.json (structured data for your app)');
console.log('- car_setups_readable.txt (human-readable format)');
