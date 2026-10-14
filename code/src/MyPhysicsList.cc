#include "MyPhysicsList.hh"

#include "G4SystemOfUnits.hh"
#include "G4EmStandardPhysics.hh"
#include "G4DecayPhysics.hh"
#include "G4HadronPhysicsQGSP_BIC_HP.hh"
#include "G4RadioactiveDecayPhysics.hh"
#include "G4HadronElasticPhysics.hh"
#include "G4GenericBiasingPhysics.hh"
#include <G4HadronPhysicsFTFP_BERT.hh>
#include <G4EmLivermorePhysics.hh>
#include <G4IonPhysics.hh>
#include <G4StoppingPhysics.hh>


MyPhysicsList::MyPhysicsList()
    : G4VModularPhysicsList()
{
    SetDefaultCutValue(0.7 * mm);
    SetVerboseLevel(1);

    // ===== EM Standard =====
    //RegisterPhysics(new G4EmLivermorePhysics());//EM  interaction at low energey, usually for gamma, electron, positron
	RegisterPhysics(new G4EmStandardPhysics());//EM interaction at high energy

    // ===== Nuclear - Hadron =====
    RegisterPhysics(new G4HadronElasticPhysics());//Hadron Elastic Scattering
    RegisterPhysics(new G4HadronPhysicsFTFP_BERT());//Hadron Inelastic Scattering
    RegisterPhysics(new G4StoppingPhysics());//Stopping proccess
    RegisterPhysics(new G4IonPhysics());//Ion interaction
    RegisterPhysics(new G4HadronPhysicsQGSP_BIC_HP());

    // ===== Decay =====
    RegisterPhysics(new G4DecayPhysics());// Elemental Particles Decay
    RegisterPhysics(new G4RadioactiveDecayPhysics());//Nuclear Decay
}


MyPhysicsList::~MyPhysicsList() {}
