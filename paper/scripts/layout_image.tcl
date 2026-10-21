# Export a placement/routing image of a finished OpenROAD run (final.def) with the OpenROAD GUI renderer (headless).
# env: RUN (run directory), IMG (output png), RES (um per pixel)
set P $::env(ORFS_PLATFORMS)/nangate45
read_lef $P/lef/NangateOpenCellLibrary.tech.lef
read_lef $P/lef/NangateOpenCellLibrary.macro.mod.lef
read_def $::env(RUN)/final.def
save_image -resolution $::env(RES) $::env(IMG)
exit
