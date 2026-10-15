// =========================================================================
// Header Definition
// =========================================================================

// 1. Include Local headers
#include "MyRunAction.hh"            // Run action class definition

// 2. Include Geant4 headers
#include "G4Run.hh"                  // Run information
#include "G4SystemOfUnits.hh"        // Units (MeV, cm, g, etc.)
#include "G4AccumulableManager.hh"   // Manager for accumulable variables
#include "G4AnalysisManager.hh"      // Analysis manager for histograms/ntuples
#include "G4ios.hh"                  // Geant4 I/O (cout-like)
// 3. Include Standard Library
#include <cmath>                     // For log and math operations

// =========================================================================
// Constructor
// =========================================================================
// - Initializes accumulable variables for tracking energy deposition,
//   fluence, and transmission.
// - Registers them with the G4AccumulableManager for thread-safe accumulation.
MyRunAction::MyRunAction()
    : G4UserRunAction(),
    fEdepNaIDet(0.0),
    fPulseNaIDet(0.0)
{
    // Register accumulables for thread-safe accumulation
    auto* accMan = G4AccumulableManager::Instance();
    accMan->RegisterAccumulable(fEdepNaIDet);
    accMan->RegisterAccumulable(fPulseNaIDet);

    // Initialize Analysis Manager
    auto* analysisManager = G4AnalysisManager::Instance();
    analysisManager->SetVerboseLevel(1);
    analysisManager->SetNtupleMerging(true); // allow merging for MT mode
    analysisManager->SetDefaultFileType("root");
    //analysisManager->SetFileName("Ra226_NaI_Calibration");


    // ---------------------------------------------------------------------
    // Histogram Definitions
    // ---------------------------------------------------------------------
    // H1 ID = 0 : Energy deposition spectrum (up to 15 MeV to cover prompt neutron capture gammas & high energy gammas)
    analysisManager->CreateH1(
        "E_dep",
        "Deposited Energy Spectrum in NaI(Tl)",
        15000,              // bins (1 keV/bin)
        0.0,
        15000.0 * keV       // range up to 15 MeV
    );
	// H1 ID = 1 : Pulse count histogram
    analysisManager->CreateH1(
        "Pulse_Counts",
        "Counts per Event in NaI(Tl) Detector",
        10,                // bins
        0.0,
        10.0               // range
    );

    // ---------------------------------------------------------------------
    // Ntuple Definitions
    // ---------------------------------------------------------------------
    analysisManager->CreateNtuple("Hits", "Event Data");
    analysisManager->CreateNtupleDColumn("Edep_keV");  // Deposited energy
    analysisManager->FinishNtuple();
}

// =========================================================================
// Destructor
// =========================================================================
MyRunAction::~MyRunAction() = default;

// =========================================================================
// BeginOfRunAction
// =========================================================================
// - Called at the start of each run.
// - Resets accumulable variables so results are not mixed across runs.
void MyRunAction::BeginOfRunAction(const G4Run*) {
    // Reset accumulables
    G4AccumulableManager::Instance()->Reset();
    // Open output file
    auto* analysisManager = G4AnalysisManager::Instance();
    analysisManager->Reset();
    analysisManager->OpenFile();
}

// =========================================================================
// EndOfRunAction
// =========================================================================
// - Called at the end of each run.
// - Merges results from all worker threads.
// - Prints accumulated values and calculates attenuation coefficient.
// =========================================================================
void MyRunAction::EndOfRunAction(const G4Run* run) {
    G4AccumulableManager::Instance()->Merge(); // Merge results across threads
    auto* analysisManager = G4AnalysisManager::Instance();

    if (run->GetNumberOfEvent() == 0) return;  // Skip if no events

    // Retrieve accumulated values
	G4double edepNaIDet = fEdepNaIDet.GetValue();
	G4double PusleNaIDet = fPulseNaIDet.GetValue();

    // Print results only once (in master thread)
    if (IsMaster()) {
        G4cout << "\n================ ANALYSIS RESULTS ================\n";
        G4cout << "Number of events: " << run->GetNumberOfEvent() << G4endl;

        // Energy deposition
        G4cout << "[Edep] NaI Detector = " << edepNaIDet / MeV << " MeV" << G4endl;

        // Pulse counters
        G4cout << "[Pulse] NaI Detector = " << PusleNaIDet << G4endl;

        G4cout << "=============================================\n";
    }

    // Write and close output file
    analysisManager->Write();
    analysisManager->CloseFile();
}

// =========================================================================
// Accumulation functions
// =========================================================================
// - Called by EventAction to add contributions from each event.
// - Each adds to an accumulable (thread-safe accumulation).

// Accumulation functions
void MyRunAction::AddEdepNaIDet(G4double edep) {
    // edep is the TOTAL energy deposited in this event (units: internal ie. MeV if returned so)
    fEdepNaIDet += edep; // accumulable, thread-safe

    // Fill histogram and ntuple (each thread has its own analysis manager instance when running MT)
    auto* analysisManager = G4AnalysisManager::Instance();
    analysisManager->FillH1(0, edep);            // fill per-event energy
    analysisManager->FillNtupleDColumn(0, edep / keV);
    analysisManager->AddNtupleRow();
}

void MyRunAction::AddCountedNaIDet() {
    // increment the accumulable counter
    fPulseNaIDet += 1.0;

    // For histogram of counts-per-event, record one entry per event that had a counted pulse
    auto* analysisManager = G4AnalysisManager::Instance();
    analysisManager->FillH1(1, 1.0); // fill value '1' once per event with a pulse
}