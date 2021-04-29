# Duke3D World Tour GRP Downgrader

This Python script downgrades the World Tour `DUKE3D.GRP` file to a checksum-accurate 
version found in Atomic Edition v1.5, which is considered the de-facto default and
is supported by most mods and source ports.

To use, place `downgrade_patch.dat` and `duke3d_wt_downgrader.py` in the same directory
with the World Tour `DUKE3D.GRP` and run `duke3d_wt_downgrader.py`. It will downgrade
the `DUKE3D.GRP` to v1.5 Atomic Edition, along with making a backup of the World Tour 
`DUKE3D.GRP` as `DUKE3D.GRP.bak`.

Requires Python v3.7 or newer to run.
