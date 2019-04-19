from cpt.packager import ConanMultiPackager

if __name__ == "__main__":
    builder = ConanMultiPackager(
        # package id
        username = "mpusz",
        channel = "testing",
        stable_branch_pattern = r"v\d+\.\d+\.\d+.*",
        
        # dependencies
        remotes = None,
        build_policy = None,
        upload_dependencies=False,

        # build configurations
        archs = ["x86_64"],

        # package upload (REMEMBER to set CONAN_PASSWORD environment variable in Travis CI and AppVeyor)
        login_username = "mpusz",
        upload = "https://api.bintray.com/conan/mpusz/conan-mpusz"
    )
    builder.add_common_builds(pure_c=False)
    builder.run()
