#include <jni.h>

JNIEXPORT jstring JNICALL Java_com_github_hiteshsondhi88_libffmpeg_ArmArchHelper_cpuArchFromJNI(JNIEnv* env, jobject obj) {
    return (*env)->NewStringUTF(env, "armv7-neon");
}
