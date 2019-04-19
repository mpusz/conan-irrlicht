from cpt.packager import ConanMultiPackager

if __name__ == "__main__":
    builder = ConanMultiPackager(username = "mpusz", login_username = "mpusz",
                                 channel = "testing",
                                 stable_branch_pattern = r"v\d+\.\d+\.\d+.*",
                                 archs = ["x86_64"],
                                 remotes = None,
                                 build_policy = None,
                                 upload = "https://api.bintray.com/conan/mpusz/conan-mpusz",
                                 upload_dependencies=False)
    builder.add_common_builds(pure_c=False)
    builder.run()
