# Unpack build dependencies into a user-local sysroot (no root needed): apt-get download + dpkg -x
set -e -o pipefail
R=~/lwe_agent_handoff/phase2/ext/tools/sca/sysroot; mkdir -p $R/debs; cd $R/debs
PK="libboost1.83-dev libboost-program-options1.83-dev libboost-program-options1.83.0 libboost-log1.83-dev libboost-log1.83.0
 libboost-thread1.83-dev libboost-thread1.83.0 libboost-system1.83-dev libboost-system1.83.0 libboost-filesystem1.83-dev
 libboost-filesystem1.83.0 libboost-python1.83-dev libboost-python1.83.0 libboost-regex1.83.0 libboost-atomic1.83.0
 libboost-date-time1.83.0 libflint-dev libflint18t64 libmpfr-dev libgmp-dev libpython3.12-dev
 python3.12-dev libqhull-dev libqhull-r8.0 libqhullcpp8.0 zlib1g-dev libicu74 libgmp10 libmpfr6 libgmpxx4ldbl libpython3.12t64"
apt-get download $PK 2>&1 | tail -3
for f in *.deb; do dpkg -x $f $R; done
ls $R/usr/lib/x86_64-linux-gnu | grep -E "boost_program|flint|python3.12|qhull" | head
