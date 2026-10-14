// =========================================================================
// MyEventAction.cc - PHIÊN BẢN ĐÃ SỬA
// =========================================================================

#include "MyEventAction.hh"
#include "MyRunAction.hh"
#include "MyHits.hh"

#include "G4Event.hh"
#include "G4HCofThisEvent.hh"

// =========================================================================
// Constructor
// =========================================================================
MyEventAction::MyEventAction(MyRunAction* runAction)
    : G4UserEventAction(), fRunAction(runAction), fEdepEvent(0.) {
}

// =========================================================================
// Destructor
// =========================================================================
MyEventAction::~MyEventAction() = default;

// =========================================================================
// BeginOfEventAction
// =========================================================================
void MyEventAction::BeginOfEventAction(const G4Event*) {
    // Chỉ reset energy, KHÔNG cần fCountedNaIDet nữa
    fEdepEvent = 0.;
}

// =========================================================================
// EndOfEventAction - ĐÃ SỬA
// =========================================================================
void MyEventAction::EndOfEventAction(const G4Event* event) {
    if (!fRunAction) return;

    auto hce = event->GetHCofThisEvent();
    if (!hce) return;

    // --- Loop through all hits collections ---
    for (int i = 0; i < hce->GetNumberOfCollections(); i++) {
        auto hc = dynamic_cast<MyHitsCollection*>(hce->GetHC(i));
        if (!hc) continue;

        // --- Loop through ALL hits ---
        for (unsigned int j = 0; j < hc->entries(); j++) {
            auto hit = (*hc)[j];
            const auto& volName = hit->GetVolumeName();

            // ============================================================
            // SỬA: Cộng TẤT CẢ energy deposits từ MỌI particle, MỌI hit
            // ============================================================
            if (volName == "NaI_Detector") {
                fEdepEvent += hit->GetEdep();
            }
        }
    }

    // ================================================================
    // SỬA: Đếm event nếu có BẤT KỲ năng lượng nào deposited
    // Không quan tâm particle là gamma hay electron
    // ================================================================
    if (fEdepEvent > 0.) {
        fRunAction->AddEdepNaIDet(fEdepEvent);
        fRunAction->AddCountedNaIDet();  // Đếm mọi event có tương tác
    }
}
