from register_part import RegisterPart


def main():

    print(
        "KiCAD Library Manager V0.1"
    )

    print()

    part_name = input(
        "Part Name : "
    ).strip()

    category = input(
        "Category : "
    ).strip()

    symbol_file = input(
        "Symbol File : "
    ).strip()

    footprint_file = input(
        "Footprint File : "
    ).strip()

    model_file = input(
        "STEP File : "
    ).strip()

    datasheet_url = input(
        "Datasheet URL : "
    ).strip()

    mgr = RegisterPart(
        "config.json"
    )

    mgr.register(
        part_name=part_name,
        category=category,
        symbol_file=symbol_file,
        footprint_file=footprint_file,
        model_file=model_file,
        datasheet_url=datasheet_url
    )

    print()
    print(
        "Register Complete"
    )


if __name__ == "__main__":
    main()