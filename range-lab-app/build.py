"""Build the Range Lab Android app (RangeLab.apk) without Gradle.

Steps: assemble the web assets from the two trainer pages, compile resources with aapt2,
compile the activity with javac, dex it with d8, then zipalign and sign with apksigner.

Usage:  python build.py
Tools:  JDK 21 and the Android SDK (platform 35, build-tools 35.0.0) under C:\\Users\\there\\android-build
"""
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT.parent                      # folder holding the two trainer pages and their data files
TOOLS = Path(r"C:\Users\there\android-build")
JDK = next((TOOLS / "jdk").glob("jdk-*"))
SDK = TOOLS / "sdk"
BT = SDK / "build-tools" / "35.0.0"
ANDROID_JAR = SDK / "platforms" / "android-35" / "android.jar"
BUILD = ROOT / "build"
DIST = ROOT / "dist"
APK = DIST / "RangeLab.apk"
KEYSTORE = ROOT / "android" / "rangelab.keystore"
KEY_ALIAS = "rangelab"
KEY_PASS = "rangelab-local"                 # local sideload key; keep the keystore so updates install over the old app

ENV = dict(os.environ, JAVA_HOME=str(JDK), PATH=str(JDK / "bin") + os.pathsep + os.environ.get("PATH", ""))


def run(*args):
    args = [str(a) for a in args]
    print(">", " ".join(args)[:160])
    subprocess.run(args, check=True, env=ENV)


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one match for: {old[:60]!r}")
    return text.replace(old, new)


def app_page(src, renames):
    """Wrap an artifact page as a standalone app page: doctype, app class, home button, app stylesheet."""
    body = src.read_text(encoding="utf-8")
    for old, new in renames:
        body = replace_once(body, old, new)
    body = replace_once(body, '<div class="brand">', '<a class="home-link" href="index.html" aria-label="Back to Range Lab">&lsaquo;</a><div class="brand">')
    body = body.replace("'Roboto Condensed',sans-serif", "'Roboto Condensed','sans-serif-condensed',sans-serif")
    body = replace_once(body, "</style>", '</style>\n<link rel="stylesheet" href="app.css">')
    if re.search(r"ville", body, re.I):
        raise SystemExit(f"{src.name}: Ville branding left in the page")
    head = ('<!doctype html>\n<html lang="en" class="app">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n</head>\n<body>\n')
    return head + body + '\n<script src="app.js"></script>\n</body>\n</html>\n'


def build_assets():
    www = BUILD / "assets" / "www"
    shutil.rmtree(BUILD / "assets", ignore_errors=True)
    www.mkdir(parents=True)
    for name in ("index.html", "app.css", "app.js"):
        shutil.copy(ROOT / "web" / name, www / name)
    (www / "tournament.html").write_text(app_page(SOURCES / "ville600-range-lab.html", [
        ("<title>Ville 600 Range Lab</title>", "<title>Tournament · Range Lab</title>"),
        ('<div class="chip-mark" aria-hidden="true">600</div><div><b>Ville 600 Range Lab</b><span>Preflop tournament ranges, 5–100bb</span></div>',
         '<div class="chip-mark" aria-hidden="true">MTT</div><div><b>Tournament</b><span>Preflop ranges, 5–100bb</span></div>'),
        ("How to use this before the Ville 600", "How to study tournament ranges"),
    ]), encoding="utf-8")
    (www / "cash.html").write_text(app_page(SOURCES / "cash-range-lab.html", [
        ("<title>Live Cash Range Lab</title>", "<title>Live cash · Range Lab</title>"),
        ("<b>Live Cash Range Lab</b><span>8-handed preflop, regular and straddle games</span>", "<b>Live cash</b><span>8-handed, regular and straddle</span>"),
    ]), encoding="utf-8")
    shutil.copy(SOURCES / "data.js", www / "data.js")
    shutil.copy(SOURCES / "cash-data.js", www / "cash-data.js")


def build_apk():
    classes, dex = BUILD / "classes", BUILD / "dex"
    for d in (classes, dex):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
    DIST.mkdir(exist_ok=True)

    run(BT / "aapt2.exe", "compile", "--dir", ROOT / "android" / "res", "-o", BUILD / "res.zip")
    run(BT / "aapt2.exe", "link", "-o", BUILD / "base.apk", "-I", ANDROID_JAR,
        "--manifest", ROOT / "android" / "AndroidManifest.xml", "-A", BUILD / "assets",
        "--min-sdk-version", "30", "--target-sdk-version", "35", BUILD / "res.zip")

    java = sorted((ROOT / "android" / "src").rglob("*.java"))
    run(JDK / "bin" / "javac.exe", "-source", "11", "-target", "11", "-Xlint:-options",
        "-classpath", ANDROID_JAR, "-d", classes, *java)
    run(BT / "d8.bat", "--release", "--min-api", "30", "--lib", ANDROID_JAR, "--output", dex, *sorted(classes.rglob("*.class")))

    # Repack aapt2's output with classes.dex added; writing a fresh zip keeps local and central headers consistent.
    unsigned = BUILD / "unsigned.apk"
    with zipfile.ZipFile(BUILD / "base.apk") as src, zipfile.ZipFile(unsigned, "w") as out:
        for info in src.infolist():
            out.writestr(zipfile.ZipInfo(info.filename, info.date_time), src.read(info), compress_type=info.compress_type)
        out.write(dex / "classes.dex", "classes.dex", compress_type=zipfile.ZIP_DEFLATED)
    aligned = BUILD / "aligned.apk"
    run(BT / "zipalign.exe", "-P", "16", "-f", "4", unsigned, aligned)

    if not KEYSTORE.exists():
        run(JDK / "bin" / "keytool.exe", "-genkeypair", "-keystore", KEYSTORE, "-alias", KEY_ALIAS,
            "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
            "-storepass", KEY_PASS, "-keypass", KEY_PASS, "-dname", "CN=Range Lab, O=Personal")
    run(BT / "apksigner.bat", "sign", "--ks", KEYSTORE, "--ks-key-alias", KEY_ALIAS,
        "--ks-pass", "pass:" + KEY_PASS, "--key-pass", "pass:" + KEY_PASS, "--out", APK, aligned)
    run(BT / "apksigner.bat", "verify", APK)
    print(f"\nBuilt {APK} ({APK.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    build_assets()
    build_apk()
