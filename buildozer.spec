[app]

# (str) Title of your application
title = e-Jiro

# (str) Package name
package.name = ejiro

# (str) Package domain (needed for android/ios packaging)
package.domain = org.ejiro

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,db,md

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec
source.exclude_dirs = venv, tests, .git, .github, __pycache__, .pytest_cache, .ruff_cache

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3==3.11.5,kivy==2.3.0,kivymd==1.2.0,fpdf2,pillow,android,pyjnius,sdl2,sqlite3,freetype

# (str) Application icon
icon.filename = %(source.dir)s/logo_e-jiro.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, VIBRATE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, then skip trying to update the Android sdk
# This can be useful to avoid android sdk updates on CI machines.
android.skip_update = False

# (str) ANDROID_NDK_HOME path to use. If the value is left empty, the
# default Android NDK path will be used.
# android.ndk_path =

# (str) ANDROID_SDK_HOME path to use if it's not in your $PATH
# android.sdk_path =

# (bool) If True, then automatically accept SDK license
# agreements. This is intended for automation only. If set to False,
# the default, you will be required to accept the SDK license when
# first running buildozer.
android.accept_sdk_license = True

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (str) Log level for Kivy (0=error, 1=info, 2=debug)
log_level = 2

# (bool) Android allow backup feature (disabled by default)
android.allow_backup = True

# (str) The format used to package the app for release mode (aab or apk or both).
android.release_artifact = apk

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
