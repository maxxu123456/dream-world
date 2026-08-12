import json
from pathlib import Path

MASK = 2147483647  # 0x7FFFFFFF


def calculate_pid(friend_code: str) -> int:
    friend_code = friend_code.replace("-", "").replace(" ", "")
    
    if not len(friend_code) == 12:
        raise ValueError("Friend Code must contain 12 digits.")
    
    if not friend_code.isdigit():
        raise ValueError("Friend Code must contain only digits.")
    
    num_fc = int(friend_code)
    
    # The upper seven bits are a game-code-specific checksum. Checking only its
    # range keeps this utility compatible with every Black/White/B2/W2 region.
    checksum = num_fc >> 32 & 0xFFFFFFFF
    if checksum > 0x7F or (num_fc & MASK) == 0:
        raise ValueError("Friend Code is invalid. Please double-check your Pal Pad.")
    
    return num_fc & MASK


def main():
    print("Error 60000 Fix\n")

    friend_code = input("Enter your in-game Friend Code from your Pal Pad (with or without dashes): ")

    pid = calculate_pid(friend_code)

    print(f"\nCalculated PID: {pid}")

    root_dir = Path(__file__).resolve().parent.parent
    save_dir = root_dir / "save_data"

    files = sorted(save_dir.glob("WFC-*.json"))

    if not files:
        print(f"No WFC profiles found in {save_dir}")
        return

    if len(files) > 1:
        print(
            "Multiple WFC accounts were found. This legacy utility cannot safely "
            "identify which account owns the code, so nothing was changed. Use "
            "the desktop app with the matching save instead."
        )
        return

    print("Found 1 save file.\n")

    for file_path in files:
        with open(file_path, encoding="UTF-8") as f:
            data = json.load(f)

        profiles = data.get("profiles", {})
        updated = 0

        for profile_name, profile in profiles.items():
            old_pid = profile.get("id")
            profile["id"] = pid

            print(
                f"{file_path.name}: "
                f"{profile_name} "
                f"({old_pid} -> {pid})"
            )

            updated += 1

        if updated:
            with open(file_path, "w", encoding="UTF-8") as f:
                json.dump(data, f, indent=2)

    print("\nDone.")
    print("Restart the game sync server and try connecting again.")


if __name__ == "__main__":
    main()
