{pkgs}: {
  deps = [
    pkgs.tk
    pkgs.tcl
    pkgs.qhull
    pkgs.pkg-config
    pkgs.gtk3
    pkgs.gobject-introspection
    pkgs.ghostscript
    pkgs.freetype
    pkgs.cairo
    pkgs.ffmpeg-full
    pkgs.portaudio
    pkgs.lsof
    pkgs.avahi
    pkgs.shairport-sync
    pkgs.iana-etc
  ];
}
