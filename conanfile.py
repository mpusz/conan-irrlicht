import os
import shutil

from conan import ConanFile
from conan.tools.cmake import cmake_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools
from conan.tools.files import chdir, collect_libs, copy, get, replace_in_file, patch
from conan.tools.microsoft import MSBuildToolchain, MSBuild
from conan.tools.system.package_manager import Apt, Yum

required_conan_version = ">=2.0.2"


class IrrlichtConan(ConanFile):
    name = "irrlicht"
    version = "1.8.4"
    license = "http://irrlicht.sourceforge.net/?page_id=294"
    url = "https://github.com/mpusz/conan-irrlicht"
    description = "An open source high performance realtime 3D engine written in C++"
    exports = "LICENSE.md"
    exports_sources = ["*.patch"]
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "directx9": [True, False],
    }
    default_options = {"shared": False, "fPIC": True, "directx9": False}
    package_type = "library"

    @property
    def _subfolder(self):
        return "irrlicht-%s" % self.version

    def _patch_incorrect_template(self):
        replace_in_file(
            self,
            os.path.join(self.source_folder, "include", "irrXML.h"),
            "xmlChar<T>",
            "xmlChar",
        )

    def _patch_register(self):
        replace_in_file(
            self,
            os.path.join(self.source_folder, "source", "Irrlicht", "CMY3DHelper.h"),
            "register int",
            "int",
        )
        replace_in_file(
            self,
            os.path.join(
                self.source_folder, "source", "Irrlicht", "CColorConverter.cpp"
            ),
            "register u32",
            "u32",
        )

    def _patch_add_shared_lib_links(self):
        # Irrlicht does that only for install step and without the links create Conan does not link correctly
        replace_in_file(
            self,
            "Makefile",
            "cp $(SHARED_FULLNAME) $(LIB_PATH)",
            """cp $(SHARED_FULLNAME) $(LIB_PATH)
	cd $(LIB_PATH) && ln -s -f $(SHARED_FULLNAME) $(SONAME)
	cd $(LIB_PATH) && ln -s -f $(SONAME) $(SHARED_LIB)""",
        )

    def _patch_change_sysctl(self):
        replace_in_file(self, "COSOperator.cpp", "<sys/sysctl.h>", "<linux/sysctl.h>")

    def _patch_msvc(self):
        # Allows to inject platform toolset, and props file generated by MSBuildToolchain & MSBuildDeps
        # TODO: to remove once https://github.com/conan-io/conan/pull/12817 available in conan client
        vcxproj_files = ["Irrlicht11.0.vcxproj"]
        platform_toolset = MSBuildToolchain(self).toolset
        import_conan_generators = ""
        for props_file in ["conantoolchain.props"]:
            props_path = os.path.join(self.generators_folder, props_file)
            if os.path.exists(props_path):
                import_conan_generators += f'<Import Project="{props_path}" />'
        for vcxproj_file in vcxproj_files:
            replace_in_file(
                self,
                vcxproj_file,
                "<PlatformToolset>Windows7.1SDK</PlatformToolset>",
                f"<PlatformToolset>{platform_toolset}</PlatformToolset>",
            )
            if props_path:
                replace_in_file(
                    self,
                    vcxproj_file,
                    '<Import Project="$(VCTargetsPath)\\Microsoft.Cpp.targets" />',
                    f'{import_conan_generators}<Import Project="$(VCTargetsPath)\\Microsoft.Cpp.targets" />',
                )
            replace_in_file(self, vcxproj_file, "; _ITERATOR_DEBUG_LEVEL=0", "")

    def _patch_mingw(self):
        # patch library name
        replace_in_file(self, "Makefile", "-ld3dx9d", "-ld3dx9")

    def _patch_macos(self):
        # fix compilation
        shutil.move("Irrlicht.cpp", "Irrlicht.mm")
        shutil.move("COpenGLDriver.cpp", "COpenGLDriver.mm")
        # comment unsupported options
        replace_in_file(
            self,
            "Makefile",
            "staticlib_osx sharedlib_osx: LDFLAGS += --no-export-all-symbols --add-stdcall-alias",
            "#staticlib_osx sharedlib_osx: LDFLAGS += --no-export-all-symbols --add-stdcall-alias",
        )
        # uncomment Macosx linker flags
        replace_in_file(
            self, "Makefile", "#sharedlib_osx: LDFLAGS", "sharedlib_osx: LDFLAGS"
        )
        # add Macosx specific sources
        replace_in_file(
            self,
            "Makefile",
            "Irrlicht.o os.o",
            "Irrlicht.o os.o MacOSX/CIrrDeviceMacOSX.o MacOSX/OSXClipboard.o MacOSX/AppDelegate.o",
        )
        # fix window creation
        patch(
            self,
            base_path=self.source_folder,
            patch_file=os.path.join(
                self.export_sources_folder, "patches", "osx-window-creation.patch"
            ),
        )
        # fix shared libraries
        self._patch_add_shared_lib_links()

    def _patch_linux(self):
        # fix shared libraries
        self._patch_add_shared_lib_links()
        self._patch_change_sysctl()

    @property
    def _msbuild_configuration(self):
        build_type = "Debug" if self.settings.build_type == "Debug" else "Release"
        if self.options.shared:
            return build_type
        else:
            return "Static lib - %s" % build_type

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        else:
            del self.options.directx9

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(
            self,
            "http://downloads.sourceforge.net/irrlicht/irrlicht-%s.zip" % self.version,
            sha1="38bf0223fe868d243d6a39d0dc191c8df6e03b3b",
            strip_root=True,
        )
        self._patch_incorrect_template()
        self._patch_register()

    def system_requirements(self):
        Apt(self).install(
            ["libgl1-mesa-dev", "libxcursor-dev", "libxxf86vm-dev", "libxext-dev"]
        )
        if self.settings.arch == "x86":
            arch_suffix = ".i686"
        elif self.settings.arch == "x86_64":
            arch_suffix = ".x86_64"
        Yum(self).install(
            ["mesa-libGL-devel%s" % arch_suffix, "libXcursor-devel%s" % arch_suffix]
        )

    def generate(self):
        if self.settings.compiler == "msvc":
            tc = MSBuildToolchain(self)
            tc.configuration = self._msbuild_configuration
            if self.options.directx9 == False:
                tc.preprocessor_definitions["NO_IRR_COMPILE_WITH_DIRECT3D_9_"] = "1"
            tc.generate()
        else:
            tc = AutotoolsToolchain(self)
            compiler = self.settings.compiler
            if compiler == "clang":
                tc.extra_cflags.append("-Wno-register")
                tc.extra_cxxflags.append("-Wno-register")
            if self.settings.os == "Macos":
                tc.configure_args.append("--includedir=${prefix}")
            tc.generate()

    def build(self):
        with chdir(self, os.path.join(self.source_folder, "source", "Irrlicht")):
            if self.settings.compiler == "msvc":
                self._patch_msvc()
                msbuild = MSBuild(self)
                msbuild.build_type = self._msbuild_configuration
                msbuild.build("Irrlicht11.0.sln")
            else:
                autotools = Autotools(self)
                if self.settings.os == "Windows":
                    self._patch_mingw()
                    make_target = (
                        "sharedlib_win32" if self.options.shared else "staticlib_win32"
                    )
                elif self.settings.os == "Macos":
                    self._patch_macos()
                    make_target = (
                        "sharedlib_osx" if self.options.shared else "staticlib_osx"
                    )
                else:
                    self._patch_linux()
                    make_target = "sharedlib" if self.options.shared else "staticlib"
                autotools.make(target=make_target)

    def package(self):
        copy(
            self,
            "*license*",
            self.source_folder,
            os.path.join(self.package_folder, "licenses"),
            ignore_case=True,
            keep_path=False,
        )

        include_folder = os.path.join(self.source_folder, "include")
        self.output.info(include_folder)
        copy(self, "*", include_folder, os.path.join(self.package_folder, "include"))

        media_folder = os.path.join(self.source_folder, "media")
        copy(self, "*", media_folder, os.path.join(self.package_folder, "media"))

        if self.settings.os == "Windows":
            if self.settings.compiler == "msvc":
                if self.settings.arch == "x86_64":
                    folder = "Win64-visualStudio"
                else:
                    folder = "Win32-visualStudio"
            else:
                folder = "Win32-gcc"
        elif self.settings.os == "Macos":
            folder = "MacOSX"
        else:
            folder = "Linux"

        bin_src = os.path.join(self.source_folder, "bin", folder)
        lib_src = os.path.join(self.source_folder, "lib", folder)
        bin_dst = os.path.join(self.package_folder, "bin")
        lib_dst = os.path.join(self.package_folder, "lib")

        copy(self, "*.dll", bin_src, bin_dst, keep_path=False)
        copy(self, "*.lib", lib_src, lib_dst, keep_path=False)
        copy(self, "*.a", lib_src, lib_dst, keep_path=False)
        copy(self, "*.so*", lib_src, lib_dst, keep_path=False)
        copy(self, "*.dylib*", lib_src, lib_dst, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        self.output.info(self.cpp_info.libs)
        self.cpp_info.resdirs = ["media"]
        if self.settings.os == "Windows":
            if not self.options.shared:
                self.cpp_info.defines.extend(["_IRR_STATIC_LIB_"])
                self.cpp_info.system_libs.extend(["opengl32", "winmm"])
                if self.settings.compiler != "msvc":
                    self.cpp_info.system_libs.extend(["m"])
        elif self.settings.os == "Macos":
            frameworks = ["Cocoa", "Carbon", "OpenGL", "IOKit"]
            for framework in frameworks:
                self.cpp_info.exelinkflags.append("-framework %s" % framework)
            self.cpp_info.sharedlinkflags = self.cpp_info.exelinkflags
        else:
            if not self.options.shared:
                self.cpp_info.system_libs.extend(
                    ["GL", "Xxf86vm", "Xext", "X11", "Xcursor"]
                )

        if self.settings.compiler == "clang":
            self.cpp_info.cxxflags = ["-Wno-register"]
