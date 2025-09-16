from models.database import create_tables


def main() -> None:
    create_tables()
    print("DB creada")


if __name__ == "__main__":
    main()


