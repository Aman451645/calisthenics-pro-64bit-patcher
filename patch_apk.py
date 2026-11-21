import os
import subprocess
import urllib.request
import zipfile
import io

scratch_dir = r"C:\Users\HP\.gemini\antigravity\scratch\cali_patch"
os.makedirs(scratch_dir, exist_ok=True)

original_apk = r"C:\Users\HP\Downloads\Calisthenics-Pro-1.2.1(www.farsroid.com) (2).apk"
unaligned_apk = os.path.join(scratch_dir, "calisthenics_unaligned.apk")
aligned_apk = os.path.join(scratch_dir, "calisthenics_aligned.apk")
final_apk = r"C:\Users\HP\Downloads\Calisthenics-Pro-1.2.1-64bit.apk"

print("1. Compiling libARM_ARCH.so for arm64-v8a...")
c_src = os.path.join(scratch_dir, "archArm.c")
with open(c_src, "w") as f:
    f.write('''#include <jni.h>

JNIEXPORT jstring JNICALL Java_com_github_hiteshsondhi88_libffmpeg_ArmArchHelper_cpuArchFromJNI(JNIEnv* env, jobject obj) {
    return (*env)->NewStringUTF(env, "armv7-neon");
}
''')

clang_exe = r"C:\Users\HP\AppData\Local\Android\Sdk\ndk\28.2.13676358\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe"
arm_arch_so = os.path.join(scratch_dir, "libARM_ARCH.so")
res = subprocess.run([
    clang_exe,
    "--target=aarch64-linux-android28",
    "-shared",
    "-O2",
    c_src,
    "-o", arm_arch_so
], capture_output=True, text=True)

if res.returncode != 0:
    print("Clang error:", res.stderr)
    raise RuntimeError("Failed to compile libARM_ARCH.so")
print("libARM_ARCH.so compiled successfully. Size:", os.path.getsize(arm_arch_so))

print("2. Downloading official 64-bit AARs from Maven Central...")
url_gif = "https://repo1.maven.org/maven2/pl/droidsonroids/gif/android-gif-drawable/1.2.16/android-gif-drawable-1.2.16.aar"
url_card = "https://repo1.maven.org/maven2/io/card/android-sdk/5.5.1/android-sdk-5.5.1.aar"

with urllib.request.urlopen(url_gif) as resp:
    gif_aar = resp.read()
with urllib.request.urlopen(url_card) as resp:
    card_aar = resp.read()

arm64_files = {}

with zipfile.ZipFile(io.BytesIO(gif_aar)) as z:
    for n in z.namelist():
        if "arm64-v8a" in n and n.endswith(".so"):
            filename = os.path.basename(n)
            arm64_files[f"lib/arm64-v8a/{filename}"] = z.read(n)
            print("Extracted from gif-drawable:", filename)

with zipfile.ZipFile(io.BytesIO(card_aar)) as z:
    for n in z.namelist():
        if "arm64-v8a" in n and n.endswith(".so"):
            filename = os.path.basename(n)
            arm64_files[f"lib/arm64-v8a/{filename}"] = z.read(n)
            print("Extracted from card.io:", filename)

with open(arm_arch_so, "rb") as f:
    arm64_files["lib/arm64-v8a/libARM_ARCH.so"] = f.read()
print("Added compiled libARM_ARCH.so")

print(f"Total 64-bit libraries gathered: {len(arm64_files)}")

print("3. Repackaging APK...")
# Note: Because extractNativeLibs="false", all .so files MUST be stored UNCOMPRESSED (ZIP_STORED)
# and page-aligned to 4096 bytes via zipalign -p.
if os.path.exists(unaligned_apk):
    os.remove(unaligned_apk)

with zipfile.ZipFile(original_apk, "r") as z_in:
    with zipfile.ZipFile(unaligned_apk, "w") as z_out:
        for item in z_in.infolist():
            # Skip old signature files
            if item.filename.startswith("META-INF/") and (
                item.filename.endswith(".RSA") or item.filename.endswith(".SF") or item.filename.endswith(".MF")
            ):
                continue
            
            # Skip old 32-bit libraries (we only want 64-bit arm64-v8a for modern 64-bit device)
            if item.filename.startswith("lib/armeabi-v7a/") or item.filename.startswith("lib/x86/"):
                continue

            data = z_in.read(item.filename)
            zinfo = zipfile.ZipInfo(item.filename)
            zinfo.date_time = item.date_time
            zinfo.external_attr = item.external_attr
            
            # Ensure .so files are ZIP_STORED, everything else keeps original compression
            if item.filename.endswith(".so"):
                zinfo.compress_type = zipfile.ZIP_STORED
            else:
                zinfo.compress_type = item.compress_type

            z_out.writestr(zinfo, data)

        # Inject 64-bit arm64-v8a libraries with ZIP_STORED
        for path, data in arm64_files.items():
            zinfo = zipfile.ZipInfo(path)
            zinfo.compress_type = zipfile.ZIP_STORED
            zinfo.date_time = (2026, 1, 1, 0, 0, 0)
            z_out.writestr(zinfo, data)

print("4. Aligning APK with zipalign -p 4...")
zipalign_exe = r"C:\Users\HP\AppData\Local\Android\Sdk\build-tools\34.0.0\zipalign.exe"
if os.path.exists(aligned_apk):
    os.remove(aligned_apk)

# -f: overwrite, -p: page-align uncompressed .so files, 4: 4-byte align others
subprocess.run([zipalign_exe, "-f", "-p", "4", unaligned_apk, aligned_apk], check=True)

print("5. Verifying alignment with zipalign -c -v -p 4...")
res = subprocess.run([zipalign_exe, "-c", "-v", "-p", "4", aligned_apk], capture_output=True, text=True)
lines = [l for l in res.stdout.splitlines() if "lib/" in l]
for l in lines:
    print(" ", l)

print("6. Signing APK with apksigner...")
keystore_path = os.path.join(scratch_dir, "debug.keystore")
keytool_exe = r"C:\Program Files\Microsoft\jdk-17.0.20.101-hotspot\bin\keytool.exe"
if not os.path.exists(keystore_path):
    subprocess.run([
        keytool_exe, "-genkey", "-v",
        "-keystore", keystore_path,
        "-alias", "androiddebugkey",
        "-keyalg", "RSA",
        "-keysize", "2048",
        "-validity", "10000",
        "-storepass", "android",
        "-keypass", "android",
        "-dname", "CN=Android Debug,O=Android,C=US"
    ], check=True)

if os.path.exists(final_apk):
    os.remove(final_apk)

apksigner_bat = r"C:\Users\HP\AppData\Local\Android\Sdk\build-tools\34.0.0\apksigner.bat"
subprocess.run([
    apksigner_bat, "sign",
    "--ks", keystore_path,
    "--ks-key-alias", "androiddebugkey",
    "--ks-pass", "pass:android",
    "--key-pass", "pass:android",
    "--out", final_apk,
    aligned_apk
], check=True)

print("SUCCESS! Output written to:", final_apk)
