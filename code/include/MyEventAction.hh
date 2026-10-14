// ============================================================================
// MyEventAction.hh
// Definition of the MyEventAction class
//
// This class defines actions to be taken at the beginning and end of
// each event. It works together with MyRunAction to accumulate
// statistics such as energy deposition and particle fluence.
// ============================================================================

#ifndef MYEVENTACTION_HH
#define MYEVENTACTION_HH

// ============================================================================
// Geant4 Includes
// ============================================================================
#include "G4UserEventAction.hh"
#include "globals.hh"
#include <set>

// Forward declarations
class G4Event;
class MyRunAction;

// ============================================================================
// MyEventAction
// ============================================================================
// Inherits from G4UserEventAction.
//
// Responsibilities:
// - BeginOfEventAction(): reset per-event bookkeeping
// - EndOfEventAction(): process hits from sensitive detectors, classify
//   them by volume, and pass results to MyRunAction for accumulation.
// ============================================================================
class MyEventAction : public G4UserEventAction {
public:
	// ========================================================================
	// Constructor / Destructor
	// ========================================================================
	explicit MyEventAction(MyRunAction* runAction);
	~MyEventAction() override;

	// ========================================================================
	// BeginOfEventAction: Called at the start of each event
	// ========================================================================
	void BeginOfEventAction(const G4Event*) override;

	// ========================================================================
	// EndOfEventAction: Called at the end of each event
	// Processes all hits and updates run-level statistics
	// ========================================================================
	void EndOfEventAction(const G4Event* event) override;

private:
	/// Pointer to the RunAction object for accumulating results
	MyRunAction* fRunAction;

	/// Track IDs already counted in this event (per detector type)
	std::set<G4int> fCountedNaIDet;
	G4double fEdepEvent = 0.; // Total energy deposited
};

#endif // MYEVENTACTION_HH
