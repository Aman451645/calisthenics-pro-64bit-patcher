# Calisthenics Pro 64-bit Patcher (Snapdragon 8 Elite / Android 15+)

A tool to patch and modernize legacy 32-bit APKs (specifically Calisthenics Pro) to run natively on modern 64-bit-only hardware (such as Snapdragon 8 Elite, Dimensity 9400, Tensor G4+) and Android 15/16 without losing original assets, routines, or identity.

---

## 🔍 The Problem
Modern Android chipsets (e.g., Snapdragon 8 Elite / Oryon CPU) have dropped hardware-level 32-bit execution units (`armeabi-v7a`, `x86`). When attempting to run legacy 32-bit apps, Android rejects installation:
```text
INSTALL_FAILED_NO_MATCHING_ABIS: Failed to extract native libraries, res=-113
```

Furthermore, Android 15+ enforces strict runtime page memory mapping (`extractNativeLibs="false"`). If uncompressed shared libraries (`.so`) are not page-aligned (4096-byte / 16KB boundary), PackageManager throws:
```text
INSTALL_FAILED_INVALID_APK: Failed to extract native libraries, res=-2
```

---

## 🛠️ What This Patcher Does

1. **Native 64-bit Library Acquisition (`arm64-v8a`)**:
   * Slices out outdated 32-bit binaries (`armeabi-v7a`, `x86`).
   * Fetches official 64-bit native `.so` builds from Maven Central:
     - `pl.droidsonroids.gif:android-gif-drawable:1.2.16` (`libpl_droidsonroids_gif.so`)
     - `io.card:android-sdk:5.5.1` (`libcardioDecider.so`, `libcardioRecognizer.so`, `libopencv_core.so`, `libopencv_imgproc.so`).
2. **JNI Architecture Bridge**:
   * Compiles `libARM_ARCH.so` using Android NDK Clang (`--target=aarch64-linux-android28`) to intercept JNI CPU architecture checks and prevent `UnsatisfiedLinkError` crashes.
3. **Android 15 Page Alignment**:
   * Packages `.so` files uncompressed (`ZIP_STORED`).
   * Aligns shared objects to 4096-byte page boundaries via `zipalign -p 4`.
4. **Modern v2/v3 Signing**:
   * Re-signs the package with `apksigner` for compatibility with modern Android package verification.

---

## 🚀 Usage

### Prerequisites
* Python 3.8+
* Android SDK (`zipalign`, `apksigner`)
* Android NDK (Clang compiler)
* JDK 17+

### Running the Patcher
```bash
python patch_apk.py
```

---

## 📄 License
MIT License. Original APK assets belong to their respective copyright holders.
