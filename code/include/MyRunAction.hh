// ============================================================================
// MyRunAction.hh
// Definition of the MyRunAction class
//
// This class controls actions at the beginning and end of a run.
// It accumulates physics quantities (energy deposition, fluence,
// transmission, etc.) across all events and handles multi-threaded
// accumulation via G4Accumulable.
//
// Responsibilities:
// - Initialize and reset accumulables.
// - Collect energy deposition and fluence data from EventAction.
// - Print summary statistics at the end of each run.
// ============================================================================

#ifndef MYRUNACTION_HH
#define MYRUNACTION_HH

// ============================================================================
// Geant4 Includes
// ============================================================================
#include "G4UserRunAction.hh"
#include "G4Accumulable.hh"
#include "globals.hh"

// ============================================================================
// Local Includes
// ============================================================================
#include "MyPrimaryGeneratorAction.hh"

// Forward Declaration
class G4Run;

// ============================================================================
// MyRunAction
// ============================================================================
class MyRunAction : public G4UserRunAction {
public:
	// Constructor / Destructor
	MyRunAction();
	~MyRunAction() override;

	// ========================================================================
	// Run Control Methods
	// ========================================================================
		void BeginOfRunAction(const G4Run* run) override;
	void EndOfRunAction(const G4Run* run) override;

	// ========================================================================
	// Accumulable Methods (called from EventAction)
	// ========================================================================
	void AddEdepNaIDet(G4double edep);
	void AddCountedNaIDet();

private:
	// ========================================================================
	// Accumulable Variables
	// ========================================================================
	// These hold accumulated quantities across all events in a run.
	// Geant4 handles merging across worker threads automatically.
	G4Accumulable<G4double> fEdepNaIDet;
	G4Accumulable<G4double> fPulseNaIDet;

	// Pointer to primary generator (to access particle info if needed)
	MyPrimaryGeneratorAction* fParticleGun = nullptr;

};

#endif // MYRUNACTION_HH
