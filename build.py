from cpt.packager import ConanMultiPackager
from collections import defaultdict

if __name__ == "__main__":
    builder = ConanMultiPackager(curpage="x86", total_pages=2)
    named_builds = defaultdict(list)
    builder.add_common_builds(shared_option_name="mypackagename:shared", pure_c=False)
    for settings, options, env_vars, build_requires, reference in builder.items:
        named_builds[settings['arch']].append([settings, options, env_vars, build_requires, reference])
    builder.named_builds = named_builds
    builder.run()
