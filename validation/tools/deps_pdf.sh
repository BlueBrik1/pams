# pdftotext (poppler-utils) into the user-local sysroot, no root
R=~/lwe_agent_handoff/phase2/ext/tools/sca/sysroot; cd $R/debs
apt-get download poppler-utils libpoppler134 libopenjp2-7 liblcms2-2 libnss3 libnspr4 libjpeg-turbo8 libtiff6 \
  libgpgme11t64 libassuan0 libjbig0 libdeflate0 libwebp7 libsharpyuv0 liblerc4 2>&1 | tail -1
for f in poppler-utils_*.deb libpoppler134_*.deb libopenjp2-7_*.deb liblcms2-2_*.deb libnss3_*.deb libnspr4_*.deb \
  libjpeg-turbo8_*.deb libtiff6_*.deb libgpgme11t64_*.deb libassuan0_*.deb libjbig0_*.deb libdeflate0_*.deb \
  libwebp7_*.deb libsharpyuv0_*.deb liblerc4_*.deb; do dpkg -x "$f" $R; done
LD_LIBRARY_PATH=$R/usr/lib/x86_64-linux-gnu $R/usr/bin/pdftotext -v 2>&1 | head -1
