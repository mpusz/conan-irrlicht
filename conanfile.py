from conans import ConanFile, AutoToolsBuildEnvironment, MSBuild, tools
import os
import shutil

class IrrlichtConan(ConanFile):
    name = "irrlicht"
    version = "1.8.4"
    license = "http://irrlicht.sourceforge.net/?page_id=294"
    url = "https://github.com/mpusz/conan-irrlicht"
    description = "An open source high performance realtime 3D engine written in C++"
    exports = "LICENSE.md"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    @property
    def _subfolder(self):
        return "irrlicht-%s" % self.version

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def source(self):
        zip_name = "irrlicht-%s.zip" % self.version
        tools.get("http://downloads.sourceforge.net/irrlicht/%s" % zip_name, sha1="38bf0223fe868d243d6a39d0dc191c8df6e03b3b")

    def system_requirements(self):
        if self.settings.os == "Macos":
            self.run("brew cask install xquartz")

        if self.settings.os == "Linux" and tools.os_info.is_linux:
            installer = tools.SystemPackageTool()
            if tools.os_info.with_apt:
                if self.settings.arch == "x86":
                    arch_suffix = ':i386'
                elif self.settings.arch == "x86_64":
                    arch_suffix = ':amd64'
                packages = ['libgl1-mesa-dev%s' % arch_suffix]
                packages.append('libxcursor-dev%s' % arch_suffix)

            if tools.os_info.with_yum:
                if self.settings.arch == "x86":
                    arch_suffix = '.i686'
                elif self.settings.arch == 'x86_64':
                    arch_suffix = '.x86_64'
                packages = ['mesa-libGL-devel%s' % arch_suffix]
                packages.append('libXcursor-devel%s' % arch_suffix)

            for package in packages:
                installer.install(package)

    def _patch_windows(self):
        # patch library name
        tools.replace_in_file("Makefile", "-ld3dx9d", "-ld3dx9")

    def _patch_macos(self):
        # patch OSX build
        shutil.move("Irrlicht.cpp", "Irrlicht.mm")
        shutil.move("COpenGLDriver.cpp", "COpenGLDriver.mm")

    def build(self):
        if self.settings.compiler == "Visual Studio":
            msbuild = MSBuild(self)
            msbuild.build("../source/%s/source/Irrlicht/Irrlicht11.0.sln" % self._subfolder)
            # TBD....
        else:
            with tools.chdir(os.path.join(self._subfolder, "source", "Irrlicht")):
                autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
                if self.settings.os != 'Windows':
                    autotools.fpic = self.options.fPIC

                if tools.os_info.is_windows:
                    self._patch_windows()
                    make_target = "sharedlib_win32" if self.options.shared else "staticlib_win32"
                elif tools.os_info.is_macos:
                    self._patch_macos()
                    make_target = "sharedlib_osx" if self.options.shared else "staticlib_osx"
                else:
                    make_target = "sharedlib" if self.options.shared else "staticlib"

                autotools.make(target=make_target)

    def package(self):
        self.copy(pattern="*license*", dst="licenses", ignore_case=True, keep_path=False)

        include_folder = os.path.join(self._subfolder, "include")
        self.copy(pattern="*", dst="include", src=include_folder)

        media_folder = os.path.join(self._subfolder, "media")
        self.copy(pattern="*", dst="media", src=media_folder)

        if tools.os_info.is_windows:
            folder = "Win32-gcc"
        elif tools.os_info.is_macos:
            folder = "MacOSX"
        else:
            folder = "Linux"

        lib_folder = os.path.join(self._subfolder, "lib", folder)
        bin_folder = os.path.join(self._subfolder, "bin", folder)

        self.copy(pattern="*.dll", src=bin_folder, dst="bin", keep_path=False)
        self.copy(pattern="*.lib", src=lib_folder, dst="lib", keep_path=False)
        self.copy(pattern="*.a", src=lib_folder, dst="lib", keep_path=False)
        self.copy(pattern="*.so*", src=lib_folder, dst="lib", keep_path=False)
        self.copy(pattern="*.dylib", src=lib_folder, dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Windows":
            self.cpp_info.libs.append("opengl32")
            self.cpp_info.libs.append("m")

        if self.settings.os == "Macos":
            self.cpp_info.exelinkflags.append("-framework OpenGL")
        
        if self.settings.os == "Linux":
            if not self.options.shared:
                self.cpp_info.libs.append("GL")
                self.cpp_info.libs.append("Xxf86vm")
                self.cpp_info.libs.append("Xext")
                self.cpp_info.libs.append("X11")
                self.cpp_info.libs.append("Xcursor")

        self.output.info(self.cpp_info.libs)
