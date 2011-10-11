import shutil

def zip_build(build_plan):
    base_name = build_plan.get_zip_base_name_shutil()
    shutil.make_archive(base_name=base_name,
                        format="zip",
                        root_dir=build_plan.build_directory)

