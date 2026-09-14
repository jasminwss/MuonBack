# Warum `{thr}_digihit_topology_phi` bei phi≈90° und phi≈270° leere Bins hat, `vetopoint_topology_phi` aber nicht

**Untersucht am:** 2026-09-14
**Input-Datei:** `/afs/cern.ch/work/j/jaweiss/private/MuonBack/TRY6LiSc_full_onlySIM.root`
**Geometrie-Datei:** `/eos/user/j/jaweiss/MuonBack/TRY6LiSc/11921562/job_1026/geo_11921562_1026.root` (Key `FAIRGeom`)
**Analysierter Code:** `MuonBack/Inspection/inspect_Back.py`, `sw/SOURCES/FairShip/master/0c23afad9c/veto/vetoHit.cxx`, `sw/SOURCES/FairShip/master/0c23afad9c/veto/veto.cxx`

## Kurzfassung

Es gibt im gesamten SBT (alle 854 Zellen, alle 6 Shape-Typen, beide Blocks, alle Z-Layer) **keine einzige Zelle, deren geometrisches Zentrum näher als ca. 69°/111° an 90° liegt** (gespiegelt: 249°/291° an 270°). Das ist eine reale Eigenschaft der Detektor-Segmentierung, kein Bug in `inspect_Back.py` und kein Artefakt der Achsen-Konvention (Bin-Kanten o.ä.).

`vetopoint_topology_phi` ist trotzdem überall ungleich null, weil es die **kontinuierliche, wahre** Geant4-Treffer-Position (`veto_MCPoint.GetX()/GetY()`) verwendet — nicht die Zellzentren. Teilchen, die physikalisch die Mitte der Seitenwand (wahres y≈0) treffen, werden zwar digitalisiert, aber der Digihit wird beim Plotten auf das **Zentrum der getroffenen Zelle** (`vetoHit::GetXYZ()`, BBox-Origin → global) projiziert — und die nächstgelegene Zelle ist eben nie näher als ~69°/111° an 90°.

## Warum: die SBT-Seitenwand-Segmentierung

`vetoHit::GetXYZ()` (`veto/vetoHit.cxx:32-43`) liefert **nicht** die tatsächliche Trefferposition, sondern den lokalen BBox-Ursprung (= Zentrum) der ganzen physischen Zelle/des Bars, ins globale Koordinatensystem transformiert. Die SBT-Geometrie (`veto/veto.cxx`) besteht aus 6 Shape-Typen:

| ShapeType | Name | Rolle | phi-Bereich (diese Geometrie) |
|---|---|---|---|
| 1 | LiScX | flache Bars oben/unten | [0°, 180°] |
| 2 | LiScY | Seitenwand-Zellen | [57.3°, 302.7°] |
| 3 | LiSc_S3 | Eckstück | [18.2°, 205.4°] |
| 4 | LiSc_S4 | Eckstück | [27.6°, 221.1°] |
| 5 | LiSc_S5 | Eckstück | [154.6°, 341.8°] |
| 6 | LiSc_S6 | Eckstück | [138.9°, 332.4°] |

Entscheidend: **ShapeType 2 (LiScY, Seitenwand) hat pro Z-Layer nur 2 Zellen** — keine feine Unterteilung entlang y:
- `number=1` (obere Hälfte der Wand): phi läuft von 122.1° (Tankanfang, Block 2, Zlayer 1) bis 111.0° (Tankende, Zlayer 60)
- `number=2` (untere Hälfte der Wand): phi läuft von 57.9° bis 69.0° über denselben Bereich

D.h. selbst am äußersten stromabwärtigen Ende des Tanks (z≈8270 cm, dort ist der Tank am breitesten und die Zellzentren kommen `y=0` am nächsten) reicht keine Zelle näher als 69.0°/111.0° an die 90°-Marke heran. Weiter vorne im Tank ist die Lücke sogar noch breiter (58°-122°).

Die vier Eckstück-Typen (3-6) decken jeweils diagonale Winkelbereiche ab und kommen ebenfalls nirgends in die Nähe von 90°/270°.

**Bestätigt per direkter Geometrie-Abfrage** (Skript 05): Die größte Lücke zwischen benachbarten Zellzentren (phi-sortiert, über alle 854 Zellen) ist exakt **69.02°–110.98°** (Breite 41.97°) und gespiegelt **249.02°–290.98°** — das deckt sich (bis auf Rundung durch die 10°-Histogramm-Bins) exakt mit der leeren Region in `0_digihit_topology_phi`.

## Beweiskette (Skripte in `scripts/`, Rohausgabe in `results/`)

1. **`01_phi_profile_compare.py`** → `results/01_phi_profile_compare.txt`
   phi-Projektion (über z summiert) von `vetopoint_topology_phi` vs. `0_digihit_topology_phi`.
   Ergebnis: vetopoint ist in allen 36 Bins > 0; digihit ist exakt 0 in den Bins 8-11 (phi 70°-110°) und 26-29 (phi 250°-290°), plus zwei einzelne statistische Nullbins bei ~180°/~0° (nur niedrige Statistik, nicht der systematische Effekt).

2. **`02_shapewise_compare.py`** → `results/02_shapewise_compare.txt`
   Vergleich vetopoint- vs. digihit-Zählraten pro Shape-Typ (1-6). Alle 6 Shapes sind in beiden Histogrammen vorhanden und proportional zueinander (~Faktor 3) — die Lücke kommt also **nicht** daher, dass ein ganzer Shape-Typ in den Digihits fehlt.

3. **`03_digihit_xy_positions.py`** → `results/03_digihit_xy_positions.txt`
   Projektion von `0_digihit_topology` (3D: x,z,y) auf die x-y-Ebene: listet alle 342 tatsächlich getroffenen, diskreten (x,y)-Zellzentren mit ihrem phi. Zeigt den harten Sprung von phi=69.9° (x=205,y=-75) direkt zu phi=110.1° (x=205,y=75) — keine einzige gefüllte Zelle dazwischen, obwohl x=205 dort schon der maximale x-Wert ist (Tank an dieser Stelle am breitesten).

4. **`04_geometry_liscy_cells.py`** → `results/04_geometry_liscy_cells.txt`
   Lädt die echte Geometrie (`geo_11921562_1026.root`) und berechnet für alle 244 LiScY-Zellen (ShapeType 2) die wahre Master-Frame-Position genau wie `vetoHit::GetXYZ()`. Zeigt: nur `number ∈ {1,2}` pro Seite/Z-Layer (obere/untere Wandhälfte), und wie deren phi mit z von ~58°/122° (Tankanfang) auf ~69°/111° (Tankende) driftet.

5. **`05_geometry_full_gap_scan.py`** → `results/05_geometry_full_gap_scan.txt`
   Berechnet phi für **alle** 854 platzierten SBT-Zellen (alle Shapes, beide Blocks, alle Z-Layer) und sucht die größten Lücken zwischen benachbarten phi-Werten. Bestätigt: größte Lücke ist 69.02°-110.98° (und Spiegelung 249.02°-290.98°) — exakt die beobachtete leere Region im Histogramm.

## Fazit / Einordnung

- **Kein Bug.** Weder in `inspect_Back.py` noch in `vetoHit.cxx`/`veto.cxx` — es ist eine reale, bewusste (oder zumindest so gebaute) Detektorsegmentierung: die Seitenwand ist pro Z-Layer nur in 2 Hälften geteilt, keine davon ist bei y=0 zentriert.
- **Nicht behebbar auf Digihit-Ebene.** Feinere phi-Auflösung um 90°/270° gibt es nur in `vetopoint_topology_phi` (wahre MC-Trefferposition), nicht in den `{thr}_digihit_*`-Histogrammen, da diese strukturell an Zellzentren gebunden sind.
- Für zukünftige Analysen (insb. das laufende `z_phi_origin.py`-Skript zur Origin-Aufteilung, siehe Memory `muonback-z-phi-origin-script`): diese Lücke ist erwartet und muss nicht weiter debuggt werden.

## Nützliche Referenzen

- `vetoHit::GetXYZ()`: `sw/SOURCES/FairShip/master/0c23afad9c/veto/vetoHit.cxx:32-43`
- `vetoHit::GetNode()` (detID-Dekodierung, Pfad-Konstruktion): `sw/SOURCES/FairShip/master/0c23afad9c/veto/vetoHit.cxx:57-93`
- SBT-Geometrieaufbau (Shapes, Blocks, Z-Layer, Rotationen): `sw/SOURCES/FairShip/master/0c23afad9c/veto/veto.cxx` (v.a. Zeilen 337-654)
- `Phicalc()` und die Fill-Aufrufe: `MuonBack/Inspection/inspect_Back.py:63-78,390,465`
- detID-Schema: `id = ShapeType*100000 + blockNr*10000 + Zlayer*100 + number*10 + position`
