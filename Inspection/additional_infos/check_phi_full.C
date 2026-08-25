void check_phi_full() {
    TFile* f = TFile::Open("/eos/user/j/jaweiss/MuonBack/TRY6LiSc/z_phi_origin/phi-z-plots.root");
    TH2D* hveto = (TH2D*)f->Get("vetopoint_topology_phi cavern");
    TH2D* h0 = (TH2D*)f->Get("0_digihit_topology_phi cavern");

    printf("phi bin | phi range | vetopoint(sum over z) | digihit_0MeV(sum over z)\n");
    for (int ybin=1; ybin<=hveto->GetNbinsY(); ybin++) {
        double lo = hveto->GetYaxis()->GetBinLowEdge(ybin);
        double hi = hveto->GetYaxis()->GetBinUpEdge(ybin);
        double sveto=0, s0=0;
        for (int xbin=1; xbin<=hveto->GetNbinsX(); xbin++) {
            sveto += hveto->GetBinContent(xbin, ybin);
            s0 += h0->GetBinContent(xbin, ybin);
        }
        printf("  bin %2d | [%5.1f,%5.1f) | %14.6g | %14.6g\n", ybin, lo, hi, sveto, s0);
    }

    printf("\ndigihit_0MeV total integral = %g, entries = %g\n", h0->Integral(), h0->GetEntries());
    printf("vetopoint total integral = %g, entries = %g\n", hveto->Integral(), hveto->GetEntries());
}
