from cpt.packager import ConanMultiPackager

if __name__ == "__main__":
    builder = ConanMultiPackager(username = "mpusz", login_username = "mpusz",
                                 channel = "testing",
                                 stable_branch_pattern = r"v\d+\.\d+\.\d+.*",
                                 upload = "https://api.bintray.com/conan/mpusz/conan-mpusz",
                                 remotes = None,
                                 build_policy = None,
                                 upload_dependencies=None)
    builder.add_common_builds(pure_c=False)
    builder.run()
