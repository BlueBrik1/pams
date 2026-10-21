export PATH=$(ls -d ~/.TinyTeX/bin/*):$PATH
rm -f /tmp/TinyTeX-1-linux-x86_64.tar.xz
tlmgr install latexmk pgf pgfplots circuitikz siunitx listings xcolor booktabs caption enumitem multirow microtype cleveref hyperref natbib doi url mathtools amsmath amsfonts float placeins xstring etoolbox environ trimspaces tcolorbox listingsutf8 lm cm-super algorithms algorithmicx lineno titlesec sectsty fancyhdr lastpage changepage threeparttable makecell colortbl standalone preview pdfcrop tools sttools preprint graphics oberdiek > ~/tinytex_pkgs2.log 2>&1; echo tlmgr rc=$?
grep -iE 'not present|error' ~/tinytex_pkgs2.log | head
for s in tikz.sty pgfplots.sty circuitikz.sty siunitx.sty listings.sty booktabs.sty subcaption.sty tabularx.sty cleveref.sty natbib.sty microtype.sty stfloats.sty afterpage.sty bm.sty tcolorbox.sty enumitem.sty threeparttable.sty makecell.sty; do printf "%s %s\n" $s "$(kpsewhich $s >/dev/null && echo ok || echo MISSING)"; done
