# Assembly and test plan

The CAD models show unloaded assemblies with bonded steel end caps and separate upper/lower M6 studs. No continuous steel rod crosses the rubber. Do not add a tight through-bolt that bypasses the isolator. Threads and rubber-to-metal bonding are simplified; use rated purchased isolators or independently developed bonded parts, not uncharacterized printed rubber.

The base is 220×180×4 mm and the isolated plate 200×160×4 mm. Four mount centers lie on a 140×110 mm rectangle. M6 studs pass through Ø6.6 mm holes, giving 0.3 mm nominal radial clearance. The base anchor pattern is 190×150 mm with Ø8.5 mm holes. The example compressor interface is 100×70 mm with Ø8.5 mm holes. Confirm actual foot spacing, center of gravity, fastener capacity and temperature before fabrication. Plate rigidity and bolt strength are not verified by FEA.

Use STEP for CAD exchange. STL coordinates are metres: a millimetre-based slicer requires a factor of 1000 on import. The geometry source is `src/vibramount/cad.py`; JSON inputs and native FreeCAD `Parameters` length properties are editable. Python proxy recomputation requires the package on FreeCAD's Python path.

Measure loaded sag and corner loads, check that studs/guards do not contact the opposite structure, and confirm no bottoming or lateral instability. Start with a low-amplitude shaker or controlled bench excitation. Measure base and plate motion for base excitation, or applied/transmitted force for a fixed-base force test; do not interchange the ratios. Record sensor calibration, mounting, excitation amplitude, frequency and temperature. Compare the measured resonance and damping with the model before using the predicted operating-band improvement.

Startup traverses resonance even though the operating band lies above it. The selected property combination permits greater resonance amplification than the reference; the peak constraint is therefore part of the selection rather than an afterthought. No physical test or noise-reduction measurement has been performed.
