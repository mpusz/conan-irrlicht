from cpt.packager import ConanMultiPackager

if __name__ == "__main__":
    builder = ConanMultiPackager(curpage=1, total_pages=2)
    builder.add_common_builds(shared_option_name="irrlicht:shared", pure_c=False)
    builder.run()
