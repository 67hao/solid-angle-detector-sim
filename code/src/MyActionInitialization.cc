// =========================================================================
// Header Definition
// =========================================================================

// 1. Include Local headers
#include "MyActionInitialization.hh"   // Action initialization class
#include "MyPrimaryGeneratorAction.hh" // Defines primary particle generator
#include "MyRunAction.hh"              // Handles run-level actions
#include "MyEventAction.hh"            // Handles event-level actions

// =========================================================================
// Constructor
// =========================================================================
// - Inherits from G4VUserActionInitialization.
// - Called once to prepare action classes for master and worker threads.
MyActionInitialization::MyActionInitialization()
	: G4VUserActionInitialization() {
}

// =========================================================================
// Destructor
// =========================================================================
MyActionInitialization::~MyActionInitialization() = default;

// =========================================================================
// Build (Worker Threads)
// =========================================================================
// - Defines actions executed in each worker thread.
// - Actions include:
//   + PrimaryGeneratorAction (defines the particle source).
//   + RunAction (accumulates run-level statistics).
//   + EventAction (processes per-event data, linked to RunAction).
void MyActionInitialization::Build() const {
	// 1. Primary generator action
	SetUserAction(new MyPrimaryGeneratorAction());

	// 2. Run action
	auto runAction = new MyRunAction();
	SetUserAction(runAction);

	// 3. Event action (requires RunAction pointer for accumulation)
	SetUserAction(new MyEventAction(runAction));

}

// =========================================================================
// BuildForMaster (Master Thread)
// =========================================================================
// - Defines actions executed in the master thread.
// - Master only needs RunAction (no event-level or generator action).
// - Purpose: Collects and merges results from all worker threads.
void MyActionInitialization::BuildForMaster() const {
	auto runAction = new MyRunAction();
	SetUserAction(runAction);
}
