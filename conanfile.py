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
    exports_sources = ["*.patch"]
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
#        if self.settings.os == "Macos":
#            self.run("brew cask install xquartz")

        if self.settings.os == "Linux" and tools.os_info.is_linux:
            installer = tools.SystemPackageTool()
            if tools.os_info.with_apt:
                packages = ['libgl1-mesa-dev', 'libxcursor-dev', 'libxxf86vm-dev']

            if tools.os_info.with_yum:
                if self.settings.arch == "x86":
                    arch_suffix = '.i686'
                elif self.settings.arch == 'x86_64':
                    arch_suffix = '.x86_64'
                packages = ['mesa-libGL-devel%s' % arch_suffix]
                packages.append('libXcursor-devel%s' % arch_suffix)

            for package in packages:
                installer.install(package)

    def _patch_add_shared_lib_links(self):
        # Irrlicht does that only for install step and without the links create Conan does not link correctly
        tools.replace_in_file("Makefile", "cp $(SHARED_FULLNAME) $(LIB_PATH)", """cp $(SHARED_FULLNAME) $(LIB_PATH)
	cd $(LIB_PATH) && ln -s -f $(SHARED_FULLNAME) $(SONAME)
	cd $(LIB_PATH) && ln -s -f $(SONAME) $(SHARED_LIB)""")

    def _patch_mingw(self):
        # patch library name
        tools.replace_in_file("Makefile", "-ld3dx9d", "-ld3dx9")

    def _patch_macos(self):
        # fix compilation
        shutil.move("Irrlicht.cpp", "Irrlicht.mm")
        shutil.move("COpenGLDriver.cpp", "COpenGLDriver.mm")
        # comment unsupported options
        tools.replace_in_file("Makefile", "staticlib_osx sharedlib_osx: LDFLAGS += --no-export-all-symbols --add-stdcall-alias", "#staticlib_osx sharedlib_osx: LDFLAGS += --no-export-all-symbols --add-stdcall-alias")
        # uncomment Macosx linker flags
        tools.replace_in_file("Makefile", "#sharedlib_osx: LDFLAGS", "sharedlib_osx: LDFLAGS")
        # add Macosx specific sources
        tools.replace_in_file("Makefile", "Irrlicht.o os.o", "Irrlicht.o os.o MacOSX/CIrrDeviceMacOSX.o MacOSX/OSXClipboard.o MacOSX/AppDelegate.o")
        # fix window creation
        tools.patch(patch_file=os.path.join(self.source_folder, "osx-window-creation.patch"), strip=2)
        # fix shared libraries
        self._patch_add_shared_lib_links()

    def _patch_linux(self):
        # fix shared libraries
        self._patch_add_shared_lib_links()

    def build(self):
        with tools.chdir(os.path.join(self._subfolder, "source", "Irrlicht")):
            if self.settings.compiler == "Visual Studio":
                msbuild = MSBuild(self)
                if self.options.shared:
                    build_type = self.settings.build_type
                else:
                    build_type = "Static lib - %s" % self.settings.build_type
                msbuild.build("Irrlicht11.0.sln", build_type=build_type, use_env=False)
            else:
                autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
                if self.settings.os != 'Windows':
                    autotools.fpic = self.options.fPIC

                if tools.os_info.is_windows:
                    self._patch_mingw()
                    make_target = "sharedlib_win32" if self.options.shared else "staticlib_win32"
                elif tools.os_info.is_macos:
                    self._patch_macos()
                    autotools.include_paths.append(os.getcwd())
                    make_target = "sharedlib_osx" if self.options.shared else "staticlib_osx"
                else:
                    self._patch_linux()
                    make_target = "sharedlib" if self.options.shared else "staticlib"

                autotools.make(target=make_target)

    def package(self):
        self.copy(pattern="*license*", dst="licenses", ignore_case=True, keep_path=False)

        include_folder = os.path.join(self._subfolder, "include")
        self.copy(pattern="*", dst="include", src=include_folder)

        media_folder = os.path.join(self._subfolder, "media")
        self.copy(pattern="*", dst="media", src=media_folder)

        if tools.os_info.is_windows:
            if self.settings.compiler == "Visual Studio":
                if self.settings.arch == 'x86_64':
                    folder = "Win64-visualStudio"
                else:
                    folder = "Win32-visualStudio"
            else:
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
        self.copy(pattern="*.dylib*", src=lib_folder, dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if tools.os_info.is_windows:
            if not self.options.shared:
                self.cpp_info.defines.extend(['_IRR_STATIC_LIB_'])
                self.cpp_info.libs.extend(['opengl32', 'winmm'])
                if self.settings.compiler != "Visual Studio":
                    self.cpp_info.libs.extend(['m'])
        elif tools.os_info.is_macos:
            frameworks = ['Cocoa', 'Carbon', 'OpenGL', 'IOKit']
            for framework in frameworks:
                self.cpp_info.exelinkflags.append("-framework %s" % framework)
            self.cpp_info.sharedlinkflags = self.cpp_info.exelinkflags
        else:
            if not self.options.shared:
                self.cpp_info.libs.extend(['GL', 'Xxf86vm', 'Xext', 'X11', 'Xcursor'])

        self.output.info(self.cpp_info.libs)
