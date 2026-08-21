from getpass import getpass

from app.core.security import hash_password


def main() -> None:
    first = getpass("MarketSense password: ")
    second = getpass("Confirm password: ")
    if first != second:
        raise SystemExit("Passwords do not match")
    print(hash_password(first))


if __name__ == "__main__":
    main()
