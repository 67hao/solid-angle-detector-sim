#include <fstream>
#include <iostream>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>

int main() {
    // ------------------------------------------------------------------------
    // Parameters
    // ------------------------------------------------------------------------
    double step_distance = 10.0; // mm
    double min_distance = 100.0;   // mm
    double max_distance = 200.0; // mm
    double initial_z = 95.0;     // mm, tọa độ ban đầu

    // ------------------------------------------------------------------------
    // Energy list: 2.2 MeV → 10 MeV (2200 keV → 10000 keV), step = 100 keV
    // ------------------------------------------------------------------------
    std::vector<int> energies;
    for (int e = 100; e <= 10000; e += 100) { // keV
        energies.push_back(e);
    }

    // ------------------------------------------------------------------------
    // Create master macro file
    // ------------------------------------------------------------------------
    std::ofstream master(std::string(MACROPATH) + std::string("/run_all.mac"));
    if (!master) {
        std::cerr << "=== Failed to create master macro file ===" << std::endl;
        return 1;
    }

    master << "/control/verbose 2\n";

    // ------------------------------------------------------------------------
    // Loop over distances and energies
    // ------------------------------------------------------------------------
    for (double distance = min_distance; distance <= max_distance + 0.001; distance += step_distance) {
        for (int energy : energies) {

            // Compute z position based on initial position + distance
            double z_pos = initial_z + distance;

            // Format strings for filename
            std::ostringstream ossD, ossE;
            ossD << std::fixed << std::setprecision(0) << distance;
            ossE << energy;

            std::string D_str = ossD.str();
            std::string E_str = ossE.str();

            // Filename for individual macro
            std::string filename = "run_D" + D_str + "_E" + E_str + ".mac";

            // ----------------------------------------------------------------
            // Write macro file
            // ----------------------------------------------------------------
            std::ofstream macfile(std::string(MACROPATH) + "/" + filename);
            if (!macfile) {
                std::cerr << "=== File Generating Failed === " << filename << std::endl;
                continue;
            }

            // Set source-detector distance and position
            macfile << "/DetectorConstruction/Sample_Detector_Distance " << distance << "\n";
            macfile << "/DetectorConstruction/update\n";
            macfile << "/gun/energy " << energy << " keV\n";

            // -------------------- Histogram setup --------------------
            macfile << "/analysis/setFileName hist_D" << D_str << "_E" << E_str << "\n";

            // Run events
            macfile << "/run/beamOn 1000000\n";

            macfile.close();

            // Add macro to master macro
            master << "/control/execute " << filename << "\n";
            std::cout << "== Generated: " << filename << std::endl;
        }
    }

    // ------------------------------------------------------------------------
    // Finalize master macro
    // ------------------------------------------------------------------------
    master.close();
    std::cout << "\nAll macros generated successfully at: " << MACROPATH << std::endl;
    std::cout << "Master macro file: run_all.mac" << std::endl;
    std::cout << "Total combinations: "
        << ((int)((max_distance - min_distance) / step_distance + 1) * energies.size())
        << std::endl;

    std::cout << "Press Enter to exit...";
    std::cin.get();

    return 0;
}
