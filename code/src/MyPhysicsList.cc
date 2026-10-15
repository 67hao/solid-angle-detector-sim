#include "MyPhysicsList.hh"

#include "G4SystemOfUnits.hh"
#include "G4EmStandardPhysics.hh"
#include "G4DecayPhysics.hh"
#include "G4HadronPhysicsQGSP_BIC_HP.hh"
#include "G4RadioactiveDecayPhysics.hh"
#include "G4HadronElasticPhysicsHP.hh"
#include "G4ThermalNeutrons.hh"
#include "G4GenericBiasingPhysics.hh"
#include <G4EmLivermorePhysics.hh>
#include <G4IonPhysics.hh>
#include <G4StoppingPhysics.hh>


MyPhysicsList::MyPhysicsList()
    : G4VModularPhysicsList()
{
    SetDefaultCutValue(0.7 * mm);
    SetVerboseLevel(1);

    // ===== EM Standard =====
    RegisterPhysics(new G4EmStandardPhysics()); // EM interaction at standard energy

    // ===== Nuclear - Hadron & Neutron =====
    RegisterPhysics(new G4HadronElasticPhysicsHP());    // High Precision Hadron/Neutron Elastic Scattering (G4NDL)
    RegisterPhysics(new G4ThermalNeutrons());           // Thermal Neutron Scattering S(alpha, beta) for E < 4 eV
    RegisterPhysics(new G4HadronPhysicsQGSP_BIC_HP());  // Inelastic Hadron/Neutron with High Precision
    RegisterPhysics(new G4StoppingPhysics());          // Stopping process
    RegisterPhysics(new G4IonPhysics());               // Ion interaction

    // ===== Decay =====
    RegisterPhysics(new G4DecayPhysics());             // Elemental Particles Decay
    RegisterPhysics(new G4RadioactiveDecayPhysics());  // Nuclear Decay
}


MyPhysicsList::~MyPhysicsList() {}
