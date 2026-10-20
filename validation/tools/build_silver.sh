# Build SILVER (Knichel, Sasdrich, Moradi, ASIACRYPT 2020) with Sylvan at the commit its README pins,
# against the user-local sysroot from deps.sh (Boost 1.83 headers + program_options).
set -e -o pipefail
T=~/lwe_agent_handoff/phase2/ext/tools/sca; R=$T/sysroot; L=$R/usr/lib/x86_64-linux-gnu
cd $T; [ -d sylvan ] || git clone -q https://github.com/trolando/sylvan.git
cd sylvan; git checkout -q 5e9da9782885f6215f6b509ac250212df30aaf70
mkdir -p build; cd build
[ -f src/libsylvan.so ] || cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON -DSYLVAN_BUILD_EXAMPLES=OFF -DSYLVAN_BUILD_TESTS=OFF \
  -DCMAKE_C_FLAGS="-Wno-error -I$R/usr/include -I$R/usr/include/x86_64-linux-gnu" -DGMP_INCLUDE_DIR=$R/usr/include/x86_64-linux-gnu \
  -DGMP_LIBRARIES=$L/libgmp.so > cmake.log 2>&1 || { tail -20 cmake.log; exit 1; }
[ -f src/libsylvan.so ] || make -j16 > make.log 2>&1 || { grep -E "error" make.log | head; exit 1; }
cd $T/SILVER
mkdir -p lib inc/sylvan
cp -a $T/sylvan/build/src/libsylvan.so* lib/ 2>/dev/null || cp -a $(find $T/sylvan/build -name "libsylvan.so*") lib/
cp $T/sylvan/src/*.h inc/sylvan/; cp $T/sylvan/build/src/*.h inc/sylvan/ 2>/dev/null || true
cp $T/sylvan/src/lace*.h inc/sylvan/ 2>/dev/null || true
make release BOOST=$R/usr/include LIBRARIES="-L./lib -lsylvan -L$L -lboost_program_options -Wl,-rpath,$L -Wl,-rpath,$T/SILVER/lib" > build.log 2>&1 || { grep -E "error" build.log | head -20; exit 1; }
ls -la bin
